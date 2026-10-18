#include "ble.h"

#include <NimBLEDevice.h>
#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>

// Requests from the NimBLE task to loop(). A full queue drops the write: a client writing faster
// than loop() runs (thousands of passes per second) is misbehaving anyway.
static QueueHandle_t requests = nullptr;
static NimBLEServer* server = nullptr;
static NimBLECharacteristic* chars[6] = {};  // indexed like the BleField bits

static volatile bool disconnected = false;  // set by the NimBLE task, cleared by blePoll()
static volatile bool connected = false;     // written by the NimBLE task, read by loop()

static void queue(const BleRequest& r) { xQueueSend(requests, &r, 0); }

// NimBLE host task. No Serial, no NVS, no state machine: decode and queue only.
class WriteCallbacks : public NimBLECharacteristicCallbacks {
 public:
  explicit WriteCallbacks(BleChar ch) : ch_(ch) {}
  void onWrite(NimBLECharacteristic* c, NimBLEConnInfo&) override {
    const NimBLEAttValue& v = c->getValue();
    BleRequest r = parseWrite(ch_, v.data(), v.size());
    if (r.kind != BleRequest::None) queue(r);
  }

 private:
  BleChar ch_;
};

// NimBLE host task too.
class ServerCallbacks : public NimBLEServerCallbacks {
  void onConnect(NimBLEServer*, NimBLEConnInfo&) override { connected = true; }
  void onDisconnect(NimBLEServer*, NimBLEConnInfo&, int) override {
    connected = false;
    // A flag, not the queue: a full queue drops requests, and this one stops a test spin.
    disconnected = true;
    // advertiseOnDisconnect() restarts advertising; one connection at a time
    // (CONFIG_BT_NIMBLE_MAX_CONNECTIONS=1, and advertising stops when a client connects).
  }
};

static WriteCallbacks targetCallbacks(BleChar::Target);
static WriteCallbacks commandCallbacks(BleChar::Command);
static WriteCallbacks presetsCallbacks(BleChar::Presets);
static WriteCallbacks configCallbacks(BleChar::Config);
static ServerCallbacks serverCallbacks;

static uint8_t fieldIndex(uint8_t field) {
  uint8_t i = 0;
  while (field > 1) {
    field >>= 1;
    i++;
  }
  return i;
}

static void setField(BleField field, const BleValues& v) {
  uint8_t buf[sizeof(ConfigV1)];
  size_t len = encodeField(field, v, buf);
  chars[fieldIndex(field)]->setValue(buf, len);
}

void bleBegin(const BleValues& initial) {
  requests = xQueueCreate(8, sizeof(BleRequest));
  NimBLEDevice::init(BLE_DEVICE_NAME);
  server = NimBLEDevice::createServer();
  server->setCallbacks(&serverCallbacks);
  server->advertiseOnDisconnect(true);

  NimBLEService* service = server->createService(BLE_SERVICE_UUID);
  // WRITE (with response) is what the app uses; WRITE_NR is accepted too, same handling.
  constexpr uint16_t kWrite = NIMBLE_PROPERTY::WRITE | NIMBLE_PROPERTY::WRITE_NR;
  constexpr uint16_t kRead = NIMBLE_PROPERTY::READ;
  constexpr uint16_t kNotify = NIMBLE_PROPERTY::NOTIFY;
  NimBLECharacteristic* target =
      service->createCharacteristic(BLE_CHAR_TARGET_UUID, kRead | kWrite | kNotify);
  NimBLECharacteristic* command = service->createCharacteristic(BLE_CHAR_COMMAND_UUID, kWrite);
  NimBLECharacteristic* count =
      service->createCharacteristic(BLE_CHAR_COUNT_UUID, kRead | kNotify);
  NimBLECharacteristic* state =
      service->createCharacteristic(BLE_CHAR_STATE_UUID, kRead | kNotify);
  NimBLECharacteristic* battery =
      service->createCharacteristic(BLE_CHAR_BATTERY_UUID, kRead | kNotify);
  NimBLECharacteristic* presets =
      service->createCharacteristic(BLE_CHAR_PRESETS_UUID, kRead | kWrite);
  NimBLECharacteristic* config = service->createCharacteristic(BLE_CHAR_CONFIG_UUID, kRead | kWrite);
  target->setCallbacks(&targetCallbacks);
  command->setCallbacks(&commandCallbacks);
  presets->setCallbacks(&presetsCallbacks);
  config->setCallbacks(&configCallbacks);
  chars[fieldIndex(FIELD_TARGET)] = target;
  chars[fieldIndex(FIELD_COUNT)] = count;
  chars[fieldIndex(FIELD_STATE)] = state;
  chars[fieldIndex(FIELD_BATTERY)] = battery;
  chars[fieldIndex(FIELD_PRESETS)] = presets;
  chars[fieldIndex(FIELD_CONFIG)] = config;
  // First reads must be right: every value is set before anyone can connect.
  // The GATT server itself starts with the advertising, below.
  for (uint8_t f = 1; f < FIELD_ALL; f <<= 1) setField(static_cast<BleField>(f), initial);

  // Flags (3) + 128-bit UUID (18) + name (11) = 32 > 31 bytes: the name goes in the scan response.
  NimBLEAdvertising* adv = NimBLEDevice::getAdvertising();
  NimBLEAdvertisementData data;
  data.setFlags(BLE_HS_ADV_F_DISC_GEN | BLE_HS_ADV_F_BREDR_UNSUP);
  data.addServiceUUID(BLE_SERVICE_UUID);
  adv->setAdvertisementData(data);
  NimBLEAdvertisementData scan;
  scan.setName(BLE_DEVICE_NAME);
  adv->setScanResponseData(scan);
  adv->enableScanResponse(true);
  adv->start();
}

bool blePoll(BleRequest* out) {
  if (disconnected) {
    disconnected = false;
    *out = BleRequest();
    out->kind = BleRequest::Disconnected;
    return true;
  }
  return requests != nullptr && xQueueReceive(requests, out, 0) == pdTRUE;
}

void blePush(uint8_t fields, const BleValues& v) {
  // Count before state: DONE must find the final count already sent.
  static const BleField order[] = {FIELD_COUNT, FIELD_STATE, FIELD_TARGET,
                                   FIELD_BATTERY, FIELD_PRESETS, FIELD_CONFIG};
  for (BleField f : order) {
    if (!(fields & f)) continue;
    setField(f, v);
    // presets and config have no notify property: setting the value keeps reads current.
    if (f != FIELD_PRESETS && f != FIELD_CONFIG) chars[fieldIndex(f)]->notify();
  }
}

bool bleConnected() { return connected; }
