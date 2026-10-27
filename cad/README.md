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
the box at their height, and that the ledge gauge rests on the step all round and cannot drop
into the lower part of the box. On the feed bench rig, see [what `check.py` checks](#what-checkpy-checks-on-the-rig).

## Parts

| Part           | What it is                                                                  |
| -------------- | --------------------------------------------------------------------------- |
| `fit_coupon`   | Print this first. Test bores and sockets at several tolerances, labelled.   |
| `ir_collar`    | Joins the two halves of the cut barrel and holds the IR LED and phototransistor. |
| `encoder_knob` | Big ridged knob for the KY-040 encoder, to turn with gloves on.             |
| `floor_gauge`  | Thin frame the size of the box floor. Checks the `BOX_` numbers at the bottom. |
| `ledge_gauge`  | Thin frame that rests on the box ledge. Checks the seat of the top plate (#18). |
| `test_ring`    | M0 smoke test of the build pipeline.                                        |
| `feed_*`       | Bench rig for the low-inlet feed mechanism (#54). See [Feed bench rig](#feed-bench-rig). |

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

The box has two parts, one above the other: a wide upper part under the rim (254 × 121 at the rim,
measured mid-wall) and a narrower lower part down to the floor. Where they meet, about 129 to
136 mm above the floor, the wall steps in by about 8 mm at each end and 10 mm at each side: that
step is the ledge, a sloped shelf facing up. Nothing sticks into the box, so anything that fits the
floor goes in flat. The walls bow out in the middle, so the upper part is tighter at the corners
than the mid-wall numbers say.

- **`floor_gauge`**, engraved `FLOOR 231x94.5`: the floor minus 1 mm per side, 2 mm wall,
  `FLOOR_CORNER_R` corners. Drop it flat onto the floor. The first print (228 × 93, R10) had
  3 mm to spare in length, 1.5 mm in width and gaps in the corners; the second (231 × 94.5, R8)
  fits.
- **`ledge_gauge`**, engraved `LEDGE 252x117`: the first print (246 × 115) had 6 mm to spare in
  length and 2 mm in width, so it is now bigger than the original BULLOADER top plate (249 × 117).
  The second print (252 × 117) fits, with maybe 1 mm to spare.
  Its opening is 3 mm smaller than the lower part on each side. Lay it on the step from above: it
  rests on about 7 mm of step at the ends and 8 mm at the sides. Its outline is `seat_layout()` in
  `build.py`, which the top plate (#18) will reuse. It fits the 256 mm bed straight (2 mm to spare
  at each end); `check.py` would also accept it turned on the diagonal.
- **`corner_gauge_r2` … `corner_gauge_r8`**: one file per radius in `CORNER_GAUGE_RADII`, each a
  18 mm tab with one rounded corner and its radius engraved. Push each into a bottom corner of the box: a tab whose radius is too small
  stops short of both walls; too big, it touches both walls with a gap in the corner. The right one
  touches both walls with no gap. Report that number: it becomes `FLOOR_CORNER_R`. The first
  round gave R4.

A good fit: it lies flat on its own, rocks or slides a little, and shows an even gap of about 1 mm
all round (a BB does not fall through anywhere). Push the walls in and out: nothing should move
the gauge or bend it. On the ledge gauge, the frame rests on the step all round, and it does not
tip into the lower part when you press on any side.

If it is wrong, report:

- **Too big** (it has to be forced, it bows up, or it spreads the walls): which way (length or
  width) and by how much it overlaps or bows. Do not push it down; the box flexes and hides the
  error.
- **Too small**: the gap at each of the four walls, measured with calipers or feeler gauges (or
  count the BBs that fit), at the middle of each side.
- **Ledge gauge only**: the height of its top above the floor at each side (it should be
  `BOX_LEDGE_Z1` + 3 = 139), whether it rests flat on the step or rocks on its inner edge (the
  step is sloped), and the gap to the wall at the corners and at mid-wall (the walls bow out in the
  middle). If the corners touch first, raise `SEAT_CORNER_R` or lower `SEAT_L` / `SEAT_W`.
- **Corners**: whether a gauge corner touches the box corner before the sides do (then the box
  corners are bigger than R10, raise `CORNER_R`).

Those go back into the `BOX_` values (and the `TODO: confirm with the gauge` notes come off), then
`uv run python check.py` and reprint if anything moved by more than 0.5 mm.

## Feed bench rig

Concept B of #54, on the bench, before the final unit is drawn: a disc lying flat with 14 notches,
BBs dropping into them through a window in a cover, a cut-off edge at the end of the window, a
tongue under the cover that pushes each BB out into a straight channel, and an elbow that turns the
channel up into the real barrel. It is there to answer four questions with Basile's servo and real
BBs:

1. Do the notches fill every time, with a full pile and with a nearly empty one?
2. Does the cut-off edge jam, and which of the three edge shapes jams least?
3. Does the elbow pass BBs into the barrel, and which bend radius is enough?
4. Does backing off 1 or 2 pockets clear a jam we cause on purpose?

It does **not** test the final servo tower or the fit in the box. One thing is different from the
final design on purpose: the servo sits on top of an 11 cm hopper and drives the disc through a long
hex shaft, instead of sitting just above the disc. With the servo right over the disc, its ears
would hang over the inner edge of the window and there would be no room for a pile of BBs over it.
On the bench, the pile has to sit right over the window, so the servo goes up out of the way.

### How it fits together

Frame used in the code (`feed_layout()` in `build.py`): table at Z = 0, disc axis at the origin.
The disc turns **counter-clockwise seen from above**. The exit channel leaves on +X along +Y.

- **`feed_base`** stands on the table. Its block has a round pocket the disc turns in (the pocket
  wall is the shroud that keeps each BB in its notch), a 5 mm pin in the middle the disc turns on,
  the start of the exit channel (`BB_GUIDE_D` wide, as tall as the slot), nut traps underneath for
  the cover screws, and two cheeks that hold the elbow on the channel exit.
- **`feed_disc`**: 14 U-shaped notches, 6.5 mm wide, open at the rim, on a 22 mm radius (9.9 mm
  apart, 3.35 mm of land between two). 49.5 mm across and 3.7 mm thick: thinner than a BB, so the
  top 2.3 mm of each BB sticks up for the tongue. A raised hub in the middle has the pin bore
  underneath and a hex socket on top for the shaft. It lies on the floor; the BBs roll on the floor
  too, pushed by the notch walls at their middle.
- **`feed_cover_radial`, `feed_cover_skew30`, `feed_cover_skew45`**: the same cover with three
  shapes of the cut-off edge (engraved `CUT 0`, `CUT 30`, `CUT 45` on top). It lies on the base
  block, so there is 6.4 mm (`FEED_SLOT_H`) between the floor and its underside: room for one
  layer of BBs in the notches, and a BB lying on the disc (3.7 + 5.95 mm) can never follow them
  under it. The window spans 150° on the BB circle and also opens the land between the hub and the
  notches. On the skewed covers the edge is tilted from radial with its outer end set back toward
  the window, so a BB caught on it is pushed inward onto the land, where it is free, rather than out
  against the shroud. Inside 18 mm (no notches there) the edge turns radial. Both window edges have a
  45° chamfer underneath (`FEED_LIFT_CHAMFER`, 3 mm): a BB riding too high meets a slope that lifts
  it back into the window instead of a square edge that shears it. The start edge is a mirror of the
  cut-off edge, because on a reverse it becomes the cut-off. The tongue hangs from the cover 0.4 mm
  over the disc, from the strip point for 90°; its edge is the channel's inner wall, so each BB is
  pushed out of its notch along the channel. Between the end of the tongue and the window there are
  75° (about 3 pockets) of full slot height, so a 1-2 pocket reverse carries BBs back under the
  cover without meeting the tongue.
- **`feed_elbow_r25_*`, `_r30_*`, `_r40_*`**: three elbows, each in two halves (`a`, `b`) split on
  the plane of the bend. Bore `BB_GUIDE_D` (6.2 mm), its bottom level with the channel floor and
  as wide as the channel, with a 0.6 mm lead-in at the mouth so a 0.2 mm misfit between the elbow
  and the base still leaves no lip. 4 mm straight, the bend, 4 mm straight up, then a socket that
  grips the barrel (`BARREL_OD + FIT_TOLERANCE`, `GRIP_LENGTH` long) above a shoulder it butts on.
  Round the socket the split faces are set back 0.3 mm each, so the two screws there clamp the
  barrel. Barrel shoulder at 32.1 / 37.1 / 47.1 mm over the floor (36.7 / 41.7 / 51.7 over the
  table), barrel axis 29 / 34 / 44 mm out from the base block.
- **`feed_shaft`**: 12 mm hex, 90.8 mm long. It stands in the disc's hex socket and goes up 6 mm
  into the drive hub, with 2 mm to spare over its top: the servo height can be off by that much.
- **`feed_drive_hub`**: screwed to the servo horn. From the top: the 20 mm recess the horn sits in,
  a plate with the 4 horn holes (3.5 mm, on a 14 mm circle) and a hole for the spline screw head,
  a chamber for the 4 screw heads, then the hex socket.
- **`feed_hopper`**: an open square tube, 110 mm tall over the cover, standing in a groove in the
  cover's top. The BBs pile in it, round the sleeve.
- **`feed_servo_bracket`**: a plate on top of the hopper that holds the servo upside down over the
  disc axis (case through a cut-out, ears screwed into 2.5 mm pilot holes). Under the plate, a
  closed house round the servo case and the drive hub, closed at the bottom by a 45° cone onto a
  sleeve that runs down to 0.5 mm over the cover round the shaft. The BBs never reach a turning
  part. Corner tabs locate it in the hopper and take the servo's reaction. Two openings either side
  of the house are where you pour the BBs in.
- **`feed_coupon`**: three slot pockets (`FEED_SLOT_H` −0.2, 0, +0.2), four pin bores
  (`FEED_PIN_D` +0.1 to +0.4) and four hex sockets (`FEED_SHAFT_AF` +0.1 to +0.4), labelled.

### Print list

Print without supports, 0.2 mm layers, 4 perimeters. PETG or PLA; the disc, the covers and the
elbows in a smooth filament (PETG), since BBs slide on them. Every STL is already the right way up.

| STL                                         | Qty | Way up                                    | Bridges (all short)      |
| ------------------------------------------- | --- | ----------------------------------------- | ------------------------ |
| `feed_coupon`                               | 1   | flat                                      | none                     |
| `feed_shaft`                                | 1   | lying on a flat face                      | none                     |
| `feed_base`                                 | 1   | as it stands                              | nut trap ceilings        |
| `feed_disc`                                 | 1   | as it lies, hub up                        | none (the pin bore ends in a 45° cone) |
| `feed_cover_radial`, `_skew30`, `_skew45`   | 1 each | upside down: top on the bed, tongue up | hopper groove and label  |
| `feed_elbow_r25_a/_b`, `r30`, `r40`         | 1 each | split face up                          | nut trap ceilings (`b`)  |
| `feed_drive_hub`                            | 1   | socket down                               | screw-head chamber ceiling (20 mm across) |
| `feed_hopper`                               | 1   | as it stands                              | none                     |
| `feed_servo_bracket`                        | 1   | upside down: plate on the bed             | ends of the ear holes    |

Everything else that faces down is at 45° or steeper, and `check.py` fails if it is not.

Hardware, all M3: 4 × M3 × 14 and nuts (cover to base, nuts pressed into the base from under);
4 × M3 × 6 (drive hub to horn, into the horn's threads); 4 × M3 × 6 (servo ears, cutting their own
thread in the bracket: no longer at the end next to the spline, the house wall is right under it);
per elbow 4 × M3 × 12 and nuts (nuts pressed into half `b`) and 1 × M3 × 20 and a nut (through the
base cheeks); a piece of the inner barrel, its lower end chamfered inside (see the IR collar notes).

### Assembly

1. Print `feed_coupon` and `feed_shaft` first. Lay a steel rule over the slot pockets: a BB must
   roll along under it freely in the one marked 0. If it only does in +.2, add 0.2 to `FEED_SLOT_H`.
   Push the base's pin, or a 5 mm drill shank, in the pin bores: the one it turns in freely without
   wobble gives `FEED_PIN_CLEARANCE`. Slide the shaft in the hex sockets: the one it goes into
   without turning play gives `FEED_HEX_TOLERANCE`. Update `params.py`, run `check.py`, then
   `build.py`, then print the rest.
2. Base: press the 4 nuts into the traps underneath.
3. Disc on the pin, hub up. It must lie flat and turn freely.
4. A cover on the block, 4 × M3 × 14 from the top. Turn the disc by its hex socket with a finger:
   nothing rubs.
5. Elbow: press the nuts into half `b`, put the halves together with the 4 screws loose, push the
   barrel into the socket down to the shoulder, stand the elbow between the cheeks with its mouth
   against the channel, put the M3 × 20 through the cheeks, then tighten everything.
6. Shaft into the disc's socket.
7. Drive hub: screw it to the horn first (4 × M3 × 6, put in through the hex socket and driven with
   a ball-end key at a slight angle). Push the horn onto the spline and drive the spline screw
   through the hub's centre hole.
8. Servo upside down into the bracket, case through the plate, 4 ear screws.
9. Hopper into the cover's groove.
10. Lower the bracket onto the hopper, corner tabs inside, turning the disc by hand until the shaft
    drops into the drive hub.

To swap a cover: lift the bracket and the servo off (the hub slides off the shaft), empty and lift
the hopper, undo the 4 cover screws, lift the cover over the shaft. The disc and the elbow stay.

**Direction.** The rig is drawn for the disc turning counter-clockwise seen from above. If the
servo's forward turns it the other way, say so: the rig will be mirrored in the code (do not mirror
STLs one by one, the base, the covers and the elbows all go together).

### Test protocol

Drive the servo the way the device does (the firmware's load command, or a servo tester at the
speed the firmware uses). Count BBs by weight (a 0.20 g BB is 0.20 g, so 100 BBs = 20 g) or with
the IR collar if it is on the barrel. Use a clean barrel and the R30 elbow unless the test says
otherwise. Write down the BB brand and weight for every run.

1. **Filling, full pile.** Hopper filled to about 10 cm (about 2,500 BBs). Run 100 pockets
   (about 7 turns). Count the BBs that came out, and watch the notches as they leave the window:
   how many went under the cover empty?
2. **Filling, near-empty pile.** Same with only one layer of BBs left on the cover round the window.
   Same counts.
3. **Cut-off edges.** For each cover (`CUT 0`, `CUT 30`, `CUT 45`): run 200 pockets, count jams
   (the servo stops or stalls) and crushed or chipped BBs. Then provoke the bad case 10 times: stop
   the disc with a notch half under the cut-off edge, push a BB so it sits half in that notch and
   half on the land, and run forward. Does it get lifted back into the window, pushed in onto the
   land, or wedged? Keep the cover that jams least for the next tests.
4. **Elbow radii.** For R25, R30 and R40: fill the barrel (it stays full once primed), run 200 BBs,
   count jams. Note the lowest radius that never jams.
5. **Reverse.** With the best cover and elbow: provoke a jam (a BB half in a notch at the cut-off
   edge, or hold the barrel's top shut by hand until the servo stalls, then let go). Reverse 1
   pocket, then forward. If it does not clear, try 2 pockets. Ten times each. Note how many BBs fall
   back down the barrel during the reverse (count them at the channel, or through the IR collar).
6. **Endurance.** 500 BBs in a row with 0.20 g BBs, then 500 with 0.32 g BBs, full pile, best cover
   and elbow, no hand on the rig. Count jams and stops. Repeat once with a near-empty pile.

**Report back**, for each test: cover and elbow used, BB brand and weight, pockets or BBs run,
empty pockets, jams (and where: cut-off edge, tongue, channel, elbow, barrel), crushed BBs, and for
the reverse whether 1 or 2 pockets cleared it and how many BBs fell back. Also: does the disc rub
anywhere, does the shaft or the hub slip on the horn, does any BB escape under the sleeve or out of
the hopper, and the measured values for every `TODO: measure` below. Photos of any jam help.

### What `check.py` checks on the rig

- **The numbers:** 14 notches, pitch and land (at least `FEED_MIN_LAND`), notch width over the
  largest BB plus `FIT_TOLERANCE` but under two small ones, nowhere for two BBs one behind the other
  in a notch, slot height over the largest BB even printed `FIT_TOLERANCE` low but under two smallest
  BBs even printed high, a BB lying on the disc too tall for the slot, the tongue catching at least
  1 mm of the smallest BB, the channel and elbow bore over the largest BB even printed small, and the
  full-height stretch before the window at least 2 pockets long.
- **The disc:** counts the notches round the BB circle and checks they are evenly spaced, probes
  each one's width, its round end and that it goes straight through, the pin bore, the wall over it
  and the hex socket.
- **Each cover:** the slot height between the base floor and the cover, the window open over the
  whole notch band, both edges crossing the BB circle at their angle, the lift chamfer, the tilt of
  the edges (and that the outer end is set back toward the window), the tongue's edge on the
  channel's inner wall and its height over the disc, where the tongue ends, the cover solid under
  the sleeve all round, the hopper groove, and at least `FIT_TOLERANCE` (it is `FEED_RUN_GAP`) to
  the turning disc.
- **The assembly:** no two parts overlap; the shaft, the disc and the drive hub keep at least
  `FIT_TOLERANCE` from the cover, the bracket and the hopper; the disc clears the shroud all round;
  the servo case clears the bracket; the shaft goes far enough into the drive hub.
- **Each elbow:** radius at least `FEED_ELBOW_MIN_R`; the bore hollow just inside and solid just
  outside all along the run, the bend and the rise; at the mouth, every point a BB can occupy in
  the channel is open just inside the elbow even with the elbow `FIT_TOLERANCE` off in any direction
  (so there is no step to catch on); bore bottom on the channel floor, as wide as the channel, on
  its axis; the barrel socket, its shoulder and the clamp gap; `MIN_WALL` round every screw hole and
  nut trap.
- **Printing:** every feed part as exported fits the bed and sits on it, and no face points down
  flatter than 45° except the documented bridges above and the tops of small horizontal holes.

### Still to measure for the rig

All `TODO: measure` in `params.py`, sections "Servo" and "Feed mechanism":

- The servo: `SERVO_BODY_L` and `SERVO_BODY_W` (40 × 20), `SERVO_SPLINE_OFFSET` (10.2, spline axis
  to the near end of the body), `SERVO_EAR_PITCH_L` and `SERVO_EAR_PITCH_W` (48.6 × 9.9, ear hole
  centres), `SERVO_EAR_SPAN` (54.5, overall over the ears), `SERVO_FACE_TO_EARS` (11, from the
  output face of the case to the face of the ears on that side) and `SERVO_HORN_GAP` (2, from the
  output face to the back of the horn once pushed on). The last two only move the drive hub; the
  shaft takes ±2 mm.
- The horn: `FEED_HORN_D` (20), `FEED_HORN_T` (3), `FEED_HORN_HOLE_CIRCLE` (14), whether its 4
  holes are threaded M3 (if not, use screws from the horn side and nuts in the chamber), and
  `FEED_HORN_SCREW_HEAD_D` (7, the head of the screw on the spline).
- Calibrate with `feed_coupon`: `FEED_SLOT_H`, `FEED_PIN_CLEARANCE`, `FEED_HEX_TOLERANCE`; and
  `FIT_TOLERANCE` with `fit_coupon`, which sets the barrel socket.

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

For the feed bench rig (servo, horn, slot, pin and hex fits), see [Still to measure for the rig](#still-to-measure-for-the-rig).

The electronics cradle dimensions (perfboard, ESP32, buck) will be added once the parts arrive.
