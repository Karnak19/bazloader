// Pins and tunable defaults. The single place to change hardware wiring or default behaviour.
#pragma once

#include <stdint.h>

// ---- Pins (ESP32-C3 SuperMini) ----
// GPIO 2, 8 and 9 are strapping pins (8 also drives the onboard LED): keep them free.
constexpr uint8_t PIN_BATTERY_ADC = 0;  // LiPo voltage through the divider
constexpr uint8_t PIN_IR_SENSOR   = 1;  // IR phototransistor, interrupt on beam break
constexpr uint8_t PIN_SERVO       = 3;  // Servo PWM (LEDC)
constexpr uint8_t PIN_GO_BUTTON   = 4;  // GO button, INPUT_PULLUP, dry contact to GND
constexpr uint8_t PIN_ENC_A       = 5;
constexpr uint8_t PIN_ENC_B       = 6;
constexpr uint8_t PIN_ENC_SW      = 7;
constexpr uint8_t PIN_I2C_SDA     = 10; // OLED
constexpr uint8_t PIN_I2C_SCL     = 20; // OLED (usable because Serial is on native USB)

// ---- Servo (continuous rotation), defaults overridable from NVS ----
constexpr uint16_t SERVO_NEUTRAL_US      = 1500; // pulse width where the servo stops
constexpr int16_t  SERVO_FULL_OFFSET_US  = 300;  // added to neutral at full speed
constexpr int16_t  SERVO_SLOW_OFFSET_US  = 100;  // added to neutral in slowdown
constexpr bool     SERVO_REVERSE         = false;
// Stopped servo gets no pulse at all, so a slightly wrong neutral can't make it creep.
// Fallback if the real servo misbehaves without signal (#13): set to true for a neutral pulse.
constexpr bool     SERVO_STOP_NEUTRAL    = false;
constexpr uint8_t  SERVO_LEDC_CHANNEL    = 0;
constexpr uint8_t  SERVO_LEDC_BITS       = 14; // C3 max at 50 Hz

// ---- Run logic ----
constexpr uint8_t  SLOWDOWN_N     = 4;    // switch to slow speed when <= N BBs remain
constexpr uint16_t JAM_TIMEOUT_MS = 1500; // no BB for this long -> jam
// The first BB comes later: the mechanism spins up and the feed fills.
constexpr uint16_t FIRST_BB_TIMEOUT_MS = 4000;
constexpr uint16_t DONE_HOLD_MS   = 2000; // DONE stays shown this long, then IDLE
// With a pull-up, a cut beam turns the phototransistor off and the pin goes HIGH (RISING).
// Set to false if the wiring inverts it.
constexpr bool IR_BREAK_RISING = true;
// Minimum gap between two counted BBs. A 6 mm BB crosses the beam in well under 1 ms even at
// low speed, and the loader feeds at most a few dozen BBs/s (>= ~20 ms apart), so 5 ms rejects
// edge bounce without risking a missed BB.
constexpr uint32_t IR_MIN_INTERVAL_US = 5000;

constexpr uint16_t TARGET_MIN = 1;
constexpr uint16_t TARGET_MAX = 9999;
constexpr uint16_t DEFAULT_PRESETS[4] = {30, 50, 120, 300};

// ---- Battery (2S LiPo) ----
constexpr uint16_t BATT_WARN_MV   = 7000; // warn below this
constexpr uint16_t BATT_REFUSE_MV = 6600; // refuse to start below this
// Divider: 100k on top, 27k to GND -> V_batt = V_adc * (100 + 27) / 27.
constexpr float BATT_DIVIDER_RATIO = (100.0f + 27.0f) / 27.0f;
constexpr float BATT_CALIBRATION   = 1.0f; // tweak after measuring with a multimeter
// Leaving LOW_BATT (and the warning) needs this much above the threshold, so noise can't flicker.
constexpr uint16_t BATT_HYSTERESIS_MV = 100;
// With USB and no battery the ADC reads ~0 V. A 2S pack never sits below 6 V in normal use, so
// anything under this is "no battery": report 0 mV and skip the guard (the servo has no power).
constexpr uint16_t BATT_USB_BELOW_MV = 3000;
// The pack sags under servo load: a run stops only after this long below BATT_REFUSE_MV.
constexpr uint16_t BATT_SAG_MS = 2000;
constexpr uint16_t BATT_READ_PERIOD_MS = 500;
constexpr uint8_t  BATT_ADC_SAMPLES    = 16; // averaged per reading

// ---- Simulation (env:sim) ----
constexpr uint16_t SIM_BB_PER_SECOND = 15; // fake IR pulse rate when SIMULATE_IR is set
// Fake BBs in the hopper, refilled at each GO. A target above it ends in JAM.
constexpr uint16_t SIM_HOPPER_CAPACITY = 100;

// ---- BLE notifications ----
constexpr uint32_t COUNT_NOTIFY_THROTTLE_MS = 50;   // ~20 Hz
constexpr uint32_t BATTERY_NOTIFY_PERIOD_MS = 5000;
