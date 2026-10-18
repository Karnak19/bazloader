// The OLED layout: draws a ScreenModel into a U8g2 frame buffer. U8g2's C core only, no Arduino,
// so the host tests render the very same pixels (`pio test -e native`).
//
// Laid out for the common yellow/blue SSD1306 module, whose colours are a fixed filter: the top
// 16 rows show yellow, the rest blue, with a dark gap between them. The status bar lives in the
// yellow band, everything else in the blue one, and nothing is ever drawn on the gap row, so no
// glyph is cut in two. On a single-colour module the gap is just a blank line.
#pragma once

#include <clib/u8g2.h>

#include "screen.h"

constexpr int kScreenWidth = 128;
constexpr int kScreenHeight = 64;
constexpr int kStatusBarRows = 16;  // rows 0-15: the status bar (yellow)
constexpr int kGapRow = 16;         // never lit
constexpr int kMainTop = 17;        // rows 17-63: the main area (blue)

// Clears the buffer and draws `m` into it. Doesn't send anything to the display.
void drawScreen(u8g2_t* u8g2, const ScreenModel& m);

// drawScreen() is these, in order. Separate so the tests can check where each part lands.
void clearScreen(u8g2_t* u8g2);
void drawStatusLabel(u8g2_t* u8g2, const ScreenModel& m);  // status bar, left: the state
void drawStatusIcons(u8g2_t* u8g2, const ScreenModel& m);  // status bar, right: BT, gauge or USB
void drawMain(u8g2_t* u8g2, const ScreenModel& m);         // main area: number, message, progress
