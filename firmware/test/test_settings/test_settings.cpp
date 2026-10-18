// Host tests for src/settings.cpp (and the runtime-config parts of run.cpp): `pio test -e native`.
#include <string.h>
#include <unity.h>

#include "config.h"
#include "run.h"
#include "settings.h"

// In-memory Store: up to three keys, counts the writes.
struct FakeStore : Store {
  struct Entry {
    const char* key = nullptr;
    uint8_t data[32];
    size_t len = 0;
  };
  Entry entries[3];
  int writes = 0;

  Entry* find(const char* key, bool create) {
    for (Entry& e : entries) {
      if (e.key && strcmp(e.key, key) == 0) return &e;
    }
    if (!create) return nullptr;
    for (Entry& e : entries) {
      if (!e.key) {
        e.key = key;
        return &e;
      }
    }
    return nullptr;
  }
  void put(const char* key, const void* buf, size_t len) {
    Entry* e = find(key, true);
    memcpy(e->data, buf, len);
    e->len = len;
  }
  size_t read(const char* key, void* buf, size_t size) override {
    Entry* e = find(key, false);
    if (!e) return 0;
    if (e->len <= size) memcpy(buf, e->data, e->len);
    return e->len;
  }
  void write(const char* key, const void* buf, size_t len) override {
    writes++;
    put(key, buf, len);
  }
};

static ConfigV1 validConfig() {
  ConfigV1 c = {CONFIG_VERSION, 1520, 250, 80, 1, 6, 2000};
  return c;
}

static void assertDefaults(const ConfigV1& c) {
  ConfigV1 d = defaultConfig();
  TEST_ASSERT_EQUAL_MEMORY(&d, &c, sizeof c);
  TEST_ASSERT_EQUAL_UINT16(1500, c.servo_neutral_us);
}

void setUp() {}
void tearDown() {}

// ---- Loading ----

static void test_valid_blobs_load() {
  FakeStore store;
  ConfigV1 c = validConfig();
  store.put(KEY_CONFIG, &c, sizeof c);
  uint16_t presets[4] = {10, 20, 40, 80};
  store.put(KEY_PRESETS, presets, sizeof presets);
  uint16_t target = 777;
  store.put(KEY_TARGET, &target, sizeof target);

  Settings s(store, TARGET_SAVE_DELAY_MS);
  LoadReport r = s.load();
  TEST_ASSERT_EQUAL(LoadResult::Ok, r.config);
  TEST_ASSERT_EQUAL(LoadResult::Ok, r.presets);
  TEST_ASSERT_EQUAL(LoadResult::Ok, r.target);
  TEST_ASSERT_EQUAL_MEMORY(&c, &s.config(), sizeof c);
  TEST_ASSERT_EQUAL_UINT16_ARRAY(presets, s.presets().values, 4);
  TEST_ASSERT_EQUAL_UINT16(777, s.target());
  TEST_ASSERT_EQUAL(0, store.writes);  // loading never writes
}

static void test_empty_store_gives_defaults() {
  FakeStore store;
  Settings s(store, TARGET_SAVE_DELAY_MS);
  LoadReport r = s.load();
  TEST_ASSERT_EQUAL(LoadResult::Missing, r.config);
  TEST_ASSERT_EQUAL(LoadResult::Missing, r.presets);
  TEST_ASSERT_EQUAL(LoadResult::Missing, r.target);
  assertDefaults(s.config());
  uint16_t expected[4] = {30, 50, 120, 300};
  TEST_ASSERT_EQUAL_UINT16_ARRAY(expected, s.presets().values, 4);
  TEST_ASSERT_EQUAL_UINT16(DEFAULT_TARGET, s.target());
}

static void test_wrong_version_gives_defaults() {
  FakeStore store;
  ConfigV1 c = validConfig();
  c.version = CONFIG_VERSION + 1;
  store.put(KEY_CONFIG, &c, sizeof c);
  Settings s(store, TARGET_SAVE_DELAY_MS);
  TEST_ASSERT_EQUAL(LoadResult::BadVersion, s.load().config);
  assertDefaults(s.config());
}

static void test_wrong_length_gives_defaults() {
  ConfigV1 c = validConfig();
  ConfigV1 out;
  TEST_ASSERT_EQUAL(LoadResult::BadLength, parseConfig(&c, sizeof c - 1, &out));
  assertDefaults(out);

  // Longer than any valid blob: the store doesn't even copy it.
  FakeStore store;
  uint8_t big[20] = {CONFIG_VERSION};
  store.put(KEY_CONFIG, big, sizeof big);
  uint16_t shortPresets[3] = {10, 20, 30};
  store.put(KEY_PRESETS, shortPresets, sizeof shortPresets);
  uint8_t oneByte = 5;
  store.put(KEY_TARGET, &oneByte, 1);
  Settings s(store, TARGET_SAVE_DELAY_MS);
  LoadReport r = s.load();
  TEST_ASSERT_EQUAL(LoadResult::BadLength, r.config);
  TEST_ASSERT_EQUAL(LoadResult::BadLength, r.presets);
  TEST_ASSERT_EQUAL(LoadResult::BadLength, r.target);
  assertDefaults(s.config());
  TEST_ASSERT_EQUAL_UINT16(30, s.presets().values[0]);
  TEST_ASSERT_EQUAL_UINT16(DEFAULT_TARGET, s.target());
}

// Each field just outside its range rejects the whole blob.
static void test_out_of_range_field_gives_defaults() {
  ConfigV1 bad[9];
  for (ConfigV1& c : bad) c = validConfig();
  bad[0].servo_neutral_us = 999;
  bad[1].servo_neutral_us = 2001;
  bad[2].speed_full_offset_us = 501;
  bad[3].speed_full_offset_us = -501;
  bad[4].speed_slow_offset_us = 501;
  bad[5].reverse = 2;
  bad[6].jam_timeout_ms = 299;
  bad[7].jam_timeout_ms = 10001;
  bad[8].speed_slow_offset_us = -501;
  for (const ConfigV1& c : bad) {
    ConfigV1 out;
    TEST_ASSERT_EQUAL(LoadResult::OutOfRange, parseConfig(&c, sizeof c, &out));
    assertDefaults(out);
  }
  // The edges themselves are accepted.
  ConfigV1 edge = {CONFIG_VERSION, 1000, -500, 500, 0, 0, 300};
  TEST_ASSERT_TRUE(configValid(edge));
  edge = {CONFIG_VERSION, 2000, 500, -500, 1, 255, 10000};
  TEST_ASSERT_TRUE(configValid(edge));
  TEST_ASSERT_TRUE(configValid(defaultConfig()));

  uint16_t target = 10000;
  uint16_t out;
  TEST_ASSERT_EQUAL(LoadResult::OutOfRange, parseTarget(&target, sizeof target, &out));
  TEST_ASSERT_EQUAL_UINT16(DEFAULT_TARGET, out);
  target = 0;
  TEST_ASSERT_EQUAL(LoadResult::OutOfRange, parseTarget(&target, sizeof target, &out));
}

static void test_presets_validation() {
  Presets p = {{1, 50, 120, 9999}};
  TEST_ASSERT_TRUE(presetsValid(p));
  p.values[0] = 0;
  TEST_ASSERT_FALSE(presetsValid(p));
  p.values[0] = 30;
  p.values[3] = 10000;
  TEST_ASSERT_FALSE(presetsValid(p));

  Presets out;
  TEST_ASSERT_EQUAL(LoadResult::OutOfRange, parsePresets(&p, sizeof p, &out));
  TEST_ASSERT_EQUAL_UINT16(300, out.values[3]);  // all defaults, not just the bad one
  TEST_ASSERT_EQUAL_UINT16(30, out.values[0]);

  FakeStore store;
  Settings s(store, TARGET_SAVE_DELAY_MS);
  s.load();
  TEST_ASSERT_FALSE(s.setPresets(p));
  TEST_ASSERT_EQUAL(0, store.writes);
  TEST_ASSERT_EQUAL_UINT16(300, s.presets().values[3]);
}

// ---- Writes ----

static void test_presets_written_only_on_change() {
  FakeStore store;
  Settings s(store, TARGET_SAVE_DELAY_MS);
  s.load();
  TEST_ASSERT_TRUE(s.setPresets(defaultPresets()));  // same values: no write
  TEST_ASSERT_EQUAL(0, store.writes);
  Presets p = {{10, 20, 40, 80}};
  TEST_ASSERT_TRUE(s.setPresets(p));
  TEST_ASSERT_EQUAL(1, store.writes);
  TEST_ASSERT_EQUAL_UINT16(40, s.presets().values[2]);
  TEST_ASSERT_TRUE(s.setPresets(p));
  TEST_ASSERT_EQUAL(1, store.writes);

  // And they come back after a "power cycle".
  Settings again(store, TARGET_SAVE_DELAY_MS);
  TEST_ASSERT_EQUAL(LoadResult::Ok, again.load().presets);
  TEST_ASSERT_EQUAL_UINT16_ARRAY(p.values, again.presets().values, 4);
}

static void test_config_written_only_on_change_and_reloads() {
  FakeStore store;
  Settings s(store, TARGET_SAVE_DELAY_MS);
  s.load();
  TEST_ASSERT_TRUE(s.setConfig(defaultConfig(), false));
  TEST_ASSERT_EQUAL(0, store.writes);
  ConfigV1 c = validConfig();
  TEST_ASSERT_TRUE(s.setConfig(c, false));
  TEST_ASSERT_EQUAL(1, store.writes);
  Settings again(store, TARGET_SAVE_DELAY_MS);
  TEST_ASSERT_EQUAL(LoadResult::Ok, again.load().config);
  TEST_ASSERT_EQUAL_MEMORY(&c, &again.config(), sizeof c);
}

static void test_config_refused_while_running_or_invalid() {
  FakeStore store;
  Settings s(store, TARGET_SAVE_DELAY_MS);
  s.load();
  TEST_ASSERT_FALSE(s.setConfig(validConfig(), true));
  assertDefaults(s.config());
  ConfigV1 bad = validConfig();
  bad.jam_timeout_ms = 100;
  TEST_ASSERT_FALSE(s.setConfig(bad, false));
  bad = validConfig();
  bad.version = 2;
  TEST_ASSERT_FALSE(s.setConfig(bad, false));
  assertDefaults(s.config());
  TEST_ASSERT_EQUAL(0, store.writes);

  // The run refuses new timing during a run too, and takes it when stopped.
  Run run({SLOWDOWN_N, JAM_TIMEOUT_MS, FIRST_BB_TIMEOUT_MS, DONE_HOLD_MS});
  run.setTarget(50);
  run.go(0, true);
  TEST_ASSERT_FALSE(run.setTiming(10, 3000));
  run.update(10, 41);  // 9 left: still full speed with N=4
  TEST_ASSERT_EQUAL(Speed::Full, run.speed());
  run.stop();
  TEST_ASSERT_TRUE(run.setTiming(10, 3000));
  run.go(100, true);
  run.update(110, 40);  // 10 left: slow with N=10
  TEST_ASSERT_EQUAL(Speed::Slow, run.speed());
  run.update(110 + 2999, 40);
  TEST_ASSERT_EQUAL(Speed::Slow, run.speed());  // jam timeout is now 3000 ms
  run.update(110 + 3000, 40);
  TEST_ASSERT_EQUAL(Speed::Off, run.speed());
}

// ---- Target debounce ----

static void test_target_spin_saves_once_after_delay() {
  FakeStore store;
  Settings s(store, TARGET_SAVE_DELAY_MS);
  s.load();
  // 10 s of encoder spin, a new target every 30 ms.
  uint32_t now = 1000;
  uint16_t target = DEFAULT_TARGET;
  for (int i = 0; i < 333; i++) {
    target = target + 3;
    TEST_ASSERT_FALSE(s.updateTarget(target, now));
    now += 30;
  }
  uint32_t lastChange = now - 30;
  // Loop passes keep polling with the same target.
  for (; now < lastChange + TARGET_SAVE_DELAY_MS; now += 10) {
    TEST_ASSERT_FALSE(s.updateTarget(target, now));
  }
  TEST_ASSERT_EQUAL(0, store.writes);
  TEST_ASSERT_TRUE(s.updateTarget(target, lastChange + TARGET_SAVE_DELAY_MS));
  TEST_ASSERT_EQUAL(1, store.writes);
  for (int i = 0; i < 100; i++) s.updateTarget(target, now + i * 100);
  TEST_ASSERT_EQUAL(1, store.writes);  // no more writes while it stays put

  Settings again(store, TARGET_SAVE_DELAY_MS);
  again.load();
  TEST_ASSERT_EQUAL_UINT16(target, again.target());
}

static void test_target_change_resets_the_timer() {
  FakeStore store;
  Settings s(store, TARGET_SAVE_DELAY_MS);
  s.load();
  s.updateTarget(60, 0);
  s.updateTarget(60, 1999);
  s.updateTarget(70, 1999);  // changed 1 ms before the save: the timer restarts
  TEST_ASSERT_FALSE(s.updateTarget(70, 2000));
  TEST_ASSERT_FALSE(s.updateTarget(70, 3998));
  TEST_ASSERT_TRUE(s.updateTarget(70, 3999));
  TEST_ASSERT_EQUAL(1, store.writes);
  TEST_ASSERT_EQUAL_UINT16(70, s.target());
}

static void test_target_back_to_saved_value_is_not_written() {
  FakeStore store;
  Settings s(store, TARGET_SAVE_DELAY_MS);
  s.load();
  s.updateTarget(DEFAULT_TARGET + 1, 0);
  s.updateTarget(DEFAULT_TARGET, 500);
  TEST_ASSERT_FALSE(s.updateTarget(DEFAULT_TARGET, 5000));
  TEST_ASSERT_EQUAL(0, store.writes);
}

// ---- Runtime servo pulse ----

static void test_servo_pulse_uses_runtime_config() {
  ConfigV1 c = {CONFIG_VERSION, 1520, 250, 80, 0, 4, 1500};
  TEST_ASSERT_EQUAL_UINT16(1770, servoPulseUs(Speed::Full, c));
  TEST_ASSERT_EQUAL_UINT16(1600, servoPulseUs(Speed::Slow, c));
  TEST_ASSERT_EQUAL_UINT16(0, servoPulseUs(Speed::Off, c));
  c.reverse = 1;
  TEST_ASSERT_EQUAL_UINT16(1270, servoPulseUs(Speed::Full, c));
  TEST_ASSERT_EQUAL_UINT16(1440, servoPulseUs(Speed::Slow, c));

  // Loaded from the store, the same numbers come out.
  FakeStore store;
  store.put(KEY_CONFIG, &c, sizeof c);
  Settings s(store, TARGET_SAVE_DELAY_MS);
  s.load();
  TEST_ASSERT_EQUAL_UINT16(1270, servoPulseUs(Speed::Full, s.config()));

  // Stop duty: no pulse by default, else the runtime neutral.
  uint32_t expected = SERVO_STOP_NEUTRAL ? servoDuty(1520, SERVO_LEDC_BITS) : 0;
  TEST_ASSERT_EQUAL_UINT32(expected, servoStopDuty(1520));
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_valid_blobs_load);
  RUN_TEST(test_empty_store_gives_defaults);
  RUN_TEST(test_wrong_version_gives_defaults);
  RUN_TEST(test_wrong_length_gives_defaults);
  RUN_TEST(test_out_of_range_field_gives_defaults);
  RUN_TEST(test_presets_validation);
  RUN_TEST(test_presets_written_only_on_change);
  RUN_TEST(test_config_written_only_on_change_and_reloads);
  RUN_TEST(test_config_refused_while_running_or_invalid);
  RUN_TEST(test_target_spin_saves_once_after_delay);
  RUN_TEST(test_target_change_resets_the_timer);
  RUN_TEST(test_target_back_to_saved_value_is_not_written);
  RUN_TEST(test_servo_pulse_uses_runtime_config);
  return UNITY_END();
}
