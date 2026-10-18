"""Sanity checks on the IR collar and the fit coupon, over the plausible barrel range.

Run: uv run python check.py
Probes points just inside and just outside each feature, so a wrong bore, a
socket off its axis or two sockets that are not coaxial fail loudly.
"""

import math

from build123d import GeomType, Vector

import build
import params as p

BARREL_ODS = (8.5, 9.0, 9.5)  # The plausible range from the brief.
EPS = 0.05  # How far on each side of a wall we probe.


def cylinders(part) -> list:
    """Cylindrical faces of a part (the radius is None on some faces OCC reports)."""
    return [f for f in part.faces() if f.geom_type == GeomType.CYLINDER and f.radius is not None]


def solid_at(part, x: float, y: float, z: float) -> bool:
    return part.is_inside(Vector(x, y, z))


def check_collar(od: float) -> None:
    p.BARREL_OD = od
    part = build.ir_collar()
    k = build.collar_layout()
    assert part.is_valid, "collar is not a valid solid"
    assert len(part.solids()) == 1, f"collar has {len(part.solids())} solids"

    # Bore: hollow just inside its radius, solid just outside it, all round the
    # tube, at a height away from the beam (the aperture) and away from the slot.
    z = k["beam_z"] / 2
    slot_half_angle = math.degrees(math.asin((p.CLAMP_SLOT / 2 + EPS) / k["bore_r"]))
    for deg in range(0, 360, 15):
        if abs(deg - 90) <= slot_half_angle + 1:
            continue
        c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        r_in, r_out = k["bore_r"] - EPS, k["bore_r"] + EPS
        assert not solid_at(part, r_in * c, r_in * s, z), f"bore too small at {deg} deg"
        assert solid_at(part, r_out * c, r_out * s, z), f"bore too large at {deg} deg"
    assert not solid_at(part, 0, k["bore_r"] + EPS, z), "clamp slot missing"

    # Sockets: each one is a cylinder whose axis is the X axis at beam height,
    # i.e. both on one line through the tube centre.
    sockets = [
        f
        for f in cylinders(part)
        if min(abs(f.radius - k["led_r"]), abs(f.radius - k["photo_r"])) < 1e-6
        and abs(abs(f.axis_of_rotation.direction.X) - 1) < 1e-6
    ]
    sockets = [f for f in sockets if abs(f.axis_of_rotation.position.Y) < 1e-6]
    sides = sorted({round(f.center().X, 3) for f in sockets})
    assert len(sockets) == 2, f"expected 2 socket faces, found {len(sockets)}"
    for f in sockets:
        axis = f.axis_of_rotation
        assert abs(axis.position.Z - k["beam_z"]) < 1e-6, "socket axis not at beam height"
        assert abs(axis.position.Y) < 1e-6, "socket axis off the tube centre"
    assert abs(sides[0] + sides[1]) < 1e-6, f"sockets not symmetric: {sides}"

    # Probe both sockets the same way: hollow inside, solid outside, all round.
    z0 = k["beam_z"]
    for side, r in ((-1, k["led_r"]), (1, k["photo_r"])):
        x = side * (k["shoulder_x"] + p.SOCKET_DEPTH / 2)
        for deg in range(0, 360, 30):
            c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
            assert not solid_at(part, x, (r - EPS) * c, z0 + (r - EPS) * s), "socket too small"
            assert solid_at(part, x, (r + EPS) * c, z0 + (r + EPS) * s), "socket too large"
        # Stop shoulder: solid just in front of it (outside the aperture), hollow just behind.
        ring = (r + p.APERTURE_D / 2) / 2
        assert solid_at(part, side * (k["shoulder_x"] - EPS), 0, z0 + ring), "no shoulder"
        assert not solid_at(part, side * (k["shoulder_x"] + EPS), 0, z0 + ring), "shoulder misplaced"
        # Aperture: open on the axis through the wall, closed just above it.
        x_ap = side * (k["bore_r"] + p.APERTURE_LEN / 2)
        assert not solid_at(part, x_ap, 0, z0), "aperture blocked"
        assert solid_at(part, x_ap, 0, z0 + p.APERTURE_D / 2 + EPS), "aperture too tall"
        # Socket closed above and below along the tube: the light shield.
        assert solid_at(part, x, 0, z0 + r + p.SOCKET_WALL / 2), "no wall above socket"
    # The beam line itself is clear from one shoulder to the other.
    for i in range(41):
        x = -k["shoulder_x"] + 2 * k["shoulder_x"] * i / 40
        assert not solid_at(part, x, 0, z0), f"beam blocked at x={x:.2f}"

    bb = part.bounding_box()
    assert abs(bb.min.Z) < 1e-6 and abs(bb.max.Z - p.COLLAR_LENGTH) < 1e-6, "length wrong"
    print(
        f"BARREL_OD {od}: collar OK  bore d={2 * k['bore_r']:.2f}  "
        f"sockets at x={sides[0]:+.2f}/{sides[1]:+.2f} on y=0 z={z0:.1f}  "
        f"size {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}  vol {part.volume:.0f} mm3"
    )


def check_coupon(od: float) -> None:
    p.BARREL_OD = od
    part = build.fit_coupon()
    assert part.is_valid and len(part.solids()) == 1, "coupon is not one valid solid"
    radii = sorted(
        round(f.radius * 2, 3)
        for f in cylinders(part)
        if abs(f.axis_of_rotation.direction.Z) > 0.99 and abs(f.radius - p.EDGE_FILLET) > 1e-6
    )
    want = sorted(round(od + o, 3) for o in p.COUPON_BORE_OFFSETS)
    assert radii == want, f"coupon bores {radii} != {want}"
    sockets = sorted(
        round(f.radius * 2, 3)
        for f in cylinders(part)
        if abs(f.axis_of_rotation.direction.Y) > 0.99
    )
    want_s = sorted(round(p.IR_LED_DIAMETER + o, 3) for o in p.COUPON_SOCKET_OFFSETS)
    assert sockets == want_s, f"coupon sockets {sockets} != {want_s}"
    print(f"BARREL_OD {od}: coupon OK  bores {radii}  sockets {sockets}")


if __name__ == "__main__":
    original = p.BARREL_OD
    for od in BARREL_ODS:
        check_collar(od)
        check_coupon(od)
    p.BARREL_OD = original
    print("all checks passed")
