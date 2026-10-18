"""Every dimension of the BULLOADER+ parts, in millimetres.

Change values here, never in build.py. Anything marked `TODO: measure` is a
placeholder until the real part is in hand.
"""

# --- Printing ---------------------------------------------------------------
FIT_TOLERANCE = 0.2  # TODO: calibrate with fit_coupon. Clearance added to every hole that fits around a real part.
MIN_WALL = 1.6  # Thinnest wall we print (4 perimeters at 0.4 mm nozzle).
EDGE_FILLET = 0.8  # Rounding of the outer edges along the tube, so nothing is sharp in the hand.

# --- Inner barrel (IR collar sits around it) --------------------------------
BARREL_OD = 8.55  # Outer diameter of the 120 mm inner barrel: a standard AEG inner barrel. Confirm with calipers (#16).
BARREL_ID = 6.05  # Bore of that barrel, the usual 6.05 mm AEG bore. The beam window must fit inside it.

# --- IR barrier ---------------------------------------------------------------
IR_LED_DIAMETER = 3.0  # TODO: measure. Body of the 3 mm IR LED.
PHOTOTRANSISTOR_DIAMETER = 3.0  # TODO: measure. Body of the 3 mm phototransistor.
IR_BODY_LENGTH = 4.0  # TODO: measure. Straight body of each component, from the start of the dome to the flange.

# --- IR collar ----------------------------------------------------------------
# Printed standing on its end face, tube axis vertical: the bore comes out round
# and both sockets are built in the same layers, so they stay coaxial.
SOCKET_TOLERANCE = 0.2  # TODO: calibrate with fit_coupon. Clearance on the 3 mm sockets.
SOCKET_DEPTH = 3.5  # Guide length up to the stop shoulder. Below IR_BODY_LENGTH, so the flange stays outside.
SOCKET_WALL = 1.6  # Wall around each socket.
APERTURE_D = 1.5  # Height of the window between socket and bore, along the tube. Narrower = sharper beam (#12).
APERTURE_W = 1.5  # Width of that window across the tube. Equal to APERTURE_D: round hole; wider: horizontal slit.
APERTURE_LEN = 1.2  # Length of the window, i.e. the thinnest wall between the stop shoulder and the bore.
BEAM_OFFSET = 2.0  # Beam moved sideways off the tube axis (#12). BBs travel touching, and where two touch the
# axis is still solid, so a beam through the axis is never let through. Off-axis it sees the gap between two
# balls: about 83 % of the light at 2.0 mm, against 4 % on the axis. Keep it + APERTURE_W / 2 inside BARREL_ID.
COLLAR_WALL = 2.0  # Radial wall around the bore.
COLLAR_LENGTH = 16.0  # Length along the tube. The beam sits in the middle, half of it shields each side.
WIRE_CHANNEL_W = 3.4  # Groove for one pair of leads (2.54 mm pitch + wire), from under each socket to the bottom end.
WIRE_CHANNEL_DEPTH = 1.5  # Depth of that groove.
CLAMP_SLOT = 1.5  # Gap of the C-clamp, closed by the M3 screw. Far more than the bore clearance it has to take up.

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
COUPON_THICKNESS = 3.0  # Plate thickness, i.e. how long the barrel test bores are.
COUPON_BORE_OFFSETS = (-0.2, 0.0, 0.2, 0.4)  # Bore = BARREL_OD + offset. The best slide gives FIT_TOLERANCE.
COUPON_SOCKET_OFFSETS = (0.0, 0.1, 0.2)  # Socket = IR_LED_DIAMETER + offset. The best hold gives SOCKET_TOLERANCE.
COUPON_SHAFT_OFFSETS = (0.1, 0.2, 0.3)  # D-flat bore = SHAFT_D/SHAFT_FLAT + offset. The best fit gives SHAFT_TOLERANCE.
COUPON_PRESS_OFFSETS = (-0.2, -0.1, 0.0, 0.1)  # Round bore = SHAFT_D + offset. Tightest one that goes on: KNOB_PRESS_FIT.
COUPON_KNOB_THICKNESS = 6.0  # The knob test bores go through a thicker strip, so the grip is felt over some length.
COUPON_GAP = 3.0  # Material between two test holes.
COUPON_TEXT_SIZE = 3.0  # Height of the engraved labels.
COUPON_TEXT_DEPTH = 0.4  # Engraving depth (2 layers at 0.2).

# --- Smoke-test ring (M0 only, proves the build pipeline) --------------------
RING_WALL = 2.0  # Radial wall thickness of the test ring.
RING_HEIGHT = 5.0  # Height of the test ring along the barrel axis.
