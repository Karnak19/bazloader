"""Every dimension of the BULLOADER+ parts, in millimetres.

Change values here, never in build.py. Anything marked `TODO: measure` is a
placeholder until the real part is in hand.
"""

# --- Printing ---------------------------------------------------------------
FIT_TOLERANCE = 0.2  # TODO: calibrate with fit_coupon. Clearance added to every hole that fits around a real part.
MIN_WALL = 1.6  # Thinnest wall we print (4 perimeters at 0.4 mm nozzle).
EDGE_FILLET = 0.8  # Rounding of the outer edges along the tube, so nothing is sharp in the hand.

# --- Inner barrel (IR collar sits around it) --------------------------------
BARREL_OD = 9.0  # TODO: measure. Outer diameter of the 120 mm inner barrel, expected 8.5-9.5.

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
APERTURE_LEN = 1.2  # Length of the window, i.e. the wall between the stop shoulder and the bore.
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

# --- Fit coupon (print it first, then update the tolerances above) -----------
COUPON_THICKNESS = 3.0  # Plate thickness, i.e. how long the barrel test bores are.
COUPON_BORE_OFFSETS = (-0.2, 0.0, 0.2, 0.4)  # Bore = BARREL_OD + offset. The best slide gives FIT_TOLERANCE.
COUPON_SOCKET_OFFSETS = (0.0, 0.1, 0.2)  # Socket = IR_LED_DIAMETER + offset. The best hold gives SOCKET_TOLERANCE.
COUPON_GAP = 3.0  # Material between two test holes.
COUPON_TEXT_SIZE = 3.0  # Height of the engraved labels.
COUPON_TEXT_DEPTH = 0.4  # Engraving depth (2 layers at 0.2).

# --- Smoke-test ring (M0 only, proves the build pipeline) --------------------
RING_WALL = 2.0  # Radial wall thickness of the test ring.
RING_HEIGHT = 5.0  # Height of the test ring along the barrel axis.
