#include <Arduino.h>
#include <soc/gpio_reg.h>
#include <soc/ledc_struct.h>

#include "battery.h"
#include "ble_uuids.h"
#include "config.h"
#include "controls.h"
#include "display.h"
#include "nvs_store.h"
#include "run.h"
#include "screen.h"
#include "settings.h"

#ifdef SIMULATE_IR
constexpr bool kSimulateIr = true;
#else
constexpr bool kSimulateIr = false;
#endif

// Settings from NVS: presets, last target and the servo/run config, applied at boot (setup()).
static NvsStore nvs;
static Settings settings(nvs, TARGET_SAVE_DELAY_MS);

// LEDC duty of a stopped servo, from the runtime neutral. Precomputed in loop context whenever the
// config changes (only when stopped), so the count ISR only reads one aligned word from DRAM.
static volatile DRAM_ATTR uint32_t stopDuty = 0;

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
  ch.duty.duty = stopDuty << 4;  // 4 fractional bits
  ch.conf1.duty_start = 1;
  ch.conf0.low_speed_update = 1;  // latch at the next period
  servoMoving = false;
}

static void setServo(Speed speed) {
  uint16_t us = servoPulseUs(speed, settings.config());
  uint32_t duty = us ? servoDuty(us, SERVO_LEDC_BITS) : stopDuty;
  servoMoving = speed != Speed::Off;
  ledcWrite(SERVO_LEDC_CHANNEL, duty);
  // The target BB may have landed while we were writing: its cut must win. Test the requested
  // speed, not servoMoving, which the ISR has already cleared in exactly that case.
  if (speed != Speed::Off && counter.count >= counter.stopAt) {
    ledcWrite(SERVO_LEDC_CHANNEL, stopDuty);
    servoMoving = false;
    duty = stopDuty;
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

// ---- Encoder and buttons ----

static Encoder encoder(ENCODER_STEPS_PER_DETENT, 3);  // KY-040 rests with A and B high
static EncoderAccel encoderAccel(ENCODER_FAST_MS, ENCODER_FAST_STEP);
static Button goButton(BUTTON_DEBOUNCE_MS, LONG_CLICK_MS);
static Button encoderButton(BUTTON_DEBOUNCE_MS, LONG_CLICK_MS);
static ClickHandler clicks;

// A/B pin change. Reads both pins at once from the GPIO input register (no flash code).
static IRAM_ATTR void encoderEdge() {
  uint32_t in = REG_READ(GPIO_IN_REG);
  encoder.edge((in >> PIN_ENC_A) & 1, (in >> PIN_ENC_B) & 1);
}

static void applyAction(UiAction action, const char* source) {
  switch (action) {
    case UiAction::None: return;
    case UiAction::Start:
      Serial.printf("[%lu ms] %s: go\n", (unsigned long)millis(), source);
      go();
      return;
    case UiAction::Stop:
      Serial.printf("[%lu ms] %s: stop\n", (unsigned long)millis(), source);
      stop();
      return;
    case UiAction::NextPreset:
      Serial.printf("[%lu ms] %s: preset, target %u\n", (unsigned long)millis(), source,
                    run.setTarget(nextPreset(settings.presets(), run.target())));
      return;
  }
}

// Polled every loop pass: encoder detents, then the two buttons (active low).
static void pollControls() {
  static int32_t seenPosition = 0;
  uint32_t now = millis();
  int32_t position = encoder.position;  // single word written by the ISR: atomic read
  int32_t detents = position - seenPosition;
  seenPosition = position;
  if (ENCODER_REVERSE) detents = -detents;
  int32_t change = encoderAccel.apply(detents, now);
  if (change != 0) {
    uint16_t before = run.target();
    uint16_t after = run.setTarget(before + change);  // ignored during a run
    if (after != before) Serial.printf("  target %u\n", after);
  }
  // GO acts on the press itself, not the release: a stop shouldn't wait for the thumb.
  if (goButton.update(now, digitalRead(PIN_GO_BUTTON) == LOW) == ButtonEvent::Press) {
    UiAction action = goAction(run.state(), battery.ok());
    if (action == UiAction::None) Serial.printf("  GO ignored: battery %u mV\n", battery.mv());
    applyAction(action, "GO");
  }
  applyAction(clicks.handle(encoderButton.update(now, digitalRead(PIN_ENC_SW) == LOW), run.state()),
              "click");
}

// ---- OLED ----

static bool displayFound = false;
static uint32_t redrawLastUs = 0, redrawMaxUs = 0;

// Redraws when the screen content changed, at most every OLED_MIN_REDRAW_MS. A redraw blocks the
// loop for the I2C transfer, but not the stop: the count ISR cuts the servo on its own.
static void updateDisplay(bool force) {
  static ScreenModel shown;
  static uint32_t lastDrawMs = 0;
  if (!displayFound) return;
  uint32_t now = millis();
  if (!force && now - lastDrawMs < OLED_MIN_REDRAW_MS) return;
  ScreenModel m = screenModel(run.state(), run.target(), counter.count, battery.mv(),
                              battery.usb(), battery.warn());
  if (!force && m == shown) return;
  shown = m;
  lastDrawMs = now;
  redrawLastUs = displayDraw(m);
  if (redrawLastUs > redrawMaxUs) redrawMaxUs = redrawLastUs;
}

static void printDisplay() {
  if (!displayFound) {
    Serial.printf("  oled not found at 0x%02X\n", OLED_I2C_ADDRESS);
    return;
  }
  Serial.printf("  oled redraw %lu us (max %lu us)\n", (unsigned long)redrawLastUs,
                (unsigned long)redrawMaxUs);
}

// ---- Settings ----

// Pushes the runtime config to the run and the servo output. Only called while stopped.
static void applyConfig() {
  const ConfigV1& c = settings.config();
  run.setTiming(c.slowdown_n, c.jam_timeout_ms);
  stopDuty = servoStopDuty(c.servo_neutral_us);
  if (!servoMoving) ledcWrite(SERVO_LEDC_CHANNEL, stopDuty);
}

static bool runActive() { return run.speed() != Speed::Off; }

// Hooks for BLE (#6), called from loop() only: validate, apply live, persist if changed.
// false: out of range, or (config only) a run is in progress.
bool setConfig(const ConfigV1& cfg) {
  if (!settings.setConfig(cfg, runActive())) return false;
  applyConfig();
  return true;
}

bool setPresets(const Presets& presets) { return settings.setPresets(presets); }

static void printSettings() {
  const ConfigV1& c = settings.config();
  Serial.printf("  config v%u: neutral %u us, full %+d us, slow %+d us, reverse %u, slowdown %u,"
                " jam %u ms\n",
                c.version, c.servo_neutral_us, c.speed_full_offset_us, c.speed_slow_offset_us,
                c.reverse, c.slowdown_n, c.jam_timeout_ms);
  const Presets& p = settings.presets();
  Serial.printf("  presets %u %u %u %u, saved target %u\n", p.values[0], p.values[1], p.values[2],
                p.values[3], settings.target());
}

static void loadSettings() {
  if (!nvs.begin("bulloader")) Serial.println("  nvs: can't open, using defaults");
  LoadReport r = settings.load();
  const char* names[] = {KEY_CONFIG, KEY_PRESETS, KEY_TARGET};
  LoadResult results[] = {r.config, r.presets, r.target};
  for (uint8_t i = 0; i < 3; i++) {
    if (results[i] != LoadResult::Ok) {
      Serial.printf("  nvs: %s %s, using defaults\n", names[i], loadResultName(results[i]));
    }
  }
  applyConfig();
  run.setTarget(settings.target());
  printSettings();
}

// ---- Serial commands (still the only way to drive it without the hardware) ----

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
    case 'c': {
      // `c` alone dumps; `c<neutral>,<full>,<slow>,<reverse>,<slowdown>,<jam>` sets the config.
      int v[6];
      if (sscanf(line + 1, "%d,%d,%d,%d,%d,%d", &v[0], &v[1], &v[2], &v[3], &v[4], &v[5]) == 6) {
        ConfigV1 c = {CONFIG_VERSION, (uint16_t)v[0], (int16_t)v[1], (int16_t)v[2],
                      (uint8_t)v[3], (uint8_t)v[4], (uint16_t)v[5]};
        bool inRange = v[0] >= 0 && v[0] <= UINT16_MAX && v[1] >= INT16_MIN &&
                       v[1] <= INT16_MAX && v[2] >= INT16_MIN && v[2] <= INT16_MAX &&
                       v[3] >= 0 && v[3] <= UINT8_MAX && v[4] >= 0 && v[4] <= UINT8_MAX &&
                       v[5] >= 0 && v[5] <= UINT16_MAX;
        if (!inRange || !setConfig(c)) Serial.println("  config refused (range, or running)");
      }
      printSettings();
      break;
    }
    case 'P': {
      int v[PRESET_COUNT];
      if (sscanf(line + 1, "%d,%d,%d,%d", &v[0], &v[1], &v[2], &v[3]) == PRESET_COUNT) {
        Presets p;
        bool inRange = true;
        for (uint8_t i = 0; i < PRESET_COUNT; i++) {
          inRange = inRange && v[i] >= 0 && v[i] <= UINT16_MAX;
          p.values[i] = (uint16_t)v[i];
        }
        if (!inRange || !setPresets(p)) Serial.println("  presets refused (range)");
      }
      printSettings();
      break;
    }
    case '?':
      Serial.printf("  %s count=%lu target=%u\n", stateName(run.state()),
                    (unsigned long)counter.count, run.target());
      printBattery();
      printDisplay();
      break;
    default:
      Serial.println("  commands: t<n> target, g go, s stop, ? status, c settings,"
                     " c<neutral>,<full>,<slow>,<rev>,<n>,<jam> set config,"
                     " P<a>,<b>,<c>,<d> set presets (sim: p close pulse pair)");
  }
}

static void readSerial() {
  static char buf[48];
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
  loadSettings();  // before the first servo write: the stop duty depends on the neutral
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

  pinMode(PIN_GO_BUTTON, INPUT_PULLUP);
  pinMode(PIN_ENC_SW, INPUT_PULLUP);
  // The KY-040 has its own pull-ups to its + pin (3.3 V); the internal ones only help when the
  // encoder is unplugged, so the pins don't float.
  pinMode(PIN_ENC_A, INPUT_PULLUP);
  pinMode(PIN_ENC_B, INPUT_PULLUP);
  encoder.ab = (digitalRead(PIN_ENC_A) ? 2 : 0) | (digitalRead(PIN_ENC_B) ? 1 : 0);
  attachInterrupt(PIN_ENC_A, encoderEdge, CHANGE);
  attachInterrupt(PIN_ENC_B, encoderEdge, CHANGE);

  displayFound = displayBegin();
  updateDisplay(true);
  printDisplay();

  Serial.printf("target %u. commands: t<n>, g, s, ?, c, P\n", run.target());
}

void loop() {
  readSerial();
  pollControls();
  run.update(millis(), counter.count);
  syncState();
  updateBattery(false);
  updateDisplay(false);
  settings.updateTarget(run.target(), millis());  // written 2 s after it stops changing
}
