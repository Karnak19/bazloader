[English](README.md) · **Français**

# BULLOADER+

BULLOADER+ améliore le [BULLOADER](https://makerworld.com/models/2680291), un chargeur de billes
électrique pour l'airsoft imprimé en 3D, publié par son auteur sur MakerWorld. Vous choisissez
combien de billes vous voulez, et le chargeur s'arrête tout seul une fois ce nombre atteint : les
billes sont comptées une à une par une barrière infrarouge. On le règle sur le chargeur lui-même
(une molette et un petit écran OLED) ou depuis une appli web sur Android, en Bluetooth. Tout marche
hors ligne : pas de compte, pas de cloud, pas besoin de réseau sur le terrain.

<img src="https://raw.githubusercontent.com/Karnak19/bulloader-plus/pr-media/pr-35/fr-FR-1-main.png" width="260" alt="L'écran principal de l'appli BULLOADER+ en mode démo : cible 50, presets 30, 50, 120 et 300, boutons GO et STOP">

*L'appli en mode démo, reliée à un chargeur simulé.*

## Liens

- **Documentation :** <https://karnak19.github.io/bulloader-plus/> (en anglais : <https://karnak19.github.io/bulloader-plus/en/>)
- **L'appli :** <https://karnak19.github.io/bulloader-plus/app/>. Pas encore de chargeur ? Ouvrez
  [`/app/?mock`](https://karnak19.github.io/bulloader-plus/app/?mock) pour l'essayer avec un
  appareil simulé.
- **Liste des pièces :** <https://karnak19.github.io/bulloader-plus/liste-des-pieces/>
- **Câblage :** <https://karnak19.github.io/bulloader-plus/cablage/>
- **Protocole BLE :** <https://karnak19.github.io/bulloader-plus/protocole-ble/>

## Où en est le projet

Le projet est en cours, et **il n'a pas encore été monté sur du vrai matériel.**

- Fait : le firmware et l'appli fonctionnent de bout en bout en simulation, avec de fausses
  billes ([M1](https://github.com/Karnak19/bulloader-plus/milestone/1),
  [M2](https://github.com/Karnak19/bulloader-plus/milestone/2)).
- En cours : l'intégration du matériel, c'est-à-dire le vrai servo, la vraie barrière IR et la
  calibration ([M3](https://github.com/Karnak19/bulloader-plus/milestone/3)), puis les pièces
  imprimées et le guide de montage ([M4](https://github.com/Karnak19/bulloader-plus/milestone/4)).

Il n'y a encore ni photos d'un montage fini ni chiffres de précision. Pour suivre l'avancement :
les [jalons](https://github.com/Karnak19/bulloader-plus/milestones) et les
[issues](https://github.com/Karnak19/bulloader-plus/issues).

## Ce qu'il faut

- Un BULLOADER imprimé à améliorer, et les pièces de la [liste des pièces](https://karnak19.github.io/bulloader-plus/liste-des-pieces/)
  (ESP32-C3 SuperMini, LED IR et phototransistor, molette, écran OLED et quelques petites pièces).
- Pour l'appli : **Chrome sur Android**, car elle passe par le Web Bluetooth. Pas d'iPhone ni
  d'iPad : Safari n'a pas de Web Bluetooth. Le chargeur s'utilise très bien sans téléphone.

## Contenu du repo

| Dossier     | Ce que c'est                                                           | Compiler / vérifier                                                                         |
| ----------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `firmware/` | Firmware ESP32-C3, PlatformIO + Arduino                                | `pio run` (vraie barrière IR), `pio run -e sim` (fausses billes), `pio test -e native` (tests de la logique) |
| `web/`      | Un seul site Astro : la documentation, et l'appli sur `/app/` (Preact) | `bun install`, `bun run dev`, `bun test`, `bun run build`                                   |
| `cad/`      | Pièces conçues de zéro avec build123d (collier du capteur IR, etc.)    | `uv run python build.py` (STL/STEP dans `cad/out/`), `uv run python check.py`               |

Chaque dossier a son propre README (en anglais) avec les détails. [`BRIEF.md`](BRIEF.md) contient
le cahier des charges complet.

## Licence

Le code de ce repo et les pièces conçues ici de zéro sont sous [licence MIT](LICENSE).

Le BULLOADER original est sous MakerWorld Exclusive License. Ses fichiers, et le panneau de
contrôle remixé qui en découle, ne sont pas dans ce repo et n'y seront jamais. Le remix sera publié
uniquement sur MakerWorld, en citant l'original.
