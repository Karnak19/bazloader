// Run logic: state machine, BB counter and servo pulse maths.
// Plain C++ with no Arduino include, so `pio test -e native` can run it on the host.
#pragma once

#include <stdint.h>

#include "ble_uuids.h"

// The counter is called from an ISR on the ESP32; on the host there is no IRAM.
#if __has_include(<esp_attr.h>)
#include <esp_attr.h>
#endif
#ifndef IRAM_ATTR
#define IRAM_ATTR
#endif

uint16_t clampTarget(int32_t target);

// BB counter shared between the count ISR (writer) and loop() (reader).
// Every field is a single aligned word, so each read or write is atomic on the C3.
struct Counter {
  uint32_t minIntervalUs;
  volatile uint32_t count = 0;
  volatile uint32_t stopAt = 0;    // count that ends the run
  volatile bool enabled = false;   // count only between GO and the end of the run
  volatile uint32_t lastUs = 0;    // time of the last accepted pulse
  volatile bool primed = false;    // false until the first pulse ever: no interval to check

  explicit Counter(uint32_t minIntervalUs) : minIntervalUs(minIntervalUs) {}

  // Resets the count for a new run. Safe against the ISR: nothing counts until the last line.
  void arm(uint32_t target) {
    enabled = false;  // first, so a pulse landing mid-way isn't counted against stale fields
    count = 0;
    stopAt = target;
    enabled = true;
  }

  // One beam cut. Returns true on the pulse that reaches stopAt: the caller cuts the servo.
  // The interval runs from the last accepted pulse; rejected ones don't extend it.
  IRAM_ATTR bool pulse(uint32_t nowUs) {
    if (primed && nowUs - lastUs < minIntervalUs) return false;
    primed = true;
    lastUs = nowUs;
    if (!enabled) return false;
    count = count + 1;
    return count == stopAt;
  }
};

enum class Speed : uint8_t { Off, Full, Slow };

struct RunConfig {
  uint8_t slowdownN;
  uint16_t jamTimeoutMs;
  uint16_t firstBbTimeoutMs;
  uint16_t doneHoldMs;
};

class Run {
 public:
  explicit Run(RunConfig cfg) : cfg_(cfg) {}

  State state() const { return state_; }
  uint16_t target() const { return target_; }
  Speed speed() const;
  bool counting() const;  // whether BBs should still be counted. Never during a test spin.

  // Ignored during a run. Returns the target in use.
  uint16_t setTarget(int32_t target);
  // New slowdown N and jam timeout, from the runtime config. Refused (false) during a run.
  bool setTiming(uint8_t slowdownN, uint16_t jamTimeoutMs);
  // Starts a run from any stopped state (not from TESTING). Returns true if the servo should start.
  bool go(uint32_t nowMs, bool batteryOk);
  // Test spin (calibration): TESTING at `speed` (Full or Slow) until stop. No counting, no jam.
  // Accepted from the same states as GO, and from TESTING to switch speed; refused during a run.
  // A low battery refuses it like GO does (LOW_BATT). Returns true if the servo should spin.
  bool test(Speed speed, bool batteryOk);
  // Any state -> IDLE. The count stays wherever the caller keeps it.
  void stop() { state_ = State::Idle; }
  // The battery stayed flat under load: a run or a test spin ends in LOW_BATT. Ignored otherwise.
  void lowBattery();
  // Drives the transitions from the current count and time.
  void update(uint32_t nowMs, uint32_t count);

 private:
  RunConfig cfg_;
  State state_ = State::Idle;
  uint16_t target_ = 50;
  uint32_t lastCount_ = 0;
  uint32_t lastBbMs_ = 0;  // time of the last new BB (or of GO)
  uint32_t doneMs_ = 0;
  Speed testSpeed_ = Speed::Off;
};

// Servo pulse width for a speed. `reverse` flips the offset; Off returns 0 (no pulse).
uint16_t servoPulseUs(Speed speed, uint16_t neutralUs, int16_t fullOffsetUs,
                      int16_t slowOffsetUs, bool reverse);
// Same, from the runtime config (neutral, offsets, reverse).
uint16_t servoPulseUs(Speed speed, const ConfigV1& cfg);
// LEDC duty for a pulse width at 50 Hz (20 ms period), rounded.
constexpr uint32_t servoDuty(uint16_t pulseUs, uint8_t resolutionBits) {
  return ((static_cast<uint32_t>(pulseUs) << resolutionBits) + 10000) / 20000;
}

// LEDC duty for a stopped servo: 0 (no pulse), or the neutral pulse if SERVO_STOP_NEUTRAL.
uint32_t servoStopDuty(uint16_t neutralUs);

const char* stateName(State state);
