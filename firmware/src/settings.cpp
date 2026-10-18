#include "settings.h"

#include <string.h>

#include "config.h"

const char* loadResultName(LoadResult r) {
  switch (r) {
    case LoadResult::Ok: return "ok";
    case LoadResult::Missing: return "missing";
    case LoadResult::BadLength: return "wrong length";
    case LoadResult::BadVersion: return "wrong version";
    case LoadResult::OutOfRange: return "out of range";
  }
  return "?";
}

ConfigV1 defaultConfig() {
  ConfigV1 c;
  c.version = CONFIG_VERSION;
  c.servo_neutral_us = SERVO_NEUTRAL_US;
  c.speed_full_offset_us = SERVO_FULL_OFFSET_US;
  c.speed_slow_offset_us = SERVO_SLOW_OFFSET_US;
  c.reverse = SERVO_REVERSE ? 1 : 0;
  c.slowdown_n = SLOWDOWN_N;
  c.jam_timeout_ms = JAM_TIMEOUT_MS;
  return c;
}

static bool offsetValid(int16_t us) {
  return us >= -SERVO_OFFSET_MAX_US && us <= SERVO_OFFSET_MAX_US;
}

bool configValid(const ConfigV1& c) {
  // slowdown_n needs no check: SLOWDOWN_N_MAX is the whole uint8 range.
  static_assert(SLOWDOWN_N_MAX == UINT8_MAX, "add a slowdown_n check");
  return c.version == CONFIG_VERSION && c.servo_neutral_us >= SERVO_NEUTRAL_MIN_US &&
         c.servo_neutral_us <= SERVO_NEUTRAL_MAX_US && offsetValid(c.speed_full_offset_us) &&
         offsetValid(c.speed_slow_offset_us) && c.reverse <= 1 &&
         c.jam_timeout_ms >= JAM_TIMEOUT_MIN_MS && c.jam_timeout_ms <= JAM_TIMEOUT_MAX_MS;
}

bool presetsValid(const Presets& p) {
  for (uint8_t i = 0; i < PRESET_COUNT; i++) {
    if (p.values[i] < PRESET_MIN || p.values[i] > PRESET_MAX) return false;
  }
  return true;
}

bool targetValid(uint16_t t) { return t >= TARGET_MIN && t <= TARGET_MAX; }

LoadResult parseConfig(const void* data, size_t len, ConfigV1* out) {
  *out = defaultConfig();
  if (len == 0) return LoadResult::Missing;
  // The version byte first: a future format is more likely a version bump than corruption.
  if (static_cast<const uint8_t*>(data)[0] != CONFIG_VERSION) return LoadResult::BadVersion;
  if (len != sizeof(ConfigV1)) return LoadResult::BadLength;
  ConfigV1 c;
  memcpy(&c, data, sizeof c);
  if (!configValid(c)) return LoadResult::OutOfRange;
  *out = c;
  return LoadResult::Ok;
}

LoadResult parsePresets(const void* data, size_t len, Presets* out) {
  *out = defaultPresets();
  if (len == 0) return LoadResult::Missing;
  if (len != sizeof(Presets)) return LoadResult::BadLength;
  Presets p;
  memcpy(&p, data, sizeof p);
  if (!presetsValid(p)) return LoadResult::OutOfRange;
  *out = p;
  return LoadResult::Ok;
}

LoadResult parseTarget(const void* data, size_t len, uint16_t* out) {
  *out = DEFAULT_TARGET;
  if (len == 0) return LoadResult::Missing;
  if (len != sizeof(uint16_t)) return LoadResult::BadLength;
  uint16_t t;
  memcpy(&t, data, sizeof t);
  if (!targetValid(t)) return LoadResult::OutOfRange;
  *out = t;
  return LoadResult::Ok;
}

static_assert(sizeof(Presets) == PRESET_COUNT * sizeof(uint16_t), "presets stored as uint16[4]");

Settings::Settings(Store& store, uint16_t targetSaveDelayMs)
    : store_(store),
      saveDelayMs_(targetSaveDelayMs),
      config_(defaultConfig()),
      presets_(defaultPresets()),
      savedTarget_(DEFAULT_TARGET),
      seenTarget_(DEFAULT_TARGET) {}

// Reads one key into `buf` (one byte larger than any valid blob) and parses it. A blob too long to
// fit wasn't copied: report it as the wrong length without looking at the buffer.
template <typename T, typename Parse>
static LoadResult loadKey(Store& store, const char* key, T* out, Parse parse) {
  uint8_t buf[sizeof(T) + 1] = {};
  size_t len = store.read(key, buf, sizeof buf);
  if (len > sizeof buf) {
    parse(buf, 0, out);  // fills the defaults
    return LoadResult::BadLength;
  }
  return parse(buf, len, out);
}

LoadReport Settings::load() {
  LoadReport r;
  r.config = loadKey(store_, KEY_CONFIG, &config_, parseConfig);
  r.presets = loadKey(store_, KEY_PRESETS, &presets_, parsePresets);
  r.target = loadKey(store_, KEY_TARGET, &savedTarget_, parseTarget);
  seenTarget_ = savedTarget_;
  pending_ = false;
  return r;
}

bool Settings::setConfig(const ConfigV1& cfg, bool running) {
  if (running || !configValid(cfg)) return false;
  if (memcmp(&cfg, &config_, sizeof cfg) != 0) {
    config_ = cfg;
    store_.write(KEY_CONFIG, &config_, sizeof config_);
  }
  return true;
}

bool Settings::setPresets(const Presets& presets) {
  if (!presetsValid(presets)) return false;
  if (memcmp(&presets, &presets_, sizeof presets) != 0) {
    presets_ = presets;
    store_.write(KEY_PRESETS, &presets_, sizeof presets_);
  }
  return true;
}

bool Settings::updateTarget(uint16_t target, uint32_t nowMs) {
  if (target != seenTarget_) {
    seenTarget_ = target;
    changedMs_ = nowMs;
    pending_ = true;
    return false;
  }
  if (!pending_ || nowMs - changedMs_ < saveDelayMs_) return false;
  pending_ = false;
  if (target == savedTarget_ || !targetValid(target)) return false;
  savedTarget_ = target;
  store_.write(KEY_TARGET, &savedTarget_, sizeof savedTarget_);
  return true;
}
