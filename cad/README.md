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

To check the IR collar and the coupon over the whole plausible barrel range (8.5, 9.0 and 9.5 mm),
and the encoder knob with both bore types:

```sh
uv run python check.py
```

On the collar it probes both grip bores, the clamp slots (and that they stop at the ring), the
ring's two shoulders and its BB guide, both sockets, their shoulders and the window, the walls
around them, the screws and the wire grooves, and fails if the sockets are not on one line
`BEAM_OFFSET` off the axis. On the knob it probes the bore (size, flat, depth, on the
axis), the recess, the ridges and the top chamfer. On the box gauges it checks that the hand
measurements agree with each other, that both gauges fit the bed and keep `WALL_CLEARANCE` to
the box at their height, and that the ledge gauge rests on the ledge all round and cannot fall
through its opening.

## Parts

| Part           | What it is                                                                  |
| -------------- | --------------------------------------------------------------------------- |
| `fit_coupon`   | Print this first. Test bores and sockets at several tolerances, labelled.   |
| `ir_collar`    | Joins the two halves of the cut barrel and holds the IR LED and phototransistor. |
| `encoder_knob` | Big ridged knob for the KY-040 encoder, to turn with gloves on.             |
| `floor_gauge`  | Thin frame the size of the box floor. Checks the `BOX_` numbers at the bottom. |
| `ledge_gauge`  | Thin frame that rests on the box ledge. Checks the seat of the top plate (#18). |
| `test_ring`    | M0 smoke test of the build pipeline.                                        |

### `fit_coupon`

A plate with four barrel bores (`BARREL_OD` −0.2, 0, +0.2, +0.4), three BB guide bores
(`BB_GUIDE_D` −0.1, 0, +0.1), a rib with three horizontal
sockets (`IR_LED_DIAMETER` +0, +0.1, +0.2), and a thicker strip with the encoder shaft bores: three
D-flats (`SHAFT_D` and `SHAFT_FLAT` +0.1, +0.2, +0.3) and four round ones (`SHAFT_D` −0.2, −0.1,
0, +0.1). Each hole has its offset engraved next to it. Print it the same way and in the same
filament as the collar and the knob, then:

- slide it on the barrel: the label of the bore that slides on without play is your `FIT_TOLERANCE`;
- drop a BB through the BB guide bores: it must fall freely through the one marked 0. If it only
  goes through +.1, add 0.1 to `BB_GUIDE_D`;
- push the LED and the phototransistor in: the label of the socket that holds them straight without
  forcing is your `SOCKET_TOLERANCE`;
- D-flat shaft: push it into the D-flat row. The label of the one that goes on by hand without
  wobble is your `SHAFT_TOLERANCE`;
- knurled shaft: push it into the round row. The label of the tightest one that still goes on is
  your `KNOB_PRESS_FIT`, and set `KNOB_BORE = "round"`.

The sockets are horizontal on purpose: they are horizontal in the collar too, and a printer makes
horizontal holes a little smaller than vertical ones.

### `ir_collar`

The output inner barrel is metal, so infrared can't get through it. Rather than drilling it, you
cut it in two and the collar joins the halves: a sleeve, with a grip bore for one half at each end
and a printed ring in the middle. The beam crosses that ring, so there is nothing to drill.

- **Grip bores.** `BARREL_OD + FIT_TOLERANCE`, `GRIP_LENGTH` (10 mm) long at each end. That's over
  one barrel diameter, so each half sits straight, and it leaves room for the nut trap with
  `MIN_WALL` to the end.
- **Ring.** Between the grips, `BARREL_GAP` (6.5 mm) long. Its two faces are the shoulders both
  halves butt against, so the gap and the alignment come from the print, not from how far you
  push. Its bore is the BB guide, `BB_GUIDE_D` (6.2 mm): a bit over the 6.05 mm barrel bore, so a
  hole printed slightly small still never pinches a 5.95 to 6 mm BB. Both guide edges have a 45°
  chamfer (`RING_CHAMFER`), which also shortens the overhang under the ring when printing. 6.5 mm
  is what it takes to hold the 3.2 mm sockets with `SOCKET_WALL` above and below, so no socket
  breaks into a grip bore; that leaves 2 mm of ring above and below the window.
- **Clamps.** One C-clamp per half: a slot along each grip on +Y, two ears, an M3 × 10 screw (head
  on the LED side) and its nut pressed into a hexagonal trap. The slots stop at the ring, so the
  ring stays a closed circle: tightening the screws squeezes the barrel halves, never the BB guide.
  A single slot over the whole length would close the guide too, and one screw in the middle would
  not hold two separate tubes. One piece rather than two shells, because both sockets are then
  printed in the same layers and stay coaxial whatever the screws do. The nut traps have a corner
  on top, so they print without support.
- **Sockets.** The LED goes in from the outside on one side, the phototransistor on the other, both
  in the ring. Each stops on a flat shoulder at the same distance from the BB guide, with a small
  window (`APERTURE_D`) between the shoulder and the guide. The window narrows the beam: a thin
  beam sees the gap between two touching BBs better (see #12) and lets in less stray light. Set
  `APERTURE_W` wider than `APERTURE_D` to get a horizontal slit with more light but the same
  sharpness along the tube.
- **Beam off the axis.** The beam does not cross the tube through its centre but `BEAM_OFFSET`
  (2 mm) to the side, on the opposite side from the clamp slots. The BBs travel touching each
  other, and where two touch, the centre line is still solid, so a beam through the axis never sees
  light. Off the axis it sees the gap between two balls: with a 1.5 mm window, about 83 % of the
  light passes at 2 mm, against 4 % on the axis. The window must stay inside the BB guide
  (`BEAM_OFFSET + APERTURE_W / 2` under `BB_GUIDE_D / 2`), which `check.py` checks.
- **Light shield.** The sockets are closed all round, the leads come out at the back, and the beam
  crosses inside the ring, with the barrel halves pushed in on both sides: no light gets to the
  phototransistor except down the bore.
- **Wires.** Each pair of leads bends down at the back of its socket into a groove that runs to the
  bottom end of the collar. The grooves keep `MIN_WALL` to the grip bore (on a thick barrel the
  sockets move out a little to keep it).

Overall, at `BARREL_OD` 8.55: about 15.5 × 20.6 mm across and 26.5 mm long. Where the collar goes
on the barrel comes from #12.

**Cutting the barrel.** Remove `BARREL_GAP` (6.5 mm) of tube in total, where the collar will sit:
two cuts 6.5 mm apart, or one cut then trim one half by 6.5 mm. The collar puts that gap back, so
the reassembled barrel keeps its original length. Cut square, with a tube cutter if you have one
(else a hacksaw in a mitre box). Deburr inside and out, and put a light chamfer on the **inner**
edge of both cut ends (a deburring tool, or a countersink bit turned by hand): BBs come out of the
6.2 mm guide into the 6.05 mm barrel, and the chamfer keeps them from catching on that step. Blow
the chips out, push each half in until it stops on the ring, and tighten both screws.

**Before printing:**

1. Measure `BARREL_OD` with calipers, and the bodies of the two components (`IR_LED_DIAMETER`,
   `PHOTOTRANSISTOR_DIAMETER`, `IR_BODY_LENGTH`).
2. Print `fit_coupon`, set `FIT_TOLERANCE` and `SOCKET_TOLERANCE`, and check a BB drops freely
   through the BB guide hole marked 0.
3. Run `uv run python check.py`, then `uv run python build.py`.

**Printing:** stand the collar on its flat end face (Z = 0, the end the wire grooves open onto).
No supports. Use a **dark, opaque filament** (black PETG or PLA): white or light colours let infrared
through the walls and can blind the phototransistor in sunlight. For extra shading, slide black
heat-shrink over the back of the phototransistor and its leads.

### `encoder_knob`

A 24 mm knob, 15 mm tall, for the KY-040's bare 6 mm shaft. It is turned with gloves on, so it is
big and has 18 rounded grooves, 1.2 mm deep, round its side: deep enough to feel through a glove,
with rounded edges so they do not dig in. The top edge has a 1.2 mm chamfer.

- **Bore.** D-flat by default (`KNOB_BORE = "dflat"`): `SHAFT_D` and `SHAFT_FLAT`, both plus
  `SHAFT_TOLERANCE`. Many KY-040s have an 18-tooth knurled shaft instead: set `KNOB_BORE = "round"`
  for a plain round bore `KNOB_PRESS_FIT` under size, pressed on. A small lead-in chamfer helps find
  the shaft.
- **Depth.** The bore is `KNOB_SHAFT_GAP` (1 mm) shorter than the free shaft, so when it is pushed
  fully down the shaft tip touches the bore end, and the knob never bottoms on the nut.
- **Recess.** Underneath, a round recess clears the nut corners (`ENCODER_NUT_AF`). Pushed fully
  down, the skirt sits `KNOB_PANEL_GAP` (1 mm) above the panel, so it never rubs.
- **Panel cutout (#18).** Leave at least `KNOB_OD` / 2 plus a finger's room around the encoder hole.

**Printing:** top face down on the bed (the STL is already that way up). The recess and the bore
both open upward, so every layer sits on the one below; the only slope is the 45° top chamfer at the
bed, which also hides elephant's foot. No supports. Any filament; four perimeters make the ridges
solid.

### Box fit gauges (`floor_gauge`, `ledge_gauge`)

The box numbers in `params.py` (section "Box: Plano interior") were measured by hand, ±1 mm, and
the box flexes. Before printing anything big for the box, print these two frames (3 mm tall, a few
minutes each, any filament, no supports) and try them in the real box. Box frame used in the code:
floor at Z = 0, X along the length, Y along the width, centred on the box. Every part keeps
`WALL_CLEARANCE` (1 mm) to every wall and has `CORNER_R` (R10) vertical corners, never a press fit.

- **`floor_gauge`**, engraved `FLOOR 228x93`: the floor minus 1 mm per side, 2 mm wall. It is the
  full floor size, so it does not go through the ledge flat: twist it in on edge, it bends back.
  Drop it on the floor.
- **`ledge_gauge`**, engraved `LEDGE 235.6x98.4`: the box at the top of the ledge (Z = 136, from
  the draft) minus 1 mm per side, with an opening 3 mm narrower than the ledge opening on each
  side. Lay it on the ledge from above. Its outline is `seat_layout()` in `build.py`, which the top
  plate (#18) will reuse.

A good fit: it lies flat on its own, rocks or slides a little, and shows an even gap of about 1 mm
all round (a BB does not fall through anywhere). Push the walls in and out: nothing should move
the gauge or bend it. On the ledge gauge, the frame rests on the ledge all round, and it does not
tip into the opening when you press on any side.

If it is wrong, report:

- **Too big** (it has to be forced, it bows up, or it spreads the walls): which way (length or
  width) and by how much it overlaps or bows. Do not push it down; the box flexes and hides the
  error.
- **Too small**: the gap at each of the four walls, measured with calipers or feeler gauges (or
  count the BBs that fit), at the middle of each side.
- **Ledge gauge only**: the height of its top above the floor at each side (it should be
  `BOX_LEDGE_Z1` + 3 = 139), and whether it rests on the ledge at its outer edge or rocks on the
  inner edge of the ledge (the ledge is sloped).
- **Corners**: whether a gauge corner touches the box corner before the sides do (then the box
  corners are bigger than R10, raise `CORNER_R`).

Those go back into the `BOX_` values (and the `TODO: confirm with the gauge` notes come off), then
`uv run python check.py` and reprint if anything moved by more than 0.5 mm.

## License rule

The original BULLOADER is under the MakerWorld Exclusive License. Its files go in `original/`, and
the remixed control panel goes in `remix/`. Both folders are gitignored: **never commit them**, not
even exported STL/STEP of the remix. Parts designed from scratch here (IR collar, electronics
cradle, encoder knob) are fine to commit.

## Still to measure

Placeholders marked `TODO: measure` in `params.py`:

- `BARREL_OD`: outer diameter of the 120 mm inner barrel (8.55 mm on a standard AEG barrel;
  `check.py` covers 8.5 to 9.5).
- `IR_LED_DIAMETER`: body of the IR LED (nominal 3.0 mm).
- `PHOTOTRANSISTOR_DIAMETER`: body of the phototransistor (nominal 3.0 mm).
- `IR_BODY_LENGTH`: straight body of each component, from the start of the dome to the flange
  (about 4 mm). `SOCKET_DEPTH` must stay below it, so the flange never hits the back before the
  front reaches the shoulder.

For the encoder knob, with calipers on the encoder fitted to the panel. The defaults are the
common EC11 datasheet values (Alps EC11 and its clones, the encoder on most KY-040 boards):

- `SHAFT_D`: shaft diameter (6.0 mm). On a knurled shaft, measure over the teeth.
- `SHAFT_FLAT`: on a D-flat shaft, from the flat to the opposite side (4.5 mm on EC11).
- `ENCODER_TOP_HEIGHT`: height above the panel of the highest fixed part, the nut and washer or
  the bushing tip if it sticks out past the nut (about 2 mm).
- `SHAFT_FREE_LENGTH`: shaft length above that highest fixed part (about 12 to 15 mm). If it is
  longer than the knob can take, the build stops and asks for a taller `KNOB_HEIGHT`.
- `ENCODER_NUT_AF`: the hex nut on the M7 bushing, across flats (9 to 10 mm).

And tolerances to calibrate with `fit_coupon`: `FIT_TOLERANCE`, `SOCKET_TOLERANCE`, and either
`SHAFT_TOLERANCE` (D-flat shaft) or `KNOB_PRESS_FIT` (knurled shaft).

The electronics cradle dimensions (perfboard, ESP32, buck) will be added once the parts arrive.
