// Battery guard: smoothing, USB detection, warn flag, start refusal and sag abort.
// Plain C++ with no Arduino include, so `pio test -e native` can run it on the host.
#pragma once

#include <stdint.h>

struct BatteryConfig {
  uint16_t warnMv;        // warn below this
  uint16_t refuseMv;      // refuse GO below this
  uint16_t hysteresisMv;  // a low or warn flag clears only this far above its threshold
  uint16_t usbBelowMv;    // below this there's no battery: USB power, guard off
  uint16_t sagMs;         // during a run, abort only after this long below refuseMv
};

// Battery voltage from the ADC pin voltage: divider ratio times calibration, rounded.
uint32_t batteryMvFromAdc(uint32_t adcMv, float dividerRatio, float calibration);

class Battery {
 public:
  explicit Battery(BatteryConfig cfg) : cfg_(cfg) {}

  // One reading (battery mV, already scaled). `running` is whether the servo is driven:
  // under load the voltage sags, so the start guard is frozen and the sag timer runs instead.
  void update(uint32_t nowMs, uint32_t readingMv, bool running);

  // Smoothed voltage, 0 on USB power (and before the first reading).
  uint16_t mv() const { return usb() ? 0 : filteredMv_; }
  bool usb() const { return filteredMv_ < cfg_.usbBelowMv; }
  bool warn() const { return !usb() && warn_; }
  // Whether GO is allowed. Always true on USB: with no battery the servo has no power anyway.
  bool ok() const { return usb() || !low_; }
  // Whether the current run must stop: below refuseMv for sagMs.
  bool sagged() const { return sagged_; }

 private:
  BatteryConfig cfg_;
  uint32_t readings_[3] = {0, 0, 0};  // last three, for the median
  uint8_t next_ = 0;
  bool primed_ = false;
  uint16_t filteredMv_ = 0;
  bool low_ = false;
  bool warn_ = false;
  bool sagged_ = false;
  bool lowInRun_ = false;
  uint32_t lowSinceMs_ = 0;
};
