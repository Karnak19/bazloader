// NimBLE glue: the GATT service from protocole-ble.md, advertising, and the hand-off to loop().
// The callbacks run on the NimBLE host task: they only decode a write (parseWrite) and queue it.
// loop() takes the requests with blePoll() and applies them; nothing else crosses tasks.
#pragma once

#include "ble_logic.h"

// Creates the service, sets every value from `initial`, then starts advertising.
void bleBegin(const BleValues& initial);
// Takes the next request queued by a callback. Loop context only.
bool blePoll(BleRequest* out);
// Sets the value of each field in `fields` (so reads are current) and notifies it.
// Count goes before state, so a client sees a run's final count before DONE. Loop context only.
void blePush(uint8_t fields, const BleValues& v);
// Whether a client is connected (for the status line).
bool bleConnected();
