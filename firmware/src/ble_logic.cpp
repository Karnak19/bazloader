#include "ble_logic.h"

#include <string.h>

static uint16_t readU16(const uint8_t* p) { return static_cast<uint16_t>(p[0] | (p[1] << 8)); }

static void writeU16(uint8_t* p, uint16_t v) {
  p[0] = static_cast<uint8_t>(v);
  p[1] = static_cast<uint8_t>(v >> 8);
}

static BleRequest refresh(BleChar ch) {
  BleRequest r;
  r.kind = BleRequest::Refresh;
  r.ch = ch;
  return r;
}

BleRequest parseWrite(BleChar ch, const uint8_t* data, size_t len) {
  BleRequest r;
  r.ch = ch;
  switch (ch) {
    case BleChar::Target:
      if (len != sizeof(uint16_t)) return refresh(ch);
      r.kind = BleRequest::SetTarget;
      r.target = readU16(data);
      return r;
    case BleChar::Command:
      if (len != 1 || data[0] > static_cast<uint8_t>(Command::TestSlow)) return r;  // None
      r.kind = BleRequest::RunCommand;
      r.command = static_cast<Command>(data[0]);
      return r;
    case BleChar::Presets:
      if (len != PRESET_COUNT * sizeof(uint16_t)) return refresh(ch);
      r.kind = BleRequest::SetPresets;
      for (uint8_t i = 0; i < PRESET_COUNT; i++) r.presets.values[i] = readU16(data + 2 * i);
      return r;
    case BleChar::Config:
      if (len != sizeof(ConfigV1) || data[0] != CONFIG_VERSION) return refresh(ch);
      r.kind = BleRequest::SetConfig;
      memcpy(&r.config, data, sizeof(ConfigV1));  // packed, little-endian like the C3
      return r;
  }
  return r;
}

static uint8_t fieldOf(BleChar ch) {
  switch (ch) {
    case BleChar::Target: return FIELD_TARGET;
    case BleChar::Presets: return FIELD_PRESETS;
    case BleChar::Config: return FIELD_CONFIG;
    case BleChar::Command: return 0;
  }
  return 0;
}

uint8_t applyBleRequest(const BleRequest& r, BleActions& a) {
  switch (r.kind) {
    case BleRequest::None: return 0;
    case BleRequest::SetTarget:
      a.setTarget(r.target);
      return FIELD_TARGET;
    case BleRequest::RunCommand:
      switch (r.command) {
        case Command::Stop: a.stop(); break;
        case Command::Go: a.go(); break;
        case Command::TestFull: a.test(Speed::Full); break;
        case Command::TestSlow: a.test(Speed::Slow); break;
      }
      return 0;
    case BleRequest::SetPresets:
      a.setPresets(r.presets);
      return FIELD_PRESETS;
    case BleRequest::SetConfig:
      a.setConfig(r.config);
      return FIELD_CONFIG;
    case BleRequest::Refresh:
      return fieldOf(r.ch);
    case BleRequest::Disconnected:
      if (a.state() == State::Testing) a.stop();
      return 0;
  }
  return 0;
}

size_t encodeField(BleField field, const BleValues& v, uint8_t* out) {
  switch (field) {
    case FIELD_TARGET:
      writeU16(out, v.target);
      return 2;
    case FIELD_COUNT:
      writeU16(out, v.count > UINT16_MAX ? UINT16_MAX : static_cast<uint16_t>(v.count));
      return 2;
    case FIELD_STATE:
      out[0] = static_cast<uint8_t>(v.state);
      return 1;
    case FIELD_BATTERY:
      writeU16(out, v.batteryMv);
      return 2;
    case FIELD_PRESETS:
      for (uint8_t i = 0; i < PRESET_COUNT; i++) writeU16(out + 2 * i, v.presets.values[i]);
      return PRESET_COUNT * 2;
    case FIELD_CONFIG:
      memcpy(out, &v.config, sizeof(ConfigV1));
      return sizeof(ConfigV1);
    default:
      return 0;
  }
}

void BleOutbox::start(const BleValues& v, uint32_t nowMs) {
  sent_ = v;
  forced_ = 0;
  countSentMs_ = nowMs;
  batterySentMs_ = nowMs;
}

uint8_t BleOutbox::update(const BleValues& v, uint32_t nowMs) {
  uint8_t out = forced_;
  forced_ = 0;
  if (v.target != sent_.target) out |= FIELD_TARGET;
  if (v.state != sent_.state) out |= FIELD_STATE;
  // With a state change the count goes too, throttle or not: DONE carries its final count.
  if (v.count != sent_.count &&
      (nowMs - countSentMs_ >= countThrottleMs_ || (out & FIELD_STATE))) {
    out |= FIELD_COUNT;
  }
  if (nowMs - batterySentMs_ >= batteryPeriodMs_) out |= FIELD_BATTERY;
  if (memcmp(&v.presets, &sent_.presets, sizeof v.presets) != 0) out |= FIELD_PRESETS;
  if (memcmp(&v.config, &sent_.config, sizeof v.config) != 0) out |= FIELD_CONFIG;

  if (out & FIELD_TARGET) sent_.target = v.target;
  if (out & FIELD_STATE) sent_.state = v.state;
  if (out & FIELD_COUNT) {
    sent_.count = v.count;
    countSentMs_ = nowMs;
  }
  if (out & FIELD_BATTERY) {
    sent_.batteryMv = v.batteryMv;
    batterySentMs_ = nowMs;
  }
  if (out & FIELD_PRESETS) sent_.presets = v.presets;
  if (out & FIELD_CONFIG) sent_.config = v.config;
  return out;
}
