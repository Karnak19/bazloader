[English](README.md) · [Français](README.fr.md) · [Español](README.es.md) · **Deutsch**

# BULLOADER+

BULLOADER+ ist ein Upgrade für den [BULLOADER](https://makerworld.com/models/2680291), einen
3D-gedruckten elektrischen BB-Lader für Airsoft, den sein Urheber auf MakerWorld veröffentlicht
hat. Du wählst, wie viele BBs du willst, und der Lader stoppt von selbst, sobald so viele
durchgelaufen sind, einzeln gezählt von einer Infrarot-Lichtschranke. Eingestellt wird er direkt am
Lader (Drehknopf und kleines OLED-Display) oder per Bluetooth über eine Web-App auf Android. Alles
funktioniert offline: kein Konto, keine Cloud, kein Netz auf dem Spielfeld nötig.

<img src="https://raw.githubusercontent.com/Karnak19/bulloader-plus/pr-media/pr-35/en-US-1-main.png" width="260" alt="Der Hauptbildschirm der BULLOADER+-App im Demomodus: Ziel 50, Voreinstellungen 30, 50, 120 und 300, Tasten GO und STOP">

*Die App im Demomodus, verbunden mit einem simulierten Lader. Die App gibt es auf Englisch und
Französisch, die Dokumentation auch auf Deutsch.*

## Links

- **Dokumentation:** <https://karnak19.github.io/bulloader-plus/de/>
- **Die App:** <https://karnak19.github.io/bulloader-plus/app/>. Noch kein Lader? Öffne
  [`/app/?mock`](https://karnak19.github.io/bulloader-plus/app/?mock), um sie mit einem
  simulierten Gerät auszuprobieren.
- **Stückliste:** <https://karnak19.github.io/bulloader-plus/de/liste-des-pieces/>
- **Verkabelung:** <https://karnak19.github.io/bulloader-plus/de/cablage/>
- **BLE-Protokoll (auf Englisch):** <https://karnak19.github.io/bulloader-plus/de/protocole-ble/>

## Stand der Dinge

Das Projekt ist in Arbeit, und **es wurde noch nicht auf echter Hardware aufgebaut.**

- Fertig: Firmware und App funktionieren in der Simulation von Anfang bis Ende, mit simulierten
  BBs ([M1](https://github.com/Karnak19/bulloader-plus/milestone/1),
  [M2](https://github.com/Karnak19/bulloader-plus/milestone/2)).
- In Arbeit: die Hardware-Integration, also das echte Servo, die echte IR-Lichtschranke und die
  Kalibrierung ([M3](https://github.com/Karnak19/bulloader-plus/milestone/3)), danach die
  Druckteile und die Bauanleitung ([M4](https://github.com/Karnak19/bulloader-plus/milestone/4)).

Fotos eines fertigen Aufbaus und Zahlen zur Genauigkeit gibt es noch nicht. Den Fortschritt kannst
du in den [Meilensteinen](https://github.com/Karnak19/bulloader-plus/milestones) und
[Issues](https://github.com/Karnak19/bulloader-plus/issues) verfolgen.

## Was du brauchst

- Einen gedruckten BULLOADER zum Aufrüsten und die Teile aus der [Stückliste](https://karnak19.github.io/bulloader-plus/de/liste-des-pieces/)
  (ESP32-C3 SuperMini, IR-LED und Fototransistor, Drehgeber, OLED-Display und ein paar Kleinteile).
- Für die App: **Chrome unter Android**, weil sie Web Bluetooth nutzt. iPhone und iPad werden nicht
  unterstützt: Safari hat kein Web Bluetooth. Der Lader funktioniert auch ohne Handy einwandfrei.

## Was im Repo steckt

| Ordner      | Was es ist                                                              | Bauen / prüfen                                                                          |
| ----------- | ----------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `firmware/` | ESP32-C3-Firmware, PlatformIO + Arduino                                 | `pio run` (echte IR-Lichtschranke), `pio run -e sim` (simulierte BBs), `pio test -e native` (Logiktests) |
| `web/`      | Eine einzige Astro-Site: die Dokumentation und die App unter `/app/` (Preact) | `bun install`, `bun run dev`, `bun test`, `bun run build`                         |
| `cad/`      | Von Grund auf in build123d konstruierte Teile (IR-Sensorring usw.)      | `uv run python build.py` (STL/STEP in `cad/out/`), `uv run python check.py`             |

Jeder Ordner hat sein eigenes README (auf Englisch) mit den Details. [`BRIEF.md`](BRIEF.md) ist die
vollständige Spezifikation (auf Französisch).

## Lizenz

Der Code in diesem Repo und die hier von Grund auf konstruierten Teile stehen unter der
[MIT-Lizenz](LICENSE).

Der Original-BULLOADER steht unter der MakerWorld Exclusive License. Seine Dateien und das daraus
geremixte Bedienfeld sind nicht in diesem Repo und werden es nie sein. Der Remix wird nur auf
MakerWorld veröffentlicht, mit Verweis auf das Original.
