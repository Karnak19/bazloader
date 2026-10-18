// BLE logic with no NimBLE in it: decoding and validating writes, applying them, encoding values and
// deciding what to notify when. ble.cpp is the thin NimBLE glue around it.
// Plain C++ with no Arduino include, so `pio test -e native` can run it on the host.
#pragma once

#include <stddef.h>
#include <stdint.h>

#include "ble_uuids.h"
#include "controls.h"  // Presets
#include "run.h"       // Speed

// The characteristics a client can write.
enum class BleChar : uint8_t { Target, Command, Presets, Config };

// The characteristics the device pushes, as bit flags so several fit in one mask.
enum BleField : uint8_t {
  FIELD_TARGET = 1 << 0,
  FIELD_COUNT = 1 << 1,
  FIELD_STATE = 1 << 2,
  FIELD_BATTERY = 1 << 3,
  FIELD_PRESETS = 1 << 4,
  FIELD_CONFIG = 1 << 5,
  FIELD_ALL = 0x3F,
};

// A request handed from the NimBLE task to loop(). Plain bytes, copied through a FreeRTOS queue.
struct BleRequest {
  enum Kind : uint8_t {
    None,          // nothing to do (unknown command)
    SetTarget,     // `target`
    RunCommand,    // `command`, a known value
    SetPresets,    // `presets`
    SetConfig,     // `config`, version 1
    Refresh,       // a write to a readable characteristic that was ignored: push the real value
    Disconnected,  // the client went away
  };
  Kind kind = None;
  BleChar ch = BleChar::Command;  // the characteristic written (Refresh uses it)
  Command command = Command::Stop;
  uint16_t target = 0;
  Presets presets = {};
  ConfigV1 config = {};
};

// Decodes one write. Wrong length or a config version other than 1: Refresh (ignored, and the real
// value goes back so a client reading it isn't left with the rejected bytes). Unknown command: None.
// Doesn't range-check: the target is clamped and presets/config are validated when applied.
// Cheap and allocation-free: safe to call from the NimBLE task.
BleRequest parseWrite(BleChar ch, const uint8_t* data, size_t len);

// What loop() can do for a request: the existing hooks in main.cpp.
struct BleActions {
  virtual State state() = 0;
  virtual uint16_t setTarget(uint16_t target) = 0;  // returns the target in use
  virtual void go() = 0;
  virtual void stop() = 0;
  virtual void test(Speed speed) = 0;
  virtual bool setConfig(const ConfigV1& cfg) = 0;    // false: refused (range or running)
  virtual bool setPresets(const Presets& presets) = 0;  // false: refused (range)
};

// Applies one request. Returns the fields to push back even if they didn't change: every write to
// `target`, `presets` or `config` is answered with the real value, taken or not (refused during a
// run, clamped, out of range, malformed), so the client corrects itself. `target` notifies;
// `presets` and `config` have no notify property, so the answer is the value a read returns.
// presets are taken during a run too (Settings::setPresets doesn't look at the run): they only
// change what the next preset click picks.
// A disconnect stops a test spin; a normal run carries on (it ends on its own).
uint8_t applyBleRequest(const BleRequest& r, BleActions& actions);

// Everything the device publishes.
struct BleValues {
  uint16_t target;
  uint32_t count;
  State state;
  uint16_t batteryMv;  // 0 on USB power
  Presets presets;
  ConfigV1 config;
};

// Little-endian bytes of one field into `out` (at least 11 bytes). Returns the length.
size_t encodeField(BleField field, const BleValues& v, uint8_t* out);

// Decides, every loop pass, which fields to set and notify.
// - target, state: on every change.
// - count: on change, at most once per `countThrottleMs`. A change held back by the throttle is
//   sent as soon as it allows, and straight away with a state change (before the state), so the
//   final count of a run always goes out.
// - battery: every `batteryPeriodMs`.
// - presets, config: on every change.
// - plus whatever force() asked for (writes answered with the real value).
class BleOutbox {
 public:
  BleOutbox(uint32_t countThrottleMs, uint32_t batteryPeriodMs)
      : countThrottleMs_(countThrottleMs), batteryPeriodMs_(batteryPeriodMs) {}

  // Takes `v` as what the characteristics hold now (set before advertising).
  void start(const BleValues& v, uint32_t nowMs);
  void force(uint8_t fields) { forced_ |= fields; }
  // Fields to push for `v` now. Remembers them as sent.
  uint8_t update(const BleValues& v, uint32_t nowMs);

 private:
  uint32_t countThrottleMs_;
  uint32_t batteryPeriodMs_;
  BleValues sent_ = {};
  uint8_t forced_ = 0;
  uint32_t countSentMs_ = 0;
  uint32_t batterySentMs_ = 0;
};
