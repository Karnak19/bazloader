#include "display.h"

#include <Arduino.h>
#include <U8g2lib.h>
#include <Wire.h>

#include "config.h"
#include "screen_draw.h"

// Full frame buffer (1 KB): one sendBuffer() per redraw. The pins are passed too, so U8g2's own
// Wire.begin() keeps ours instead of falling back to the default ones.
static U8G2_SSD1306_128X64_NONAME_F_HW_I2C oled(U8G2_R0, U8X8_PIN_NONE, PIN_I2C_SCL, PIN_I2C_SDA);

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
  drawScreen(oled.getU8g2(), m);  // the layout, shared with the host tests
  oled.sendBuffer();
  return micros() - start;
}
