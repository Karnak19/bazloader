#include "run.h"

#include "config.h"

uint16_t clampTarget(int32_t target) {
  if (target < TARGET_MIN) return TARGET_MIN;
  if (target > TARGET_MAX) return TARGET_MAX;  // same range as the BLE protocol
  return static_cast<uint16_t>(target);
}

static bool isRunning(State s) { return s == State::Running || s == State::Slowdown; }

Speed Run::speed() const {
  if (state_ == State::Running) return Speed::Full;
  if (state_ == State::Slowdown) return Speed::Slow;
  return Speed::Off;
}

// DONE keeps counting so the BBs pushed after the stop (overshoot) show up.
bool Run::counting() const { return isRunning(state_) || state_ == State::Done; }

uint16_t Run::setTarget(int32_t target) {
  if (!isRunning(state_)) target_ = clampTarget(target);
  return target_;
}

bool Run::go(uint32_t nowMs, bool batteryOk) {
  if (isRunning(state_)) return false;
  if (!batteryOk) {
    state_ = State::LowBatt;
    return false;
  }
  // A target within the slowdown window starts slow straight away.
  state_ = target_ <= cfg_.slowdownN ? State::Slowdown : State::Running;
  lastCount_ = 0;
  lastBbMs_ = nowMs;
  return true;
}

void Run::update(uint32_t nowMs, uint32_t count) {
  if (state_ == State::Done) {
    if (nowMs - doneMs_ >= cfg_.doneHoldMs) state_ = State::Idle;
    return;
  }
  if (!isRunning(state_)) return;

  if (count >= target_) {
    state_ = State::Done;
    doneMs_ = nowMs;
    return;
  }
  if (count != lastCount_) {
    lastCount_ = count;
    lastBbMs_ = nowMs;
  }
  // The first BB comes late: the mechanism spins up and the feed fills.
  uint32_t timeout = lastCount_ == 0 ? cfg_.firstBbTimeoutMs : cfg_.jamTimeoutMs;
  if (nowMs - lastBbMs_ >= timeout) {
    state_ = State::Jam;
    return;
  }
  if (target_ - count <= cfg_.slowdownN) state_ = State::Slowdown;
}

uint16_t servoPulseUs(Speed speed, uint16_t neutralUs, int16_t fullOffsetUs,
                      int16_t slowOffsetUs, bool reverse) {
  if (speed == Speed::Off) return 0;
  int32_t offset = speed == Speed::Full ? fullOffsetUs : slowOffsetUs;
  if (reverse) offset = -offset;
  return static_cast<uint16_t>(neutralUs + offset);
}

const char* stateName(State state) {
  switch (state) {
    case State::Idle: return "IDLE";
    case State::Running: return "RUNNING";
    case State::Slowdown: return "SLOWDOWN";
    case State::Done: return "DONE";
    case State::Jam: return "JAM";
    case State::LowBatt: return "LOW_BATT";
    case State::Testing: return "TESTING";
  }
  return "?";
}
