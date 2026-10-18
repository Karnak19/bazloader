#include <Arduino.h>

#include "ble_uuids.h"
#include "config.h"

#ifdef SIMULATE_IR
constexpr bool kSimulateIr = true;
#else
constexpr bool kSimulateIr = false;
#endif

void setup() {
  Serial.begin(115200);
  // Native USB CDC: give the host a moment to open the port so the boot line isn't lost.
  delay(1500);
  Serial.printf("%s boot, SIMULATE_IR=%s\n", BLE_DEVICE_NAME, kSimulateIr ? "on" : "off");
}

void loop() {
  static uint32_t last = 0;
  if (millis() - last >= 5000) {
    last = millis();
    Serial.printf("alive %lus\n", (unsigned long)(last / 1000));
  }
}
