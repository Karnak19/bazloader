# CAD

Parts for BULLOADER+, written in [build123d](https://github.com/gumyr/build123d). Every dimension
lives in `params.py`; `build.py` only describes shapes.

## Build

```sh
cd cad
uv run python build.py
```

uv fetches Python 3.12 and build123d on the first run (build123d does not support older Pythons).
Each part is written to `out/<name>.stl` (for slicing) and `out/<name>.step` (for other CAD tools).
`out/` is gitignored.

To add a part: write a function in `build.py` that returns a shape, then add one line to `PARTS`.

## License rule

The original BULLOADER is under the MakerWorld Exclusive License. Its files go in `original/`, and
the remixed control panel goes in `remix/`. Both folders are gitignored: **never commit them**, not
even exported STL/STEP of the remix. Parts designed from scratch here (IR collar, electronics
cradle) are fine to commit.

## Still to measure

Placeholders marked `TODO: measure` in `params.py`:

- `BARREL_OD`: outer diameter of the 120 mm inner barrel (expected 8.5 to 9.5 mm, set to 9.0).
- `IR_LED_DIAMETER`: body of the IR LED (nominal 3.0 mm).
- `PHOTOTRANSISTOR_DIAMETER`: body of the phototransistor (nominal 3.0 mm).

The electronics cradle dimensions (perfboard, ESP32, buck) will be added once the parts arrive.
