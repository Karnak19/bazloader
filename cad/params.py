"""Every dimension of the BULLOADER+ parts, in millimetres.

Change values here, never in build.py. Anything marked `TODO: measure` is a
placeholder until the real part is in hand.
"""

# --- Printing ---------------------------------------------------------------
BED_SIZE = 256.0  # Printer build volume, each axis (256 x 256 x 256).
FIT_TOLERANCE = 0.2  # TODO: calibrate with fit_coupon. Clearance added to every hole that fits around a real part.
MIN_WALL = 1.6  # Thinnest wall we print (4 perimeters at 0.4 mm nozzle).
EDGE_FILLET = 0.8  # Rounding of the outer edges along the tube, so nothing is sharp in the hand.

# --- Inner barrel (cut in two, the IR collar joins the halves) ----------------
BARREL_OD = 8.55  # Outer diameter of the 120 mm inner barrel: a standard AEG inner barrel. Confirm with calipers (#16).
BARREL_ID = 6.05  # Bore of that barrel, the usual 6.05 mm AEG bore. The printed BB guide must be wider.

# --- IR barrier ---------------------------------------------------------------
IR_LED_DIAMETER = 3.0  # TODO: measure. Body of the 3 mm IR LED.
PHOTOTRANSISTOR_DIAMETER = 3.0  # TODO: measure. Body of the 3 mm phototransistor.
IR_BODY_LENGTH = 4.0  # TODO: measure. Straight body of each component, from the start of the dome to the flange.

# --- IR collar ----------------------------------------------------------------
# The barrel is cut in two. The collar is a sleeve: each end grips one half, and a
# printed ring between them sets the gap and guides the BBs across it. The beam
# crosses that ring, so nothing is drilled. Printed standing on its end face, tube
# axis vertical: the bores come out round and both sockets are built in the same
# layers, so they stay coaxial.
SOCKET_TOLERANCE = 0.2  # TODO: calibrate with fit_coupon. Clearance on the 3 mm sockets.
SOCKET_DEPTH = 3.5  # Guide length up to the stop shoulder. Below IR_BODY_LENGTH, so the flange stays outside.
SOCKET_WALL = 1.6  # Wall around each socket.
APERTURE_D = 1.5  # Height of the window between socket and bore, along the tube. Narrower = sharper beam (#12).
APERTURE_W = 1.5  # Width of that window across the tube. Equal to APERTURE_D: round hole; wider: horizontal slit.
APERTURE_LEN = 1.2  # Length of the window, i.e. the thinnest wall between the stop shoulder and the BB guide.
BEAM_OFFSET = 2.0  # Beam moved sideways off the tube axis (#12). BBs travel touching, and where two touch the
# axis is still solid, so a beam through the axis is never let through. Off-axis it sees the gap between two
# balls: about 83 % of the light at 2.0 mm, against 4 % on the axis. Keep it + APERTURE_W / 2 inside BB_GUIDE_D.
BB_GUIDE_D = 6.2  # Bore of the printed ring the BBs cross. Over BARREL_ID, so a hole printed a bit small still
# clears a 5.95-6 mm BB; the step back into the 6.05 barrel is what the chamfer on the cut ends is for.
BARREL_GAP = 6.5  # Ring length = gap between the two barrel halves = tube to remove when cutting. Holds the
# 3.2 mm socket with SOCKET_WALL above and below (6.4), so no socket breaks into a grip bore; that also leaves
# well over MIN_WALL of ring above and below the 1.5 mm window.
GRIP_LENGTH = 10.0  # Bore gripping each barrel half. Over one barrel diameter, so the halves stay coaxial, and
# long enough for the M3 nut trap (6.7 mm tall) with MIN_WALL to the end.
RING_CHAMFER = 0.5  # 45 deg chamfer on both edges of the BB guide. Shortens the overhang under the ring when
# printing, and takes off the edge a BB could catch on.
COLLAR_WALL = 2.0  # Radial wall around the grip bores.
WIRE_CHANNEL_W = 3.4  # Groove for one pair of leads (2.54 mm pitch + wire), from under each socket to the bottom end.
WIRE_CHANNEL_DEPTH = 1.5  # Depth of that groove.
CLAMP_SLOT = 1.5  # Gap of each C-clamp, closed by its M3 screw. Far more than the bore clearance it has to take up.

# --- Hardware ---------------------------------------------------------------
M3_CLEARANCE = 3.4  # Through-hole for an M3 screw.
M3_NUT_AF = 5.5  # M3 hex nut, across flats.
M3_NUT_THICKNESS = 2.4  # M3 hex nut thickness.
NUT_TOLERANCE = 0.3  # Clearance on the nut trap, so the nut presses in by hand.

# --- Rotary encoder (KY-040 module, EC11-type encoder) ----------------------
# Defaults come from the common EC11 datasheet values (Alps EC11 series and its
# clones, the encoder on most KY-040 boards): 6 mm shaft, D-cut flat leaving
# 4.5 mm, M7 x 0.75 bushing with a hex nut, shaft 15-30 mm long from the mounting
# face depending on the version. KY-040 sellers ship both a D-flat and an
# 18-tooth knurled "half shaft", so measure yours.
SHAFT_D = 6.0  # TODO: measure. Outer diameter of the shaft.
SHAFT_FLAT = 4.5  # TODO: measure. Across the D-flat: from the flat to the opposite side (EC11: 4.5).
ENCODER_TOP_HEIGHT = 2.0  # TODO: measure. Highest fixed part (nut + washer, or bushing tip) above the panel.
SHAFT_FREE_LENGTH = 12.0  # TODO: measure. Shaft above that highest fixed thing (nut or bushing tip), expected 12-15.
ENCODER_NUT_AF = 10.0  # TODO: measure. Hex nut on the M7 bushing, across flats (9-10 on KY-040 kits).

# --- Encoder knob -----------------------------------------------------------
# Printed top face down on the bed: the recess and the bore open upward, so no
# overhang at all except the 45 deg chamfer at the bed.
SHAFT_TOLERANCE = 0.2  # TODO: calibrate with fit_coupon. Clearance on the D-flat bore (diameter and flat).
KNOB_BORE = "dflat"  # "dflat" for a D-flat shaft, "round" for a knurled shaft (press fit).
KNOB_PRESS_FIT = -0.1  # TODO: calibrate with fit_coupon. Round bore = SHAFT_D + this; under size so it grips.
KNOB_OD = 24.0  # Outer diameter over the ridges. Also the minimum clearance around the panel hole (#18).
KNOB_HEIGHT = 15.0  # Overall height. Must fit the recess, the bore and a MIN_WALL cap.
KNOB_RIDGES = 18  # Number of grooves round the side.
KNOB_RIDGE_DEPTH = 1.2  # Depth of each groove: deep enough to feel through a glove.
KNOB_RIDGE_WIDTH = 2.8  # Width of each groove at the surface (land between grooves is what is left).
KNOB_RIDGE_FILLET = 0.4  # Rounds the groove edges, so the ridges grip without being sharp.
KNOB_TOP_CHAMFER = 1.2  # 45 deg chamfer on the top edge (prints on the bed, also stops elephant's foot).
KNOB_SHAFT_GAP = 1.0  # Bore depth = SHAFT_FREE_LENGTH - this, so the knob never bottoms on the nut.
KNOB_RECESS_CLEARANCE = 0.8  # Radial clearance around the nut corners in the recess underneath.
KNOB_PANEL_GAP = 1.0  # Gap left between the knob's skirt and the panel when it is pushed fully down.
KNOB_BORE_CHAMFER = 0.5  # Lead-in chamfer at the bore entrance, helps find the shaft.

# --- Fit coupon (print it first, then update the tolerances above) -----------
COUPON_THICKNESS = 3.0  # Plate thickness, i.e. how long the barrel and BB guide test bores are.
COUPON_BORE_OFFSETS = (-0.2, 0.0, 0.2, 0.4)  # Bore = BARREL_OD + offset. The best slide gives FIT_TOLERANCE.
COUPON_GUIDE_OFFSETS = (-0.1, 0.0, 0.1)  # BB guide = BB_GUIDE_D + offset. A BB must drop through the 0 one freely.
COUPON_SOCKET_OFFSETS = (0.0, 0.1, 0.2)  # Socket = IR_LED_DIAMETER + offset. The best hold gives SOCKET_TOLERANCE.
COUPON_SHAFT_OFFSETS = (0.1, 0.2, 0.3)  # D-flat bore = SHAFT_D/SHAFT_FLAT + offset. The best fit gives SHAFT_TOLERANCE.
COUPON_PRESS_OFFSETS = (-0.2, -0.1, 0.0, 0.1)  # Round bore = SHAFT_D + offset. Tightest one that goes on: KNOB_PRESS_FIT.
COUPON_KNOB_THICKNESS = 6.0  # The knob test bores go through a thicker strip, so the grip is felt over some length.
COUPON_GAP = 3.0  # Material between two test holes.
COUPON_TEXT_SIZE = 3.0  # Height of the engraved labels.
COUPON_TEXT_DEPTH = 0.4  # Engraving depth (2 layers at 0.2).

# --- Box: Plano interior (Basile's box) --------------------------------------
# Measured by hand inside the box (+/- 1 mm), 2026-10-27 (#52). Frame: box floor at Z=0,
# Z up to the rim; X along the length, Y along the width, the interior centred on X=0, Y=0.
# Two parts, one above the other: a wide upper part under the rim and a narrower lower part down
# to the floor. Where they meet, the wall steps in: that step is the ledge, a shelf facing up.
# Nothing sticks into the box, so nothing narrows the way in. Both parts lean out (draft), so
# each grows linearly with Z. A small notch in the ledge at the front is ignored.
# THE BOX FLEXES: a part that forces at the bottom spreads the walls and changes the fit higher
# up. Every part keeps WALL_CLEARANCE to every wall, never a press fit.
BOX_FLOOR_L = 233.0  # Interior length at the floor (Z=0). Measured 230; the first floor gauge (228) had 3 mm to spare.
BOX_FLOOR_W = 96.5  # Interior width at the floor. Measured 95; the first floor gauge (93) had 1.5 mm to spare.
BOX_REF_Z = 125.0  # Height of the second measurement, used to get the draft.
BOX_REF_L = 237.0  # TODO: confirm with the gauge. Interior length at BOX_REF_Z.
BOX_REF_W = 100.0  # TODO: confirm with the gauge. Interior width at BOX_REF_Z.
BOX_TAPER_L = (BOX_REF_L - BOX_FLOOR_L) / BOX_REF_Z  # Interior length gained per mm of height (both ends together).
BOX_TAPER_W = (BOX_REF_W - BOX_FLOOR_W) / BOX_REF_Z  # Interior width gained per mm of height (both sides together).
BOX_HEIGHT = 153.0  # TODO: confirm with the gauge. Floor to rim.
CORNER_R = 10.0  # Vertical corner radius of our parts. The box's interior corners are under 10 mm, so a part
# with R10 always fits; the worst gap left in a corner is about 4 mm, under one BB.
FLOOR_CORNER_R = 8.0  # TODO: confirm with the gauge. Corner radius of parts on the floor: the floor gauge at R10 left
# visible gaps in the corners, so the box corners are tighter down there. Also the box model's corners below the ledge.
WALL_CLEARANCE = 1.0  # Gap kept between every part and every box wall, per side. Under one BB, never a press fit.

# Ledge: the step all round the inside wall where the wide upper part meets the narrower lower part.
# It is sloped, and it is what the top plate (#18) sits on. Below it, the lower part (the BOX_FLOOR_
# and BOX_REF_ numbers above); above it, the upper part, up to the rim.
BOX_LEDGE_Z0 = 129.0  # TODO: confirm with the gauge. Bottom of the ledge, where the lower wall ends (24 mm under the rim).
BOX_LEDGE_Z1 = 136.0  # TODO: confirm with the gauge. Top of the ledge: the height a part rests at (17 mm under the rim).
BOX_RIM_L = 255.0  # Interior length of the upper part at the rim (Z = BOX_HEIGHT). Measured 254 mid-wall; raised to
# 255 because the ledge gauge showed room for a 252 seat, which needs ~254 at the ledge with WALL_CLEARANCE.
BOX_RIM_W = 121.0  # TODO: confirm with the gauge. Interior width of the upper part at the rim, mid-wall.
# Those two were measured at the MIDDLE of the walls. The walls bow out there, so the upper part is
# tighter at the corners: they give the step's width, not the size of a part that sits on it.
# Upper part's draft: taken equal to the lower part's (BOX_TAPER_L / _W), as only the rim was measured
# up there. Then the step (mid-wall) is the same width at any height:
BOX_STEP_L = (BOX_RIM_L - BOX_FLOOR_L - BOX_TAPER_L * BOX_HEIGHT) / 2  # Step width at each end, mid-wall (about 7.7).
BOX_STEP_W = (BOX_RIM_W - BOX_FLOOR_W - BOX_TAPER_W * BOX_HEIGHT) / 2  # Step width at each side, mid-wall (about 9.9).

# Seat: the outline of anything that rests on the ledge (ledge_gauge now, the top plate #18 later).
# Sized for the corners, not the mid-wall numbers above. Reference: the original BULLOADER top plate
# rests on this ledge in two pieces, 117 x 172 and 117 x 77 (249 x 117 in all), and already forces
# at the corners (the two pieces overlap a little once fitted). So the seat is a bit under it both
# ways. Inside: it reaches SEAT_INSET past the step's inner edge (the lower wall), so it covers the
# whole step whatever its exact width.
SEAT_L = 252.0  # Outer length of the seat. The first ledge gauge (246) had 6 mm to spare; TODO: confirm with the reprint.
SEAT_W = 117.0  # Outer width of the seat. The first ledge gauge (115) had 2 mm to spare; TODO: confirm with the reprint.
SEAT_CORNER_R = CORNER_R  # Vertical corner radius of the seat. Raise it if the box corners are tighter up there.
SEAT_INSET = 3.0  # How far the seat reaches in past the lower wall, per side.
SEAT_MIN_REST = 3.0  # Least width of step a seated part must rest on, per side.

# --- Box fit gauges (print them before any large part in the box) -------------
# Thin closed frames, one at the floor, one on the ledge. They print in minutes and tell us
# whether the BOX_ numbers above are right before a 200 mm part is printed.
GAUGE_HEIGHT = 3.0  # Frame height (thickness on the bed).
GAUGE_WALL = 2.0  # Width of the floor gauge frame (the ledge gauge is as wide as the seat).
GAUGE_TEXT_SIZE = 5.0  # Height of the engraved label.
GAUGE_TEXT_DEPTH = 0.6  # Engraving depth (3 layers at 0.2).
GAUGE_TAB_MARGIN = 2.0  # Material round the label on its tab.
CORNER_GAUGE_RADII = (2, 4, 6, 8)  # R10 is known to be too big.  # One corner tab per radius, to find the box's bottom corner radius.
CORNER_GAUGE_SIZE = 30.0  # Side of each square corner tab.

# --- Smoke-test ring (M0 only, proves the build pipeline) --------------------
RING_WALL = 2.0  # Radial wall thickness of the test ring.
RING_HEIGHT = 5.0  # Height of the test ring along the barrel axis.
