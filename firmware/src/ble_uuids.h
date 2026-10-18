// BLE protocol constants.
// Must match web/src/content/docs/protocole-ble.md and web/src/ble/protocol.ts
#pragma once

#include <stdint.h>

constexpr const char* BLE_DEVICE_NAME = "BULLOADER";

constexpr const char* BLE_SERVICE_UUID = "8adb7600-5374-47c7-9127-d9895246807a";

constexpr const char* BLE_CHAR_TARGET_UUID  = "8adb7601-5374-47c7-9127-d9895246807a"; // uint16, read/write/notify
constexpr const char* BLE_CHAR_COMMAND_UUID = "8adb7602-5374-47c7-9127-d9895246807a"; // uint8, write
constexpr const char* BLE_CHAR_COUNT_UUID   = "8adb7603-5374-47c7-9127-d9895246807a"; // uint16, read/notify
constexpr const char* BLE_CHAR_STATE_UUID   = "8adb7604-5374-47c7-9127-d9895246807a"; // uint8, read/notify
constexpr const char* BLE_CHAR_BATTERY_UUID = "8adb7605-5374-47c7-9127-d9895246807a"; // uint16 mV, read/notify
constexpr const char* BLE_CHAR_PRESETS_UUID = "8adb7606-5374-47c7-9127-d9895246807a"; // uint16[4], read/write
constexpr const char* BLE_CHAR_CONFIG_UUID  = "8adb7607-5374-47c7-9127-d9895246807a"; // ConfigV1, read/write

enum class State : uint8_t {
  Idle     = 0,
  Running  = 1,
  Slowdown = 2,
  Done     = 3,
  Jam      = 4,
  LowBatt  = 5,
  Testing  = 6,
};

enum class Command : uint8_t {
  Stop     = 0,
  Go       = 1,
  TestFull = 2,
  TestSlow = 3,
};

constexpr uint8_t CONFIG_VERSION = 1;

// `config` characteristic payload, little-endian (native on ESP32-C3).
struct __attribute__((packed)) ConfigV1 {
  uint8_t  version;              // 0: CONFIG_VERSION
  uint16_t servo_neutral_us;     // 1
  int16_t  speed_full_offset_us; // 3
  int16_t  speed_slow_offset_us; // 5
  uint8_t  reverse;              // 7: 1 = invert rotation
  uint8_t  slowdown_n;           // 8
  uint16_t jam_timeout_ms;       // 9
};
static_assert(sizeof(ConfigV1) == 11, "ConfigV1 must be 11 bytes, see protocole-ble.md");
