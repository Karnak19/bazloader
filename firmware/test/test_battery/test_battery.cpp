// Host tests for src/battery.cpp (and the LOW_BATT abort in src/run.cpp): `pio test -e native`.
#include <unity.h>

#include "battery.h"
#include "config.h"
#include "run.h"

static const BatteryConfig kCfg = {BATT_WARN_MV, BATT_REFUSE_MV, BATT_HYSTERESIS_MV,
                                   BATT_USB_BELOW_MV, BATT_SAG_MS};
static const RunConfig kRunCfg = {SLOWDOWN_N, JAM_TIMEOUT_MS, FIRST_BB_TIMEOUT_MS, DONE_HOLD_MS};

void setUp() {}
void tearDown() {}

// Feeds the same reading `n` times, BATT_READ_PERIOD_MS apart from `*now`.
static void feed(Battery& b, uint32_t* now, uint32_t mv, int n, bool running = false) {
  for (int i = 0; i < n; i++) {
    b.update(*now, mv, running);
    *now += BATT_READ_PERIOD_MS;
  }
}

static void test_adc_scaling() {
  // 1500 mV at the pin through 100k/27k is 7056 mV at the pack.
  TEST_ASSERT_EQUAL_UINT32(7056, batteryMvFromAdc(1500, BATT_DIVIDER_RATIO, 1.0f));
  TEST_ASSERT_EQUAL_UINT32(7126, batteryMvFromAdc(1500, BATT_DIVIDER_RATIO, 1.01f));
  TEST_ASSERT_EQUAL_UINT32(0, batteryMvFromAdc(0, BATT_DIVIDER_RATIO, 1.0f));
}

static void test_usb_reads_zero_and_guard_off() {
  Battery b(kCfg);
  uint32_t now = 0;
  feed(b, &now, 120, 3);  // ADC noise with no pack
  TEST_ASSERT_TRUE(b.usb());
  TEST_ASSERT_EQUAL_UINT16(0, b.mv());
  TEST_ASSERT_TRUE(b.ok());
  TEST_ASSERT_FALSE(b.warn());
  feed(b, &now, 2999, 3);
  TEST_ASSERT_TRUE(b.usb());
  TEST_ASSERT_TRUE(b.ok());
  // Even a long "run" on USB never aborts.
  feed(b, &now, 0, 20, true);
  TEST_ASSERT_FALSE(b.sagged());
  // At 3000 it's a (very flat) battery: reported and refused.
  feed(b, &now, 3000, 3);
  TEST_ASSERT_FALSE(b.usb());
  TEST_ASSERT_EQUAL_UINT16(3000, b.mv());
  TEST_ASSERT_FALSE(b.ok());
}

static void test_before_first_reading_is_usb() {
  Battery b(kCfg);
  TEST_ASSERT_EQUAL_UINT16(0, b.mv());
  TEST_ASSERT_TRUE(b.ok());
}

static void test_refuses_below_6600() {
  Battery b(kCfg);
  uint32_t now = 0;
  feed(b, &now, 6600, 3);
  TEST_ASSERT_TRUE(b.ok());
  feed(b, &now, 6599, 3);
  TEST_ASSERT_FALSE(b.ok());
  TEST_ASSERT_EQUAL_UINT16(6599, b.mv());

  Run run(kRunCfg);
  TEST_ASSERT_FALSE(run.go(now, b.ok()));
  TEST_ASSERT_EQUAL_STRING("LOW_BATT", stateName(run.state()));
}

static void test_refusal_hysteresis() {
  Battery b(kCfg);
  uint32_t now = 0;
  feed(b, &now, 6650, 3);
  TEST_ASSERT_TRUE(b.ok());  // never been low: 6650 is fine
  feed(b, &now, 6500, 3);
  TEST_ASSERT_FALSE(b.ok());
  feed(b, &now, 6650, 3);
  TEST_ASSERT_FALSE(b.ok());  // was low: needs +100 mV
  feed(b, &now, 6699, 3);
  TEST_ASSERT_FALSE(b.ok());
  feed(b, &now, 6750, 3);
  TEST_ASSERT_TRUE(b.ok());

  // GO from LOW_BATT works again once the battery is back.
  Run run(kRunCfg);
  run.go(0, false);
  TEST_ASSERT_TRUE(run.go(now, b.ok()));
  TEST_ASSERT_EQUAL_STRING("RUNNING", stateName(run.state()));
}

static void test_warn_below_7000() {
  Battery b(kCfg);
  uint32_t now = 0;
  feed(b, &now, 8400, 3);
  TEST_ASSERT_FALSE(b.warn());
  feed(b, &now, 7000, 3);
  TEST_ASSERT_FALSE(b.warn());
  feed(b, &now, 6999, 3);
  TEST_ASSERT_TRUE(b.warn());
  TEST_ASSERT_TRUE(b.ok());  // a warning doesn't block GO
  feed(b, &now, 7050, 3);
  TEST_ASSERT_TRUE(b.warn());  // hysteresis, no flicker around 7000
  feed(b, &now, 7100, 3);
  TEST_ASSERT_FALSE(b.warn());
}

// A dip of `dipMs` to 6400 mV in the middle of a run, readings every 500 ms.
static bool dipStopsRun(uint32_t dipMs) {
  Battery b(kCfg);
  Run run(kRunCfg);
  run.setTarget(9999);
  uint32_t now = 0;
  feed(b, &now, 7400, 3);
  TEST_ASSERT_TRUE(run.go(now, b.ok()));
  uint32_t dipEnd = now + dipMs;
  for (int i = 0; i < 20; i++) {
    uint32_t mv = now < dipEnd ? 6400 : 7400;
    b.update(now, mv, true);
    if (b.sagged()) run.lowBattery();
    if (run.state() == State::LowBatt) {
      TEST_ASSERT_EQUAL(Speed::Off, run.speed());
      TEST_ASSERT_FALSE(run.counting());
      TEST_ASSERT_FALSE(b.ok());
      return true;
    }
    now += BATT_READ_PERIOD_MS;
  }
  return false;
}

static void test_one_second_dip_during_run_does_not_stop_it() {
  TEST_ASSERT_FALSE(dipStopsRun(1000));
  TEST_ASSERT_FALSE(dipStopsRun(1500));
}

static void test_three_second_dip_during_run_stops_it() {
  TEST_ASSERT_TRUE(dipStopsRun(3000));
}

static void test_start_guard_frozen_during_run() {
  // Sag under load doesn't latch the start guard: after a run with short dips, GO is still OK.
  Battery b(kCfg);
  uint32_t now = 0;
  feed(b, &now, 6800, 3);
  feed(b, &now, 6400, 2, true);
  feed(b, &now, 6800, 3, true);
  feed(b, &now, 6650, 3);
  TEST_ASSERT_TRUE(b.ok());
}

static void test_one_bad_sample_does_not_flip_state() {
  Battery b(kCfg);
  uint32_t now = 0;
  feed(b, &now, 7400, 3);
  b.update(now, 0, false);  // would read as USB
  now += BATT_READ_PERIOD_MS;
  TEST_ASSERT_FALSE(b.usb());
  TEST_ASSERT_EQUAL_UINT16(7400, b.mv());
  feed(b, &now, 7400, 2);
  b.update(now, 6000, false);  // would refuse
  now += BATT_READ_PERIOD_MS;
  TEST_ASSERT_TRUE(b.ok());
  TEST_ASSERT_FALSE(b.warn());
  TEST_ASSERT_EQUAL_UINT16(7400, b.mv());

  // And on USB, a single spike doesn't make up a battery.
  Battery u(kCfg);
  now = 0;
  feed(u, &now, 0, 3);
  u.update(now, 8000, false);
  TEST_ASSERT_TRUE(u.usb());
}

static void test_low_battery_ignored_when_not_running() {
  Run run(kRunCfg);
  run.lowBattery();
  TEST_ASSERT_EQUAL_STRING("IDLE", stateName(run.state()));
  run.setTarget(10);
  run.go(0, true);
  run.update(100, 8);
  run.lowBattery();  // from SLOWDOWN too
  TEST_ASSERT_EQUAL_STRING("LOW_BATT", stateName(run.state()));
}

static uint8_t bars(uint16_t mv, uint8_t previous = kGaugeUnknown) {
  return gaugeBars(mv, previous, BATT_GAUGE_MV, BATT_GAUGE_HYSTERESIS_MV);
}

static void test_gauge_bars_at_each_threshold() {
  TEST_ASSERT_EQUAL_UINT8(4, bars(8400));
  TEST_ASSERT_EQUAL_UINT8(4, bars(8000));
  TEST_ASSERT_EQUAL_UINT8(3, bars(7999));
  TEST_ASSERT_EQUAL_UINT8(3, bars(7600));
  TEST_ASSERT_EQUAL_UINT8(2, bars(7599));
  TEST_ASSERT_EQUAL_UINT8(2, bars(7200));
  TEST_ASSERT_EQUAL_UINT8(1, bars(7199));
  TEST_ASSERT_EQUAL_UINT8(1, bars(6800));
  TEST_ASSERT_EQUAL_UINT8(0, bars(6799));
  TEST_ASSERT_EQUAL_UINT8(0, bars(0));
}

static void test_gauge_drops_at_once_and_climbs_back_with_hysteresis() {
  // Every boundary: a bar goes just below its threshold, and only comes back 100 mV above it.
  for (uint8_t i = 0; i < kGaugeBars; i++) {
    uint16_t t = BATT_GAUGE_MV[i];
    uint8_t b = bars(t);  // i + 1 bars
    TEST_ASSERT_EQUAL_UINT8(i + 1, b);
    b = bars(t - 1, b);
    TEST_ASSERT_EQUAL_UINT8(i, b);
    b = bars(t, b);
    TEST_ASSERT_EQUAL_UINT8(i, b);
    b = bars(t + BATT_GAUGE_HYSTERESIS_MV - 1, b);
    TEST_ASSERT_EQUAL_UINT8(i, b);
    b = bars(t + BATT_GAUGE_HYSTERESIS_MV, b);
    TEST_ASSERT_EQUAL_UINT8(i + 1, b);
  }
}

static void test_gauge_does_not_flicker_on_a_boundary() {
  // Noise of +-40 mV around 7600 mV: at most one change, then it holds.
  uint8_t b = bars(7640);
  uint8_t changes = 0;
  for (int i = 0; i < 200; i++) {
    uint8_t next = bars(i % 2 ? 7560 : 7640, b);
    if (next != b) changes++;
    b = next;
  }
  TEST_ASSERT_LESS_OR_EQUAL_UINT8(1, changes);
  TEST_ASSERT_EQUAL_UINT8(2, b);
}

static void test_gauge_jumps_several_bars_at_once() {
  TEST_ASSERT_EQUAL_UINT8(0, bars(6500, 4));  // a run sagging hard
  TEST_ASSERT_EQUAL_UINT8(4, bars(8400, 0));  // a fresh pack plugged in
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_gauge_bars_at_each_threshold);
  RUN_TEST(test_gauge_drops_at_once_and_climbs_back_with_hysteresis);
  RUN_TEST(test_gauge_does_not_flicker_on_a_boundary);
  RUN_TEST(test_gauge_jumps_several_bars_at_once);
  RUN_TEST(test_adc_scaling);
  RUN_TEST(test_usb_reads_zero_and_guard_off);
  RUN_TEST(test_before_first_reading_is_usb);
  RUN_TEST(test_refuses_below_6600);
  RUN_TEST(test_refusal_hysteresis);
  RUN_TEST(test_warn_below_7000);
  RUN_TEST(test_one_second_dip_during_run_does_not_stop_it);
  RUN_TEST(test_three_second_dip_during_run_stops_it);
  RUN_TEST(test_start_guard_frozen_during_run);
  RUN_TEST(test_one_bad_sample_does_not_flip_state);
  RUN_TEST(test_low_battery_ignored_when_not_running);
  return UNITY_END();
}
