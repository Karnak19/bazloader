---
title: BLE protocol
description: UUIDs, types and byte layouts shared by the firmware and the web app.
---

The ESP32 is the source of truth. Every change, whether it comes from the encoder or from BLE, is
notified so the OLED and the PWA stay in sync.

- Advertised name: `BazLoader`
- All integers are **little-endian**.
- All UUIDs share one random base; only the 3rd and 4th hex digits change:
  `8adb76XX-5374-47c7-9127-d9895246807a`.

Any change here must land together with both constant files:
`firmware/src/ble_uuids.h` and `web/src/ble/protocol.ts`.

## Service

| Name    | UUID                                   |
| ------- | -------------------------------------- |
| service | `8adb7600-5374-47c7-9127-d9895246807a` |

## Characteristics

| Name      | UUID                                   | Type              | Properties          |
| --------- | -------------------------------------- | ----------------- | ------------------- |
| `target`  | `8adb7601-5374-47c7-9127-d9895246807a` | uint16            | read, write, notify |
| `command` | `8adb7602-5374-47c7-9127-d9895246807a` | uint8             | write               |
| `count`   | `8adb7603-5374-47c7-9127-d9895246807a` | uint16            | read, notify        |
| `state`   | `8adb7604-5374-47c7-9127-d9895246807a` | uint8             | read, notify        |
| `battery` | `8adb7605-5374-47c7-9127-d9895246807a` | uint16 (mV)       | read, notify        |
| `presets` | `8adb7606-5374-47c7-9127-d9895246807a` | uint16[4]         | read, write         |
| `config`  | `8adb7607-5374-47c7-9127-d9895246807a` | packed struct (v1)| read, write         |

### `target`

Number of BBs to load, 1–9999. A write while a run is in progress is ignored; the firmware then
notifies the real value back so the client corrects itself. Out-of-range values are clamped.

### `command`

| Value | Meaning                                                           |
| ----- | ----------------------------------------------------------------- |
| 0     | Stop (anything running: a load or a test spin)                    |
| 1     | Go (start loading `target` BBs)                                   |
| 2     | Test spin at full speed, until stop (calibration, M3)             |
| 3     | Test spin at slow speed, until stop (calibration, M3)             |

Unknown values are ignored.

### `count`

BBs counted in the current (or last) run. Reset to 0 when a run starts. Notifications are throttled
to ~20 Hz, but the final value of a run is always notified.

### `state`

| Value | State      |
| ----- | ---------- |
| 0     | idle       |
| 1     | running    |
| 2     | slowdown   |
| 3     | done       |
| 4     | jam        |
| 5     | low_batt   |
| 6     | testing    |

`testing` is a test spin started by commands 2 or 3.

### `battery`

LiPo voltage in millivolts. Notified every ~5 s.

### `presets`

Four uint16, 8 bytes. Defaults 30 / 50 / 120 / 300. Persisted in NVS on write. A write with the
wrong length is ignored.

### `config`

Packed struct, 11 bytes. The first byte is a format version: the firmware ignores writes whose
version or length doesn't match, and the PWA refuses to decode an unknown version instead of
showing garbage.

| Offset | Type   | Field                   | Default | Notes                                |
| ------ | ------ | ----------------------- | ------- | ------------------------------------ |
| 0      | uint8  | `version`               | 1       |                                      |
| 1      | uint16 | `servo_neutral_us`      | 1500    | Pulse width where the servo stops    |
| 3      | int16  | `speed_full_offset_us`  | 300     | Added to neutral at full speed       |
| 5      | int16  | `speed_slow_offset_us`  | 100     | Added to neutral in slowdown         |
| 7      | uint8  | `reverse`               | 0       | 1 = invert rotation direction        |
| 8      | uint8  | `slowdown_n`            | 4       | Switch to slow when ≤ N BBs remain   |
| 9      | uint16 | `jam_timeout_ms`        | 1500    | No BB for this long → jam            |

Persisted in NVS on write.
