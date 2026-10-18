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

To check the IR collar and the coupon over the whole plausible barrel range (8.5, 9.0 and 9.5 mm):

```sh
uv run python check.py
```

It probes the bore, both sockets, the shoulders and the apertures, and fails if the sockets are not
on one line through the tube centre.

## Parts

| Part         | What it is                                                                 |
| ------------ | -------------------------------------------------------------------------- |
| `fit_coupon` | Print this first. Test bores and sockets at several tolerances, labelled.  |
| `ir_collar`  | Clamps on the output inner barrel and holds the IR LED and phototransistor. |
| `test_ring`  | M0 smoke test of the build pipeline.                                        |

### `fit_coupon`

A plate with four barrel bores (`BARREL_OD` −0.2, 0, +0.2, +0.4) and a rib with three horizontal
sockets (`IR_LED_DIAMETER` +0, +0.1, +0.2). Each hole has its offset engraved next to it. Print it
the same way and in the same filament as the collar, then:

- slide it on the barrel: the label of the bore that slides on without play is your `FIT_TOLERANCE`;
- push the LED and the phototransistor in: the label of the socket that holds them straight without
  forcing is your `SOCKET_TOLERANCE`.

The sockets are horizontal on purpose: they are horizontal in the collar too, and a printer makes
horizontal holes a little smaller than vertical ones.

### `ir_collar`

One piece, closed around the barrel by a single M3 screw.

- **Clamp.** A C-clamp: one slot along the tube, two ears, an M3 × 10 screw (head on the LED side),
  and the nut pressed into a hexagonal trap in the other ear. One piece rather than two halves,
  because both sockets are then printed in the same layers and stay coaxial whatever the screw does.
  The nut trap has a corner on top, so it prints without support.
- **Sockets.** The LED goes in from the outside on one side, the phototransistor on the other. Each
  stops on a flat shoulder at the same distance from the bore, with a small window (`APERTURE_D`)
  between the shoulder and the bore. The window narrows the beam: a thin beam sees the gap between
  two touching BBs better (see #12) and lets in less stray light. Set `APERTURE_W` wider than
  `APERTURE_D` to get a horizontal slit with more light but the same sharpness along the tube.
- **Light shield.** The sockets are closed all round, the leads come out at the back, and the collar
  runs `COLLAR_LENGTH / 2` along the tube on each side of the beam, so the sun cannot shine straight
  onto the phototransistor through the gap around the barrel.
- **Wires.** Each pair of leads bends down at the back of its socket into a groove that runs to the
  bottom end of the collar.

The beam sits at mid-length of the collar. Where the collar goes on the barrel comes from #12.

**Before printing:**

1. Measure `BARREL_OD` with calipers where the collar will sit, and the bodies of the two components
   (`IR_LED_DIAMETER`, `PHOTOTRANSISTOR_DIAMETER`, `IR_BODY_LENGTH`).
2. Print `fit_coupon`, set `FIT_TOLERANCE` and `SOCKET_TOLERANCE`.
3. Check that the barrel lets 940 nm through where the beam crosses it. If it is opaque, drill two
   holes in line with the windows.
4. Run `uv run python check.py`, then `uv run python build.py`.

**Printing:** stand the collar on its flat end face (Z = 0, the end the wire grooves open onto).
No supports. Use a **dark, opaque filament** (black PETG or PLA): white or light colours let infrared
through the walls and can blind the phototransistor in sunlight. For extra shading, slide black
heat-shrink over the back of the phototransistor and its leads.

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
- `IR_BODY_LENGTH`: straight body of each component, from the start of the dome to the flange
  (about 4 mm). `SOCKET_DEPTH` must stay below it, so the flange never hits the back before the
  front reaches the shoulder.

And two tolerances to calibrate with `fit_coupon`: `FIT_TOLERANCE` and `SOCKET_TOLERANCE`.

The electronics cradle dimensions (perfboard, ESP32, buck) will be added once the parts arrive.
