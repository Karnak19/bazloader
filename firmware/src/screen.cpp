#include "screen.h"

#include <stdio.h>

#include "config.h"

static void copy(char* dst, size_t size, const char* src) {
  snprintf(dst, size, "%s", src);
}

ScreenModel screenModel(const ScreenInputs& in) {
  ScreenModel m;
  memset(&m, 0, sizeof(m));  // operator== compares raw bytes, unused tails included

  // The label fits the status bar next to the gauge; a longer explanation goes below it, in the
  // main area, on two lines.
  const char* label = "";
  const char* message1 = "";
  const char* message2 = "";
  bool showCount = true;
  bool progress = false;
  switch (in.state) {
    case State::Idle: label = "Prêt"; showCount = false; break;
    case State::Running: label = "Chargement"; progress = true; break;
    case State::Slowdown: label = "Ralenti"; progress = true; break;
    case State::Done: label = "Terminé"; progress = true; break;
    case State::Jam: label = "Arrêt"; message1 = "Bourrage /"; message2 = "trémie vide"; break;
    // GO was refused, or a run stopped on a flat pack: show what GO would load next.
    case State::LowBatt:
      label = "Arrêt";
      message1 = "Batterie";
      message2 = "faible";
      showCount = false;
      break;
    case State::Testing: label = "Test moteur"; showCount = false; break;
  }
  copy(m.label, sizeof(m.label), label);
  copy(m.message1, sizeof(m.message1), message1);
  copy(m.message2, sizeof(m.message2), message2);

  m.bluetooth = in.bleConnected;
  m.usb = in.usb;
  if (!in.usb) {
    m.bars = in.bars > 4 ? 4 : in.bars;
    unsigned tenths = (in.batteryMv + 50) / 100;  // 7350 mV -> "7.4V"
    snprintf(m.volts, sizeof(m.volts), "%u.%uV", tenths / 10, tenths % 10);
    // Inverted every other OLED_BLINK_MS: the model, so the screen, changes at most that often.
    m.inverted = in.warn && (in.nowMs / OLED_BLINK_MS) % 2 == 0;
  }

  if (showCount) {
    snprintf(m.big, sizeof(m.big), "%lu", (unsigned long)in.count);
    snprintf(m.detail, sizeof(m.detail), "/ %u", in.target);
  } else {
    snprintf(m.big, sizeof(m.big), "%u", in.target);
    copy(m.detail, sizeof(m.detail), "Cible");
  }
  if (progress && in.target > 0) {
    uint32_t done = in.count < in.target ? in.count : in.target;
    m.progress = true;
    m.progressPx = static_cast<uint8_t>(done * kProgressMaxPx / in.target);
  }
  return m;
}
