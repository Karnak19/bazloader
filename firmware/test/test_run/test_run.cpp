// Host tests for src/run.cpp: `pio test -e native`.
#include <unity.h>

#include "config.h"
#include "run.h"

static const RunConfig kCfg = {SLOWDOWN_N, JAM_TIMEOUT_MS, FIRST_BB_TIMEOUT_MS, DONE_HOLD_MS};

void setUp() {}
void tearDown() {}

static void assertState(State expected, const Run& run) {
  TEST_ASSERT_EQUAL_STRING(stateName(expected), stateName(run.state()));
}

// Feeds one BB every 50 ms from t=100 ms and checks every transition on the way to DONE.
static void test_run_to_done_with_slowdown_at_target_minus_n() {
  Run run(kCfg);
  run.setTarget(50);
  TEST_ASSERT_TRUE(run.go(0, true));
  assertState(State::Running, run);
  TEST_ASSERT_EQUAL(Speed::Full, run.speed());

  uint32_t now = 0;
  for (uint32_t count = 1; count <= 50; count++) {
    now = 50 + count * 50;
    run.update(now, count);
    if (count < 50 - SLOWDOWN_N) {
      assertState(State::Running, run);
    } else if (count < 50) {
      assertState(State::Slowdown, run);  // first at 46
      TEST_ASSERT_EQUAL(Speed::Slow, run.speed());
    }
  }
  assertState(State::Done, run);
  TEST_ASSERT_EQUAL(Speed::Off, run.speed());
  TEST_ASSERT_TRUE(run.counting());  // overshoot still counted

  run.update(now + DONE_HOLD_MS - 1, 50);
  assertState(State::Done, run);
  run.update(now + DONE_HOLD_MS, 51);
  assertState(State::Idle, run);
  TEST_ASSERT_FALSE(run.counting());
}

static void test_slowdown_entered_exactly_at_46_of_50() {
  Run run(kCfg);
  run.setTarget(50);
  run.go(0, true);
  run.update(10, 45);
  assertState(State::Running, run);
  run.update(20, 46);
  assertState(State::Slowdown, run);
}

static void test_target_within_slowdown_window_starts_slow() {
  Run run(kCfg);
  run.setTarget(SLOWDOWN_N);
  run.go(0, true);
  assertState(State::Slowdown, run);
}

static void test_count_jump_past_target_goes_done() {
  Run run(kCfg);
  run.setTarget(10);
  run.go(0, true);
  run.update(10, 12);
  assertState(State::Done, run);
}

static void test_first_bb_gets_longer_timeout() {
  Run run(kCfg);
  run.go(1000, true);
  run.update(1000 + JAM_TIMEOUT_MS, 0);  // would jam with the normal timeout
  assertState(State::Running, run);
  run.update(1000 + FIRST_BB_TIMEOUT_MS - 1, 0);
  assertState(State::Running, run);
  run.update(1000 + FIRST_BB_TIMEOUT_MS, 0);
  assertState(State::Jam, run);
  TEST_ASSERT_EQUAL(Speed::Off, run.speed());
  TEST_ASSERT_FALSE(run.counting());
}

static void test_jam_after_bbs_stop_coming() {
  Run run(kCfg);
  run.setTarget(50);
  run.go(0, true);
  run.update(3000, 1);  // first BB late but within the first-BB timeout
  run.update(3100, 2);
  run.update(3100 + JAM_TIMEOUT_MS - 1, 2);
  assertState(State::Running, run);
  run.update(3100 + JAM_TIMEOUT_MS, 2);
  assertState(State::Jam, run);
}

static void test_jam_in_slowdown() {
  Run run(kCfg);
  run.setTarget(10);
  run.go(0, true);
  run.update(100, 8);
  assertState(State::Slowdown, run);
  run.update(100 + JAM_TIMEOUT_MS, 8);
  assertState(State::Jam, run);
}

static void test_stop_from_running() {
  Run run(kCfg);
  run.go(0, true);
  run.update(100, 3);
  run.stop();
  assertState(State::Idle, run);
  TEST_ASSERT_EQUAL(Speed::Off, run.speed());
}

static void test_stop_from_slowdown() {
  Run run(kCfg);
  run.setTarget(10);
  run.go(0, true);
  run.update(100, 7);
  assertState(State::Slowdown, run);
  run.stop();
  assertState(State::Idle, run);
  TEST_ASSERT_EQUAL(Speed::Off, run.speed());
}

static void test_stop_from_done_jam_and_low_batt() {
  Run run(kCfg);
  run.setTarget(5);
  run.go(0, true);
  run.update(10, 5);
  assertState(State::Done, run);
  run.stop();
  assertState(State::Idle, run);

  run.go(0, true);
  run.update(FIRST_BB_TIMEOUT_MS, 0);
  assertState(State::Jam, run);
  run.stop();
  assertState(State::Idle, run);

  TEST_ASSERT_FALSE(run.go(0, false));
  assertState(State::LowBatt, run);
  run.stop();
  assertState(State::Idle, run);
}

static void test_go_from_done_starts_new_run() {
  Run run(kCfg);
  run.setTarget(20);
  run.go(0, true);
  run.update(100, 20);
  assertState(State::Done, run);
  TEST_ASSERT_TRUE(run.go(200, true));
  assertState(State::Running, run);
  // Fresh timers: the first-BB timeout counts from the new GO, and count restarts at 0.
  run.update(200 + JAM_TIMEOUT_MS, 0);
  assertState(State::Running, run);
}

static void test_go_ignored_while_running() {
  Run run(kCfg);
  run.go(0, true);
  TEST_ASSERT_FALSE(run.go(10, true));
  assertState(State::Running, run);
}

static void test_go_from_jam_retries() {
  Run run(kCfg);
  run.go(0, true);
  run.update(FIRST_BB_TIMEOUT_MS, 0);
  assertState(State::Jam, run);
  TEST_ASSERT_TRUE(run.go(FIRST_BB_TIMEOUT_MS + 1, true));
  assertState(State::Running, run);
}

static void test_low_battery_refuses_start() {
  Run run(kCfg);
  TEST_ASSERT_FALSE(run.go(0, false));
  assertState(State::LowBatt, run);
  TEST_ASSERT_EQUAL(Speed::Off, run.speed());
}

static void test_target_clamped() {
  TEST_ASSERT_EQUAL_UINT16(1, clampTarget(0));
  TEST_ASSERT_EQUAL_UINT16(1, clampTarget(-5));
  TEST_ASSERT_EQUAL_UINT16(1, clampTarget(1));
  TEST_ASSERT_EQUAL_UINT16(9999, clampTarget(9999));
  TEST_ASSERT_EQUAL_UINT16(9999, clampTarget(10000));
  TEST_ASSERT_EQUAL_UINT16(9999, clampTarget(70000));
  Run run(kCfg);
  TEST_ASSERT_EQUAL_UINT16(9999, run.setTarget(123456));
  TEST_ASSERT_EQUAL_UINT16(1, run.setTarget(0));
}

static void test_target_locked_during_run() {
  Run run(kCfg);
  run.setTarget(50);
  run.go(0, true);
  TEST_ASSERT_EQUAL_UINT16(50, run.setTarget(10));
  run.stop();
  TEST_ASSERT_EQUAL_UINT16(10, run.setTarget(10));
}

static void test_counter_debounces_close_pulses() {
  Counter c(IR_MIN_INTERVAL_US);
  c.arm(50);
  c.pulse(1000000);
  c.pulse(1000000 + IR_MIN_INTERVAL_US / 5);  // same BB bouncing
  TEST_ASSERT_EQUAL_UINT32(1, c.count);
  c.pulse(1000000 + IR_MIN_INTERVAL_US - 1);
  TEST_ASSERT_EQUAL_UINT32(1, c.count);
  c.pulse(1000000 + IR_MIN_INTERVAL_US);  // next BB, exactly at the limit
  TEST_ASSERT_EQUAL_UINT32(2, c.count);
}

static void test_counter_rejected_pulses_dont_extend_window() {
  Counter c(IR_MIN_INTERVAL_US);
  c.arm(50);
  c.pulse(0 + 10);
  c.pulse(4000);  // rejected
  c.pulse(5010);  // 5000 after the accepted one: counts
  TEST_ASSERT_EQUAL_UINT32(2, c.count);
}

static void test_counter_survives_micros_wraparound() {
  Counter c(IR_MIN_INTERVAL_US);
  c.arm(50);
  c.pulse(0xFFFFFFFFu - 1000);
  c.pulse(1000);  // 2001 us later across the wrap: rejected
  TEST_ASSERT_EQUAL_UINT32(1, c.count);
  c.pulse(5000);  // 6001 us later: counts
  TEST_ASSERT_EQUAL_UINT32(2, c.count);
}

static void test_counter_signals_target_once_and_ignores_when_disabled() {
  Counter c(IR_MIN_INTERVAL_US);
  TEST_ASSERT_FALSE(c.pulse(0));  // not armed: not counted
  TEST_ASSERT_EQUAL_UINT32(0, c.count);
  c.arm(3);
  TEST_ASSERT_FALSE(c.pulse(10000));
  TEST_ASSERT_FALSE(c.pulse(20000));
  TEST_ASSERT_TRUE(c.pulse(30000));  // target BB: cut the servo
  TEST_ASSERT_FALSE(c.pulse(40000)); // overshoot counted, no second cut
  TEST_ASSERT_EQUAL_UINT32(4, c.count);
  c.arm(3);  // new run resets the count
  TEST_ASSERT_EQUAL_UINT32(0, c.count);
}

static void test_servo_pulse_and_duty() {
  TEST_ASSERT_EQUAL_UINT16(1800, servoPulseUs(Speed::Full, 1500, 300, 100, false));
  TEST_ASSERT_EQUAL_UINT16(1600, servoPulseUs(Speed::Slow, 1500, 300, 100, false));
  TEST_ASSERT_EQUAL_UINT16(1200, servoPulseUs(Speed::Full, 1500, 300, 100, true));
  TEST_ASSERT_EQUAL_UINT16(1400, servoPulseUs(Speed::Slow, 1500, 300, 100, true));
  TEST_ASSERT_EQUAL_UINT16(0, servoPulseUs(Speed::Off, 1500, 300, 100, false));
  // 14 bits over 20 ms: 0.8192 counts per us.
  TEST_ASSERT_EQUAL_UINT32(1229, servoDuty(1500, 14));
  TEST_ASSERT_EQUAL_UINT32(1475, servoDuty(1800, 14));
  TEST_ASSERT_EQUAL_UINT32(983, servoDuty(1200, 14));
  TEST_ASSERT_EQUAL_UINT32(16384, servoDuty(20000, 14));
}

// ---- Test spins (TESTING) ----

static void test_test_spin_entered_from_rest_states_at_its_speed() {
  Run run(kCfg);
  TEST_ASSERT_TRUE(run.test(Speed::Full, true));
  assertState(State::Testing, run);
  TEST_ASSERT_EQUAL(Speed::Full, run.speed());
  TEST_ASSERT_TRUE(run.test(Speed::Slow, true));  // switching speed while testing
  TEST_ASSERT_EQUAL(Speed::Slow, run.speed());
  run.stop();
  assertState(State::Idle, run);
  TEST_ASSERT_EQUAL(Speed::Off, run.speed());

  // From DONE and JAM, like GO.
  run.setTarget(5);
  run.go(0, true);
  run.update(10, 5);
  assertState(State::Done, run);
  TEST_ASSERT_TRUE(run.test(Speed::Full, true));
  run.stop();
  run.go(0, true);
  run.update(FIRST_BB_TIMEOUT_MS, 0);
  assertState(State::Jam, run);
  TEST_ASSERT_TRUE(run.test(Speed::Slow, true));
  assertState(State::Testing, run);
  TEST_ASSERT_FALSE(run.test(Speed::Off, true));
}

static void test_test_spin_refused_during_a_run_and_on_low_battery() {
  Run run(kCfg);
  run.go(0, true);
  TEST_ASSERT_FALSE(run.test(Speed::Full, true));
  assertState(State::Running, run);
  run.update(10, 50 - SLOWDOWN_N);
  assertState(State::Slowdown, run);
  TEST_ASSERT_FALSE(run.test(Speed::Full, true));
  assertState(State::Slowdown, run);

  Run low(kCfg);
  TEST_ASSERT_FALSE(low.test(Speed::Full, false));
  assertState(State::LowBatt, low);
  TEST_ASSERT_EQUAL(Speed::Off, low.speed());
}

static void test_test_spin_never_counts_nor_jams() {
  Run run(kCfg);
  run.setTarget(10);
  run.test(Speed::Full, true);
  TEST_ASSERT_FALSE(run.counting());
  run.update(60000, 0);  // far past any jam timeout
  assertState(State::Testing, run);
  run.update(60001, 500);  // past the target: not DONE either
  assertState(State::Testing, run);
  TEST_ASSERT_EQUAL(Speed::Full, run.speed());

  // The counter, disabled as main.cpp does from counting(), counts nothing.
  Counter counter(IR_MIN_INTERVAL_US);
  counter.arm(10);
  counter.enabled = run.counting();
  TEST_ASSERT_FALSE(counter.pulse(1000000));
  TEST_ASSERT_EQUAL_UINT32(0, counter.count);
}

static void test_go_ignored_while_testing_and_target_still_settable() {
  Run run(kCfg);
  run.test(Speed::Slow, true);
  TEST_ASSERT_FALSE(run.go(0, true));
  assertState(State::Testing, run);
  TEST_ASSERT_EQUAL_UINT16(120, run.setTarget(120));
}

static void test_test_spin_stops_on_battery_sag() {
  Run run(kCfg);
  run.test(Speed::Full, true);
  run.lowBattery();
  assertState(State::LowBatt, run);
  TEST_ASSERT_EQUAL(Speed::Off, run.speed());
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_run_to_done_with_slowdown_at_target_minus_n);
  RUN_TEST(test_slowdown_entered_exactly_at_46_of_50);
  RUN_TEST(test_target_within_slowdown_window_starts_slow);
  RUN_TEST(test_count_jump_past_target_goes_done);
  RUN_TEST(test_first_bb_gets_longer_timeout);
  RUN_TEST(test_jam_after_bbs_stop_coming);
  RUN_TEST(test_jam_in_slowdown);
  RUN_TEST(test_stop_from_running);
  RUN_TEST(test_stop_from_slowdown);
  RUN_TEST(test_stop_from_done_jam_and_low_batt);
  RUN_TEST(test_go_from_done_starts_new_run);
  RUN_TEST(test_go_ignored_while_running);
  RUN_TEST(test_go_from_jam_retries);
  RUN_TEST(test_low_battery_refuses_start);
  RUN_TEST(test_target_clamped);
  RUN_TEST(test_target_locked_during_run);
  RUN_TEST(test_counter_debounces_close_pulses);
  RUN_TEST(test_counter_rejected_pulses_dont_extend_window);
  RUN_TEST(test_counter_survives_micros_wraparound);
  RUN_TEST(test_counter_signals_target_once_and_ignores_when_disabled);
  RUN_TEST(test_servo_pulse_and_duty);
  RUN_TEST(test_test_spin_entered_from_rest_states_at_its_speed);
  RUN_TEST(test_test_spin_refused_during_a_run_and_on_low_battery);
  RUN_TEST(test_test_spin_never_counts_nor_jams);
  RUN_TEST(test_go_ignored_while_testing_and_target_still_settable);
  RUN_TEST(test_test_spin_stops_on_battery_sag);
  return UNITY_END();
}
