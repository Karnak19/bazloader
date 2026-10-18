// Host tests for src/ble_logic.cpp: `pio test -e native`.
// Byte vectors match web/src/ble/protocol.test.ts.
#include <unity.h>

#include <string.h>

#include <initializer_list>

#include "ble_logic.h"
#include "config.h"
#include "run.h"
#include "settings.h"

void setUp() {}
void tearDown() {}

static const RunConfig kCfg = {SLOWDOWN_N, JAM_TIMEOUT_MS, FIRST_BB_TIMEOUT_MS, DONE_HOLD_MS};

// The loop's hooks, backed by a real Run and the real validation (no store).
struct FakeActions : BleActions {
  Run run{kCfg};
  ConfigV1 config = defaultConfig();
  Presets presets = defaultPresets();
  int stops = 0, gos = 0;

  State state() override { return run.state(); }
  uint16_t setTarget(uint16_t t) override { return run.setTarget(t); }
  void go() override {
    gos++;
    run.go(0, true);
  }
  void stop() override {
    stops++;
    run.stop();
  }
  void test(Speed speed) override { run.test(speed, true); }
  // Like main.cpp's setConfig: refused while the servo is driven.
  bool setConfig(const ConfigV1& c) override {
    if (run.speed() != Speed::Off || !configValid(c)) return false;
    config = c;
    return true;
  }
  bool setPresets(const Presets& p) override {
    if (!presetsValid(p)) return false;
    presets = p;
    return true;
  }
  BleValues values(uint32_t count = 0) {
    return {run.target(), count, run.state(), 7400, presets, config};
  }
};

// ---- parseWrite ----

static void test_target_decodes_little_endian() {
  const uint8_t b[] = {0x32, 0x00};  // 50
  BleRequest r = parseWrite(BleChar::Target, b, 2);
  TEST_ASSERT_EQUAL(BleRequest::SetTarget, r.kind);
  TEST_ASSERT_EQUAL_UINT16(50, r.target);
  const uint8_t big[] = {0x0f, 0x27};  // 9999
  TEST_ASSERT_EQUAL_UINT16(9999, parseWrite(BleChar::Target, big, 2).target);
}

static void test_wrong_lengths_are_ignored_and_refreshed() {
  const uint8_t b[12] = {CONFIG_VERSION};
  for (size_t len : {0u, 1u, 3u}) {
    BleRequest r = parseWrite(BleChar::Target, b, len);
    TEST_ASSERT_EQUAL(BleRequest::Refresh, r.kind);
    TEST_ASSERT_EQUAL(BleChar::Target, r.ch);
  }
  for (size_t len : {0u, 7u, 9u}) {
    TEST_ASSERT_EQUAL(BleRequest::Refresh, parseWrite(BleChar::Presets, b, len).kind);
  }
  for (size_t len : {1u, 10u, 12u}) {
    TEST_ASSERT_EQUAL(BleRequest::Refresh, parseWrite(BleChar::Config, b, len).kind);
  }
  TEST_ASSERT_EQUAL(BleRequest::None, parseWrite(BleChar::Command, b, 0).kind);
  TEST_ASSERT_EQUAL(BleRequest::None, parseWrite(BleChar::Command, b, 2).kind);
}

static void test_commands_and_unknown_command() {
  for (uint8_t c = 0; c <= 3; c++) {
    BleRequest r = parseWrite(BleChar::Command, &c, 1);
    TEST_ASSERT_EQUAL(BleRequest::RunCommand, r.kind);
    TEST_ASSERT_EQUAL(c, static_cast<uint8_t>(r.command));
  }
  for (uint8_t c : {4, 0x7f, 0xff}) {
    TEST_ASSERT_EQUAL(BleRequest::None, parseWrite(BleChar::Command, &c, 1).kind);
  }
}

static void test_presets_decode() {
  const uint8_t b[] = {0x1e, 0x00, 0x32, 0x00, 0x78, 0x00, 0x2c, 0x01};  // 30 50 120 300
  BleRequest r = parseWrite(BleChar::Presets, b, sizeof b);
  TEST_ASSERT_EQUAL(BleRequest::SetPresets, r.kind);
  const uint16_t want[] = {30, 50, 120, 300};
  TEST_ASSERT_EQUAL_UINT16_ARRAY(want, r.presets.values, 4);
}

// Same bytes as the defaults vector in protocol.test.ts.
static const uint8_t kDefaultConfig[] = {0x01, 0xdc, 0x05, 0x2c, 0x01, 0x64,
                                         0x00, 0x00, 0x04, 0xdc, 0x05};

static void test_config_decodes_from_unaligned_buffer() {
  uint8_t buf[sizeof kDefaultConfig + 1];
  memcpy(buf + 1, kDefaultConfig, sizeof kDefaultConfig);  // odd address on purpose
  BleRequest r = parseWrite(BleChar::Config, buf + 1, sizeof kDefaultConfig);
  TEST_ASSERT_EQUAL(BleRequest::SetConfig, r.kind);
  ConfigV1 d = defaultConfig();
  TEST_ASSERT_EQUAL_MEMORY(&d, &r.config, sizeof d);

  uint8_t neg[sizeof kDefaultConfig];
  memcpy(neg, kDefaultConfig, sizeof neg);
  neg[3] = 0xd4;  // -300
  neg[4] = 0xfe;
  TEST_ASSERT_EQUAL_INT16(-300, parseWrite(BleChar::Config, neg, sizeof neg).config.speed_full_offset_us);
}

static void test_config_version_2_is_ignored() {
  uint8_t b[sizeof kDefaultConfig];
  memcpy(b, kDefaultConfig, sizeof b);
  b[0] = 2;
  TEST_ASSERT_EQUAL(BleRequest::Refresh, parseWrite(BleChar::Config, b, sizeof b).kind);
}

// ---- applyBleRequest ----

static BleRequest targetWrite(uint16_t t) {
  uint8_t b[] = {static_cast<uint8_t>(t), static_cast<uint8_t>(t >> 8)};
  return parseWrite(BleChar::Target, b, 2);
}

static BleRequest command(Command c) {
  uint8_t b = static_cast<uint8_t>(c);
  return parseWrite(BleChar::Command, &b, 1);
}

static void test_target_write_applies_and_answers() {
  FakeActions a;
  TEST_ASSERT_EQUAL(FIELD_TARGET, applyBleRequest(targetWrite(120), a));
  TEST_ASSERT_EQUAL_UINT16(120, a.run.target());
  applyBleRequest(targetWrite(0), a);  // clamped
  TEST_ASSERT_EQUAL_UINT16(TARGET_MIN, a.run.target());
}

static void test_target_and_config_refused_during_a_run_answer_the_real_value() {
  FakeActions a;
  applyBleRequest(targetWrite(50), a);
  applyBleRequest(command(Command::Go), a);
  TEST_ASSERT_EQUAL(State::Running, a.run.state());

  BleOutbox box(COUNT_NOTIFY_THROTTLE_MS, BATTERY_NOTIFY_PERIOD_MS);
  box.start(a.values(), 0);
  box.force(applyBleRequest(targetWrite(300), a));
  TEST_ASSERT_EQUAL_UINT16(50, a.run.target());

  uint8_t c[sizeof kDefaultConfig];
  memcpy(c, kDefaultConfig, sizeof c);
  c[1] = 0xe0;  // neutral 1504
  box.force(applyBleRequest(parseWrite(BleChar::Config, c, sizeof c), a));
  TEST_ASSERT_EQUAL_UINT16(SERVO_NEUTRAL_US, a.config.servo_neutral_us);

  BleValues v = a.values();
  uint8_t fields = box.update(v, 1);
  TEST_ASSERT_EQUAL(FIELD_TARGET | FIELD_CONFIG, fields);
  uint8_t out[11];
  TEST_ASSERT_EQUAL(2, encodeField(FIELD_TARGET, v, out));
  TEST_ASSERT_EQUAL_UINT8(0x32, out[0]);  // the real 50 goes back, not 300
  TEST_ASSERT_EQUAL_UINT8(0x00, out[1]);
  TEST_ASSERT_EQUAL(11, encodeField(FIELD_CONFIG, v, out));
  TEST_ASSERT_EQUAL_MEMORY(kDefaultConfig, out, 11);
}

static void test_malformed_writes_change_nothing_and_answer() {
  FakeActions a;
  a.run.setTarget(77);
  const uint8_t three[] = {1, 2, 3};
  TEST_ASSERT_EQUAL(FIELD_TARGET, applyBleRequest(parseWrite(BleChar::Target, three, 3), a));
  TEST_ASSERT_EQUAL_UINT16(77, a.run.target());
  TEST_ASSERT_EQUAL(FIELD_PRESETS, applyBleRequest(parseWrite(BleChar::Presets, three, 3), a));
  uint8_t v2[sizeof kDefaultConfig];
  memcpy(v2, kDefaultConfig, sizeof v2);
  v2[0] = 2;
  v2[1] = 0xe0;
  TEST_ASSERT_EQUAL(FIELD_CONFIG, applyBleRequest(parseWrite(BleChar::Config, v2, sizeof v2), a));
  TEST_ASSERT_EQUAL_UINT16(SERVO_NEUTRAL_US, a.config.servo_neutral_us);
  uint8_t unknown = 9;
  TEST_ASSERT_EQUAL(0, applyBleRequest(parseWrite(BleChar::Command, &unknown, 1), a));
  TEST_ASSERT_EQUAL(State::Idle, a.run.state());
  TEST_ASSERT_EQUAL(0, a.gos + a.stops);
}

static void test_presets_taken_during_a_run() {
  FakeActions a;
  applyBleRequest(command(Command::Go), a);
  const uint8_t b[] = {10, 0, 20, 0, 30, 0, 40, 0};
  applyBleRequest(parseWrite(BleChar::Presets, b, sizeof b), a);
  TEST_ASSERT_EQUAL_UINT16(10, a.presets.values[0]);
}

static void test_commands_drive_the_run() {
  FakeActions a;
  applyBleRequest(command(Command::TestSlow), a);
  TEST_ASSERT_EQUAL(State::Testing, a.run.state());
  TEST_ASSERT_EQUAL(Speed::Slow, a.run.speed());
  applyBleRequest(command(Command::Stop), a);
  TEST_ASSERT_EQUAL(State::Idle, a.run.state());
  applyBleRequest(command(Command::Go), a);
  TEST_ASSERT_EQUAL(State::Running, a.run.state());
}

static void test_disconnect_stops_a_test_spin_only() {
  BleRequest disc;
  disc.kind = BleRequest::Disconnected;

  FakeActions a;
  applyBleRequest(command(Command::TestFull), a);
  TEST_ASSERT_EQUAL(Speed::Full, a.run.speed());
  applyBleRequest(disc, a);
  TEST_ASSERT_EQUAL(State::Idle, a.run.state());
  TEST_ASSERT_EQUAL(Speed::Off, a.run.speed());

  FakeActions b;
  applyBleRequest(command(Command::Go), b);
  applyBleRequest(disc, b);
  TEST_ASSERT_EQUAL(State::Running, b.run.state());  // a run ends on its own
  TEST_ASSERT_EQUAL(0, b.stops);
}

// ---- encodeField ----

static void test_encode_fields() {
  FakeActions a;
  BleValues v = a.values(70000);  // a count past uint16 saturates
  v.state = State::Testing;
  uint8_t out[11];
  TEST_ASSERT_EQUAL(2, encodeField(FIELD_COUNT, v, out));
  TEST_ASSERT_EQUAL_UINT8(0xff, out[0]);
  TEST_ASSERT_EQUAL_UINT8(0xff, out[1]);
  TEST_ASSERT_EQUAL(1, encodeField(FIELD_STATE, v, out));
  TEST_ASSERT_EQUAL_UINT8(6, out[0]);
  TEST_ASSERT_EQUAL(2, encodeField(FIELD_BATTERY, v, out));
  TEST_ASSERT_EQUAL_UINT8(0xe8, out[0]);  // 7400 = 0x1ce8
  TEST_ASSERT_EQUAL_UINT8(0x1c, out[1]);
  const uint8_t presets[] = {0x1e, 0x00, 0x32, 0x00, 0x78, 0x00, 0x2c, 0x01};
  TEST_ASSERT_EQUAL(8, encodeField(FIELD_PRESETS, v, out));
  TEST_ASSERT_EQUAL_MEMORY(presets, out, 8);
}

// ---- BleOutbox ----

static BleValues base() {
  return {50, 0, State::Idle, 7400, defaultPresets(), defaultConfig()};
}

static void test_nothing_to_send_when_nothing_changes() {
  BleOutbox box(50, 5000);
  BleValues v = base();
  box.start(v, 0);
  TEST_ASSERT_EQUAL(0, box.update(v, 10));
  TEST_ASSERT_EQUAL(0, box.update(v, 4999));
}

static void test_target_and_state_on_every_change() {
  BleOutbox box(50, 5000);
  BleValues v = base();
  box.start(v, 0);
  v.target = 51;  // e.g. an encoder detent
  TEST_ASSERT_EQUAL(FIELD_TARGET, box.update(v, 1));
  v.target = 52;
  TEST_ASSERT_EQUAL(FIELD_TARGET, box.update(v, 2));  // no throttle on target
  v.state = State::Testing;
  TEST_ASSERT_EQUAL(FIELD_STATE, box.update(v, 3));
  TEST_ASSERT_EQUAL(0, box.update(v, 4));
}

static void test_battery_every_period() {
  BleOutbox box(50, 5000);
  BleValues v = base();
  box.start(v, 0);
  TEST_ASSERT_EQUAL(0, box.update(v, 4999));
  TEST_ASSERT_EQUAL(FIELD_BATTERY, box.update(v, 5000));
  TEST_ASSERT_EQUAL(0, box.update(v, 9999));
  v.batteryMv = 0;  // USB
  TEST_ASSERT_EQUAL(FIELD_BATTERY, box.update(v, 10000));
}

static void test_presets_and_config_on_change() {
  BleOutbox box(50, 5000);
  BleValues v = base();
  box.start(v, 0);
  v.presets.values[2] = 99;
  v.config.slowdown_n = 7;
  TEST_ASSERT_EQUAL(FIELD_PRESETS | FIELD_CONFIG, box.update(v, 1));
  TEST_ASSERT_EQUAL(0, box.update(v, 2));
}

static void test_count_throttled_but_final_value_always_sent() {
  BleOutbox box(COUNT_NOTIFY_THROTTLE_MS, 100000);
  BleValues v = base();
  box.start(v, 0);
  v.state = State::Running;
  TEST_ASSERT_EQUAL(FIELD_STATE, box.update(v, 0));

  // A BB every 10 ms: at most one count notification per 50 ms.
  int sent = 0;
  uint32_t lastSent = 0;
  uint32_t now = 0;
  for (uint32_t c = 1; c <= 23; c++) {
    now = c * 10;
    v.count = c;
    if (box.update(v, now) & FIELD_COUNT) {
      sent++;
      lastSent = c;
    }
  }
  TEST_ASSERT_EQUAL(4, sent);  // at 50, 100, 150, 200 ms
  TEST_ASSERT_NOT_EQUAL(23, lastSent);

  // The count stops at 23 without a state change: it still goes out once the throttle allows.
  TEST_ASSERT_EQUAL(0, box.update(v, now + 1) & FIELD_COUNT);
  TEST_ASSERT_EQUAL(FIELD_COUNT, box.update(v, 250));
  TEST_ASSERT_EQUAL(0, box.update(v, 400));
}

static void test_final_count_goes_with_the_state_change() {
  BleOutbox box(COUNT_NOTIFY_THROTTLE_MS, 100000);
  BleValues v = base();
  v.state = State::Running;
  box.start(v, 0);
  v.count = 49;
  TEST_ASSERT_EQUAL(FIELD_COUNT, box.update(v, 100));
  v.count = 50;  // last BB 1 ms later, inside the throttle window
  v.state = State::Done;
  TEST_ASSERT_EQUAL(FIELD_COUNT | FIELD_STATE, box.update(v, 101));
}

static void test_forced_fields_go_once() {
  BleOutbox box(50, 5000);
  BleValues v = base();
  box.start(v, 0);
  box.force(FIELD_TARGET);
  TEST_ASSERT_EQUAL(FIELD_TARGET, box.update(v, 1));
  TEST_ASSERT_EQUAL(0, box.update(v, 2));
}

int main(int, char**) {
  UNITY_BEGIN();
  RUN_TEST(test_target_decodes_little_endian);
  RUN_TEST(test_wrong_lengths_are_ignored_and_refreshed);
  RUN_TEST(test_commands_and_unknown_command);
  RUN_TEST(test_presets_decode);
  RUN_TEST(test_config_decodes_from_unaligned_buffer);
  RUN_TEST(test_config_version_2_is_ignored);
  RUN_TEST(test_target_write_applies_and_answers);
  RUN_TEST(test_target_and_config_refused_during_a_run_answer_the_real_value);
  RUN_TEST(test_malformed_writes_change_nothing_and_answer);
  RUN_TEST(test_presets_taken_during_a_run);
  RUN_TEST(test_commands_drive_the_run);
  RUN_TEST(test_disconnect_stops_a_test_spin_only);
  RUN_TEST(test_encode_fields);
  RUN_TEST(test_nothing_to_send_when_nothing_changes);
  RUN_TEST(test_target_and_state_on_every_change);
  RUN_TEST(test_battery_every_period);
  RUN_TEST(test_presets_and_config_on_change);
  RUN_TEST(test_count_throttled_but_final_value_always_sent);
  RUN_TEST(test_final_count_goes_with_the_state_change);
  RUN_TEST(test_forced_fields_go_once);
  return UNITY_END();
}
