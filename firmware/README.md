# BULLOADER+ firmware

ESP32-C3 SuperMini, PlatformIO + Arduino. Pins and defaults live in `src/config.h`; BLE constants
in `src/ble_uuids.h` (must match `docs/ble-protocol.md`).

## Build

```sh
pio run              # release: real IR beam
pio run -e sim       # SIMULATE_IR: fake BB pulses, no mechanism needed
```

The first build downloads the toolchain and takes a few minutes.

## Flash and monitor

```sh
pio run -e sim -t upload     # or -e release
pio device monitor           # 115200 baud
```

Serial goes through the C3's native USB (no USB-serial chip on the SuperMini), hence the
`ARDUINO_USB_*` flags in `platformio.ini`.

If the board doesn't show up as a serial port (blank chip, or crashed firmware holding the USB):
hold **BOOT**, press and release **RESET** (or plug it in while holding BOOT), release BOOT, then
upload again. Press RESET after the upload to run it.

## Power

Don't power the board from USB and from the 5 V buck at the same time until you've checked
whether the SuperMini has a protection diode between USB 5 V and the 5V pin. Unplug the LiPo (or
open the main switch) when flashing over USB.
