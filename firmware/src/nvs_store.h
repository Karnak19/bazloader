// `Store` on the ESP32's NVS through Arduino `Preferences`. Loop context only: never call it from
// an ISR or a BLE callback (NVS writes go to flash and can take tens of ms).
#pragma once

#include <Preferences.h>

#include "settings.h"

class NvsStore : public Store {
 public:
  // Opens the namespace read-write. Returns false if NVS isn't usable: the settings then stay at
  // their defaults and writes are dropped.
  bool begin(const char* ns);
  size_t read(const char* key, void* buf, size_t size) override;
  void write(const char* key, const void* buf, size_t len) override;

 private:
  Preferences prefs_;
  bool open_ = false;
};
