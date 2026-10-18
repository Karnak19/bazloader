// What the OLED shows, as plain text fields. The Arduino layer only draws them, and redraws only
// when this changes. Plain C++ with no Arduino include, so `pio test -e native` can run it.
// Texts are UTF-8 (French accents): draw them with a font that has the glyphs and drawUTF8().
#pragma once

#include <stdint.h>
#include <string.h>

#include "ble_uuids.h"

struct ScreenModel {
  char status1[16];   // state, first line
  char status2[16];   // state, second line (empty for short labels)
  char battery[12];   // "7.4 V" or "USB"
  bool batteryWarn;   // draw a warning marker next to the battery
  char big[8];        // the big number: the target at rest, the count during and after a run
  char detail[12];    // next to it: "Cible", or "/ 50" when the big number is the count

  bool operator==(const ScreenModel& o) const { return memcmp(this, &o, sizeof(*this)) == 0; }
  bool operator!=(const ScreenModel& o) const { return !(*this == o); }
};

// `batteryMv` is ignored when `usb`.
ScreenModel screenModel(State state, uint16_t target, uint32_t count, uint16_t batteryMv,
                        bool usb, bool warn);
