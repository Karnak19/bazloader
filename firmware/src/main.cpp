#include <Arduino.h>
#include <soc/ledc_struct.h>

#include "battery.h"
#include "ble_uuids.h"
#include "config.h"
#include "run.h"

#ifdef SIMULATE_IR
constexpr bool kSimulateIr = true;
#else
constexpr bool kSimulateIr = false;
#endif

constexpr uint32_t kStopDuty =
    SERVO_STOP_NEUTRAL ? servoDuty(SERVO_NEUTRAL_US, SERVO_LEDC_BITS) : 0;

static Counter counter(IR_MIN_INTERVAL_US);
static Run run({SLOWDOWN_N, JAM_TIMEOUT_MS, FIRST_BB_TIMEOUT_MS, DONE_HOLD_MS});

static volatile bool servoMoving = false;  // what the servo is commanded to do
static volatile uint32_t targetHitUs = 0;  // when the target BB was counted
static volatile uint32_t servoCutUs = 0;   // when the ISR cut the servo after it

static Battery battery(
    {BATT_WARN_MV, BATT_REFUSE_MV, BATT_HYSTERESIS_MV, BATT_USB_BELOW_MV, BATT_SAG_MS});

// ---- Servo ----

// Cuts the servo from the count ISR, so the stop doesn't wait for loop().
// ledcWrite() isn't ISR-safe in core 2.0.17 (flash code, spinlock, maybe a semaphore), so this
// writes the LEDC registers directly, the same three writes as IDF's ledc_ll helpers (whose
// header doesn't compile as C++). The C3 only has low-speed group 0.
static IRAM_ATTR void cutServoFromIsr() {
  auto& ch = LEDC.channel_group[0].channel[SERVO_LEDC_CHANNEL];
  ch.duty.duty = kStopDuty << 4;  // 4 fractional bits
  ch.conf1.duty_start = 1;
  ch.conf0.low_speed_update = 1;  // latch at the next period
  servoMoving = false;
}

static void setServo(Speed speed) {
  uint16_t us = servoPulseUs(speed, SERVO_NEUTRAL_US, SERVO_FULL_OFFSET_US, SERVO_SLOW_OFFSET_US,
                             SERVO_REVERSE);
  uint32_t duty = us ? servoDuty(us, SERVO_LEDC_BITS) : kStopDuty;
  servoMoving = speed != Speed::Off;
  ledcWrite(SERVO_LEDC_CHANNEL, duty);
  // The target BB may have landed while we were writing: its cut must win. Test the requested
  // speed, not servoMoving, which the ISR has already cleared in exactly that case.
  if (speed != Speed::Off && counter.count >= counter.stopAt) {
    ledcWrite(SERVO_LEDC_CHANNEL, kStopDuty);
    servoMoving = false;
    duty = kStopDuty;
    us = 0;
  }
  Serial.printf("  servo %u us, duty %lu/%u\n", us, (unsigned long)duty, 1u << SERVO_LEDC_BITS);
}

// ---- Counting ----

// The single count path: the IR interrupt and the simulator both come through here.
static IRAM_ATTR void countBb() {
  uint32_t now = micros();
  if (counter.pulse(now)) {
    targetHitUs = now;
    cutServoFromIsr();
    servoCutUs = micros();
  }
}

#ifdef SIMULATE_IR
static hw_timer_t* simTimer = nullptr;
static volatile uint16_t simHopper = 0;      // fake BBs left, refilled at each GO
static volatile bool simPairRequested = false;

// Timer interrupt at SIM_BB_PER_SECOND: a BB passes only while the servo turns.
static IRAM_ATTR void simTick() {
  if (!servoMoving || simHopper == 0) return;
  simHopper = simHopper - 1;
  countBb();
  if (simPairRequested) {
    // Same BB seen twice, closer than IR_MIN_INTERVAL_US: must count once.
    // A 1 ms busy wait in an ISR is fine for a debug command in the sim build only.
    simPairRequested = false;
    delayMicroseconds(IR_MIN_INTERVAL_US / 5);
    countBb();
  }
}
#endif

// ---- Run ----

static State shownState = State::Idle;

// Applies a state change: servo output, counting, log.
static void syncState() {
  State s = run.state();
  if (s == shownState) return;
  State prev = shownState;
  shownState = s;
  counter.enabled = run.counting();
  uint32_t count = counter.count;  // single word: atomic read
  Serial.printf("[%lu ms] %s count=%lu target=%u\n", (unsigned long)millis(), stateName(s),
                (unsigned long)count, run.target());
  if (s == State::Done) {
    uint32_t loopUs = micros() - targetHitUs;
    Serial.printf("  stop latency: ISR cut %lu us, loop saw DONE %lu us after the target BB\n",
                  (unsigned long)(servoCutUs - targetHitUs), (unsigned long)loopUs);
  }
  if (prev == State::Done && count > run.target()) {
    Serial.printf("  overshoot: %lu BB\n", (unsigned long)(count - run.target()));
  }
  setServo(run.speed());
}

// ---- Battery ----

// One reading: the average of BATT_ADC_SAMPLES calibrated ADC reads, scaled to the pack.
// About a millisecond in all, so loop() isn't held up.
static uint32_t readBatteryMv() {
  uint32_t sum = 0;
  for (uint8_t i = 0; i < BATT_ADC_SAMPLES; i++) sum += analogReadMilliVolts(PIN_BATTERY_ADC);
  return batteryMvFromAdc(sum / BATT_ADC_SAMPLES, BATT_DIVIDER_RATIO, BATT_CALIBRATION);
}

static void printBattery() {
  if (battery.usb()) {
    Serial.println("  battery USB");
    return;
  }
  Serial.printf("  battery %u mV%s%s\n", battery.mv(), battery.ok() ? "" : ", low",
                battery.warn() ? ", warning" : "");
}

// Reads the battery every BATT_READ_PERIOD_MS, stops a run on a flat pack, logs level changes.
static void updateBattery(bool force) {
  static uint32_t lastReadMs = 0;
  static bool shownUsb = false, shownWarn = false, shownOk = true;
  uint32_t now = millis();
  if (!force && now - lastReadMs < BATT_READ_PERIOD_MS) return;
  lastReadMs = now;
  bool running = run.speed() != Speed::Off;
  battery.update(now, readBatteryMv(), running);
  if (running && battery.sagged()) {
    run.lowBattery();
    Serial.printf("[%lu ms] battery below %u mV for %u ms\n", (unsigned long)now, BATT_REFUSE_MV,
                  BATT_SAG_MS);
    syncState();
  }
  if (!force && battery.usb() == shownUsb && battery.warn() == shownWarn &&
      battery.ok() == shownOk) {
    return;
  }
  shownUsb = battery.usb();
  shownWarn = battery.warn();
  shownOk = battery.ok();
  Serial.printf("[%lu ms]", (unsigned long)now);
  printBattery();
}

// ---- Run commands ----

static void go() {
  if (!run.go(millis(), battery.ok())) {
    if (run.state() == State::LowBatt) {
      Serial.printf("  go refused: battery %u mV\n", battery.mv());
    } else {
      Serial.println("  go ignored: already running");
    }
    syncState();
    return;
  }
  counter.arm(run.target());
#ifdef SIMULATE_IR
  simHopper = SIM_HOPPER_CAPACITY;
#endif
  syncState();
}

static void stop() {
  run.stop();
  syncState();
  // Stop also from IDLE: make sure the output is off whatever happened before.
  counter.enabled = false;
  if (servoMoving) setServo(Speed::Off);
}

// ---- Serial commands (temporary, until the OLED and BLE exist) ----

static void handleCommand(const char* line) {
  switch (line[0]) {
    case 't': {
      uint16_t t = run.setTarget(atol(line + 1));
      Serial.printf("  target %u\n", t);
      break;
    }
    case 'g': go(); break;
    case 's': stop(); break;
#ifdef SIMULATE_IR
    case 'p':
      simPairRequested = true;
      Serial.println("  next sim BB comes as a close pair");
      break;
#endif
    case '?':
      Serial.printf("  %s count=%lu target=%u\n", stateName(run.state()),
                    (unsigned long)counter.count, run.target());
      printBattery();
      break;
    default:
      Serial.println("  commands: t<n> target, g go, s stop, ? status"
                     " (sim: p close pulse pair)");
  }
}

static void readSerial() {
  static char buf[16];
  static uint8_t len = 0;
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (len == 0) continue;
      buf[len] = '\0';
      len = 0;
      handleCommand(buf);
    } else if (len < sizeof(buf) - 1) {
      buf[len++] = c;
    }
  }
}

void setup() {
  Serial.begin(115200);
  // Native USB CDC: give the host a moment to open the port so the boot line isn't lost.
  delay(1500);
  Serial.printf("%s boot, SIMULATE_IR=%s\n", BLE_DEVICE_NAME, kSimulateIr ? "on" : "off");

  ledcSetup(SERVO_LEDC_CHANNEL, 50, SERVO_LEDC_BITS);
  ledcAttachPin(PIN_SERVO, SERVO_LEDC_CHANNEL);
  setServo(Speed::Off);

#ifdef SIMULATE_IR
  simTimer = timerBegin(0, 80, true);  // 80 MHz APB / 80 = 1 us ticks
  timerAttachInterrupt(simTimer, simTick, false);
  timerAlarmWrite(simTimer, 1000000 / SIM_BB_PER_SECOND, true);
  timerAlarmEnable(simTimer);
#else
  pinMode(PIN_IR_SENSOR, INPUT_PULLUP);
  attachInterrupt(PIN_IR_SENSOR, countBb, IR_BREAK_RISING ? RISING : FALLING);
#endif
  analogSetPinAttenuation(PIN_BATTERY_ADC, ADC_11db);  // up to ~2.5 V calibrated on the C3
  updateBattery(true);  // GO must see a real reading straight away

  Serial.printf("target %u. commands: t<n>, g, s, ?\n", run.target());
}

void loop() {
  readSerial();
  run.update(millis(), counter.count);
  syncState();
  updateBattery(false);
}
