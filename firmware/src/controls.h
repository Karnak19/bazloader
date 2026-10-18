// On-device controls: KY-040 encoder decoding and acceleration, button debounce and clicks,
// presets, and what GO or a click does in each state.
// Plain C++ with no Arduino include, so `pio test -e native` can run it on the host.
#pragma once

#include <stdint.h>

#include "config.h"
#include "run.h"  // State, clampTarget, IRAM_ATTR

// Quadrature decoder, fed from the A/B pin-change ISR. Only single-bit transitions between
// neighbouring states count (+1 or -1); a contact bouncing back and forth cancels itself out and
// a jump over a state (both bits changed) is ignored. A detent is `stepsPerDetent` net steps.
// `position` has a single writer (the ISR) and is one aligned word: loop() reads it atomically.
struct Encoder {
  uint8_t stepsPerDetent;
  volatile uint8_t ab = 0;        // last A/B level, A in bit 1
  volatile int8_t steps = 0;      // transitions since the last detent
  volatile int32_t position = 0;  // detents since boot

  Encoder(uint8_t stepsPerDetent, uint8_t initialAb)
      : stepsPerDetent(stepsPerDetent), ab(initialAb & 3) {}

  IRAM_ATTR void edge(bool a, bool b) {
    // State table indexed by old AB then new AB, as two bitmasks rather than an array so it is
    // immediates in the ISR's own code, not data in flash. +1 is 00>10>11>01>00, -1 the reverse.
    constexpr uint16_t kUp = 1u << 0b0010 | 1u << 0b1011 | 1u << 0b1101 | 1u << 0b0100;
    constexpr uint16_t kDown = 1u << 0b0001 | 1u << 0b0111 | 1u << 0b1110 | 1u << 0b1000;
    uint8_t now = (a ? 2 : 0) | (b ? 1 : 0);
    uint8_t index = (ab << 2) | now;
    int8_t dir = (kUp >> index) & 1 ? 1 : (kDown >> index) & 1 ? -1 : 0;
    ab = now;
    if (dir == 0) return;
    int8_t s = steps + dir;
    if (s >= stepsPerDetent) {
      position = position + 1;
      s = 0;
    } else if (s <= -stepsPerDetent) {
      position = position - 1;
      s = 0;
    } else if (now == 3) {
      // Both high is a rest position on every KY-040. Getting here off-count means a fast turn
      // skipped a state: count the detent if most of it was seen, and resync either way.
      if (2 * s >= stepsPerDetent) position = position + 1;
      else if (2 * s <= -stepsPerDetent) position = position - 1;
      s = 0;
    }
    steps = s;
  }
};

// Turns detents into a target change: x`fastStep` while detents come less than `fastMs` apart
// in the same direction. Detents read together in one batch count as fast after the first.
class EncoderAccel {
 public:
  EncoderAccel(uint16_t fastMs, uint8_t fastStep) : fastMs_(fastMs), fastStep_(fastStep) {}
  int32_t apply(int32_t detents, uint32_t nowMs);

 private:
  uint16_t fastMs_;
  uint8_t fastStep_;
  bool primed_ = false;
  int8_t lastDir_ = 0;
  uint32_t lastMs_ = 0;
};

enum class ButtonEvent : uint8_t { None, Press, ShortClick, LongClick };

// Debounced push button, polled from loop(). Press fires as soon as the press is stable;
// LongClick fires once while still held at longMs; ShortClick on a release before that.
class Button {
 public:
  Button(uint16_t debounceMs, uint16_t longMs) : debounceMs_(debounceMs), longMs_(longMs) {}
  ButtonEvent update(uint32_t nowMs, bool pressed);

 private:
  uint16_t debounceMs_;
  uint16_t longMs_;
  bool raw_ = false;
  bool stable_ = false;
  bool longSent_ = false;
  uint32_t rawSinceMs_ = 0;
  uint32_t pressedAtMs_ = 0;
};

// Runtime copy of the presets. Defaults from config.h for now; NVS (#4) will load them here.
struct Presets {
  uint16_t values[PRESET_COUNT];
};
Presets defaultPresets();
// The preset after `current`: the next one in the list if `current` is a preset, else the first
// preset above it, wrapping to the first.
uint16_t nextPreset(const Presets& presets, uint16_t current);

enum class UiAction : uint8_t { None, Start, Stop, NextPreset };

// GO button (on Press): starts from IDLE, DONE, JAM and LOW_BATT, stops otherwise.
// In LOW_BATT with the battery still low it does nothing, so the message stays up.
UiAction goAction(State state, bool batteryOk);

// Encoder click. Any press during a run stops it straight away (on the press, not the release),
// and that press's release is then swallowed so it doesn't also cycle the preset.
// Outside a run a short click cycles presets; a long click is reserved for a menu (no-op).
class ClickHandler {
 public:
  UiAction handle(ButtonEvent event, State state);

 private:
  bool swallow_ = false;
};
