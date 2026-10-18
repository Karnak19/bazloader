---
title: Verkabelung
description: Pinbelegung des ESP32, Schaltplan und Prüfungen vor dem ersten Einschalten.
---

Mit dieser Seite verkabelst du den Lader zu Hause und schaltest ihn zum ersten Mal ein, ohne
etwas zu zerstören. Die häufigsten Fehler (ein falsch eingestellter Wandler, ein Drehgeber an 5 V,
ein Servo, das die Akkuspannung nicht verträgt) beschädigen Bauteile schon in der ersten Sekunde.
Nimm dir also die Zeit, die [Checkliste](#erste-inbetriebnahme) der Reihe nach abzuarbeiten.

## Pinbelegung des ESP32

Das Board ist ein ESP32-C3 SuperMini. Die Tabelle folgt `firmware/src/config.h`: **Sollten die
beiden einmal voneinander abweichen, gilt `config.h`.**

| GPIO | Funktion                              | Gut zu wissen                                                                              |
| ---- | ------------------------------------- | ------------------------------------------------------------------------------------------ |
| 0    | Akkuspannung (Analogeingang)          | Über einen Spannungsteiler 100 kΩ / 20 kΩ, mit einem 100-nF-Kondensator gegen Masse.       |
| 1    | IR-Fototransistor                     | Pull-up-Widerstand 10 kΩ nach 3,3 V. Das Signal geht auf High, wenn eine BB den Strahl unterbricht. |
| 3    | Servosignal (PWM)                     | Nur die Steuerleitung: Das Servo wird direkt aus dem Akku versorgt.                        |
| 4    | GO-Taster                             | Ein einfacher Kontakt zwischen GPIO 4 und GND, sonst nichts. Vollständig vom alten 12-V-Stromkreis getrennt. |
| 5    | Drehgeber KY-040, CLK                 | Das `+` des Moduls kommt an **3,3 V**, nie an 5 V.                                         |
| 6    | Drehgeber KY-040, DT                  |                                                                                            |
| 7    | Drehgeber KY-040, SW (Klick)          | Geht beim Drücken auf Low.                                                                 |
| 10   | OLED, SDA (I2C)                       | Display SSD1306 128×64, Adresse 0x3C (manchmal 0x3D).                                       |
| 20   | OLED, SCL (I2C)                       | Nutzbar, weil die serielle Schnittstelle über das native USB des Chips läuft.              |

Diese Pins bleiben frei:

- **GPIO 2, 8 und 9** sind Strapping-Pins: Ihr Pegel beim Einschalten legt fest, wie der Chip
  bootet. An Pin 8 hängt außerdem die LED des Boards.
- **GPIO 4 bis 7** dienen auch dem JTAG-Debugging. Das stört nicht, solange du über USB gehst (das
  eingebaute USB-Debugging nutzt sie nicht), aber ein externer JTAG-Adapter käme dem Taster und dem
  Drehgeber in die Quere.

## Schaltplan

Das ist ein Prinzipschaltbild: Wo ein Pin in der Zeichnung sitzt, hat nichts damit zu tun, wo er
auf dem Board liegt. Die roten Leitungen führen die Akkuspannung (7,4 V, voll geladen bis 8,4 V),
die orange Leitung die 5 V des Wandlers, die grünen Fähnchen die 3,3 V vom 3V3-Pin des ESP32. Alle
Massesymbole sind miteinander verbunden.

<div class="wiring-scroll">
<svg class="wiring" viewBox="0 0 1000 750" role="img" aria-labelledby="wiring-title wiring-desc" xmlns="http://www.w3.org/2000/svg">
<title id="wiring-title">Schaltplan des BULLOADER+</title>
<desc id="wiring-desc">Der LiPo-Akku geht über den Schalter und versorgt dann direkt das Servo (mit einem 470-µF-Kondensator daneben), den 5-V-Wandler, der den 5V-Pin des ESP32 speist, und den Spannungsteiler 100 kΩ / 20 kΩ an GPIO 0 mit 100 nF gegen Masse. Das Servo bekommt sein Signal an GPIO 3. An 3,3 V: die IR-LED mit 220 Ω, der Fototransistor mit einem 10-kΩ-Pull-up an GPIO 1, der Drehgeber KY-040 (CLK 5, DT 6, SW 7) und das OLED (SDA 10, SCL 20). Der GO-Taster verbindet GPIO 4 mit Masse. Gemeinsame Masse.</desc>
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
<text class="s m" x="85" y="75">7,4 V</text>
<text class="s m" x="85" y="92">8,4 V voll</text>
<text class="s" x="136" y="50">+</text>
<text class="s" x="137" y="94">−</text>
<path class="w vbat" d="M150 55H170"/>
<circle class="part" cx="173" cy="55" r="3"/>
<path class="w" d="M175 54L205 38"/>
<circle class="part" cx="212" cy="55" r="3"/>
<text class="s m" x="192" y="25">Schalter</text>
<path class="w vbat" d="M215 55H440"/>
<path class="w" d="M150 90H165V112"/>
<use href="#gnd" x="165" y="114"/>
<text class="s vbat" x="280" y="47">VBAT</text>
<!-- Servo -->
<rect class="box" x="440" y="25" width="170" height="85" rx="6"/>
<text class="b m" x="535" y="55">Servo 360°</text>
<text class="s m" x="535" y="75">35 kg, direkt</text>
<text class="s m" x="535" y="92">am Akku</text>
<path class="w" d="M460 110V128"/>
<use href="#gnd" x="460" y="130"/>
<path class="w" d="M540 110V230"/>
<text class="s" x="548" y="175">PWM-Signal</text>
<!-- 470 uF -->
<circle class="dot" cx="395" cy="55" r="4"/>
<path class="w vbat" d="M395 55V82"/>
<path class="w" d="M381 82H409M381 92Q395 84 409 92M395 89V118"/>
<text class="s" x="372" y="80">+</text>
<use href="#gnd" x="395" y="120"/>
<text class="e" x="374" y="102">470 µF</text>
<text class="s e" x="374" y="120">nah am Servo</text>
<!-- Battery rail down -->
<circle class="dot" cx="260" cy="55" r="4"/>
<path class="w vbat" d="M260 55V340"/>
<!-- Buck -->
<circle class="dot" cx="260" cy="270" r="4"/>
<path class="w vbat" d="M260 270H285"/>
<rect class="box" x="285" y="240" width="105" height="60" rx="6"/>
<text class="b m" x="337" y="264">Buck</text>
<text class="s m" x="337" y="284">Ausgang 5,0 V</text>
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
<text class="s m" x="370" y="410">≈ 1,4 V max.</text>
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
<text class="s v33 m" x="625" y="258">3,3 V</text>
<!-- IR LED -->
<path class="w v33" d="M690 40V28M680 28H700"/>
<text class="s v33 m" x="690" y="20">3,3 V</text>
<path class="w" d="M690 40V50"/>
<rect class="part" x="682" y="50" width="16" height="40"/>
<text class="s e" x="674" y="75">220 Ω</text>
<path class="w" d="M690 90V110"/>
<path class="part" d="M679 110H701L690 128Z"/>
<path class="w" d="M679 128H701M690 128V148"/>
<path class="w" d="M704 112L716 106M704 120L716 114"/>
<use href="#gnd" x="690" y="150"/>
<text class="s m" x="690" y="182">IR-LED</text>
<!-- Beam -->
<path class="beam" d="M722 116L828 136"/>
<text class="s m" x="780" y="69">Lichtstrahl,</text>
<text class="s m" x="780" y="84">von den BBs</text>
<text class="s m" x="780" y="99">unterbrochen</text>
<!-- Phototransistor -->
<path class="w v33" d="M860 40V28M850 28H870"/>
<text class="s v33 m" x="860" y="20">3,3 V</text>
<path class="w" d="M860 40V50"/>
<rect class="part" x="852" y="50" width="16" height="40"/>
<text class="s" x="876" y="75">10 kΩ</text>
<path class="w" d="M860 90V133"/>
<circle class="dot" cx="860" cy="120" r="4"/>
<circle class="part" cx="858" cy="145" r="17"/>
<path class="w" d="M850 135V155M850 140L860 133M850 150L860 157V180"/>
<path d="M860 157L851 155L856 149Z" fill="currentColor"/>
<use href="#gnd" x="860" y="182"/>
<text class="s m" x="858" y="214">Fototransistor</text>
<path class="w" d="M860 120H960V320H590"/>
<text class="s" x="610" y="312">IR-Signal</text>
<!-- GO button -->
<path class="w" d="M590 400H700"/>
<circle class="part" cx="703" cy="400" r="3"/>
<circle class="part" cx="747" cy="400" r="3"/>
<path class="w" d="M700 388H750M725 388V376M713 376H737"/>
<path class="w" d="M750 400H780V412"/>
<use href="#gnd" x="780" y="414"/>
<text class="b m" x="725" y="430">GO-Taster</text>
<text class="s m" x="725" y="447">vom alten 12 V getrennt</text>
<!-- KY-040 -->
<rect class="box" x="790" y="455" width="170" height="145" rx="6"/>
<text class="s" x="800" y="475">CLK</text>
<text class="s" x="800" y="505">DT</text>
<text class="s" x="800" y="535">SW</text>
<text class="s" x="800" y="565">+</text>
<text class="s" x="800" y="590">GND</text>
<text class="b m" x="905" y="520">KY-040</text>
<text class="s m" x="905" y="540">Drehgeber</text>
<path class="w" d="M590 470H790M590 500H790M590 530H790"/>
<path class="w v33" d="M790 560H745M745 552V568"/>
<text class="s v33 e" x="738" y="565">3,3 V</text>
<text class="s warn e" x="738" y="582">nie 5 V</text>
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
<text class="s v33 e" x="738" y="695">3,3 V</text>
<path class="w" d="M790 716H770V726"/>
<use href="#gnd" x="770" y="728"/>
</svg>
</div>

<style>
  .wiring-scroll { overflow-x: auto; }
  .wiring-scroll svg { display: block; width: 100%; min-width: 640px; height: auto; }
</style>

### Bauteil für Bauteil

| Bauteil                       | Anschluss                                                                                                                            |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| 2S-LiPo-Akku                  | `+` an den Hauptschalter, `−` an die gemeinsame Masse.                                                                               |
| Servo                         | `+` an den Akku hinter dem Schalter (nicht an die 5 V), `−` an Masse, Signal an GPIO 3. Ein Kondensator 470 µF 16 V zwischen `+` und Masse, so nah wie möglich am Servo, mit dem `+`-Bein auf der Akkuseite. |
| 5-V-Wandler (MP1584)          | Eingang am Akku hinter dem Schalter, Ausgang 5,0 V (mit dem Multimeter geprüft), an den **5V**-Pin des ESP32, gemeinsame Masse.       |
| Akku-Spannungsteiler          | Akku → 100 kΩ → GPIO 0 → 20 kΩ → Masse. Ein 100-nF-Kondensator zwischen GPIO 0 und Masse. Bei 8,4 V sieht der Pin 8,4 × 20 / 120 = 1,40 V. Keinen 47 kΩ stattdessen nehmen: Der Pin sähe dann etwa 2,7 V, zu viel, als dass der ADC des C3 noch gut misst. |
| IR-LED 940 nm                 | 3,3 V → 220 Ω → Anode der LED, Kathode an Masse. Sie leuchtet ständig (etwa 10 mA).                                                  |
| Fototransistor 940 nm         | Kollektor an GPIO 1, mit einem 10-kΩ-Widerstand von GPIO 1 nach 3,3 V. Emitter an Masse. Gegenüber der LED, auf der anderen Seite des Rohrs. |
| Drehgeber KY-040              | `CLK` → GPIO 5, `DT` → GPIO 6, `SW` → GPIO 7, `+` → **3,3 V**, `GND` → Masse.                                                         |
| OLED-Display SSD1306          | `SDA` → GPIO 10, `SCL` → GPIO 20, `VCC` → 3,3 V, `GND` → Masse.                                                                       |
| GO-Taster                     | Ein Draht an GPIO 4, der andere an Masse. Kein weiterer Draht: vom alten 12-V-Stromkreis getrennt.                                   |

## Erste Inbetriebnahme

In dieser Reihenfolge, bevor du irgendetwas anderes anschließt. Trag jeden gemessenen Wert unten in
die [Tabelle der Messwerte](#messwerte) ein.

1. **Den Ausgang des Wandlers mit dem Multimeter auf 5,0 V prüfen (und, wenn er einstellbar ist,
   einstellen), ESP32 abgeklemmt.** Eine Version mit festen 5 V muss nicht eingestellt werden, wird
   aber trotzdem gemessen. Eine einstellbare kommt ab Werk oft mit irgendeiner Spannung, manchmal
   nahe an der des Akkus, und die würde den ESP32 zerstören.
2. **Die Maximalspannung des Servos mit den 8,4 V des vollen Akkus vergleichen.** Es hängt direkt
   am Akku, und viele „35-kg“-Servos sind nur bis 6,8 V ausgelegt und gehen darüber kaputt. Ist es
   für weniger als 8,4 V spezifiziert, braucht es einen eigenen Regler (ein BEC oder einen zweiten
   Wandler), der seinen Blockierstrom liefern kann, also den Strom, den es zieht, wenn es blockiert
   wird und dagegen ankämpft.
3. **Prüfen, ob zwischen USB-5-V und dem 5V-Pin des SuperMini eine Diode sitzt.** Ohne Diode
   arbeiten der Wandler und der USB-Port deines Computers gegeneinander, wenn du USB ansteckst,
   während der Akku das Board versorgt. Solange das nicht geprüft ist: nie USB bei eingeschaltetem
   Akku (zum Flashen Schalter aus oder Akku abgesteckt).
4. **Das `+` des KY-040 an 3,3 V anschließen, nie an 5 V.** Das Modul hat eigene
   Pull-up-Widerstände zu seinem `+`: An 5 V würde es 5 V auf Pins des ESP32 geben, die nur 3,3 V
   vertragen.
5. **Den GO-Taster vollständig vom alten 12-V-Stromkreis trennen.** Er darf nur noch GPIO 4 und
   Masse berühren: Der kleinste Rest von 12 V auf dieser Leitung zerstört den Pin.
6. **Den 470-µF-Kondensator so nah wie möglich am Servo setzen.** Beim Anlaufen zieht das Servo
   schlagartig viel Strom: Der Kondensator verhindert, dass die Spannung so weit einbricht, dass der
   ESP32 neu startet.
7. **Den 100-nF-Kondensator zwischen GPIO 0 und Masse setzen.** Er glättet die Akkumessung, die
   durch die 100-kΩ-Widerstände empfindlich für Störungen vom Servo ist.
8. **Alle Massen miteinander verbinden.** Ohne gemeinsame Masse haben die Signale von Servo, Taster
   und Sensoren keinen Bezug, und das Board liest Unsinn.
9. **Zuerst die `sim`-Firmware flashen und das serielle Log lesen, Servo abgesteckt.** Diese
   Firmware simuliert die BBs: Du prüfst, dass das Board startet und dass Display, Drehgeber,
   Taster und Akkumessung reagieren, bevor du die Mechanik riskierst.

Wie man flasht und das serielle Log liest, steht im
[README der Firmware](https://github.com/Karnak19/bulloader-plus/blob/main/firmware/README.md)
(`pio run -e sim -t upload`, dann `pio device monitor`).

## Messwerte

:::caution[Noch zu messen]
Diese Werte wurden **noch nicht** am echten Board gemessen. Die Tabelle wird bei der ersten
Inbetriebnahme ausgefüllt.
:::

| Messung                                            | Wert           | Entscheidung oder Anmerkung                                    |
| -------------------------------------------------- | -------------- | -------------------------------------------------------------- |
| Ausgang des Wandlers, ohne Last                    | _zu messen_    |                                                                |
| Servo: Modell                                      | _zu notieren_  |                                                                |
| Servo: Maximalspannung (Datenblatt)                | _zu notieren_  | Direkt am Akku, oder BEC / zweiter Wandler?                    |
| Diode zwischen USB-5-V und dem 5V-Pin des SuperMini | _ja / nein_   | Die USB-Warnung im README entsprechend anpassen.               |
| Akku: Spannung am Multimeter                       | _zu messen_    |                                                                |
| Akku: vom Board gelesene Spannung (`?` seriell)    | _zu messen_    | `BATT_CALIBRATION` = Multimeter ÷ Wert des Boards.             |

## Siehe auch

- [BLE-Protokoll](/bulloader-plus/de/protocole-ble/): was das Board mit der App austauscht.
- [`firmware/src/config.h`](https://github.com/Karnak19/bulloader-plus/blob/main/firmware/src/config.h):
  die Referenz für Pins und Standardeinstellungen.
