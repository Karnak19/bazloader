# BULLOADER+ — Brief projet

Upgrade du BULLOADER (chargeur de billes airsoft électrique imprimé en 3D, MakerWorld #2680291) pour **choisir le nombre de billes à charger**, avec comptage réel par capteur IR, commandes physiques (molette + OLED) et une PWA Android pilotant l'appareil en Bluetooth Low Energy.

## Objectifs

- Charger un nombre précis de billes (preset ou valeur libre), arrêt automatique.
- Commandes physiques utilisables avec des gants, sans téléphone.
- PWA installable (cache hors ligne) qui pilote le même appareil en BLE.
- Aucune dépendance réseau : tout doit marcher sur un terrain sans Wi-Fi ni 4G.
- Pas d'over-engineering : code simple, lisible, peu de dépendances.

## Hors périmètre

- Pas de backend, pas de compte, pas de cloud.
- Pas de Wi-Fi sur l'ESP32 (désactivé).
- Pas de support iOS (Web Bluetooth indisponible sur Safari).

---

## Matériel


| Composant                                        | Rôle                                                |
| ------------------------------------------------ | --------------------------------------------------- |
| ESP32-C3 SuperMini                               | MCU, BLE 5                                          |
| Servo 35 kg 360° (rotation continue)             | Entraînement existant du BULLOADER                  |
| LiPo 7,4 V (2S)                                  | Alimentation existante                              |
| Buck MP1584 réglé à 5,0 V                        | Alim de l'ESP32 (pin 5V)                            |
| LED IR 3 mm 940 nm + phototransistor 3 mm 940 nm | Barrière de comptage sur l'inner barrel de sortie   |
| Encodeur KY-040                                  | Réglage du nombre + clic                            |
| OLED 0,96" I2C SSD1306 128×64                    | Affichage                                           |
| Bouton existant (12 V)                           | Devient une entrée « GO » vers le MCU (contact sec) |
| Interrupteur on/off existant                     | Coupure générale                                    |
| Condensateur 470 µF 16 V                         | Sur l'alim du servo, contre les chutes de tension   |


### Pinout proposé (à centraliser dans `config.h`)

Éviter GPIO 2, 8 et 9 (broches de strapping ; la 8 porte la LED intégrée).


| GPIO | Fonction                                  |
| ---- | ----------------------------------------- |
| 0    | ADC tension batterie (pont diviseur)      |
| 1    | Phototransistor IR (entrée, interruption) |
| 3    | PWM servo                                 |
| 4    | Bouton GO (INPUT\_PULLUP)                 |
| 5    | Encodeur A                                |
| 6    | Encodeur B                                |
| 7    | Encodeur SW                               |
| 10   | I2C SDA (OLED)                            |
| 20   | I2C SCL (OLED)                            |


### Câblage électrique

- LiPo → interrupteur → servo (direct, 7,4 V nominal / 8,4 V max ; vérifier la plage du servo) + 470 µF au plus près du servo.
- LiPo → interrupteur → buck 5 V → pin 5V de l'ESP32. **Régler le buck au multimètre avant de brancher l'ESP32.**
- Masse commune pour tout.
- LED IR : 3,3 V → 220 Ω → LED → GND (allumée en permanence, ~10 mA).
- Phototransistor : collecteur → GPIO 1 avec pull-up 10 kΩ vers 3,3 V, émetteur → GND. À ajuster selon l'alignement ; prévoir une lecture analogique avec seuil si le signal numérique n'est pas assez franc.
- Pont diviseur batterie : 100 kΩ (haut) / 27 kΩ (bas) → 8,4 V donne ~1,79 V à l'ADC. Calibrer par une constante dans `config.h`.
- Ne pas alimenter par USB et par le buck en même temps tant qu'on n'a pas vérifié la présence d'une diode de protection sur la carte.

---

## Structure du repo

```
bulloader-plus/
├── CLAUDE.md              # conventions pour l'agent
├── BRIEF.md               # ce document
├── firmware/              # PlatformIO, framework Arduino
├── pwa/                   # Vite + Preact + TypeScript
├── cad/                   # build123d (Python)
├── docs/                  # schéma de câblage, protocole BLE, notes de calibration
└── .github/workflows/     # déploiement PWA sur GitHub Pages

```

---

## Firmware (`firmware/`)

**Stack** : PlatformIO, framework Arduino, board `esp32-c3-devkitm-1` (ou équivalent SuperMini). **Bibliothèques** : NimBLE-Arduino, U8g2 (OLED), Preferences (NVS). PWM servo via LEDC directement ou ESP32Servo. Encodeur : ISR maison ou petite lib, au choix du plus simple.

### Machine à états

`IDLE` → `RUNNING` → `SLOWDOWN` → `DONE` → `IDLE` Sorties d'erreur : `JAM` (timeout), `LOW_BATT`.

- **RUNNING** : servo à vitesse pleine, comptage des billes par interruption IR.
- **SLOWDOWN** : quand il reste ≤ N billes (défaut 4), vitesse réduite pour limiter le dépassement.
- **DONE** : cible atteinte → stop servo immédiat, retour à IDLE après affichage.
- **JAM** : aucune bille détectée pendant `JAM_TIMEOUT_MS` (défaut 1500) → stop, affichage « Bourrage / trémie vide ».
- **LOW_BATT** : &lt; 7,0 V → avertissement ; &lt; 6,6 V → refus de démarrer.
- **STOP** possible à tout moment (bouton GO pendant un run, clic encodeur, commande BLE).

### Comptage IR

- Interruption sur front de coupure du faisceau.
- Anti-rebond par intervalle minimal entre deux billes (`IR_MIN_INTERVAL_US`, configurable).
- Compteur `volatile`, lecture atomique.

### Servo (rotation continue)

- Point neutre (arrêt) calibrable, défaut 1500 µs, stocké en NVS.
- Vitesse pleine et vitesse lente exprimées en offset par rapport au neutre, stockées en NVS.
- Sens de rotation inversable par config.

### Interface physique

- Molette : change la cible (pas de 1, accélération si rotation rapide), clic court = cycle entre presets, clic long = menu réglages (optionnel, plus tard).
- Bouton GO : démarre / arrête.
- OLED : cible, compteur live, état, tension batterie.

### Persistance (NVS)

Presets (4 valeurs, défauts 30 / 50 / 120 / 300), dernière cible, calibration servo, `SLOWDOWN_N`, `JAM_TIMEOUT_MS`.

### Mode simulation

Flag de compilation `SIMULATE_IR` qui génère de fausses impulsions IR à un débit configurable, pour développer et tester la machine à états, l'OLED et le BLE sans le mécanisme.

---

## Protocole BLE

- Nom d'annonce : `BULLOADER`
- Un service custom, UUID 128 bits à générer une fois et à partager entre firmware et PWA (`docs/[ble-protocol.md](http://ble-protocol.md)` + constantes dans chaque projet).
- Entiers en little-endian.


| Caractéristique | Type          | Propriétés          | Description                                                             |
| --------------- | ------------- | ------------------- | ----------------------------------------------------------------------- |
| `target`        | uint16        | read, write, notify | Nombre de billes visé                                                   |
| `command`       | uint8         | write               | 1 = go, 0 = stop                                                        |
| `count`         | uint16        | read, notify        | Compteur du run en cours (notif à chaque bille, ou throttlée à \~20 Hz) |
| `state`         | uint8         | read, notify        | 0 idle, 1 running, 2 slowdown, 3 done, 4 jam, 5 low\_batt               |
| `battery`       | uint16        | read, notify        | Tension LiPo en mV (notif toutes les \~5 s)                             |
| `presets`       | uint16\[4\]   | read, write         | Presets, persistés en NVS                                               |
| `config`        | struct packée | read, write         | Calibration : neutre servo, vitesses, slowdown N, jam timeout           |


L'ESP32 est la source de vérité. Toute modification (molette ou BLE) est notifiée, pour que l'OLED et la PWA restent synchronisés.

---

## PWA (`pwa/`)

**Stack** : Vite + Preact + TypeScript, `vite-plugin-pwa` (manifest + service worker, cache hors ligne). Pas de framework UI lourd, CSS simple. **Cible** : Chrome Android uniquement. Afficher un message clair si `navigator.bluetooth` est absent. **Déploiement** : GitHub Pages via GitHub Action (penser au `base` Vite pour le sous-chemin du repo).

### Écrans

1. **Connexion** : gros bouton « Connecter » (geste utilisateur requis par Web Bluetooth), filtre sur le service UUID. Tenter une reconnexion automatique via `navigator.bluetooth.getDevices()` si disponible, sinon retomber sur le bouton.
2. **Principal** : cible (stepper + saisie), puces des presets, gros boutons GO / STOP, progression live (compteur / cible), état, tension batterie avec code couleur.
3. **Réglages** : édition des presets, calibration servo (neutre, vitesses, avec boutons de test), slowdown N, jam timeout.

### Exigences

- Mobile-first, grosses zones tactiles, dark mode par défaut.
- Gestion propre de la déconnexion (bannière + reconnexion).
- Couche BLE isolée dans un module (`ble.ts`) avec encodage/décodage typé, testable sans appareil (mock).

---

## CAD (`cad/`)

**Stack** : build123d (Python), export STL et STEP. Tous les paramètres dans un fichier unique ([`params.py`](http://params.py)), avec une tolérance d'ajustement globale.

### Pièces

1. **Collier capteur IR** : se fixe autour de l'inner barrel de sortie (diamètre extérieur **à mesurer**, ~8,5–9,5 mm, paramètre), deux logements de 3 mm face à face alignés sur l'axe du tube, passage de fils, fixation par vis M3 ou clip.
2. **Support électronique** : berceau pour perfboard (ESP32 + buck + condensateur), trous de fixation, passages de câbles. Dimensions à confirmer à réception des composants.
3. **Panneau de contrôle remixé** : à faire plus tard, à partir des fichiers originaux (découpe OLED, trou encodeur 7 mm + ergot anti-rotation, conservation de l'interrupteur et du bouton GO). Si seul un STL est disponible : booléens via trimesh + manifold3d.

### Licence

Le modèle original est sous **MakerWorld Exclusive License** : les dérivés ne peuvent être publiés que sur MakerWorld, avec attribution, sans usage commercial. **Ne pas committer les fichiers originaux ni le panneau remixé dans un repo public.** Les pièces conçues de zéro (collier, support) ne sont pas concernées.

---

## Jalons

1. **M0 — Scaffolding** : structure du repo, [`CLAUDE.md`](http://CLAUDE.md), projets firmware / PWA / CAD qui compilent, UUIDs générés, `docs/[ble-protocol.md](http://ble-protocol.md)`.
2. **M1 — Firmware sans matériel** : machine à états + OLED + encodeur en mode `SIMULATE_IR`.
3. **M2 — BLE + PWA** : service GATT complet, PWA fonctionnelle contre l'ESP32 en simulation, déploiement GitHub Pages.
4. **M3 — Intégration matériel** : servo réel, barrière IR, calibration (neutre, vitesses, seuil IR, dépassement).
5. **M4 — CAD** : collier IR et support, puis remix du panneau.

## Inconnues à lever

- Diamètre extérieur de l'inner barrel de 120 mm.
- Fichiers du panneau de contrôle d'origine (STEP de préférence).
- Plage de tension réelle du servo et son point neutre.
- Cotes réelles de l'OLED et de l'encodeur reçus (varient selon les vendeurs).
- Qualité du signal du phototransistor (numérique direct ou analogique + seuil).
- Comportement Wi-Fi/BLE de la carte (certains lots SuperMini ont une antenne faible ; si la portée BLE est mauvaise, baisser/ajuster la puissance TX).