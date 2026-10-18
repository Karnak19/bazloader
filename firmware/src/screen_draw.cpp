#include "screen_draw.h"

// _tf fonts cover the full 32-255 range, so é, è and ê are there (the _tr variants stop at 127).
static const uint8_t* const kLabelFont = u8g2_font_6x13B_tf;  // status bar: bold, 6 px a glyph
static const uint8_t* const kSmallFont = u8g2_font_6x10_tf;   // voltage, "USB"
static const uint8_t* const kTextFont = u8g2_font_7x13B_tf;   // messages, "/ 300", "Cible"
static const uint8_t* const kBigFont = u8g2_font_logisoso24_tn;  // digits only
static const uint8_t* const kMidFont = u8g2_font_logisoso16_tn;  // digits only, under a message

// ---- Status bar, rows 0-15 ----
// The label on the left; from the right edge: the voltage, the battery, the Bluetooth rune.
// "7.4V" is always 4 glyphs of 6 px, so the icons don't move as the voltage changes.
//   Test moteur  [BT] [battery]7.4V        or        Test moteur  [BT]  USB
constexpr int kBarBaseline = 12;  // label and voltage, with room under it for descenders
constexpr int kIconGap = 2;       // between the battery tip and the voltage
constexpr int kBluetoothGap = 3;  // between the rune and the battery block (or "USB")
constexpr int kBatteryW = 16;     // 15 px body + 1 px tip
constexpr int kBatteryY = 4;      // 9 px tall: rows 4-12
constexpr int kBluetoothW = 6;
constexpr int kBluetoothY = 3;    // 11 px tall: rows 3-13
constexpr int kWarnPad = 2;       // the inverted block reaches this far left of the battery
constexpr int kWarnBoxY = 1;
constexpr int kWarnBoxH = 14;     // rows 1-14

// The Bluetooth rune, 6x11, in 1 px lines (the 45-degree strokes stay crisp).
static void drawBluetooth(u8g2_t* u, int x, int y) {
  u8g2_DrawVLine(u, x + 2, y, 11);
  u8g2_DrawLine(u, x + 2, y, x + 5, y + 3);
  u8g2_DrawLine(u, x + 5, y + 3, x, y + 8);
  u8g2_DrawLine(u, x + 2, y + 10, x + 5, y + 7);
  u8g2_DrawLine(u, x + 5, y + 7, x, y + 2);
}

// A battery lying down, tip on the right, with 0-4 bars of 2 px filling from the left.
static void drawBattery(u8g2_t* u, int x, int y, uint8_t bars) {
  u8g2_DrawFrame(u, x, y, 15, 9);
  u8g2_DrawBox(u, x + 15, y + 3, 1, 3);
  for (uint8_t i = 0; i < bars && i < 4; i++) u8g2_DrawBox(u, x + 2 + i * 3, y + 2, 2, 5);
}

void drawStatusLabel(u8g2_t* u, const ScreenModel& m) {
  u8g2_SetFont(u, kLabelFont);
  u8g2_DrawUTF8(u, 0, kBarBaseline, m.label);
}

void drawStatusIcons(u8g2_t* u, const ScreenModel& m) {
  u8g2_SetFont(u, kSmallFont);
  int left;  // left edge of what is drawn so far, going right to left
  if (m.usb) {
    left = kScreenWidth - u8g2_GetUTF8Width(u, "USB");
    u8g2_DrawUTF8(u, left, kBarBaseline, "USB");
  } else {
    int voltsX = kScreenWidth - u8g2_GetUTF8Width(u, m.volts);
    int batteryX = voltsX - kIconGap - kBatteryW;
    left = batteryX - kWarnPad;
    if (m.inverted) {
      u8g2_DrawBox(u, left, kWarnBoxY, kScreenWidth - left, kWarnBoxH);
      u8g2_SetDrawColor(u, 0);
    }
    drawBattery(u, batteryX, kBatteryY, m.bars);
    u8g2_DrawUTF8(u, voltsX, kBarBaseline, m.volts);
    u8g2_SetDrawColor(u, 1);
  }
  if (m.bluetooth) drawBluetooth(u, left - kBluetoothGap - kBluetoothW, kBluetoothY);
}

// ---- Main area, rows 17-63 ----

static void drawRightAligned(u8g2_t* u, int baseline, const char* text) {
  u8g2_DrawUTF8(u, kScreenWidth - u8g2_GetUTF8Width(u, text), baseline, text);
}

void drawMain(u8g2_t* u, const ScreenModel& m) {
  if (m.message1[0]) {
    // A two-line message, then the number smaller underneath.
    u8g2_SetFont(u, kTextFont);
    u8g2_DrawUTF8(u, 0, 28, m.message1);  // rows 19-30
    u8g2_DrawUTF8(u, 0, 42, m.message2);  // rows 33-44
    u8g2_SetFont(u, kMidFont);
    u8g2_DrawStr(u, 0, 62, m.big);  // rows 46-61
    u8g2_SetFont(u, kTextFont);
    drawRightAligned(u, 62, m.detail);
    return;
  }
  if (m.progress) {
    // The count, then the progress bar under it.
    u8g2_SetFont(u, kBigFont);
    u8g2_DrawStr(u, 0, 45, m.big);  // rows 21-44
    u8g2_SetFont(u, kTextFont);
    drawRightAligned(u, 45, m.detail);
    u8g2_DrawFrame(u, 0, 52, kScreenWidth, 10);  // rows 52-61, the fill 2 px inside
    if (m.progressPx) u8g2_DrawBox(u, 2, 54, m.progressPx, 6);
    return;
  }
  // At rest: the target, centred in the area.
  u8g2_SetFont(u, kBigFont);
  u8g2_DrawStr(u, 0, 52, m.big);  // rows 28-51
  u8g2_SetFont(u, kTextFont);
  drawRightAligned(u, 52, m.detail);
}

void clearScreen(u8g2_t* u8g2) {
  u8g2_ClearBuffer(u8g2);
  u8g2_SetDrawColor(u8g2, 1);
  u8g2_SetFontMode(u8g2, 1);  // transparent: text drawn in colour 0 on the warning block
  u8g2_SetFontPosBaseline(u8g2);
}

void drawScreen(u8g2_t* u8g2, const ScreenModel& m) {
  clearScreen(u8g2);
  drawStatusLabel(u8g2, m);
  drawStatusIcons(u8g2, m);
  drawMain(u8g2, m);
}
