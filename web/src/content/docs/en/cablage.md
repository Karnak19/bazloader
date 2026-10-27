---
title: Wiring
description: ESP32 pinout, wiring diagram and checks before powering up for the first time.
---

This page is for wiring the loader at home, then turning it on for the first time without frying
anything. The most common mistakes (a buck converter that isn't set, an encoder on 5 V, a servo
that can't take the battery's voltage) damage parts in the very first second, so take the time to
go through the [checklist](#first-power-up) in order.

## ESP32 pinout

The board is an ESP32-C3 SuperMini. This table follows `firmware/src/config.h`: **if the two ever
disagree, `config.h` wins.**

| GPIO | Function                              | Good to know                                                                               |
| ---- | ------------------------------------- | ------------------------------------------------------------------------------------------ |
| 0    | Battery voltage (analog input)        | Through a 100 kΩ / 20 kΩ voltage divider, with a 100 nF capacitor to ground.               |
| 1    | IR phototransistor                    | 10 kΩ pull-up resistor to 3.3 V. The signal goes high when a BB breaks the beam.           |
| 3    | Servo signal (PWM)                    | Only the control wire: the servo is powered straight from the battery.                     |
| 4    | GO button                             | A plain contact between GPIO 4 and GND, nothing else. Fully disconnected from the old 12 V circuit. |
| 5    | KY-040 encoder, CLK                   | The module's `+` goes to **3.3 V**, never 5 V.                                             |
| 6    | KY-040 encoder, DT                    |                                                                                            |
| 7    | KY-040 encoder, SW (click)            | Goes low when pressed.                                                                     |
| 10   | OLED, SDA (I2C)                       | SSD1306 128×64 screen, address 0x3C (sometimes 0x3D).                                       |
| 20   | OLED, SCL (I2C)                       | Free to use because the serial port goes through the chip's native USB.                    |

Leave these free:

- **GPIO 2, 8 and 9** are strapping pins: their level at power-on decides how the chip boots. Pin 8
  also drives the board's LED.
- **GPIO 4 to 7** are also used for JTAG debugging. That's no problem as long as you go through USB
  (the built-in USB debugging doesn't use them), but an external JTAG probe would clash with the
  button and the encoder.

## Wiring diagram

This is a schematic: where a pin sits on the drawing has nothing to do with where it is on the
board. Red wires carry the battery voltage (7.4 V, up to 8.4 V when full), the orange wire the
converter's 5 V, and the green flags the 3.3 V from the ESP32's 3V3 pin. All the ground symbols are
connected together.

<div class="wiring-scroll">
<svg class="wiring" viewBox="0 0 1000 750" role="img" aria-labelledby="wiring-title wiring-desc" xmlns="http://www.w3.org/2000/svg">
<title id="wiring-title">BazLoader wiring diagram</title>
<desc id="wiring-desc">The LiPo battery goes through the switch, then powers the servo directly (with a 470 µF capacitor next to it), the 5 V buck converter that feeds the ESP32's 5V pin, and the 100 kΩ / 20 kΩ divider into GPIO 0 with 100 nF to ground. The servo gets its signal on GPIO 3. On 3.3 V: the IR LED with 220 Ω, the phototransistor with a 10 kΩ pull-up to GPIO 1, the KY-040 encoder (CLK 5, DT 6, SW 7) and the OLED (SDA 10, SCL 20). The GO button connects GPIO 4 to ground. Common ground.</desc>
<style>
.wiring { --vbat: #ff6b6b; --v5: #ffa94d; --v33: #51cf66; --warn: #ff8787; color: var(--sl-color-white, currentColor); }
:root[data-theme='light'] .wiring { --vbat: #c92a2a; --v5: #c2410c; --v33: #2b8a3e; --warn: #c92a2a; }
.wiring text { font: 15px var(--__sl-font, system-ui, sans-serif); fill: currentColor; }
.wiring text.s { font-size: 13px; opacity: 0.8; }
.wiring text.b { font-weight: 700; font-size: 16px; }
.wiring text.m { text-anchor: middle; }
.wiring text.e { text-anchor: end; }
.wiring .w { stroke: currentColor; stroke-width: 2; fill: none; }
.wiring .vbat { stroke: var(--vbat); }
.wiring .v5 { stroke: var(--v5); }
.wiring .v33 { stroke: var(--v33); }
.wiring text.vbat, .wiring text.v5, .wiring text.v33 { stroke: none; }
.wiring text.vbat { fill: var(--vbat); }
.wiring text.v5 { fill: var(--v5); }
.wiring text.v33 { fill: var(--v33); }
.wiring text.warn { fill: var(--warn); font-weight: 700; opacity: 1; }
.wiring .box { stroke: currentColor; stroke-width: 2; fill: rgba(127, 127, 127, 0.08); }
.wiring .part { stroke: currentColor; stroke-width: 2; fill: var(--sl-color-bg, transparent); }
.wiring .dot { fill: currentColor; }
.wiring .beam { stroke: var(--v33); stroke-width: 2; stroke-dasharray: 6 5; fill: none; }
</style>
<defs>
<g id="gnd"><path d="M0 -2V0M-11 0H11M-7 5H7M-3 10H3" stroke="currentColor" stroke-width="2" fill="none"/></g>
</defs>
<!-- Battery and switch -->
<rect class="box" x="20" y="25" width="130" height="80" rx="6"/>
<text class="b m" x="85" y="55">LiPo 2S</text>
<text class="s m" x="85" y="75">7.4 V</text>
<text class="s m" x="85" y="92">8.4 V full</text>
<text class="s" x="136" y="50">+</text>
<text class="s" x="137" y="94">−</text>
<path class="w vbat" d="M150 55H170"/>
<circle class="part" cx="173" cy="55" r="3"/>
<path class="w" d="M175 54L205 38"/>
<circle class="part" cx="212" cy="55" r="3"/>
<text class="s m" x="192" y="25">Switch</text>
<path class="w vbat" d="M215 55H440"/>
<path class="w" d="M150 90H165V112"/>
<use href="#gnd" x="165" y="114"/>
<text class="s vbat" x="280" y="47">VBAT</text>
<!-- Servo -->
<rect class="box" x="440" y="25" width="170" height="85" rx="6"/>
<text class="b m" x="535" y="55">Servo 360°</text>
<text class="s m" x="535" y="75">35 kg, powered</text>
<text class="s m" x="535" y="92">by the battery</text>
<path class="w" d="M460 110V128"/>
<use href="#gnd" x="460" y="130"/>
<path class="w" d="M540 110V230"/>
<text class="s" x="548" y="175">PWM signal</text>
<!-- 470 uF -->
<circle class="dot" cx="395" cy="55" r="4"/>
<path class="w vbat" d="M395 55V82"/>
<path class="w" d="M381 82H409M381 92Q395 84 409 92M395 89V118"/>
<text class="s" x="372" y="80">+</text>
<use href="#gnd" x="395" y="120"/>
<text class="e" x="374" y="102">470 µF</text>
<text class="s e" x="374" y="120">close to the servo</text>
<!-- Battery rail down -->
<circle class="dot" cx="260" cy="55" r="4"/>
<path class="w vbat" d="M260 55V340"/>
<!-- Buck -->
<circle class="dot" cx="260" cy="270" r="4"/>
<path class="w vbat" d="M260 270H285"/>
<rect class="box" x="285" y="240" width="105" height="60" rx="6"/>
<text class="b m" x="337" y="264">Buck</text>
<text class="s m" x="337" y="284">5.0 V out</text>
<path class="w v5" d="M390 270H430"/>
<text class="s v5 m" x="410" y="262">5 V</text>
<path class="w" d="M337 300V318"/>
<use href="#gnd" x="337" y="320"/>
<!-- ESP32 ground -->
<path class="w" d="M430 335H412V352"/>
<use href="#gnd" x="412" y="354"/>
<!-- Battery divider -->
<rect class="part" x="252" y="340" width="16" height="45"/>
<text class="s" x="276" y="368">100 kΩ</text>
<path class="w" d="M260 385V435"/>
<circle class="dot" cx="260" cy="420" r="4"/>
<path class="w" d="M260 420H430"/>
<circle class="dot" cx="335" cy="420" r="4"/>
<rect class="part" x="252" y="435" width="16" height="45"/>
<text class="s" x="276" y="463">20 kΩ</text>
<path class="w" d="M260 480V498"/>
<use href="#gnd" x="260" y="500"/>
<path class="w" d="M335 420V448M321 448H349M321 456H349M335 456V498"/>
<use href="#gnd" x="335" y="500"/>
<text class="s" x="355" y="457">100 nF</text>
<text class="s m" x="370" y="410">≈ 1.4 V max</text>
<!-- ESP32 -->
<rect class="box" x="430" y="230" width="160" height="460" rx="8"/>
<text class="b m" x="495" y="580">ESP32-C3</text>
<text class="m" x="495" y="602">SuperMini</text>
<text class="s m" x="540" y="250">GPIO 3</text>
<text x="440" y="275">5V</text>
<text x="440" y="340">GND</text>
<text x="440" y="425">GPIO 0</text>
<text class="e" x="580" y="285">3V3</text>
<text class="e" x="580" y="325">GPIO 1</text>
<text class="e" x="580" y="405">GPIO 4</text>
<text class="e" x="580" y="475">GPIO 5</text>
<text class="e" x="580" y="505">GPIO 6</text>
<text class="e" x="580" y="535">GPIO 7</text>
<text class="e" x="580" y="635">GPIO 10</text>
<text class="e" x="580" y="665">GPIO 20</text>
<path class="w v33" d="M590 280H625V266M615 266H635"/>
<text class="s v33 m" x="625" y="258">3.3 V</text>
<!-- IR LED -->
<path class="w v33" d="M690 40V28M680 28H700"/>
<text class="s v33 m" x="690" y="20">3.3 V</text>
<path class="w" d="M690 40V50"/>
<rect class="part" x="682" y="50" width="16" height="40"/>
<text class="s e" x="674" y="75">220 Ω</text>
<path class="w" d="M690 90V110"/>
<path class="part" d="M679 110H701L690 128Z"/>
<path class="w" d="M679 128H701M690 128V148"/>
<path class="w" d="M704 112L716 106M704 120L716 114"/>
<use href="#gnd" x="690" y="150"/>
<text class="s m" x="690" y="182">IR LED</text>
<!-- Beam -->
<path class="beam" d="M722 116L828 136"/>
<text class="s m" x="780" y="84">beam</text>
<text class="s m" x="780" y="99">broken by the BBs</text>
<!-- Phototransistor -->
<path class="w v33" d="M860 40V28M850 28H870"/>
<text class="s v33 m" x="860" y="20">3.3 V</text>
<path class="w" d="M860 40V50"/>
<rect class="part" x="852" y="50" width="16" height="40"/>
<text class="s" x="876" y="75">10 kΩ</text>
<path class="w" d="M860 90V133"/>
<circle class="dot" cx="860" cy="120" r="4"/>
<circle class="part" cx="858" cy="145" r="17"/>
<path class="w" d="M850 135V155M850 140L860 133M850 150L860 157V180"/>
<path d="M860 157L851 155L856 149Z" fill="currentColor"/>
<use href="#gnd" x="860" y="182"/>
<text class="s m" x="858" y="214">Phototransistor</text>
<path class="w" d="M860 120H960V320H590"/>
<text class="s" x="610" y="312">IR signal</text>
<!-- GO button -->
<path class="w" d="M590 400H700"/>
<circle class="part" cx="703" cy="400" r="3"/>
<circle class="part" cx="747" cy="400" r="3"/>
<path class="w" d="M700 388H750M725 388V376M713 376H737"/>
<path class="w" d="M750 400H780V412"/>
<use href="#gnd" x="780" y="414"/>
<text class="b m" x="725" y="430">GO button</text>
<text class="s m" x="725" y="447">cut off from the old 12 V</text>
<!-- KY-040 -->
<rect class="box" x="790" y="455" width="170" height="145" rx="6"/>
<text class="s" x="800" y="475">CLK</text>
<text class="s" x="800" y="505">DT</text>
<text class="s" x="800" y="535">SW</text>
<text class="s" x="800" y="565">+</text>
<text class="s" x="800" y="590">GND</text>
<text class="b m" x="905" y="520">KY-040</text>
<text class="s m" x="905" y="540">encoder</text>
<path class="w" d="M590 470H790M590 500H790M590 530H790"/>
<path class="w v33" d="M790 560H745M745 552V568"/>
<text class="s v33 e" x="738" y="565">3.3 V</text>
<text class="s warn e" x="738" y="582">never 5 V</text>
<path class="w" d="M790 586H770V598"/>
<use href="#gnd" x="770" y="600"/>
<!-- OLED -->
<rect class="box" x="790" y="615" width="170" height="115" rx="6"/>
<text class="s" x="800" y="635">SDA</text>
<text class="s" x="800" y="665">SCL</text>
<text class="s" x="800" y="695">VCC</text>
<text class="s" x="800" y="720">GND</text>
<text class="b m" x="905" y="670">OLED</text>
<text class="s m" x="905" y="690">SSD1306 I2C</text>
<path class="w" d="M590 630H790M590 660H790"/>
<path class="w v33" d="M790 690H745M745 682V698"/>
<text class="s v33 e" x="738" y="695">3.3 V</text>
<path class="w" d="M790 716H770V726"/>
<use href="#gnd" x="770" y="728"/>
</svg>
</div>

<style>
  .wiring-scroll { overflow-x: auto; }
  .wiring-scroll svg { display: block; width: 100%; min-width: 640px; height: auto; }
</style>

### Part by part

| Part                          | Connections                                                                                                                          |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| 2S LiPo battery               | `+` to the main switch, `−` to the common ground.                                                                                    |
| Servo                         | `+` on the battery after the switch (not on the 5 V), `−` to ground, signal on GPIO 3. A 470 µF 16 V capacitor between `+` and ground, as close to the servo as you can, with its `+` leg on the battery side. |
| 5 V converter (MP1584)        | Input on the battery after the switch, 5.0 V output (checked with a multimeter) into the ESP32's **5V** pin, common ground.          |
| Battery voltage divider       | Battery → 100 kΩ → GPIO 0 → 20 kΩ → ground. A 100 nF capacitor between GPIO 0 and ground. At 8.4 V the pin sees 8.4 × 20 / 120 = 1.40 V. Don't swap in a 47 kΩ: the pin would see about 2.7 V, too high for the C3's ADC to measure well. |
| 940 nm IR LED                 | 3.3 V → 220 Ω → LED anode, cathode to ground. It stays on all the time (about 10 mA).                                                |
| 940 nm phototransistor        | Collector on GPIO 1, with a 10 kΩ resistor from GPIO 1 to 3.3 V. Emitter to ground. Facing the LED, across the tube.                 |
| KY-040 encoder                | `CLK` → GPIO 5, `DT` → GPIO 6, `SW` → GPIO 7, `+` → **3.3 V**, `GND` → ground.                                                        |
| SSD1306 OLED screen           | `SDA` → GPIO 10, `SCL` → GPIO 20, `VCC` → 3.3 V, `GND` → ground.                                                                      |
| GO button                     | One wire on GPIO 4, the other to ground. No other wire: disconnected from the old 12 V circuit.                                      |

## First power-up

Do these in order, before connecting anything else. Write down every value you measure in the
[measurements table](#measurements) below.

1. **Measure (and if it's adjustable, set) the converter's output to 5.0 V with a multimeter, ESP32
   unplugged.** A fixed 5 V version has nothing to set, but measure it anyway. An adjustable one
   often comes out of the factory at some random voltage, sometimes close to the battery's, which
   would kill the ESP32.
2. **Check the servo's maximum voltage against the 8.4 V of a full battery.** It's wired straight
   to the battery, and many "35 kg" servos top out at 6.8 V and die above that. If it's rated for
   less than 8.4 V, it needs its own regulator (a BEC or a second converter) that can supply its
   stall current, which is what it draws when it's forced to a standstill.
3. **Check whether there is a diode between USB 5 V and the SuperMini's 5V pin.** Without one,
   plugging in USB while the battery powers the board puts the converter and your computer's USB
   port head to head. Until you've checked: never USB with the battery on (switch open, or battery
   unplugged, when flashing).
4. **Connect the KY-040's `+` to 3.3 V, never to 5 V.** The module has its own pull-up resistors
   to its `+`: on 5 V, it would push 5 V into ESP32 pins that only take 3.3 V.
5. **Cut the GO button off from the old 12 V circuit completely.** It must only touch GPIO 4 and
   ground: the slightest bit of 12 V left on that wire fries the pin.
6. **Put the 470 µF capacitor as close to the servo as you can.** When it starts, the servo draws a
   lot of current all at once; the capacitor keeps the voltage from dropping so far that the ESP32
   reboots.
7. **Put the 100 nF capacitor between GPIO 0 and ground.** It smooths the battery reading, which the
   100 kΩ resistors make sensitive to noise from the servo.
8. **Connect all the grounds together.** Without a common ground, the servo, button and sensor
   signals have no reference and the board reads garbage.
9. **Flash the `sim` firmware first and read the serial log, servo unplugged.** This firmware fakes
   the BBs: you check that the board boots and that the screen, encoder, button and battery reading
   respond, before putting the mechanics at risk.

To flash and read the serial log, see the
[firmware README](https://github.com/Karnak19/bazloader/blob/main/firmware/README.md)
(`pio run -e sim -t upload`, then `pio device monitor`).

## Measurements

:::caution[To be measured]
These values **haven't been measured yet** on the real board. The table will be filled in at the
first power-up.
:::

| Measurement                                        | Value          | Decision or note                                               |
| -------------------------------------------------- | -------------- | -------------------------------------------------------------- |
| Converter output, no load                          | _to measure_   |                                                                |
| Servo: model                                       | _to note_      |                                                                |
| Servo: maximum voltage (datasheet)                 | _to note_      | Straight on the battery, or a BEC / second converter?          |
| Diode between USB 5 V and the SuperMini's 5V pin   | _yes / no_     | Update the USB warning in the README to match.                 |
| Battery: voltage on the multimeter                 | _to measure_   |                                                                |
| Battery: voltage read by the board (`?` on serial) | _to measure_   | `BATT_CALIBRATION` = multimeter ÷ board reading.               |

## See also

- [BLE protocol](/bazloader/en/protocole-ble/): what the board exchanges with the app.
- [`firmware/src/config.h`](https://github.com/Karnak19/bazloader/blob/main/firmware/src/config.h):
  the reference for pins and default settings.
