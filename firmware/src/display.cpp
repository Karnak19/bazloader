#include "display.h"

#include <Arduino.h>
#include <U8g2lib.h>
#include <Wire.h>

#include "config.h"

// Full frame buffer (1 KB): one sendBuffer() per redraw. The pins are passed too, so U8g2's own
// Wire.begin() keeps ours instead of falling back to the default ones.
static U8G2_SSD1306_128X64_NONAME_F_HW_I2C oled(U8G2_R0, U8X8_PIN_NONE, PIN_I2C_SCL, PIN_I2C_SDA);

// _tf fonts cover the full 32-255 range, so é, è and ê are there (the _tr variants stop at 127).
static const uint8_t* const kStatusFont = u8g2_font_7x13B_tf;
static const uint8_t* const kSmallFont = u8g2_font_6x10_tf;
static const uint8_t* const kBigFont = u8g2_font_logisoso24_tn;  // digits only

bool displayBegin() {
  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
  Wire.beginTransmission(OLED_I2C_ADDRESS);
  bool found = Wire.endTransmission() == 0;
  oled.setI2CAddress(OLED_I2C_ADDRESS << 1);  // U8g2 wants the 8-bit form
  oled.setBusClock(OLED_I2C_HZ);
  oled.begin();
  return found;
}

uint32_t displayDraw(const ScreenModel& m) {
  uint32_t start = micros();
  oled.clearBuffer();

  // Battery, top right, with a warning triangle in front of it when low.
  oled.setFont(kSmallFont);
  int16_t w = oled.getUTF8Width(m.battery);
  oled.drawUTF8(128 - w, 9, m.battery);
  if (m.batteryWarn) {
    int16_t x = 128 - w - 10;
    oled.drawTriangle(x, 9, x + 8, 9, x + 4, 0);
    oled.setDrawColor(0);
    oled.drawVLine(x + 4, 4, 3);  // the "!" cut out of the triangle
    oled.setDrawColor(1);
  }

  // State, one or two lines.
  oled.setFont(kStatusFont);
  oled.drawUTF8(0, 11, m.status1);
  oled.drawUTF8(0, 25, m.status2);

  // The big number on the left, the detail right-aligned on the same baseline.
  oled.setFont(kBigFont);
  oled.drawStr(0, 62, m.big);
  oled.setFont(kSmallFont);
  oled.drawUTF8(128 - oled.getUTF8Width(m.detail), 62, m.detail);

  oled.sendBuffer();
  return micros() - start;
}
