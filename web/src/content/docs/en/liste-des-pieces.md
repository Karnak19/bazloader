---
title: Parts list
description: Everything to order to build a BazLoader, with the traps to avoid when picking each part.
---

This page is a shopping list. Everything can be found at online electronics sellers (AliExpress and
the like). No links or prices here, they change too fast: instead you get **search terms** to copy
and paste, and above all **what to check on the product page** before you hit "buy".

The values (resistors, capacitors, pins) are the ones from the [Wiring](/bazloader/en/cablage/)
page. If the two pages ever disagree, the wiring page wins, and above it
[`firmware/src/config.h`](https://github.com/Karnak19/bazloader/blob/main/firmware/src/config.h).

The suggested quantities include a little spare: these parts cost a few cents to a few euros, and
waiting three weeks for a second delivery because of one damaged LED costs far more.

## Before you order: the servo's voltage

:::danger[Check your servo before ordering]
The original BULLOADER servo is wired **straight to the 2S battery**, which reaches **8.4 V** when
full. Many "35 kg" servos are only rated for **4.8 to 6.8 V**: above that, they overheat and
eventually burn out. Only so-called **HV** (*high voltage*) servos take 8.4 V.

1. Find the part number printed on the servo's label and look up its datasheet.
2. **If its voltage range goes up to 8.4 V (an HV servo)**: nothing to add, it stays on the
   battery.
3. **Otherwise**, add to your order a **BEC** (a small regulator from the RC hobby world) or a
   second converter, just for the servo. What to look at:
   - **current**: at least the servo's **stall current** (what it draws when it's forced to a
     standstill, on the datasheet). For a 35 kg servo, expect several amps: aim for **5 A
     continuous or more**;
   - **output voltage**: within the servo's range, for example **6.0 V** for a 4.8–6.8 V servo.
     RC UBECs often have a 5 V / 6 V jumper;
   - **input**: 2S compatible (7.4 V, 8.4 V full).

   Search terms: "UBEC 5A 6V", "UBEC 2-6S 5A".

**An MP1584 is not enough for the servo.** The one in this list only powers the ESP32: it handles
about 3 A peak, far less than a big stalled servo draws.
:::

If you add a BEC, the 470 µF capacitor goes on its output, as close to the servo as you can.

## What you already have

These parts come from the original BULLOADER and are reused. **Don't order them.**

| Part                           | Quantity | Status       | Used for                                                                                        |
| ------------------------------ | -------- | ------------ | ----------------------------------------------------------------------------------------------- |
| 2S LiPo battery (7.4 V)        | 1        | already have | Powers everything. Its LiPo charger too.                                                        |
| 35 kg 360° servo (continuous rotation) | 1 | already have | Drives the mechanism. See the box above about its voltage.                                     |
| On/off switch                  | 1        | already have | Main power cut, between the battery and everything else.                                        |
| Button (the old 12 V button)   | 1        | already have | Becomes the **GO** button: a plain contact between GPIO 4 and ground, disconnected from the old 12 V. |

## Main electronics

| Part | Quantity to order | Exact spec | What matters when picking | Used for |
| ---- | ----------------- | ---------- | ------------------------- | -------- |
| ESP32-C3 SuperMini | **3** (1 used + 2 spares) | ESP32-**C3** "SuperMini" board, USB-C, about 22 × 18 mm. Search: "ESP32-C3 SuperMini". | Make sure it's a **C3**: there are "SuperMini" boards with an S3, C6 or H2, which don't run this firmware or match this pinout. Some batches have a weak antenna (poor Bluetooth range): buying several lets you keep the best one. They're cheap. The pin headers usually come loose, not soldered. | The brain: counts the BBs, drives the servo, the screen and Bluetooth. |
| MP1584 buck converter | **2** (1 + 1 spare) | MP1584**EN** module, about 22 × 17 mm, input up to ~28 V, ~3 A peak. Preferably the **fixed 5 V output** version; otherwise the **adjustable** one (small trimmer screw). Search: "MP1584EN 5V fixed output" or "MP1584EN step down adjustable". | The **fixed 5 V** version is the safest: there's nothing to set, so no trimmer to get wrong. An adjustable one works too, but it leaves the factory at some random voltage, sometimes close to the battery's: you **must** set it to 5.0 V with a multimeter. Either way, **measure the output with a multimeter before connecting the ESP32**. Don't take another module instead: the "Mini-360" uses a different chip. | Makes the ESP32's 5 V from the battery. Not for the servo. |

## Infrared sensor

| Part | Quantity to order | Exact spec | What matters when picking | Used for |
| ---- | ----------------- | ---------- | ------------------------- | -------- |
| 3 mm infrared LED | **1 bag** (10 to 50 pieces, you need 1) | IR emitter LED, **3 mm** package, **940 nm**. Search: "3mm IR LED 940nm emitter". | The **wavelength**: **940 nm**, the same as the phototransistor. This is the most common mistake: an 850 nm LED (it glows dark red) with a 940 nm sensor, or the other way round, gives a weak and flaky signal. 3 mm package, not 5 mm: the collar is designed for 3 mm. | Sends the beam the BBs break. |
| 3 mm phototransistor | **1 bag** (10 to 50 pieces, you need 1) | NPN phototransistor, **3 mm** package, **940 nm**, 2 legs. Preferably **dark epoxy** (black or very dark purple). Search: "3mm phototransistor 940nm black". | **940 nm**, like the LED. **Dark** epoxy filters out visible light: fewer problems in direct sunlight, so prefer it. Watch out for look-alikes: a **3-leg** "IR receiver" (VS1838B, TSOP…) is a remote-control receiver and won't work here. A photodiode looks just the same but gives a much weaker signal: the product page must say *phototransistor*. | Sees the beam, and so every BB that goes through. |

## Controls

| Part | Quantity to order | Exact spec | What matters when picking | Used for |
| ---- | ----------------- | ---------- | ------------------------- | -------- |
| KY-040 rotary encoder | **2** (1 + 1 spare) | **KY-040** module: a detented encoder with a push click, on its small board with its pull-up resistors, 5 pins (CLK, DT, SW, +, GND). Search: "KY-040 rotary encoder module". | Get the **module on its board**, not the bare encoder. It runs on **3.3 V** (not 5 V), see the [wiring](/bazloader/en/cablage/). If one detent moves by 2 instead of 1 (or the other way round), that's a setting in `config.h`, no need to send the module back. | Setting the number of BBs, confirming with a click. |
| Encoder knob | **2** | Knob for a **6 mm** shaft, large (25 mm across or more), knurled or rubberised. Search: "knob 6mm shaft knurled". | Look at your KY-040's shaft: **splined** (ridges all round) or **D-shaped** (one flat side). The knob must match. Big and knurled, so you can use it **with gloves**. Some KY-040s come with a small knob, usually too small. | Turning the knob on the field. |
| 0.96" OLED screen | **2** (1 + 1 spare) | **0.96"** OLED, **128 × 64**, **SSD1306** controller, **4-pin I2C** interface (VCC, GND, SCL, SDA). Search: "0.96 OLED SSD1306 I2C 4 pin 128x64". | **4 pins, I2C.** The **7-pin** versions (SPI) are the wrong ones. **The VCC / GND order varies between sellers** (GND-VCC-SCL-SDA or VCC-GND-SCL-SDA): read the labels on the board before soldering, swapping them kills the screen. I2C address **0x3C** most of the time, sometimes **0x3D**. Prefer a single colour (white or blue): "yellow/blue" ones have a fixed yellow strip at the top. | Showing the state, the count and the battery. |

## Passive components

| Part | Quantity to order | Exact spec | What matters when picking | Used for |
| ---- | ----------------- | ---------- | ------------------------- | -------- |
| 470 µF capacitor | **5** (you need 1) | **470 µF** electrolytic, **16 V or more**. Search: "470uF 16V electrolytic capacitor". | The voltage: **16 V minimum** (25 V is fine too, just a bit bigger). A 10 V or 6.3 V one can't handle the battery's 8.4 V. It's **polarised**: the `−` leg is marked with a stripe on the can. | On the servo's power, as close to it as you can: stops the voltage from dipping when the servo starts. |
| 100 nF capacitor | **10** (you need 1) | **100 nF** ceramic (marked "104"), 50 V. Search: "100nF 104 ceramic capacitor". | Nothing tricky. Often sold in packs of 50 or 100, that's normal. | Between GPIO 0 and ground: smooths the battery reading. |
| 220 Ω resistor | in the kit (you need 1) | 220 Ω, 1/4 W. | | In series with the IR LED (about 10 mA). |
| 10 kΩ resistor | in the kit (you need 1) | 10 kΩ, 1/4 W. | | Pull-up from the phototransistor to 3.3 V. |
| 100 kΩ resistor | in the kit (you need 1) | 100 kΩ, 1/4 W. | | Battery voltage divider, battery side. |
| 20 kΩ resistor | in the kit (you need 1) | 20 kΩ, 1/4 W. | **20 kΩ** exactly: the firmware works out the battery voltage from 100 kΩ / 20 kΩ. At 8.4 V the ESP32's pin then sees 1.40 V. | Battery voltage divider, ground side. |
| Resistor kit | **1** | Assortment of 1/4 W, 1 % metal film resistors, including **220 Ω, 10 kΩ, 20 kΩ and 100 kΩ**. Search: "metal film resistor kit 1/4W 1%". | The easy way: one kit covers all four values and will come in handy later. Check that **20 kΩ** is in the kit's list of values (common 30-value kits have it). A **1 MΩ** in the kit also comes in handy if the IR receiver turns out to be a photodiode rather than a phototransistor. | All the resistors above. |

## Wiring and hardware

| Part | Quantity to order | Exact spec | What matters when picking | Used for |
| ---- | ----------------- | ---------- | ------------------------- | -------- |
| Perfboard | **1 pack** (5 to 10 boards) | Perfboard with pads, **2.54 mm** pitch, double-sided, 5 × 7 cm (to be cut down). Search: "PCB prototype board double sided 5x7". | Pads (one per hole), not strips. Double-sided, the pads hold better. The exact size of the electronics holder will come later: a 5 × 7 cm board is easy to cut down. | Holding the ESP32, the converter and the small parts. |
| 2.54 mm female header | **1 pack** | Breakable female pin headers, 2.54 mm pitch. Search: "female pin header 2.54mm". | Lets you plug the ESP32 in instead of soldering it: you can swap it in two seconds. | Socket for the ESP32 on the board. |
| Thick silicone wire | **1 m** red + **1 m** black | Soft **18 AWG** silicone wire (about 0.8 mm²). Search: "silicone wire 18AWG". | Silicone: flexible and doesn't melt under the iron. Thick enough for the **servo's current**, which is counted in amps. | Battery, switch, servo (or BEC), converter input. |
| Thin wire for signals | **1 pack** (several colours) | **26 or 28 AWG** silicone wire, several colours. Search: "silicone wire 26AWG 10 colors". | Several colours so you don't mix things up (one colour per function). Silicone bends nicely in a tight case. | IR LED, phototransistor, encoder, screen, GO button, servo signal. |
| 2.54 mm JST-XH connectors | **1 kit** (2, 3, 4 and 5 pins) | 2.54 mm JST-XH kit: solder-in headers and plugs. Easiest: **pre-crimped cables**. Search: "JST XH 2.54 pre-crimped cable" or "JST XH connector kit". | So you can **unplug** each part (screen, encoder, IR sensor, button) and take things apart without desoldering. Crimp plugs need a crimping tool: pre-crimped cables avoid that. Dupont connectors work too, but hold less well under vibration. **Not for the servo's current**: keep its original plug for that. | Connecting the electronics to the board. |
| M3 × 10 screw | **1 pack** (you need 2) | **M3 × 10 mm** socket head cap screw (hex key). Search: "M3 x 10 socket head screw". | **10 mm** long. An M3 assortment from 6 to 20 mm will also be useful later (electronics holder). | Clamps the IR collar on the tube, one screw per half. |
| M3 nut | **1 pack** (you need 2) | Standard **M3** hex nut (5.5 mm across flats, 2.4 mm thick). Search: "M3 hex nut". | A plain hex nut, not a flanged or nylon lock nut: it has to fit the collar's hexagonal pocket. | Sits in the IR collar, opposite each screw. |
| Black heat-shrink tubing | **1 assortment** | **Black** heat-shrink, 1.5 to 6 mm diameters. Search: "heat shrink tube black assortment". | **Black**: on top of insulating the joints, it shields the back of the phototransistor from light. | Insulating the joints, and shading the phototransistor and its legs. |

## Printing

| Part | Quantity to order | Exact spec | What matters when picking | Used for |
| ---- | ----------------- | ---------- | ------------------------- | -------- |
| PETG or PLA filament | **1 spool** (the collar only takes a few grams) | **Black** (or very dark), **opaque** PETG or PLA. | A light or translucent colour lets infrared through the walls and blinds the sensor in the sun. **Opaque black**, no "transparent" or "silk". | The [IR collar](https://github.com/Karnak19/bazloader/tree/main/cad) and its test piece (`fit_coupon`). |

The files to print and how to tune them are in the repo's
[`cad/`](https://github.com/Karnak19/bazloader/tree/main/cad) folder.

## Tools

| Tool | Must have? | Why |
| ---- | ---------- | --- |
| Multimeter | **Yes** | Setting the converter to 5.0 V before connecting the ESP32. No multimeter, no build. Also used to calibrate the battery reading. |
| Soldering iron, solder, flux | Yes | Every connection. An iron with temperature control is much nicer to use. |
| Calipers | Yes | Measuring the outlet tube (*inner barrel*) and the IR parts, to fit the collar. A cheap digital one is enough. |
| **Tube cutter** (best) or a hacksaw in a mitre box, and a **deburring tool** | Yes | The outlet tube is metal, so infrared can't get through it. You don't drill it: you cut it in two, the collar holds both halves end to end and the beam crosses the gap between them. A tube cutter gives a square cut with no effort. The deburring tool (or a countersink bit turned by hand) cleans up the cut ends. See [below](#cut-the-tube-and-fit-the-collar). |
| USB-C **data** cable | Yes | Flashing the ESP32. Many USB-C cables only charge: if the board doesn't show up on the computer, try another cable. |
| Wire strippers, flush cutters | Yes | Preparing the wires. |
| Heat gun or lighter | Handy | Shrinking the tubing. |
| JST-XH / Dupont crimping tool | Only with crimp plugs | Not needed with pre-crimped cables. |

## When the parts arrive

Before soldering anything:

1. **OLED screen: read the pin order** on the board's labels (VCC and GND may be swapped compared
   with the [diagram](/bazloader/en/cablage/#wiring-diagram)). Write it down.
2. **LED and phototransistor: check the 940 nm marking** on the bags, and keep the two apart so
   they don't get mixed up (they look alike).
3. **Converter: set it to 5.0 V with a multimeter, ESP32 unplugged**, before anything else. See
   the [first power-up](/bazloader/en/cablage/#first-power-up).
4. **Measure the outlet tube's diameter** with the calipers, where the collar will go, as well as
   the body of the LED and the phototransistor. Put the values into
   [`cad/params.py`](https://github.com/Karnak19/bazloader/blob/main/cad/params.py).
5. **Print the test piece** (`fit_coupon`) to find the right clearance, as explained in the
   [`cad/` folder's README](https://github.com/Karnak19/bazloader/tree/main/cad#fit_coupon),
   before printing the collar.

## Cut the tube and fit the collar

Infrared doesn't go through the metal outlet tube. Rather than drilling holes in it, you cut it in
two. The collar holds both halves end to end with a **6.5 mm** gap between them, and the beam
crosses that gap, through the printed ring that guides the BBs.

1. **Mark** a **6.5 mm** band (`BARREL_GAP` in `params.py`) where the collar is meant to go. That's
   the length of tube to remove: the collar puts back exactly that gap, so once reassembled the
   tube keeps its original length.
2. **Cut square** on each side of the band (or cut once, then shorten one half by 6.5 mm). A **tube
   cutter** is best: straight, clean cut, no effort. Otherwise, a hacksaw in a mitre box.
3. **Deburr** inside and out. On the **inner** edge of each cut end, put a **light chamfer**, with a
   deburring tool or a countersink bit turned by hand. The printed guide is 6.2 mm and the tube
   6.05 mm: without that chamfer, a BB can catch on the small step going into the outlet half.
4. **Blow** through both halves to get the chips out.
5. **Push** each half into the collar until it stops on the ring in the middle. The ring sets the
   gap and the alignment, not you.
6. **Tighten** both M3 screws, one per half.

Then, on to the [wiring](/bazloader/en/cablage/).
