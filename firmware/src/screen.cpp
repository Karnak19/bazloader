#include "screen.h"

#include <stdio.h>

static void copy(char* dst, size_t size, const char* src) {
  snprintf(dst, size, "%s", src);
}

ScreenModel screenModel(State state, uint16_t target, uint32_t count, uint16_t batteryMv,
                        bool usb, bool warn) {
  ScreenModel m;
  memset(&m, 0, sizeof(m));  // operator== compares raw bytes, unused tails included

  // Two lines of at most ~11 characters each: the battery shares the first line.
  const char* line1 = "";
  const char* line2 = "";
  bool showCount = true;
  switch (state) {
    case State::Idle: line1 = "Prêt"; showCount = false; break;
    case State::Running: line1 = "Chargement"; break;
    case State::Slowdown: line1 = "Ralenti"; break;
    case State::Done: line1 = "Terminé"; break;
    case State::Jam: line1 = "Bourrage /"; line2 = "trémie vide"; break;
    // GO was refused, or a run stopped on a flat pack: show what GO would load next.
    case State::LowBatt: line1 = "Batterie"; line2 = "faible"; showCount = false; break;
    case State::Testing: line1 = "Test moteur"; showCount = false; break;
  }
  copy(m.status1, sizeof(m.status1), line1);
  copy(m.status2, sizeof(m.status2), line2);

  if (usb) {
    copy(m.battery, sizeof(m.battery), "USB");
  } else {
    unsigned tenths = (batteryMv + 50) / 100;  // 7350 mV -> "7.4 V"
    snprintf(m.battery, sizeof(m.battery), "%u.%u V", tenths / 10, tenths % 10);
  }
  m.batteryWarn = warn && !usb;

  if (showCount) {
    snprintf(m.big, sizeof(m.big), "%lu", (unsigned long)count);
    snprintf(m.detail, sizeof(m.detail), "/ %u", target);
  } else {
    snprintf(m.big, sizeof(m.big), "%u", target);
    copy(m.detail, sizeof(m.detail), "Cible");
  }
  return m;
}
