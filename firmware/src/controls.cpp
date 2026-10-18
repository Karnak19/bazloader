#include "controls.h"

int32_t EncoderAccel::apply(int32_t detents, uint32_t nowMs) {
  if (detents == 0) return 0;
  int8_t dir = detents > 0 ? 1 : -1;
  int32_t n = detents > 0 ? detents : -detents;
  bool fast = primed_ && dir == lastDir_ && nowMs - lastMs_ < fastMs_;
  int32_t change = fast ? fastStep_ : 1;  // the first detent of the batch
  change += (n - 1) * fastStep_;          // the others came within one loop pass: fast
  primed_ = true;
  lastDir_ = dir;
  lastMs_ = nowMs;
  return dir * change;
}

ButtonEvent Button::update(uint32_t nowMs, bool pressed) {
  if (pressed != raw_) {
    raw_ = pressed;
    rawSinceMs_ = nowMs;
  }
  if (raw_ != stable_ && nowMs - rawSinceMs_ >= debounceMs_) {
    stable_ = raw_;
    if (stable_) {
      pressedAtMs_ = nowMs;
      longSent_ = false;
      return ButtonEvent::Press;
    }
    return longSent_ ? ButtonEvent::None : ButtonEvent::ShortClick;
  }
  if (stable_ && !longSent_ && nowMs - pressedAtMs_ >= longMs_) {
    longSent_ = true;
    return ButtonEvent::LongClick;
  }
  return ButtonEvent::None;
}

Presets defaultPresets() {
  Presets p;
  for (uint8_t i = 0; i < PRESET_COUNT; i++) p.values[i] = DEFAULT_PRESETS[i];
  return p;
}

uint16_t nextPreset(const Presets& presets, uint16_t current) {
  for (uint8_t i = 0; i < PRESET_COUNT; i++) {
    if (presets.values[i] == current) return presets.values[(i + 1) % PRESET_COUNT];
  }
  // Not a preset (turned by hand): the smallest preset above it, else wrap to the first.
  uint16_t best = 0;
  for (uint8_t i = 0; i < PRESET_COUNT; i++) {
    uint16_t v = presets.values[i];
    if (v > current && (best == 0 || v < best)) best = v;
  }
  return best ? best : presets.values[0];
}

static bool inRun(State s) {
  return s == State::Running || s == State::Slowdown || s == State::Testing;
}

UiAction goAction(State state, bool batteryOk) {
  if (inRun(state)) return UiAction::Stop;
  if (state == State::LowBatt && !batteryOk) return UiAction::None;
  return UiAction::Start;
}

UiAction ClickHandler::handle(ButtonEvent event, State state) {
  switch (event) {
    case ButtonEvent::None:
      return UiAction::None;
    case ButtonEvent::Press:
      swallow_ = inRun(state);
      return swallow_ ? UiAction::Stop : UiAction::None;
    case ButtonEvent::ShortClick:
      if (swallow_) {
        swallow_ = false;
        return UiAction::None;
      }
      return inRun(state) ? UiAction::Stop : UiAction::NextPreset;
    case ButtonEvent::LongClick:
      // Reserved for the settings menu. The release that follows sends no ShortClick.
      return inRun(state) ? UiAction::Stop : UiAction::None;
  }
  return UiAction::None;
}
