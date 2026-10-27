---
title: Câblage
description: Brochage de l'ESP32, schéma de câblage et vérifications avant la première mise sous tension.
---

Cette page sert à câbler le chargeur chez soi, puis à l'allumer une première fois sans rien griller.
Les erreurs les plus courantes (un convertisseur mal réglé, un encodeur branché en 5 V, un servo qui
ne supporte pas la tension de la batterie) abîment des pièces dès la première seconde : prenez le
temps de suivre la [liste de vérification](#première-mise-sous-tension) dans l'ordre.

## Brochage de l'ESP32

La carte est un ESP32-C3 SuperMini. Le tableau reprend `firmware/src/config.h` : **si les deux ne
disent pas la même chose, c'est `config.h` qui fait foi.**

| GPIO | Fonction                              | À savoir                                                                                   |
| ---- | ------------------------------------- | ------------------------------------------------------------------------------------------ |
| 0    | Tension batterie (entrée analogique)  | À travers un pont diviseur 100 kΩ / 20 kΩ, avec un condensateur de 100 nF vers la masse.    |
| 1    | Phototransistor IR                    | Résistance de tirage 10 kΩ vers 3,3 V. Le signal monte quand une bille coupe le faisceau.  |
| 3    | Signal du servo (PWM)                 | Seulement le fil de commande : le servo est alimenté directement par la batterie.          |
| 4    | Bouton GO                             | Contact sec entre GPIO 4 et GND, rien d'autre. Débranché entièrement de l'ancien circuit 12 V. |
| 5    | Encodeur KY-040, CLK                  | Le `+` du module va sur **3,3 V**, jamais 5 V.                                             |
| 6    | Encodeur KY-040, DT                   |                                                                                            |
| 7    | Encodeur KY-040, SW (clic)            | Passe à l'état bas quand on appuie.                                                        |
| 10   | OLED, SDA (I2C)                       | Écran SSD1306 128×64, adresse 0x3C (parfois 0x3D).                                          |
| 20   | OLED, SCL (I2C)                       | Utilisable car le port série passe par l'USB natif de la puce.                             |

À laisser libres :

- **GPIO 2, 8 et 9** sont des broches de démarrage (*strapping pins*) : leur niveau au moment de
  l'allumage décide du mode de démarrage de la puce. La 8 porte aussi la LED de la carte.
- **GPIO 4 à 7** servent aussi au débogage JTAG. Ça ne gêne pas tant qu'on passe par l'USB (le
  débogage USB intégré ne les utilise pas), mais une sonde JTAG externe entrerait en conflit avec le
  bouton et l'encodeur.

## Schéma de câblage

Schéma de principe : la position des broches sur le dessin ne correspond pas à leur place réelle
sur la carte. Les fils rouges portent la tension batterie (7,4 V, jusqu'à 8,4 V pleine), le fil
orange le 5 V du convertisseur, les drapeaux verts le 3,3 V fourni par la broche 3V3 de l'ESP32.
Tous les symboles de masse sont reliés entre eux.

<div class="wiring-scroll">
<svg class="wiring" viewBox="0 0 1000 750" role="img" aria-labelledby="wiring-title wiring-desc" xmlns="http://www.w3.org/2000/svg">
<title id="wiring-title">Schéma de câblage du BazLoader</title>
<desc id="wiring-desc">La batterie LiPo passe par l'interrupteur, puis alimente directement le servo (avec un condensateur de 470 µF à côté), le convertisseur 5 V qui alimente la broche 5V de l'ESP32, et le pont diviseur 100 kΩ / 20 kΩ vers GPIO 0 avec 100 nF vers la masse. Le servo reçoit son signal sur GPIO 3. En 3,3 V : la LED IR avec 220 Ω, le phototransistor avec une résistance de tirage de 10 kΩ vers GPIO 1, l'encodeur KY-040 (CLK 5, DT 6, SW 7) et l'OLED (SDA 10, SCL 20). Le bouton GO relie GPIO 4 à la masse. Masse commune.</desc>
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
<text class="s m" x="85" y="92">8,4 V pleine</text>
<text class="s" x="136" y="50">+</text>
<text class="s" x="137" y="94">−</text>
<path class="w vbat" d="M150 55H170"/>
<circle class="part" cx="173" cy="55" r="3"/>
<path class="w" d="M175 54L205 38"/>
<circle class="part" cx="212" cy="55" r="3"/>
<text class="s m" x="192" y="25">Interrupteur</text>
<path class="w vbat" d="M215 55H440"/>
<path class="w" d="M150 90H165V112"/>
<use href="#gnd" x="165" y="114"/>
<text class="s vbat" x="280" y="47">VBAT</text>
<!-- Servo -->
<rect class="box" x="440" y="25" width="170" height="85" rx="6"/>
<text class="b m" x="535" y="55">Servo 360°</text>
<text class="s m" x="535" y="75">35 kg, alimenté</text>
<text class="s m" x="535" y="92">par la batterie</text>
<path class="w" d="M460 110V128"/>
<use href="#gnd" x="460" y="130"/>
<path class="w" d="M540 110V230"/>
<text class="s" x="548" y="175">signal PWM</text>
<!-- 470 uF -->
<circle class="dot" cx="395" cy="55" r="4"/>
<path class="w vbat" d="M395 55V82"/>
<path class="w" d="M381 82H409M381 92Q395 84 409 92M395 89V118"/>
<text class="s" x="372" y="80">+</text>
<use href="#gnd" x="395" y="120"/>
<text class="e" x="374" y="102">470 µF</text>
<text class="s e" x="374" y="120">près du servo</text>
<!-- Battery rail down -->
<circle class="dot" cx="260" cy="55" r="4"/>
<path class="w vbat" d="M260 55V340"/>
<!-- Buck -->
<circle class="dot" cx="260" cy="270" r="4"/>
<path class="w vbat" d="M260 270H285"/>
<rect class="box" x="285" y="240" width="105" height="60" rx="6"/>
<text class="b m" x="337" y="264">Buck</text>
<text class="s m" x="337" y="284">sortie 5,0 V</text>
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
<text class="s m" x="370" y="410">≈ 1,4 V max</text>
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
<text class="s m" x="780" y="84">faisceau</text>
<text class="s m" x="780" y="99">coupé par les billes</text>
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
<text class="s m" x="858" y="214">Phototransistor</text>
<path class="w" d="M860 120H960V320H590"/>
<text class="s" x="610" y="312">signal IR</text>
<!-- GO button -->
<path class="w" d="M590 400H700"/>
<circle class="part" cx="703" cy="400" r="3"/>
<circle class="part" cx="747" cy="400" r="3"/>
<path class="w" d="M700 388H750M725 388V376M713 376H737"/>
<path class="w" d="M750 400H780V412"/>
<use href="#gnd" x="780" y="414"/>
<text class="b m" x="725" y="430">Bouton GO</text>
<text class="s m" x="725" y="447">isolé de l'ancien 12 V</text>
<!-- KY-040 -->
<rect class="box" x="790" y="455" width="170" height="145" rx="6"/>
<text class="s" x="800" y="475">CLK</text>
<text class="s" x="800" y="505">DT</text>
<text class="s" x="800" y="535">SW</text>
<text class="s" x="800" y="565">+</text>
<text class="s" x="800" y="590">GND</text>
<text class="b m" x="905" y="520">KY-040</text>
<text class="s m" x="905" y="540">encodeur</text>
<path class="w" d="M590 470H790M590 500H790M590 530H790"/>
<path class="w v33" d="M790 560H745M745 552V568"/>
<text class="s v33 e" x="738" y="565">3,3 V</text>
<text class="s warn e" x="738" y="582">jamais 5 V</text>
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

### Composant par composant

| Composant                     | Branchement                                                                                                                          |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Batterie LiPo 2S              | `+` vers l'interrupteur général, `−` vers la masse commune.                                                                           |
| Servo                         | `+` sur la batterie après l'interrupteur (pas sur le 5 V), `−` à la masse, signal sur GPIO 3. Condensateur 470 µF 16 V entre `+` et masse, au plus près du servo, patte `+` côté batterie. |
| Convertisseur 5 V (MP1584)    | Entrée sur la batterie après l'interrupteur, sortie à 5,0 V (vérifiée au multimètre) vers la broche **5V** de l'ESP32, masse commune. |
| Pont diviseur batterie        | Batterie → 100 kΩ → GPIO 0 → 20 kΩ → masse. Condensateur 100 nF entre GPIO 0 et la masse. À 8,4 V, la broche voit 8,4 × 20 / 120 = 1,40 V. Pas de 47 kΩ à la place : la broche verrait environ 2,7 V, trop haut pour que l'ADC du C3 mesure bien. |
| LED IR 940 nm                 | 3,3 V → 220 Ω → anode de la LED, cathode à la masse. Elle reste allumée en permanence (environ 10 mA).                                |
| Phototransistor 940 nm        | Collecteur sur GPIO 1, avec une résistance de 10 kΩ de GPIO 1 vers 3,3 V. Émetteur à la masse. Face à la LED, de l'autre côté du tube. |
| Encodeur KY-040               | `CLK` → GPIO 5, `DT` → GPIO 6, `SW` → GPIO 7, `+` → **3,3 V**, `GND` → masse.                                                         |
| Écran OLED SSD1306            | `SDA` → GPIO 10, `SCL` → GPIO 20, `VCC` → 3,3 V, `GND` → masse.                                                                       |
| Bouton GO                     | Un fil sur GPIO 4, l'autre à la masse. Aucun autre fil : débranché de l'ancien circuit 12 V.                                          |

## Première mise sous tension

À faire dans cet ordre, avant de brancher quoi que ce soit d'autre. Notez chaque valeur mesurée dans
le [tableau des mesures](#mesures-relevées) plus bas.

1. **Mesurer (et si réglable, régler) la sortie du convertisseur à 5,0 V au multimètre, ESP32
   débranché.** Une version à 5 V fixe n'a rien à régler, mais on mesure quand même. Une version
   réglable sort souvent d'usine à une tension quelconque, parfois proche de celle de la batterie,
   ce qui détruirait l'ESP32.
2. **Vérifier la tension maximale du servo face aux 8,4 V de la batterie pleine.** Il est branché
   en direct sur la batterie : beaucoup de servos « 35 kg » s'arrêtent à 6,8 V et meurent au-delà.
   S'il est donné pour moins de 8,4 V, il lui faut son propre régulateur (un BEC ou un second
   convertisseur) capable de fournir son courant de blocage, c'est-à-dire ce qu'il tire quand il
   force à l'arrêt.
3. **Vérifier s'il y a une diode entre le 5 V de l'USB et la broche 5V du SuperMini.** Sans diode,
   brancher l'USB pendant que la batterie alimente la carte met le convertisseur et le port USB de
   l'ordinateur face à face. Tant que ce n'est pas vérifié : jamais l'USB avec la batterie allumée
   (interrupteur ouvert ou batterie débranchée pour flasher).
4. **Brancher le `+` du KY-040 sur 3,3 V, jamais sur 5 V.** Le module a ses propres résistances de
   tirage vers son `+` : en 5 V, il enverrait 5 V dans des broches de l'ESP32 qui n'en supportent
   que 3,3.
5. **Isoler complètement le bouton GO de l'ancien circuit 12 V.** Il ne doit plus toucher que GPIO 4
   et la masse : le moindre reste de 12 V sur ce fil grille la broche.
6. **Mettre le condensateur de 470 µF au plus près du servo.** Au démarrage, le servo tire d'un coup
   beaucoup de courant : le condensateur évite que la tension chute au point de faire redémarrer
   l'ESP32.
7. **Mettre le condensateur de 100 nF entre GPIO 0 et la masse.** Il lisse la mesure de la batterie,
   que les résistances de 100 kΩ rendent sensible aux parasites du servo.
8. **Relier toutes les masses ensemble.** Sans masse commune, le signal du servo, du bouton et des
   capteurs n'a pas de référence et la carte lit n'importe quoi.
9. **Flasher d'abord le firmware `sim` et lire le journal série, servo débranché.** Ce firmware
   simule les billes : on vérifie que la carte démarre, que l'écran, l'encodeur, le bouton et la
   lecture batterie répondent, avant de risquer la mécanique.

Pour flasher et lire le journal série, voir le
[README du firmware](https://github.com/Karnak19/bazloader/blob/main/firmware/README.md)
(`pio run -e sim -t upload`, puis `pio device monitor`).

## Mesures relevées

:::caution[À mesurer]
Ces valeurs n'ont **pas encore été relevées** sur la vraie carte. Le tableau sera rempli lors de la
première mise sous tension.
:::

| Mesure                                             | Valeur      | Décision ou remarque                                           |
| -------------------------------------------------- | ----------- | -------------------------------------------------------------- |
| Sortie du convertisseur, à vide                    | _à mesurer_ |                                                                |
| Servo : modèle                                     | _à relever_ |                                                                |
| Servo : tension maximale (fiche technique)         | _à relever_ | Alimentation directe sur la batterie, ou BEC / second convertisseur ? |
| Diode entre USB 5 V et la broche 5V du SuperMini   | _oui / non_ | Mettre à jour l'avertissement USB du README en conséquence.    |
| Batterie : tension au multimètre                   | _à mesurer_ |                                                                |
| Batterie : tension lue par la carte (`?` en série) | _à mesurer_ | `BATT_CALIBRATION` = multimètre ÷ lecture de la carte.         |

## Voir aussi

- [Protocole BLE](/bazloader/protocole-ble/) : ce que la carte échange avec l'application.
- [`firmware/src/config.h`](https://github.com/Karnak19/bazloader/blob/main/firmware/src/config.h) :
  la référence pour les broches et les réglages par défaut.
