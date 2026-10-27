---
title: Cableado
description: Pines del ESP32, esquema de cableado y comprobaciones antes del primer encendido.
---

Esta página sirve para cablear el cargador en casa y encenderlo por primera vez sin quemar nada.
Los errores más habituales (un convertidor mal ajustado, un encoder conectado a 5 V, un servo que
no aguanta la tensión de la batería) dañan piezas en el primer segundo: tómate tu tiempo y sigue la
[lista de comprobaciones](#primer-encendido) en orden.

## Pines del ESP32

La placa es una ESP32-C3 SuperMini. La tabla sigue `firmware/src/config.h`: **si alguna vez no
coinciden, manda `config.h`.**

| GPIO | Función                                   | A tener en cuenta                                                                          |
| ---- | ----------------------------------------- | ------------------------------------------------------------------------------------------ |
| 0    | Tensión de la batería (entrada analógica) | A través de un divisor de tensión de 100 kΩ / 20 kΩ, con un condensador de 100 nF a masa.  |
| 1    | Fototransistor IR                         | Resistencia de pull-up de 10 kΩ a 3,3 V. La señal sube cuando una bola corta el haz.       |
| 3    | Señal del servo (PWM)                     | Solo el cable de control: el servo se alimenta directamente de la batería.                 |
| 4    | Botón GO                                  | Contacto seco entre GPIO 4 y GND, nada más. Totalmente desconectado del antiguo circuito de 12 V. |
| 5    | Encoder KY-040, CLK                       | El `+` del módulo va a **3,3 V**, nunca a 5 V.                                             |
| 6    | Encoder KY-040, DT                        |                                                                                            |
| 7    | Encoder KY-040, SW (pulsación)            | Pasa a nivel bajo al pulsarlo.                                                             |
| 10   | OLED, SDA (I2C)                           | Pantalla SSD1306 128×64, dirección 0x3C (a veces 0x3D).                                     |
| 20   | OLED, SCL (I2C)                           | Se puede usar porque el puerto serie va por el USB nativo del chip.                        |

Deja libres estos pines:

- **GPIO 2, 8 y 9** son pines de arranque (*strapping pins*): su nivel en el momento del encendido
  decide cómo arranca el chip. El 8 también lleva el LED de la placa.
- **GPIO 4 a 7** también sirven para la depuración JTAG. No es un problema mientras uses el USB (la
  depuración USB integrada no los usa), pero una sonda JTAG externa entraría en conflicto con el
  botón y el encoder.

## Esquema de cableado

Es un esquema de principio: la posición de los pines en el dibujo no tiene nada que ver con su
sitio real en la placa. Los cables rojos llevan la tensión de la batería (7,4 V, hasta 8,4 V con la
batería cargada), el cable naranja los 5 V del convertidor, y las banderitas verdes los 3,3 V que
da el pin 3V3 del ESP32. Todos los símbolos de masa están unidos entre sí.

<div class="wiring-scroll">
<svg class="wiring" viewBox="0 0 1000 750" role="img" aria-labelledby="wiring-title wiring-desc" xmlns="http://www.w3.org/2000/svg">
<title id="wiring-title">Esquema de cableado del BazLoader</title>
<desc id="wiring-desc">La batería LiPo pasa por el interruptor y luego alimenta directamente el servo (con un condensador de 470 µF al lado), el convertidor de 5 V que alimenta el pin 5V del ESP32, y el divisor de 100 kΩ / 20 kΩ hacia GPIO 0 con 100 nF a masa. El servo recibe su señal en GPIO 3. A 3,3 V: el LED IR con 220 Ω, el fototransistor con una resistencia de pull-up de 10 kΩ hacia GPIO 1, el encoder KY-040 (CLK 5, DT 6, SW 7) y la OLED (SDA 10, SCL 20). El botón GO une GPIO 4 a masa. Masa común.</desc>
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
<text class="s m" x="85" y="92">8,4 V cargada</text>
<text class="s" x="136" y="50">+</text>
<text class="s" x="137" y="94">−</text>
<path class="w vbat" d="M150 55H170"/>
<circle class="part" cx="173" cy="55" r="3"/>
<path class="w" d="M175 54L205 38"/>
<circle class="part" cx="212" cy="55" r="3"/>
<text class="s m" x="192" y="25">Interruptor</text>
<path class="w vbat" d="M215 55H440"/>
<path class="w" d="M150 90H165V112"/>
<use href="#gnd" x="165" y="114"/>
<text class="s vbat" x="280" y="47">VBAT</text>
<!-- Servo -->
<rect class="box" x="440" y="25" width="170" height="85" rx="6"/>
<text class="b m" x="535" y="55">Servo 360°</text>
<text class="s m" x="535" y="75">35 kg, alimentado</text>
<text class="s m" x="535" y="92">por la batería</text>
<path class="w" d="M460 110V128"/>
<use href="#gnd" x="460" y="130"/>
<path class="w" d="M540 110V230"/>
<text class="s" x="548" y="175">señal PWM</text>
<!-- 470 uF -->
<circle class="dot" cx="395" cy="55" r="4"/>
<path class="w vbat" d="M395 55V82"/>
<path class="w" d="M381 82H409M381 92Q395 84 409 92M395 89V118"/>
<text class="s" x="372" y="80">+</text>
<use href="#gnd" x="395" y="120"/>
<text class="e" x="374" y="102">470 µF</text>
<text class="s e" x="374" y="120">cerca del servo</text>
<!-- Battery rail down -->
<circle class="dot" cx="260" cy="55" r="4"/>
<path class="w vbat" d="M260 55V340"/>
<!-- Buck -->
<circle class="dot" cx="260" cy="270" r="4"/>
<path class="w vbat" d="M260 270H285"/>
<rect class="box" x="285" y="240" width="105" height="60" rx="6"/>
<text class="b m" x="337" y="264">Buck</text>
<text class="s m" x="337" y="284">salida 5,0 V</text>
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
<text class="s m" x="370" y="410">≈ 1,4 V máx.</text>
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
<text class="s m" x="690" y="182">LED IR</text>
<!-- Beam -->
<path class="beam" d="M722 116L828 136"/>
<text class="s m" x="780" y="84">haz cortado</text>
<text class="s m" x="780" y="99">por las bolas</text>
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
<text class="s" x="610" y="312">señal IR</text>
<!-- GO button -->
<path class="w" d="M590 400H700"/>
<circle class="part" cx="703" cy="400" r="3"/>
<circle class="part" cx="747" cy="400" r="3"/>
<path class="w" d="M700 388H750M725 388V376M713 376H737"/>
<path class="w" d="M750 400H780V412"/>
<use href="#gnd" x="780" y="414"/>
<text class="b m" x="725" y="430">Botón GO</text>
<text class="s m" x="725" y="447">aislado del antiguo 12 V</text>
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
<text class="s v33 e" x="738" y="565">3,3 V</text>
<text class="s warn e" x="738" y="582">nunca 5 V</text>
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

### Componente por componente

| Componente                        | Conexión                                                                                                                             |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Batería LiPo 2S                   | `+` al interruptor general, `−` a la masa común.                                                                                     |
| Servo                             | `+` a la batería después del interruptor (no a los 5 V), `−` a masa, señal en GPIO 3. Condensador de 470 µF 16 V entre `+` y masa, lo más cerca posible del servo, con la pata `+` del lado de la batería. |
| Convertidor de 5 V (MP1584)       | Entrada en la batería después del interruptor, salida a 5,0 V (comprobada con el multímetro) hacia el pin **5V** del ESP32, masa común. |
| Divisor de tensión de la batería  | Batería → 100 kΩ → GPIO 0 → 20 kΩ → masa. Condensador de 100 nF entre GPIO 0 y masa. A 8,4 V, el pin ve 8,4 × 20 / 120 = 1,40 V. No pongas una de 47 kΩ en su lugar: el pin vería unos 2,7 V, demasiado para que el ADC del C3 mida bien. |
| LED IR de 940 nm                  | 3,3 V → 220 Ω → ánodo del LED, cátodo a masa. Está siempre encendido (unos 10 mA).                                                   |
| Fototransistor de 940 nm          | Colector en GPIO 1, con una resistencia de 10 kΩ de GPIO 1 a 3,3 V. Emisor a masa. Frente al LED, al otro lado del tubo.            |
| Encoder KY-040                    | `CLK` → GPIO 5, `DT` → GPIO 6, `SW` → GPIO 7, `+` → **3,3 V**, `GND` → masa.                                                          |
| Pantalla OLED SSD1306             | `SDA` → GPIO 10, `SCL` → GPIO 20, `VCC` → 3,3 V, `GND` → masa.                                                                        |
| Botón GO                          | Un cable a GPIO 4, el otro a masa. Ningún otro cable: desconectado del antiguo circuito de 12 V.                                     |

## Primer encendido

Hazlo en este orden, antes de conectar nada más. Apunta cada valor que midas en la
[tabla de mediciones](#mediciones) de más abajo.

1. **Mide (y si es regulable, ajusta) la salida del convertidor a 5,0 V con el multímetro, con el
   ESP32 desconectado.** Una versión de 5 V fija no tiene nada que ajustar, pero mídela igualmente.
   Una regulable suele salir de fábrica con una tensión cualquiera, a veces cercana a la de la
   batería, lo que destruiría el ESP32.
2. **Compara la tensión máxima del servo con los 8,4 V de la batería cargada.** Va conectado
   directamente a la batería, y muchos servos «35 kg» solo aguantan hasta 6,8 V y mueren por
   encima. Si su tensión nominal es inferior a 8,4 V, necesita su propio regulador (un BEC o un
   segundo convertidor) capaz de dar su corriente de bloqueo, es decir, lo que consume cuando hace
   fuerza estando bloqueado.
3. **Comprueba si hay un diodo entre los 5 V del USB y el pin 5V de la SuperMini.** Sin diodo,
   conectar el USB mientras la batería alimenta la placa enfrenta el convertidor con el puerto USB
   del ordenador. Mientras no lo hayas comprobado: nunca el USB con la batería encendida
   (interruptor abierto o batería desconectada para flashear).
4. **Conecta el `+` del KY-040 a 3,3 V, nunca a 5 V.** El módulo lleva sus propias resistencias de
   pull-up hacia su `+`: a 5 V, metería 5 V en pines del ESP32 que solo aguantan 3,3 V.
5. **Aísla por completo el botón GO del antiguo circuito de 12 V.** Solo debe tocar GPIO 4 y masa:
   el más mínimo resto de 12 V en ese cable quema el pin.
6. **Pon el condensador de 470 µF lo más cerca posible del servo.** Al arrancar, el servo consume de
   golpe mucha corriente: el condensador evita que la tensión caiga tanto que el ESP32 se reinicie.
7. **Pon el condensador de 100 nF entre GPIO 0 y masa.** Suaviza la lectura de la batería, que las
   resistencias de 100 kΩ hacen sensible al ruido del servo.
8. **Une todas las masas.** Sin masa común, las señales del servo, del botón y de los sensores no
   tienen referencia y la placa lee cualquier cosa.
9. **Flashea primero el firmware `sim` y lee el registro serie, con el servo desconectado.** Este
   firmware simula las bolas: compruebas que la placa arranca y que la pantalla, el encoder, el
   botón y la lectura de la batería responden, antes de arriesgar la mecánica.

Para flashear y leer el registro serie, consulta el
[README del firmware](https://github.com/Karnak19/bazloader/blob/main/firmware/README.md)
(`pio run -e sim -t upload` y después `pio device monitor`).

## Mediciones

:::caution[Por medir]
Estos valores **todavía no se han medido** en la placa real. La tabla se completará en el primer
encendido.
:::

| Medición                                             | Valor          | Decisión u observación                                          |
| ---------------------------------------------------- | -------------- | --------------------------------------------------------------- |
| Salida del convertidor, en vacío                     | _por medir_    |                                                                 |
| Servo: modelo                                        | _por anotar_   |                                                                 |
| Servo: tensión máxima (hoja de datos)                | _por anotar_   | ¿Directo a la batería, o BEC / segundo convertidor?             |
| Diodo entre los 5 V del USB y el pin 5V de la SuperMini | _sí / no_   | Actualizar en consecuencia el aviso sobre el USB del README.    |
| Batería: tensión en el multímetro                    | _por medir_    |                                                                 |
| Batería: tensión leída por la placa (`?` por serie)  | _por medir_    | `BATT_CALIBRATION` = multímetro ÷ lectura de la placa.          |

## Ver también

- [Protocolo BLE](/bazloader/es/protocole-ble/): lo que la placa intercambia con la
  aplicación.
- [`firmware/src/config.h`](https://github.com/Karnak19/bazloader/blob/main/firmware/src/config.h):
  la referencia para los pines y los ajustes por defecto.
