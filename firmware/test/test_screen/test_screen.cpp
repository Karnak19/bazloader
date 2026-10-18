// Host tests for src/screen.cpp: `pio test -e native`.
#include <unity.h>

#include <initializer_list>

#include "screen.h"

void setUp() {}
void tearDown() {}

static void test_idle_shows_target() {
  ScreenModel m = screenModel(State::Idle, 50, 0, 7400, false, false);
  TEST_ASSERT_EQUAL_STRING("Prêt", m.status1);
  TEST_ASSERT_EQUAL_STRING("", m.status2);
  TEST_ASSERT_EQUAL_STRING("50", m.big);
  TEST_ASSERT_EQUAL_STRING("Cible", m.detail);
  TEST_ASSERT_EQUAL_STRING("7.4 V", m.battery);
  TEST_ASSERT_FALSE(m.batteryWarn);
}

static void test_running_shows_count_over_target() {
  ScreenModel m = screenModel(State::Running, 300, 137, 7400, false, false);
  TEST_ASSERT_EQUAL_STRING("Chargement", m.status1);
  TEST_ASSERT_EQUAL_STRING("137", m.big);
  TEST_ASSERT_EQUAL_STRING("/ 300", m.detail);
}

static void test_slowdown() {
  ScreenModel m = screenModel(State::Slowdown, 9999, 9997, 7400, false, false);
  TEST_ASSERT_EQUAL_STRING("Ralenti", m.status1);
  TEST_ASSERT_EQUAL_STRING("9997", m.big);
  TEST_ASSERT_EQUAL_STRING("/ 9999", m.detail);
}

static void test_done_shows_final_count_with_overshoot() {
  ScreenModel m = screenModel(State::Done, 50, 51, 7400, false, false);
  TEST_ASSERT_EQUAL_STRING("Terminé", m.status1);
  TEST_ASSERT_EQUAL_STRING("51", m.big);
  TEST_ASSERT_EQUAL_STRING("/ 50", m.detail);
}

static void test_jam_message_in_french_on_two_lines() {
  ScreenModel m = screenModel(State::Jam, 300, 100, 7400, false, false);
  TEST_ASSERT_EQUAL_STRING("Bourrage /", m.status1);
  TEST_ASSERT_EQUAL_STRING("trémie vide", m.status2);
  TEST_ASSERT_EQUAL_STRING("100", m.big);
  TEST_ASSERT_EQUAL_STRING("/ 300", m.detail);
}

static void test_low_batt_message_in_french() {
  ScreenModel m = screenModel(State::LowBatt, 120, 0, 6500, false, true);
  TEST_ASSERT_EQUAL_STRING("Batterie", m.status1);
  TEST_ASSERT_EQUAL_STRING("faible", m.status2);
  TEST_ASSERT_EQUAL_STRING("120", m.big);
  TEST_ASSERT_EQUAL_STRING("Cible", m.detail);
  TEST_ASSERT_EQUAL_STRING("6.5 V", m.battery);
  TEST_ASSERT_TRUE(m.batteryWarn);
}

static void test_usb_shows_usb_and_never_warns() {
  ScreenModel m = screenModel(State::Idle, 50, 0, 0, true, true);
  TEST_ASSERT_EQUAL_STRING("USB", m.battery);
  TEST_ASSERT_FALSE(m.batteryWarn);
}

static void test_battery_warning_and_rounding() {
  ScreenModel m = screenModel(State::Running, 50, 3, 6949, false, true);
  TEST_ASSERT_EQUAL_STRING("6.9 V", m.battery);
  TEST_ASSERT_TRUE(m.batteryWarn);
  TEST_ASSERT_EQUAL_STRING("7.0 V", screenModel(State::Idle, 50, 0, 6950, false, false).battery);
  TEST_ASSERT_EQUAL_STRING("8.4 V", screenModel(State::Idle, 50, 0, 8400, false, false).battery);
}

static void test_labels_fit_their_buffers() {
  // UTF-8 accents take two bytes: make sure nothing got truncated.
  for (State s : {State::Idle, State::Running, State::Slowdown, State::Done, State::Jam,
                  State::LowBatt, State::Testing}) {
    ScreenModel m = screenModel(s, 9999, 9999, 8400, false, true);
    TEST_ASSERT_LESS_THAN(sizeof(m.status1) - 1, strlen(m.status1));
    TEST_ASSERT_LESS_THAN(sizeof(m.status2) - 1, strlen(m.status2));
    TEST_ASSERT_LESS_THAN(sizeof(m.detail) - 1, strlen(m.detail));
  }
}

static void test_model_changes_only_when_content_changes() {
  ScreenModel a = screenModel(State::Running, 50, 10, 7400, false, false);
  ScreenModel b = screenModel(State::Running, 50, 10, 7400, false, false);
  TEST_ASSERT_TRUE(a == b);
  TEST_ASSERT_TRUE(a != screenModel(State::Running, 50, 11, 7400, false, false));
  TEST_ASSERT_TRUE(a != screenModel(State::Slowdown, 50, 10, 7400, false, false));
  TEST_ASSERT_TRUE(a != screenModel(State::Running, 50, 10, 7300, false, false));
  TEST_ASSERT_TRUE(a != screenModel(State::Running, 50, 10, 7400, false, true));
  // A few mV that round to the same tenth don't cause a redraw.
  TEST_ASSERT_TRUE(a == screenModel(State::Running, 50, 10, 7420, false, false));
  // At rest the count isn't shown, so it doesn't cause a redraw either.
  TEST_ASSERT_TRUE(screenModel(State::Idle, 50, 3, 7400, false, false) ==
                   screenModel(State::Idle, 50, 4, 7400, false, false));
}

static void test_testing_shows_test_and_the_target() {
  ScreenModel m = screenModel(State::Testing, 50, 12, 7400, false, false);
  TEST_ASSERT_EQUAL_STRING("Test moteur", m.status1);
  TEST_ASSERT_EQUAL_STRING("", m.status2);
  TEST_ASSERT_EQUAL_STRING("50", m.big);  // nothing is counted: the target, not a count
  TEST_ASSERT_EQUAL_STRING("Cible", m.detail);
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_idle_shows_target);
  RUN_TEST(test_testing_shows_test_and_the_target);
  RUN_TEST(test_running_shows_count_over_target);
  RUN_TEST(test_slowdown);
  RUN_TEST(test_done_shows_final_count_with_overshoot);
  RUN_TEST(test_jam_message_in_french_on_two_lines);
  RUN_TEST(test_low_batt_message_in_french);
  RUN_TEST(test_usb_shows_usb_and_never_warns);
  RUN_TEST(test_battery_warning_and_rounding);
  RUN_TEST(test_labels_fit_their_buffers);
  RUN_TEST(test_model_changes_only_when_content_changes);
  return UNITY_END();
}
