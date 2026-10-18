[English](README.md) · [Français](README.fr.md) · **Español** · [Deutsch](README.de.md)

# BULLOADER+

BULLOADER+ mejora el [BULLOADER](https://makerworld.com/models/2680291), un cargador eléctrico de
bolas de airsoft impreso en 3D, publicado en MakerWorld por su autor original. Eliges cuántas bolas
quieres y el cargador se para solo cuando han pasado todas, contadas una a una por una barrera
infrarroja. Se ajusta en el propio cargador (un mando giratorio y una pequeña pantalla OLED) o
desde una aplicación web en Android, por Bluetooth. Todo funciona sin conexión: sin cuenta, sin
nube, sin necesidad de red en el campo.

<img src="https://raw.githubusercontent.com/Karnak19/bulloader-plus/pr-media/pr-35/en-US-1-main.png" width="260" alt="La pantalla principal de la aplicación BULLOADER+ en modo demo: objetivo 50, preajustes 30, 50, 120 y 300, botones GO y STOP">

*La aplicación en modo demo, conectada a un cargador simulado. La aplicación está en inglés o en
francés; la documentación, también en español.*

## Enlaces

- **Documentación:** <https://karnak19.github.io/bulloader-plus/es/>
- **La aplicación:** <https://karnak19.github.io/bulloader-plus/app/>. ¿Todavía no tienes el
  cargador? Abre [`/app/?mock`](https://karnak19.github.io/bulloader-plus/app/?mock) para probarla
  con un dispositivo simulado.
- **Lista de piezas:** <https://karnak19.github.io/bulloader-plus/es/liste-des-pieces/>
- **Cableado:** <https://karnak19.github.io/bulloader-plus/es/cablage/>
- **Protocolo BLE (en inglés):** <https://karnak19.github.io/bulloader-plus/es/protocole-ble/>

## En qué punto está

El proyecto está en curso y **todavía no se ha montado en hardware real.**

- Hecho: el firmware y la aplicación funcionan de principio a fin en simulación, con bolas
  falsas ([M1](https://github.com/Karnak19/bulloader-plus/milestone/1),
  [M2](https://github.com/Karnak19/bulloader-plus/milestone/2)).
- En curso: la integración del hardware, es decir, el servo real, la barrera IR real y la
  calibración ([M3](https://github.com/Karnak19/bulloader-plus/milestone/3)), y después las piezas
  impresas y la guía de montaje ([M4](https://github.com/Karnak19/bulloader-plus/milestone/4)).

Todavía no hay fotos de un montaje terminado ni cifras de precisión. Puedes seguir el avance en
los [hitos](https://github.com/Karnak19/bulloader-plus/milestones) y las
[issues](https://github.com/Karnak19/bulloader-plus/issues).

## Qué necesitas

- Un BULLOADER impreso que mejorar, y las piezas de la [lista de piezas](https://karnak19.github.io/bulloader-plus/es/liste-des-pieces/)
  (ESP32-C3 SuperMini, LED IR y fototransistor, encoder, pantalla OLED y algunas piezas pequeñas).
- Para la aplicación: **Chrome en Android**, porque usa Web Bluetooth. iPhone y iPad no son
  compatibles: Safari no tiene Web Bluetooth. El cargador funciona perfectamente sin móvil.

## Qué hay en el repositorio

| Carpeta     | Qué es                                                                   | Compilar / comprobar                                                                    |
| ----------- | ------------------------------------------------------------------------ | --------------------------------------------------------------------------------------- |
| `firmware/` | Firmware del ESP32-C3, PlatformIO + Arduino                              | `pio run` (barrera IR real), `pio run -e sim` (bolas falsas), `pio test -e native` (tests de la lógica) |
| `web/`      | Un solo sitio Astro: la documentación, y la aplicación en `/app/` (Preact) | `bun install`, `bun run dev`, `bun test`, `bun run build`                             |
| `cad/`      | Piezas diseñadas desde cero con build123d (collar del sensor IR, etc.)   | `uv run python build.py` (STL/STEP en `cad/out/`), `uv run python check.py`             |

Cada carpeta tiene su propio README (en inglés) con los detalles. [`BRIEF.md`](BRIEF.md) es la
especificación completa (en francés).

## Licencia

El código de este repositorio y las piezas diseñadas aquí desde cero están bajo
[licencia MIT](LICENSE).

El BULLOADER original está bajo la MakerWorld Exclusive License. Sus archivos, y el panel de
control remezclado a partir de ellos, no están en este repositorio y nunca lo estarán. El remix se
publicará solo en MakerWorld, citando el original.
