#include "nvs_store.h"

#include <Arduino.h>

bool NvsStore::begin(const char* ns) {
  open_ = prefs_.begin(ns, false);
  return open_;
}

size_t NvsStore::read(const char* key, void* buf, size_t size) {
  // isKey first: getBytesLength() on a missing key logs an NVS error.
  if (!open_ || !prefs_.isKey(key)) return 0;
  size_t len = prefs_.getBytesLength(key);
  if (len > 0 && len <= size) prefs_.getBytes(key, buf, size);
  return len;
}

void NvsStore::write(const char* key, const void* buf, size_t len) {
  if (!open_) return;
  size_t written = prefs_.putBytes(key, buf, len);
  Serial.printf("[%lu ms] nvs: wrote %s (%u bytes)%s\n", (unsigned long)millis(), key,
                (unsigned)len, written == len ? "" : ", FAILED");
}
