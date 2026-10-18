// Host tests for src/controls.cpp: `pio test -e native`.
#include <unity.h>

#include <initializer_list>

#include "config.h"
#include "controls.h"
#include "run.h"

static const RunConfig kCfg = {SLOWDOWN_N, JAM_TIMEOUT_MS, FIRST_BB_TIMEOUT_MS, DONE_HOLD_MS};

void setUp() {}
void tearDown() {}

// A/B levels as the bits of `ab` (A = bit 1).
static void feed(Encoder& e, uint8_t ab) { e.edge(ab & 2, ab & 1); }

// One full detent from rest (11) in the +1 direction: 11 -> 01 -> 00 -> 10 -> 11.
static void detentUp(Encoder& e) {
  feed(e, 0b01);
  feed(e, 0b00);
  feed(e, 0b10);
  feed(e, 0b11);
}
static void detentDown(Encoder& e) {
  feed(e, 0b10);
  feed(e, 0b00);
  feed(e, 0b01);
  feed(e, 0b11);
}

// ---- Quadrature decoding ----

static void test_one_detent_is_plus_or_minus_one() {
  Encoder e(4, 0b11);
  detentUp(e);
  TEST_ASSERT_EQUAL_INT32(1, e.position);
  detentUp(e);
  TEST_ASSERT_EQUAL_INT32(2, e.position);
  detentDown(e);
  TEST_ASSERT_EQUAL_INT32(1, e.position);
  detentDown(e);
  detentDown(e);
  TEST_ASSERT_EQUAL_INT32(-1, e.position);
}

static void test_partial_detent_does_not_step() {
  Encoder e(4, 0b11);
  feed(e, 0b01);
  feed(e, 0b00);
  feed(e, 0b10);
  TEST_ASSERT_EQUAL_INT32(0, e.position);
  feed(e, 0b00);  // and back the way it came
  feed(e, 0b01);
  feed(e, 0b11);
  TEST_ASSERT_EQUAL_INT32(0, e.position);
}

static void test_bounce_does_not_step() {
  Encoder e(4, 0b11);
  // Contact A chattering at rest.
  for (int i = 0; i < 20; i++) {
    feed(e, 0b01);
    feed(e, 0b11);
  }
  TEST_ASSERT_EQUAL_INT32(0, e.position);
  // Chattering halfway through a detent, then settling back at rest.
  feed(e, 0b01);
  for (int i = 0; i < 20; i++) {
    feed(e, 0b00);
    feed(e, 0b01);
  }
  feed(e, 0b11);
  TEST_ASSERT_EQUAL_INT32(0, e.position);
  // Repeated reads of the same level (both edges firing the ISR) change nothing.
  for (int i = 0; i < 5; i++) feed(e, 0b11);
  TEST_ASSERT_EQUAL_INT32(0, e.position);
}

static void test_bounce_inside_a_detent_still_counts_once() {
  Encoder e(4, 0b11);
  feed(e, 0b01);
  feed(e, 0b11);  // bounce
  feed(e, 0b01);
  feed(e, 0b00);
  feed(e, 0b01);  // bounce
  feed(e, 0b00);
  feed(e, 0b10);
  feed(e, 0b11);
  TEST_ASSERT_EQUAL_INT32(1, e.position);
}

static void test_invalid_transition_is_ignored() {
  Encoder e(4, 0b11);
  feed(e, 0b00);  // both bits at once: no direction
  feed(e, 0b11);
  TEST_ASSERT_EQUAL_INT32(0, e.position);
  detentUp(e);
  TEST_ASSERT_EQUAL_INT32(1, e.position);  // still in step after it
}

static void test_two_steps_per_detent_modules() {
  Encoder e(2, 0b11);
  feed(e, 0b01);
  feed(e, 0b00);  // rest at 00 is a detent on these
  TEST_ASSERT_EQUAL_INT32(1, e.position);
  feed(e, 0b10);
  feed(e, 0b11);
  TEST_ASSERT_EQUAL_INT32(2, e.position);
  feed(e, 0b10);
  feed(e, 0b00);
  TEST_ASSERT_EQUAL_INT32(1, e.position);
}

// ---- Acceleration ----

static void test_slow_detents_step_by_one() {
  EncoderAccel a(ENCODER_FAST_MS, ENCODER_FAST_STEP);
  TEST_ASSERT_EQUAL_INT32(1, a.apply(1, 1000));
  TEST_ASSERT_EQUAL_INT32(1, a.apply(1, 1100));
  TEST_ASSERT_EQUAL_INT32(-1, a.apply(-1, 1200));
  TEST_ASSERT_EQUAL_INT32(0, a.apply(0, 1210));
}

static void test_fast_detents_step_by_ten() {
  EncoderAccel a(ENCODER_FAST_MS, ENCODER_FAST_STEP);
  TEST_ASSERT_EQUAL_INT32(1, a.apply(1, 1000));    // the first one is always a single step
  TEST_ASSERT_EQUAL_INT32(10, a.apply(1, 1020));   // 20 ms later
  TEST_ASSERT_EQUAL_INT32(10, a.apply(1, 1049));   // 29 ms later
  TEST_ASSERT_EQUAL_INT32(1, a.apply(1, 1079));    // 30 ms: slow again
  TEST_ASSERT_EQUAL_INT32(-1, a.apply(-1, 2000));
  TEST_ASSERT_EQUAL_INT32(-10, a.apply(-1, 2010));  // same both ways
}

static void test_direction_change_is_never_fast() {
  EncoderAccel a(ENCODER_FAST_MS, ENCODER_FAST_STEP);
  a.apply(1, 1000);
  TEST_ASSERT_EQUAL_INT32(-1, a.apply(-1, 1005));
}

static void test_batched_detents_count_as_fast() {
  EncoderAccel a(ENCODER_FAST_MS, ENCODER_FAST_STEP);
  // Three detents read in one pass after a pause: 1 + 10 + 10.
  TEST_ASSERT_EQUAL_INT32(21, a.apply(3, 5000));
  TEST_ASSERT_EQUAL_INT32(-21, a.apply(-3, 9000));
}

static void test_target_clamped_at_both_ends() {
  Run run(kCfg);
  EncoderAccel a(ENCODER_FAST_MS, ENCODER_FAST_STEP);
  run.setTarget(TARGET_MAX - 3);
  a.apply(1, 0);
  TEST_ASSERT_EQUAL_UINT16(TARGET_MAX, run.setTarget(run.target() + a.apply(1, 10)));
  TEST_ASSERT_EQUAL_UINT16(TARGET_MAX, run.setTarget(run.target() + a.apply(1, 20)));
  TEST_ASSERT_EQUAL_UINT16(TARGET_MAX, run.setTarget(run.target() + a.apply(1, 500)));

  run.setTarget(3);
  a.apply(-1, 1000);
  TEST_ASSERT_EQUAL_UINT16(TARGET_MIN, run.setTarget(run.target() + a.apply(-1, 1010)));
  TEST_ASSERT_EQUAL_UINT16(TARGET_MIN, run.setTarget(run.target() + a.apply(-1, 2000)));
}

// ---- Buttons ----

static void test_button_debounce_ignores_glitches() {
  Button b(BUTTON_DEBOUNCE_MS, LONG_CLICK_MS);
  // 100 ms of chatter, flipping every 5 ms: never holds for the debounce time.
  for (uint32_t t = 0; t < 100; t += 5) {
    TEST_ASSERT_EQUAL(ButtonEvent::None, b.update(t, (t / 5) % 2 == 0));
  }
  TEST_ASSERT_EQUAL(ButtonEvent::None, b.update(110, false));
  TEST_ASSERT_EQUAL(ButtonEvent::None, b.update(200, false));
}

static void test_short_click() {
  Button b(BUTTON_DEBOUNCE_MS, LONG_CLICK_MS);
  TEST_ASSERT_EQUAL(ButtonEvent::None, b.update(0, false));
  TEST_ASSERT_EQUAL(ButtonEvent::None, b.update(100, true));
  TEST_ASSERT_EQUAL(ButtonEvent::None, b.update(105, false));  // bounce on the way down
  TEST_ASSERT_EQUAL(ButtonEvent::None, b.update(110, true));
  TEST_ASSERT_EQUAL(ButtonEvent::None, b.update(129, true));
  TEST_ASSERT_EQUAL(ButtonEvent::Press, b.update(130, true));
  TEST_ASSERT_EQUAL(ButtonEvent::None, b.update(400, true));
  TEST_ASSERT_EQUAL(ButtonEvent::None, b.update(500, false));
  TEST_ASSERT_EQUAL(ButtonEvent::ShortClick, b.update(520, false));
  TEST_ASSERT_EQUAL(ButtonEvent::None, b.update(600, false));
}

static void test_long_click_fires_once_while_held() {
  Button b(BUTTON_DEBOUNCE_MS, LONG_CLICK_MS);
  b.update(0, true);
  TEST_ASSERT_EQUAL(ButtonEvent::Press, b.update(20, true));
  TEST_ASSERT_EQUAL(ButtonEvent::None, b.update(20 + LONG_CLICK_MS - 1, true));
  TEST_ASSERT_EQUAL(ButtonEvent::LongClick, b.update(20 + LONG_CLICK_MS, true));
  TEST_ASSERT_EQUAL(ButtonEvent::None, b.update(3000, true));
  b.update(3100, false);
  TEST_ASSERT_EQUAL(ButtonEvent::None, b.update(3200, false));  // no ShortClick after a long one
}

// ---- Presets ----

static void test_short_click_cycles_presets() {
  Presets p = defaultPresets();
  ClickHandler clicks;
  Run run(kCfg);
  run.setTarget(30);
  const uint16_t expected[] = {50, 120, 300, 30, 50};
  for (uint16_t want : expected) {
    TEST_ASSERT_EQUAL(UiAction::None, clicks.handle(ButtonEvent::Press, run.state()));
    TEST_ASSERT_EQUAL(UiAction::NextPreset, clicks.handle(ButtonEvent::ShortClick, run.state()));
    run.setTarget(nextPreset(p, run.target()));
    TEST_ASSERT_EQUAL_UINT16(want, run.target());
  }
}

static void test_next_preset_from_a_custom_target() {
  Presets p = defaultPresets();
  TEST_ASSERT_EQUAL_UINT16(120, nextPreset(p, 77));
  TEST_ASSERT_EQUAL_UINT16(30, nextPreset(p, 1));
  TEST_ASSERT_EQUAL_UINT16(30, nextPreset(p, 301));  // wraps
  TEST_ASSERT_EQUAL_UINT16(30, nextPreset(p, 9999));
}

static void test_presets_are_a_runtime_array() {
  Presets p = defaultPresets();
  p.values[1] = 75;  // what NVS will do
  TEST_ASSERT_EQUAL_UINT16(75, nextPreset(p, 30));
  TEST_ASSERT_EQUAL_UINT16(120, nextPreset(p, 75));
}

// ---- What GO and a click do ----

static void test_long_click_is_a_no_op() {
  ClickHandler clicks;
  for (State s : {State::Idle, State::Done, State::Jam, State::LowBatt}) {
    TEST_ASSERT_EQUAL(UiAction::None, clicks.handle(ButtonEvent::Press, s));
    TEST_ASSERT_EQUAL(UiAction::None, clicks.handle(ButtonEvent::LongClick, s));
  }
}

static void test_click_during_run_stops_on_press_and_swallows_release() {
  for (State s : {State::Running, State::Slowdown, State::Testing}) {
    ClickHandler clicks;
    TEST_ASSERT_EQUAL(UiAction::Stop, clicks.handle(ButtonEvent::Press, s));
    // The run is now stopped: the release must not also cycle the preset.
    TEST_ASSERT_EQUAL(UiAction::None, clicks.handle(ButtonEvent::ShortClick, State::Idle));
    // The next click is a normal one again.
    clicks.handle(ButtonEvent::Press, State::Idle);
    TEST_ASSERT_EQUAL(UiAction::NextPreset, clicks.handle(ButtonEvent::ShortClick, State::Idle));
  }
}

static void test_click_stop_with_a_real_run() {
  Run run(kCfg);
  ClickHandler clicks;
  run.setTarget(50);
  run.go(0, true);
  run.update(100, 10);
  UiAction a = clicks.handle(ButtonEvent::Press, run.state());
  TEST_ASSERT_EQUAL(UiAction::Stop, a);
  run.stop();
  TEST_ASSERT_EQUAL_STRING("IDLE", stateName(run.state()));
  TEST_ASSERT_EQUAL(UiAction::None, clicks.handle(ButtonEvent::ShortClick, run.state()));
  TEST_ASSERT_EQUAL_UINT16(50, run.target());
}

static void test_go_toggles_per_state() {
  TEST_ASSERT_EQUAL(UiAction::Start, goAction(State::Idle, true));
  TEST_ASSERT_EQUAL(UiAction::Start, goAction(State::Done, true));
  TEST_ASSERT_EQUAL(UiAction::Start, goAction(State::Jam, true));
  TEST_ASSERT_EQUAL(UiAction::Start, goAction(State::LowBatt, true));  // pack recovered
  TEST_ASSERT_EQUAL(UiAction::None, goAction(State::LowBatt, false));  // message stays up
  TEST_ASSERT_EQUAL(UiAction::Stop, goAction(State::Running, true));
  TEST_ASSERT_EQUAL(UiAction::Stop, goAction(State::Slowdown, true));
  TEST_ASSERT_EQUAL(UiAction::Stop, goAction(State::Testing, true));
  TEST_ASSERT_EQUAL(UiAction::Stop, goAction(State::Running, false));  // stop never refused
  // From IDLE with a flat pack GO still tries: Run::go turns it into LOW_BATT.
  TEST_ASSERT_EQUAL(UiAction::Start, goAction(State::Idle, false));
}

static void test_go_start_then_stop_with_a_real_run() {
  Run run(kCfg);
  TEST_ASSERT_EQUAL(UiAction::Start, goAction(run.state(), true));
  TEST_ASSERT_TRUE(run.go(0, true));
  TEST_ASSERT_EQUAL(UiAction::Stop, goAction(run.state(), true));
  run.stop();
  TEST_ASSERT_EQUAL(UiAction::Start, goAction(run.state(), true));
}

static void test_target_change_ignored_during_run() {
  Run run(kCfg);
  EncoderAccel a(ENCODER_FAST_MS, ENCODER_FAST_STEP);
  Presets p = defaultPresets();
  run.setTarget(50);
  run.go(0, true);
  TEST_ASSERT_EQUAL_UINT16(50, run.setTarget(run.target() + a.apply(1, 100)));
  TEST_ASSERT_EQUAL_UINT16(50, run.setTarget(run.target() + a.apply(1, 110)));
  TEST_ASSERT_EQUAL_UINT16(50, run.setTarget(nextPreset(p, run.target())));
  run.stop();
  TEST_ASSERT_EQUAL_UINT16(51, run.setTarget(run.target() + a.apply(1, 1000)));
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_one_detent_is_plus_or_minus_one);
  RUN_TEST(test_partial_detent_does_not_step);
  RUN_TEST(test_bounce_does_not_step);
  RUN_TEST(test_bounce_inside_a_detent_still_counts_once);
  RUN_TEST(test_invalid_transition_is_ignored);
  RUN_TEST(test_two_steps_per_detent_modules);
  RUN_TEST(test_slow_detents_step_by_one);
  RUN_TEST(test_fast_detents_step_by_ten);
  RUN_TEST(test_direction_change_is_never_fast);
  RUN_TEST(test_batched_detents_count_as_fast);
  RUN_TEST(test_target_clamped_at_both_ends);
  RUN_TEST(test_button_debounce_ignores_glitches);
  RUN_TEST(test_short_click);
  RUN_TEST(test_long_click_fires_once_while_held);
  RUN_TEST(test_short_click_cycles_presets);
  RUN_TEST(test_next_preset_from_a_custom_target);
  RUN_TEST(test_presets_are_a_runtime_array);
  RUN_TEST(test_long_click_is_a_no_op);
  RUN_TEST(test_click_during_run_stops_on_press_and_swallows_release);
  RUN_TEST(test_click_stop_with_a_real_run);
  RUN_TEST(test_go_toggles_per_state);
  RUN_TEST(test_go_start_then_stop_with_a_real_run);
  RUN_TEST(test_target_change_ignored_during_run);
  return UNITY_END();
}
