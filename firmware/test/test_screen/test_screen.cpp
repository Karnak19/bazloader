// Host tests for src/screen.cpp (what the OLED shows) and src/screen_draw.cpp (where it lands):
// `pio test -e native`. The drawing goes through U8g2's real C core into a real frame buffer, so
// these check the very pixels the module gets.
#include <unity.h>

#include <initializer_list>

#include "config.h"
#include "screen.h"
#include "screen_draw.h"

void setUp() {}
void tearDown() {}

// ---- Model ----

static const State kStates[] = {State::Idle, State::Running, State::Slowdown, State::Done,
                                State::Jam,  State::LowBatt, State::Testing};

// A screen on battery at 7.4 V, 3 bars, no phone, no warning.
static ScreenInputs inputs(State state, uint16_t target, uint32_t count) {
  return {state, target, count, 7400, false, false, 3, false, 0};
}

static ScreenModel model(State state, uint16_t target, uint32_t count) {
  return screenModel(inputs(state, target, count));
}

static void test_idle_shows_target() {
  ScreenModel m = model(State::Idle, 50, 0);
  TEST_ASSERT_EQUAL_STRING("Prêt", m.label);
  TEST_ASSERT_EQUAL_STRING("", m.message1);
  TEST_ASSERT_EQUAL_STRING("50", m.big);
  TEST_ASSERT_EQUAL_STRING("Cible", m.detail);
  TEST_ASSERT_EQUAL_STRING("7.4V", m.volts);
  TEST_ASSERT_EQUAL_UINT8(3, m.bars);
  TEST_ASSERT_FALSE(m.usb);
  TEST_ASSERT_FALSE(m.inverted);
  TEST_ASSERT_FALSE(m.bluetooth);
  TEST_ASSERT_FALSE(m.progress);
}

static void test_running_shows_count_over_target_and_progress() {
  ScreenModel m = model(State::Running, 300, 150);
  TEST_ASSERT_EQUAL_STRING("Chargement", m.label);
  TEST_ASSERT_EQUAL_STRING("150", m.big);
  TEST_ASSERT_EQUAL_STRING("/ 300", m.detail);
  TEST_ASSERT_TRUE(m.progress);
  TEST_ASSERT_EQUAL_UINT8(kProgressMaxPx / 2, m.progressPx);
  TEST_ASSERT_EQUAL_UINT8(0, model(State::Running, 300, 0).progressPx);
}

static void test_slowdown() {
  ScreenModel m = model(State::Slowdown, 9999, 9997);
  TEST_ASSERT_EQUAL_STRING("Ralenti", m.label);
  TEST_ASSERT_EQUAL_STRING("9997", m.big);
  TEST_ASSERT_EQUAL_STRING("/ 9999", m.detail);
  TEST_ASSERT_TRUE(m.progress);
}

static void test_done_shows_final_count_with_overshoot_and_a_full_bar() {
  ScreenModel m = model(State::Done, 50, 51);
  TEST_ASSERT_EQUAL_STRING("Terminé", m.label);
  TEST_ASSERT_EQUAL_STRING("51", m.big);
  TEST_ASSERT_EQUAL_STRING("/ 50", m.detail);
  TEST_ASSERT_EQUAL_UINT8(kProgressMaxPx, m.progressPx);  // capped, not past the frame
}

static void test_jam_message_goes_in_the_main_area() {
  ScreenModel m = model(State::Jam, 300, 100);
  TEST_ASSERT_EQUAL_STRING("Arrêt", m.label);
  TEST_ASSERT_EQUAL_STRING("Bourrage /", m.message1);
  TEST_ASSERT_EQUAL_STRING("trémie vide", m.message2);
  TEST_ASSERT_EQUAL_STRING("100", m.big);
  TEST_ASSERT_EQUAL_STRING("/ 300", m.detail);
}

static void test_low_batt_message_goes_in_the_main_area() {
  ScreenInputs in = inputs(State::LowBatt, 120, 0);
  in.batteryMv = 6500;
  in.warn = true;
  in.bars = 0;
  ScreenModel m = screenModel(in);
  TEST_ASSERT_EQUAL_STRING("Arrêt", m.label);
  TEST_ASSERT_EQUAL_STRING("Batterie", m.message1);
  TEST_ASSERT_EQUAL_STRING("faible", m.message2);
  TEST_ASSERT_EQUAL_STRING("120", m.big);
  TEST_ASSERT_EQUAL_STRING("Cible", m.detail);
  TEST_ASSERT_EQUAL_STRING("6.5V", m.volts);
  TEST_ASSERT_TRUE(m.inverted);  // at t = 0, the "on" phase
}

static void test_testing_shows_test_and_the_target() {
  ScreenModel m = model(State::Testing, 50, 12);
  TEST_ASSERT_EQUAL_STRING("Test moteur", m.label);
  TEST_ASSERT_EQUAL_STRING("50", m.big);  // nothing is counted: the target, not a count
  TEST_ASSERT_EQUAL_STRING("Cible", m.detail);
  TEST_ASSERT_FALSE(m.progress);
}

static void test_usb_shows_usb_no_gauge_and_never_warns() {
  ScreenInputs in = inputs(State::Idle, 50, 0);
  in.usb = true;
  in.warn = true;
  in.batteryMv = 0;
  ScreenModel m = screenModel(in);
  TEST_ASSERT_TRUE(m.usb);
  TEST_ASSERT_EQUAL_STRING("", m.volts);
  TEST_ASSERT_EQUAL_UINT8(0, m.bars);
  TEST_ASSERT_FALSE(m.inverted);
}

static void test_voltage_rounding() {
  ScreenInputs in = inputs(State::Idle, 50, 0);
  in.batteryMv = 6949;
  TEST_ASSERT_EQUAL_STRING("6.9V", screenModel(in).volts);
  in.batteryMv = 6950;
  TEST_ASSERT_EQUAL_STRING("7.0V", screenModel(in).volts);
  in.batteryMv = 8400;
  TEST_ASSERT_EQUAL_STRING("8.4V", screenModel(in).volts);
}

static void test_bluetooth_follows_the_connection() {
  ScreenInputs in = inputs(State::Idle, 50, 0);
  TEST_ASSERT_FALSE(screenModel(in).bluetooth);
  in.bleConnected = true;
  TEST_ASSERT_TRUE(screenModel(in).bluetooth);
}

static void test_labels_fit_their_buffers() {
  // UTF-8 accents take two bytes: make sure nothing got truncated.
  for (State s : kStates) {
    ScreenModel m = model(s, 9999, 9999);
    TEST_ASSERT_LESS_THAN(sizeof(m.label) - 1, strlen(m.label));
    TEST_ASSERT_LESS_THAN(sizeof(m.message1) - 1, strlen(m.message1));
    TEST_ASSERT_LESS_THAN(sizeof(m.message2) - 1, strlen(m.message2));
    TEST_ASSERT_LESS_THAN(sizeof(m.detail) - 1, strlen(m.detail));
  }
}

static void test_model_changes_only_when_content_changes() {
  ScreenModel a = model(State::Running, 50, 10);
  TEST_ASSERT_TRUE(a == model(State::Running, 50, 10));
  TEST_ASSERT_TRUE(a != model(State::Running, 50, 11));
  TEST_ASSERT_TRUE(a != model(State::Slowdown, 50, 10));
  ScreenInputs in = inputs(State::Running, 50, 10);
  in.batteryMv = 7300;
  TEST_ASSERT_TRUE(a != screenModel(in));
  in.batteryMv = 7420;  // a few mV that round to the same tenth don't cause a redraw
  TEST_ASSERT_TRUE(a == screenModel(in));
  in.bars = 2;
  TEST_ASSERT_TRUE(a != screenModel(in));
  // At rest the count isn't shown, so it doesn't cause a redraw either.
  TEST_ASSERT_TRUE(model(State::Idle, 50, 3) == model(State::Idle, 50, 4));
  // Without a warning, time alone never changes the screen.
  in = inputs(State::Running, 50, 10);
  for (uint32_t t = 0; t < 5000; t += 10) {
    in.nowMs = t;
    TEST_ASSERT_TRUE(a == screenModel(in));
  }
}

static void test_warning_blink_redraws_at_most_twice_a_second() {
  // Replays updateDisplay() in main.cpp: a pass every ms, a redraw when the model changed and
  // OLED_MIN_REDRAW_MS has passed. Nothing else changes: only the blink can cause redraws.
  ScreenInputs in = inputs(State::Running, 300, 210);
  in.batteryMv = 6950;
  in.warn = true;
  ScreenModel shown = screenModel(in);
  uint32_t lastDrawMs = 0;
  uint32_t redraws = 0;
  bool phases[2] = {false, false};
  for (uint32_t now = 1; now <= 10000; now++) {
    if (now - lastDrawMs < OLED_MIN_REDRAW_MS) continue;
    in.nowMs = now;
    ScreenModel m = screenModel(in);
    if (m == shown) continue;
    shown = m;
    lastDrawMs = now;
    redraws++;
    phases[m.inverted] = true;
  }
  TEST_ASSERT_TRUE(phases[0] && phases[1]);  // it does blink
  TEST_ASSERT_LESS_OR_EQUAL_UINT32(20, redraws);  // 10 s at <= 2 Hz
  TEST_ASSERT_GREATER_OR_EQUAL_UINT32(1000, OLED_BLINK_MS * 2);
}

// ---- Pixels ----

// Two frame buffers through U8g2's C core: the module's own 128x64, and a 256x64 one to see
// whatever would be clipped past the right edge. No display behind them: nothing is sent.
static u8g2_t screen;
static u8g2_t wide;

static bool lit(u8g2_t* u, int x, int y) {
  const uint8_t* buf = u8g2_GetBufferPtr(u);
  int width = u8g2_GetDisplayWidth(u);
  return buf[(y / 8) * width + x] & (1 << (y % 8));  // pages of 8 rows, LSB on top
}

struct Ink {
  int x0 = 9999, y0 = 9999, x1 = -1, y1 = -1;  // bounding box of the lit pixels
  int count = 0;
  bool any() const { return count > 0; }
};

static Ink ink(u8g2_t* u, int fromX = 0, int toX = 9999, int toY = kScreenHeight) {
  Ink k;
  int width = u8g2_GetDisplayWidth(u);
  for (int y = 0; y < toY; y++) {
    for (int x = fromX; x < width && x < toX; x++) {
      if (!lit(u, x, y)) continue;
      k.count++;
      if (x < k.x0) k.x0 = x;
      if (x > k.x1) k.x1 = x;
      if (y < k.y0) k.y0 = y;
      if (y > k.y1) k.y1 = y;
    }
  }
  return k;
}

static Ink render(u8g2_t* u, void (*part)(u8g2_t*, const ScreenModel&), const ScreenModel& m) {
  clearScreen(u);
  part(u, m);
  return ink(u);
}

// Every state, with every status bar variant and the extreme numbers.
template <typename F>
static void forEachModel(F check) {
  const uint16_t mvs[] = {3000, 6500, 7400, 8400, 12600};  // 12.6 V: someone plugs in a 3S pack
  struct Numbers { uint16_t target; uint32_t count; } numbers[] = {
      {1, 0}, {50, 51}, {9999, 9998}, {9999, 10099}};
  for (State s : kStates) {
    for (const Numbers& n : numbers) {
      for (int usb = 0; usb < 2; usb++) {
        for (uint16_t mv : mvs) {
          for (uint8_t bars = 0; bars <= 4; bars += 2) {
            for (int bt = 0; bt < 2; bt++) {
              for (int warn = 0; warn < 2; warn++) {
                for (uint32_t now : {0u, OLED_BLINK_MS * 1u}) {
                  ScreenInputs in = {s, n.target, n.count, usb ? (uint16_t)0 : mv, usb == 1,
                                     warn == 1, bars, bt == 1, now};
                  check(screenModel(in));
                  if (usb) break;  // the voltage doesn't matter on USB
                }
              }
            }
            if (usb) break;
          }
          if (usb) break;
        }
      }
    }
  }
}

static void test_no_pixel_on_the_gap_row() {
  int models = 0;
  forEachModel([&](const ScreenModel& m) {
    drawScreen(&screen, m);
    for (int x = 0; x < kScreenWidth; x++) TEST_ASSERT_FALSE(lit(&screen, x, kGapRow));
    models++;
  });
  TEST_ASSERT_GREATER_THAN(500, models);
}

static void test_nothing_past_the_right_edge() {
  forEachModel([](const ScreenModel& m) {
    drawScreen(&wide, m);
    TEST_ASSERT_FALSE(ink(&wide, kScreenWidth).any());
  });
}

static void test_each_part_stays_in_its_band() {
  forEachModel([](const ScreenModel& m) {
    Ink label = render(&screen, drawStatusLabel, m);
    TEST_ASSERT_TRUE(label.any());
    TEST_ASSERT_GREATER_OR_EQUAL_INT(0, label.y0);
    TEST_ASSERT_LESS_THAN_INT(kStatusBarRows, label.y1);
    Ink icons = render(&screen, drawStatusIcons, m);
    TEST_ASSERT_TRUE(icons.any());
    TEST_ASSERT_LESS_THAN_INT(kStatusBarRows, icons.y1);
    Ink main = render(&screen, drawMain, m);
    TEST_ASSERT_TRUE(main.any());
    TEST_ASSERT_GREATER_OR_EQUAL_INT(kMainTop, main.y0);
    TEST_ASSERT_LESS_THAN_INT(kScreenHeight, main.y1);
  });
}

static void test_label_never_touches_the_icons() {
  // At least 3 clear columns between the label and the Bluetooth rune, the gauge or "USB",
  // for every label, including the longest one with the widest icons (12.6 V, inverted, BT).
  forEachModel([](const ScreenModel& m) {
    Ink label = render(&wide, drawStatusLabel, m);
    Ink icons = render(&wide, drawStatusIcons, m);
    TEST_ASSERT_LESS_THAN_INT(icons.x0 - 3, label.x1);
  });
}

static void test_longest_label_fits_with_everything() {
  ScreenInputs in = {State::Testing, 9999, 0, 8400, false, true, 4, true, 0};
  ScreenModel m = screenModel(in);
  TEST_ASSERT_EQUAL_STRING("Test moteur", m.label);
  TEST_ASSERT_TRUE(m.inverted && m.bluetooth);
  Ink label = render(&wide, drawStatusLabel, m);
  Ink icons = render(&wide, drawStatusIcons, m);
  TEST_ASSERT_LESS_THAN_INT(icons.x0 - 3, label.x1);
  TEST_ASSERT_EQUAL_INT(kScreenWidth - 1, icons.x1);  // the voltage ends on the last column
}

static void test_big_number_never_touches_its_detail() {
  // The number alone, then the detail alone, in the same layout: at least 3 clear columns.
  forEachModel([](const ScreenModel& m) {
    ScreenModel big = m, detail = m;
    if (m.message1[0]) {  // keep the message layout, without the message's own pixels
      strcpy(big.message1, " ");
      strcpy(detail.message1, " ");
      big.message2[0] = detail.message2[0] = '\0';
    }
    big.detail[0] = '\0';
    detail.big[0] = '\0';
    int rows = m.progress && !m.message1[0] ? 52 : kScreenHeight;  // above the progress bar
    clearScreen(&wide);
    drawMain(&wide, big);
    Ink b = ink(&wide, 0, 9999, rows);
    clearScreen(&wide);
    drawMain(&wide, detail);
    Ink d = ink(&wide, 0, 9999, rows);
    TEST_ASSERT_TRUE(b.any() && d.any());
    TEST_ASSERT_LESS_THAN_INT(d.x0 - 3, b.x1);
  });
}

static void test_usb_shows_no_gauge() {
  ScreenInputs in = inputs(State::Idle, 50, 0);
  in.usb = true;
  Ink usb = render(&screen, drawStatusIcons, screenModel(in));
  // Only the three letters, at the right edge: 17 px of 6x10, nothing where the battery would be.
  TEST_ASSERT_GREATER_THAN_INT(kScreenWidth - 18, usb.x0);
  TEST_ASSERT_EQUAL_INT(kScreenWidth - 1, usb.x1);
}

static void test_bluetooth_rune_only_when_connected() {
  for (int usb = 0; usb < 2; usb++) {
    ScreenInputs in = inputs(State::Running, 50, 10);
    in.usb = usb == 1;
    Ink off = render(&screen, drawStatusIcons, screenModel(in));
    in.bleConnected = true;
    Ink on = render(&screen, drawStatusIcons, screenModel(in));
    // The rune adds a 6x11 shape left of the rest, and nothing else moves.
    TEST_ASSERT_EQUAL_INT(off.x1, on.x1);
    TEST_ASSERT_LESS_OR_EQUAL_INT(off.x0 - 6, on.x0);
    TEST_ASSERT_EQUAL_INT(off.count, ink(&screen, off.x0).count);
    TEST_ASSERT_EQUAL_INT(11, on.y1 - on.y0 + 1);
    TEST_ASSERT_EQUAL_INT(6, ink(&screen, 0, off.x0).x1 - on.x0 + 1);
  }
}

static void test_gauge_draws_one_bar_per_level() {
  ScreenInputs in = inputs(State::Idle, 50, 0);
  in.bars = 0;
  int empty = render(&screen, drawStatusIcons, screenModel(in)).count;
  for (uint8_t bars = 1; bars <= 4; bars++) {
    in.bars = bars;
    int count = render(&screen, drawStatusIcons, screenModel(in)).count;
    TEST_ASSERT_EQUAL_INT(empty + bars * 10, count);  // each bar is 2x5 px
  }
}

static void test_warning_inverts_the_gauge_block() {
  ScreenInputs in = inputs(State::Running, 300, 210);
  in.batteryMv = 6950;
  in.warn = true;
  in.bars = 1;
  Ink on = render(&screen, drawStatusIcons, screenModel(in));
  in.nowMs = OLED_BLINK_MS;
  Ink off = render(&screen, drawStatusIcons, screenModel(in));
  // "On": a solid block to the right edge, still inside the band, with the gauge cut out of it.
  TEST_ASSERT_GREATER_THAN_INT(off.count * 2, on.count);
  TEST_ASSERT_EQUAL_INT(kScreenWidth - 1, on.x1);
  TEST_ASSERT_LESS_OR_EQUAL_INT(off.x0, on.x0);
  TEST_ASSERT_LESS_THAN_INT(kStatusBarRows, on.y1);
  int width = on.x1 - on.x0 + 1, height = on.y1 - on.y0 + 1;
  TEST_ASSERT_EQUAL_INT(width * height - off.count, on.count);  // exactly the negative
}

static void test_progress_bar_fills_with_the_count() {
  int previous = -1;
  for (uint32_t count : {0u, 75u, 150u, 299u, 300u, 304u}) {
    ScreenModel m = model(State::Running, 300, count);
    m.big[0] = m.detail[0] = '\0';  // the bar alone
    Ink bar = render(&screen, drawMain, m);
    TEST_ASSERT_EQUAL_INT(0, bar.x0);
    TEST_ASSERT_EQUAL_INT(kScreenWidth - 1, bar.x1);
    TEST_ASSERT_GREATER_OR_EQUAL_INT(previous, bar.count);
    previous = bar.count;
  }
}

int main() {
  u8g2_Setup_ssd1306_i2c_128x64_noname_f(&screen, U8G2_R0, u8x8_byte_empty, u8x8_dummy_cb);
  u8g2_Setup_ssd1322_nhd_256x64_f(&wide, U8G2_R0, u8x8_byte_empty, u8x8_dummy_cb);
  u8g2_InitDisplay(&screen);
  u8g2_InitDisplay(&wide);

  UNITY_BEGIN();
  RUN_TEST(test_idle_shows_target);
  RUN_TEST(test_testing_shows_test_and_the_target);
  RUN_TEST(test_running_shows_count_over_target_and_progress);
  RUN_TEST(test_slowdown);
  RUN_TEST(test_done_shows_final_count_with_overshoot_and_a_full_bar);
  RUN_TEST(test_jam_message_goes_in_the_main_area);
  RUN_TEST(test_low_batt_message_goes_in_the_main_area);
  RUN_TEST(test_usb_shows_usb_no_gauge_and_never_warns);
  RUN_TEST(test_voltage_rounding);
  RUN_TEST(test_bluetooth_follows_the_connection);
  RUN_TEST(test_labels_fit_their_buffers);
  RUN_TEST(test_model_changes_only_when_content_changes);
  RUN_TEST(test_warning_blink_redraws_at_most_twice_a_second);
  RUN_TEST(test_no_pixel_on_the_gap_row);
  RUN_TEST(test_nothing_past_the_right_edge);
  RUN_TEST(test_each_part_stays_in_its_band);
  RUN_TEST(test_label_never_touches_the_icons);
  RUN_TEST(test_longest_label_fits_with_everything);
  RUN_TEST(test_big_number_never_touches_its_detail);
  RUN_TEST(test_usb_shows_no_gauge);
  RUN_TEST(test_bluetooth_rune_only_when_connected);
  RUN_TEST(test_gauge_draws_one_bar_per_level);
  RUN_TEST(test_warning_inverts_the_gauge_block);
  RUN_TEST(test_progress_bar_fills_with_the_count);
  return UNITY_END();
}
