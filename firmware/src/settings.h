// Persisted settings: the servo/run config (ConfigV1), the presets and the last target.
// Validation, fallback to defaults, write-on-change and the delayed target save live here.
// Plain C++ with no Arduino include, so `pio test -e native` can run it on the host; the actual
// NVS access is behind `Store`, implemented with `Preferences` in nvs_store.cpp.
#pragma once

#include <stddef.h>
#include <stdint.h>

#include "ble_uuids.h"
#include "controls.h"  // Presets

// Key/value byte storage. read() returns the stored length (0 if missing) and copies the bytes
// only if they fit in `size`, so a caller can tell a blob of the wrong length.
struct Store {
  virtual size_t read(const char* key, void* buf, size_t size) = 0;
  virtual void write(const char* key, const void* buf, size_t len) = 0;
};

// Storage keys, in the `bulloader` namespace.
constexpr const char* KEY_CONFIG = "config";
constexpr const char* KEY_PRESETS = "presets";
constexpr const char* KEY_TARGET = "target";

enum class LoadResult : uint8_t { Ok, Missing, BadLength, BadVersion, OutOfRange };
const char* loadResultName(LoadResult r);

ConfigV1 defaultConfig();
bool configValid(const ConfigV1& cfg);
bool presetsValid(const Presets& presets);
bool targetValid(uint16_t target);

// Parse a stored blob. Anything but Ok leaves the defaults in `out`, never part of the blob.
LoadResult parseConfig(const void* data, size_t len, ConfigV1* out);
LoadResult parsePresets(const void* data, size_t len, Presets* out);
LoadResult parseTarget(const void* data, size_t len, uint16_t* out);

struct LoadReport {
  LoadResult config, presets, target;
};

class Settings {
 public:
  Settings(Store& store, uint16_t targetSaveDelayMs);

  // Reads all three from the store; each one invalid or missing falls back to its default.
  LoadReport load();

  const ConfigV1& config() const { return config_; }
  const Presets& presets() const { return presets_; }
  uint16_t target() const { return savedTarget_; }  // the last saved (or loaded) target

  // Validate, keep and persist (only if different). A config is refused while `running`.
  // false means nothing changed. Call from loop() only, never from an ISR or a BLE callback.
  bool setConfig(const ConfigV1& cfg, bool running);
  bool setPresets(const Presets& presets);

  // Call every loop pass with the current target. It is written once it has stayed unchanged for
  // the save delay, and only if it differs from the saved one. Returns true when it wrote.
  bool updateTarget(uint16_t target, uint32_t nowMs);

 private:
  Store& store_;
  uint16_t saveDelayMs_;
  ConfigV1 config_;
  Presets presets_;
  uint16_t savedTarget_;
  uint16_t seenTarget_;
  uint32_t changedMs_ = 0;
  bool pending_ = false;
};
