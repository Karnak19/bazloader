"""Every dimension of the BULLOADER+ parts, in millimetres.

Change values here, never in build.py. Anything marked `TODO: measure` is a
placeholder until the real part is in hand.
"""

# --- Printing ---------------------------------------------------------------
FIT_TOLERANCE = 0.2  # Clearance added to every hole that fits around a real part.
MIN_WALL = 1.6  # Thinnest wall we print (4 perimeters at 0.4 mm nozzle).

# --- Inner barrel (IR collar sits around it) --------------------------------
BARREL_OD = 9.0  # TODO: measure. Outer diameter of the 120 mm inner barrel, expected 8.5-9.5.

# --- IR barrier ---------------------------------------------------------------
IR_LED_DIAMETER = 3.0  # TODO: measure. Body of the 3 mm IR LED.
PHOTOTRANSISTOR_DIAMETER = 3.0  # TODO: measure. Body of the 3 mm phototransistor.

# --- Hardware ---------------------------------------------------------------
M3_CLEARANCE = 3.4  # Through-hole for an M3 screw.

# --- Smoke-test ring (M0 only, proves the build pipeline) --------------------
RING_WALL = 2.0  # Radial wall thickness of the test ring.
RING_HEIGHT = 5.0  # Height of the test ring along the barrel axis.
