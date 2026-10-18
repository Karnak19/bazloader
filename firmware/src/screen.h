// What the OLED shows, as plain fields. screen_draw.cpp turns it into pixels, and the Arduino layer
// redraws only when this changes. Plain C++ with no Arduino include, so `pio test -e native` can
// run it. Texts are UTF-8 (French accents): draw them with a font that has the glyphs.
#pragma once

#include <stdint.h>
#include <string.h>

#include "ble_uuids.h"

// Everything the screen depends on, read in loop().
struct ScreenInputs {
  State state;
  uint16_t target;
  uint32_t count;
  uint16_t batteryMv;  // ignored on USB
  bool usb;
  bool warn;           // low-battery warning (never on USB)
  uint8_t bars;        // battery gauge, 0-4 (gaugeBars())
  bool bleConnected;   // a phone is connected
  uint32_t nowMs;      // for the warning blink
};

struct ScreenModel {
  // Status bar (the yellow band on two-colour modules).
  char label[16];     // state, one short word or two
  bool bluetooth;     // the Bluetooth rune, only while a phone is connected
  bool usb;           // "USB" instead of the gauge
  uint8_t bars;       // gauge bars, 0-4
  char volts[8];      // "7.4V"
  bool inverted;      // gauge and voltage drawn inverted: the warning, in its "on" phase

  // Main area (blue band).
  char message1[16];  // a two-line message (jam, low battery), empty otherwise
  char message2[16];
  char big[8];        // the big number: the target at rest, the count during and after a run
  char detail[12];    // next to it: "Cible", or "/ 50" when the big number is the count
  bool progress;      // show the progress bar (during and after a run)
  uint8_t progressPx; // its filled width, 0 to kProgressMaxPx

  bool operator==(const ScreenModel& o) const { return memcmp(this, &o, sizeof(*this)) == 0; }
  bool operator!=(const ScreenModel& o) const { return !(*this == o); }
};

// Inner width of the progress bar, in pixels: the model stores the fill already scaled, so a count
// that doesn't move the bar by a pixel doesn't change the model either.
constexpr uint8_t kProgressMaxPx = 124;

ScreenModel screenModel(const ScreenInputs& in);
