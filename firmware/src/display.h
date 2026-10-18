// SSD1306 OLED glue (U8g2). Draws a ScreenModel; the layout lives here, the content in screen.cpp.
#pragma once

#include <stdint.h>

#include "screen.h"

// Starts I2C and the display. Returns whether a display answered at OLED_I2C_ADDRESS.
bool displayBegin();
// Draws the whole frame and sends it. Blocks for the I2C transfer: returns how long, in us.
uint32_t displayDraw(const ScreenModel& m);
