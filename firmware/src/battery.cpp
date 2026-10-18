#include "battery.h"

uint32_t batteryMvFromAdc(uint32_t adcMv, float dividerRatio, float calibration) {
  return static_cast<uint32_t>(adcMv * dividerRatio * calibration + 0.5f);
}

static uint32_t median3(uint32_t a, uint32_t b, uint32_t c) {
  if (a > b) {
    uint32_t t = a;
    a = b;
    b = t;
  }
  // With a <= b, the median is c clamped to [a, b].
  if (c <= a) return a;
  if (c >= b) return b;
  return c;
}

// Flag with hysteresis: set below `threshold`, cleared at `threshold + hysteresis` or above.
static bool belowWithHysteresis(bool was, uint32_t mv, uint16_t threshold, uint16_t hysteresis) {
  if (mv < threshold) return true;
  if (mv >= static_cast<uint32_t>(threshold) + hysteresis) return false;
  return was;
}

void Battery::update(uint32_t nowMs, uint32_t readingMv, bool running) {
  // Each reading is already an average of many ADC samples. The median of the last three
  // then drops a single bad reading entirely, which an average would only dilute.
  if (!primed_) {
    readings_[0] = readings_[1] = readings_[2] = readingMv;
    primed_ = true;
  }
  readings_[next_] = readingMv;
  next_ = (next_ + 1) % 3;
  uint32_t m = median3(readings_[0], readings_[1], readings_[2]);
  filteredMv_ = m > 0xFFFF ? 0xFFFF : static_cast<uint16_t>(m);

  warn_ = belowWithHysteresis(warn_, filteredMv_, cfg_.warnMv, cfg_.hysteresisMv);

  if (usb()) {
    low_ = false;
    sagged_ = false;
    lowInRun_ = false;
    return;
  }

  if (!running) {
    // At rest: the start guard follows the voltage. A sag abort stays latched as low until
    // the voltage clears the hysteresis.
    sagged_ = false;
    lowInRun_ = false;
    low_ = belowWithHysteresis(low_, filteredMv_, cfg_.refuseMv, cfg_.hysteresisMv);
    return;
  }

  // Under load: a short dip is the servo pulling current, not a flat pack.
  if (filteredMv_ >= cfg_.refuseMv) {
    lowInRun_ = false;
    return;
  }
  if (!lowInRun_) {
    lowInRun_ = true;
    lowSinceMs_ = nowMs;
  }
  if (nowMs - lowSinceMs_ >= cfg_.sagMs) {
    sagged_ = true;
    low_ = true;
  }
}
