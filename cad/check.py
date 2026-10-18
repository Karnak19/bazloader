"""Sanity checks on the IR collar, the encoder knob and the fit coupon.

Run: uv run python check.py
Probes points just inside and just outside each feature, so a wrong bore, a missing
shoulder, a socket off its axis, two sockets that are not coaxial or a knob bore off
its axis fail loudly.
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


def guide_x(k: dict, y: float) -> float:
    """Where the BB guide surface sits along a beam parallel to X at height y."""
    return math.sqrt(max(0.0, k["guide_r"] ** 2 - y**2))


def wall_thickness(part, x: float, y0: float, z0: float, r: float, c: float, s: float) -> float:
    """Solid measured outward from a socket surface along (c, s) in the YZ plane, capped at 4 mm."""
    t = 0.0
    while t < 4.0 and solid_at(part, x, y0 + (r + t + 0.02) * c, z0 + (r + t + 0.02) * s):
        t += 0.02
    return t


def check_collar(od: float) -> None:
    p.BARREL_OD = od
    part = build.ir_collar()
    k = build.collar_layout()
    assert part.is_valid, "collar is not a valid solid"
    assert len(part.solids()) == 1, f"collar has {len(part.solids())} solids"
    z_lo, z_hi, L = k["ring_z0"], k["ring_z1"], k["length"]
    assert abs(L - (2 * p.GRIP_LENGTH + p.BARREL_GAP)) < 1e-9, "length is not two grips plus the gap"
    assert abs(z_hi - z_lo - p.BARREL_GAP) < 1e-9, "ring length is not the barrel gap"

    # Grip bores: hollow just inside their radius, solid just outside, all round, at mid-grip
    # (away from the ring) except across the clamp slot.
    slot_half_angle = math.degrees(math.asin((p.CLAMP_SLOT / 2 + EPS) / k["bore_r"]))
    for z in (z_lo / 2, (z_hi + L) / 2, 0.5, L - 0.5, z_lo - 0.5, z_hi + 0.5):
        for deg in range(0, 360, 15):
            if abs(deg - 90) <= slot_half_angle + 1:
                continue
            c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
            r_in, r_out = k["bore_r"] - EPS, k["bore_r"] + EPS
            assert not solid_at(part, r_in * c, r_in * s, z), f"grip bore too small at {deg} deg, z={z:.1f}"
            assert solid_at(part, r_out * c, r_out * s, z), f"grip bore too large at {deg} deg, z={z:.1f}"
        assert not solid_at(part, 0, k["bore_r"] + EPS, z), f"clamp slot missing at z={z:.1f}"
    # Grip long enough to hold a half straight: over one barrel diameter.
    assert p.GRIP_LENGTH >= od, f"GRIP_LENGTH {p.GRIP_LENGTH} under the barrel OD {od}"

    # BB guide: over the barrel bore (a BB never meets a step going in), under the barrel OD
    # (so there is a shoulder), probed all round on its flat part, above and below the window.
    assert p.BB_GUIDE_D > p.BARREL_ID, "BB guide narrower than the barrel bore"
    assert p.BARREL_ID < od - 2 * 0.5, "barrel wall implausibly thin"
    flat = p.BARREL_GAP / 2 - p.RING_CHAMFER  # Flat part of the guide, each side of the beam.
    for z in (k["beam_z"] - flat + EPS, k["beam_z"] + flat - EPS):
        for deg in range(0, 360, 15):
            c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
            r_in, r_out = k["guide_r"] - EPS, k["guide_r"] + EPS
            assert not solid_at(part, r_in * c, r_in * s, z), f"BB guide too small at {deg} deg"
            assert solid_at(part, r_out * c, r_out * s, z), f"BB guide too large at {deg} deg"
    # The ring is closed: the clamp slots stop at it, so the screws never squeeze the guide.
    for y in (k["guide_r"] + EPS, k["bore_r"] + EPS, k["ear_y"] - EPS):
        assert solid_at(part, 0, y, k["beam_z"]), f"ring cut by the clamp slot at y={y:.2f}"

    # Shoulders, both sides: all round, solid just inside the ring, hollow just outside it,
    # so each barrel half stops on a flat face, and the gap is set by the print.
    shoulder = k["bore_r"] - k["guide_r"] - p.RING_CHAMFER  # Flat width each half butts on.
    assert shoulder > 0.3, f"shoulder only {shoulder:.2f} wide"
    r_sh = (k["guide_r"] + p.RING_CHAMFER + k["bore_r"]) / 2
    for deg in range(0, 360, 15):
        c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        x, y = r_sh * c, r_sh * s
        assert solid_at(part, x, y, z_lo + EPS) and not solid_at(part, x, y, z_lo - EPS), f"no bottom shoulder at {deg}"
        assert solid_at(part, x, y, z_hi - EPS) and not solid_at(part, x, y, z_hi + EPS), f"no top shoulder at {deg}"
        # Chamfer: the guide edge is cut back at both faces.
        rc = k["guide_r"] + p.RING_CHAMFER / 2
        assert not solid_at(part, rc * c, rc * s, z_lo + EPS), f"no bottom chamfer at {deg}"
        assert not solid_at(part, rc * c, rc * s, z_hi - EPS), f"no top chamfer at {deg}"

    # Sockets: each one is a cylinder along X on the beam line (y = beam_y, z = beam_z),
    # i.e. both on one chord of the guide, BEAM_OFFSET off the axis.
    y0, z0 = k["beam_y"], k["beam_z"]
    assert abs(abs(y0) - p.BEAM_OFFSET) < 1e-9, "beam not BEAM_OFFSET off the axis"
    sockets = [
        f
        for f in cylinders(part)
        if min(abs(f.radius - k["led_r"]), abs(f.radius - k["photo_r"])) < 1e-6
        and abs(abs(f.axis_of_rotation.direction.X) - 1) < 1e-6
    ]
    sockets = [f for f in sockets if abs(f.axis_of_rotation.position.Y - y0) < 1e-6]
    sides = sorted({round(f.center().X, 3) for f in sockets})
    assert len(sockets) == 2, f"expected 2 socket faces, found {len(sockets)}"
    for f in sockets:
        axis = f.axis_of_rotation
        assert abs(axis.position.Z - z0) < 1e-6, "socket axis not at beam height"
        assert abs(axis.position.Y - y0) < 1e-6, "socket axis off the beam line"
    assert abs(sides[0] + sides[1]) < 1e-6, f"sockets not symmetric: {sides}"

    # The window fits inside the BB guide, so the whole beam crosses the BB path.
    assert p.BEAM_OFFSET + p.APERTURE_W / 2 < k["guide_r"], "window pokes past the BB guide"
    # Ring wall above and below the window, measured at the guide edge (inside the chamfer).
    window_wall = p.BARREL_GAP / 2 - p.APERTURE_D / 2 - p.RING_CHAMFER
    assert window_wall >= p.MIN_WALL, f"ring wall around the window only {window_wall:.2f}"
    x_w = guide_x(k, y0) + 0.3  # Just into the ring, on the beam line.
    for side in (-1, 1):
        for dz in (p.APERTURE_D / 2 + EPS, p.BARREL_GAP / 2 - p.RING_CHAMFER - EPS):
            assert solid_at(part, side * x_w, y0, z0 + dz), f"ring wall missing above the window, dz={dz:.2f}"
            assert solid_at(part, side * x_w, y0, z0 - dz), f"ring wall missing below the window, dz={dz:.2f}"
    # Sockets inside the ring's height with SOCKET_WALL to spare, so none breaks into a grip bore.
    socket_to_grip = p.BARREL_GAP / 2 - k["socket_r"]
    assert socket_to_grip >= p.SOCKET_WALL - 1e-9, f"socket only {socket_to_grip:.2f} from a grip bore"
    # Clamp slots, screws and nut traps stay on +Y, clear of the beam line and its sockets.
    assert y0 + k["socket_r"] < -EPS, "sockets reach the clamp slot side"
    screw_low = k["screw_y"] - max(p.M3_CLEARANCE / 2, k["nut_r"])
    assert screw_low - (y0 + k["bar_hw"]) >= p.MIN_WALL, "screw or nut trap hits the socket bar"
    assert screw_low - k["bore_r"] >= p.MIN_WALL - 1e-9, "nut trap too close to the grip bore"
    for zs, z_in in zip(k["screw_z"], (z_lo, z_hi)):
        # Nut trap inside the collar with MIN_WALL to the end, screw hole entirely over its slot.
        assert min(zs, L - zs) - k["nut_r"] >= p.MIN_WALL - 1e-9, "nut trap too close to the collar end"
        assert abs(z_in - zs) - p.M3_CLEARANCE / 2 > 0, "screw reaches the ring, past its slot"
        assert not solid_at(part, 0, k["screw_y"], zs), "screw hole missing"
        assert not solid_at(part, k["ear_hx"] - EPS, k["screw_y"], zs), "nut trap missing"
    # Wire grooves: on the back faces, -Y side, clear of the grip bore by MIN_WALL.
    gx, gy = k["back_x"] - p.WIRE_CHANNEL_DEPTH, max(0.0, abs(y0) - p.WIRE_CHANNEL_W / 2)
    groove_wall = math.hypot(gx, gy) - k["bore_r"]
    assert groove_wall >= p.MIN_WALL - 1e-9, f"wire groove only {groove_wall:.2f} from the grip bore"
    for side in (-1, 1):
        x = side * (k["back_x"] - p.WIRE_CHANNEL_DEPTH / 2)
        assert not solid_at(part, x, y0, 0.5), "wire groove missing at the bottom end"
        assert not solid_at(part, x, y0, k["channel_top"] - EPS), "wire groove too short"
        assert solid_at(part, x, y0, k["channel_top"] + EPS), "wire groove runs into the socket"

    # Probe both sockets the same way: hollow inside, solid outside, all round.
    walls, shoulder_walls = [], []
    for side, r in ((-1, k["led_r"]), (1, k["photo_r"])):
        for x in (side * (k["shoulder_x"] + 0.2), side * (k["shoulder_x"] + p.SOCKET_DEPTH / 2)):
            for deg in range(0, 360, 30):
                c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
                assert not solid_at(part, x, y0 + (r - EPS) * c, z0 + (r - EPS) * s), "socket too small"
                assert solid_at(part, x, y0 + (r + EPS) * c, z0 + (r + EPS) * s), "socket too large"
                # Wall all round the socket: still solid MIN_WALL out from its surface.
                w = r + p.MIN_WALL - EPS
                assert solid_at(part, x, y0 + w * c, z0 + w * s), f"socket wall under MIN_WALL at {deg} deg"
                walls.append(wall_thickness(part, x, y0, z0, r, c, s))
        # Stop shoulder: solid just in front of it (outside the aperture), hollow just behind.
        ring = (r + p.APERTURE_D / 2) / 2
        assert solid_at(part, side * (k["shoulder_x"] - EPS), y0, z0 + ring), "no socket shoulder"
        assert not solid_at(part, side * (k["shoulder_x"] + EPS), y0, z0 + ring), "socket shoulder misplaced"
        # Aperture: open on the beam line through the wall, closed just above it and just beside it.
        x_ap = side * (guide_x(k, y0) + k["shoulder_x"]) / 2
        assert not solid_at(part, x_ap, y0, z0), "aperture blocked"
        assert solid_at(part, x_ap, y0, z0 + p.APERTURE_D / 2 + EPS), "aperture too tall"
        assert solid_at(part, x_ap, y0 + p.APERTURE_W / 2 + EPS, z0), "aperture too wide"
        # Window wall at least APERTURE_LEN long on its worst edge (the one nearest the axis),
        # and on the whole socket face.
        for y in (y0 + p.APERTURE_W / 2, y0 - p.APERTURE_W / 2, y0 + r, y0 - r):
            wall = k["shoulder_x"] - guide_x(k, y)
            assert wall >= p.APERTURE_LEN - 1e-9, f"wall in front of the shoulder {wall:.2f} at y={y:.2f}"
            shoulder_walls.append(wall)
        # Socket closed above and below along the tube: the light shield.
        x = side * (k["shoulder_x"] + p.SOCKET_DEPTH / 2)
        assert solid_at(part, x, y0, z0 + r + p.SOCKET_WALL / 2), "no wall above socket"
    # The beam line itself is clear from one shoulder to the other.
    for i in range(41):
        x = -k["shoulder_x"] + 2 * k["shoulder_x"] * i / 40
        assert not solid_at(part, x, y0, z0), f"beam blocked at x={x:.2f}"

    bb = part.bounding_box()
    assert abs(bb.min.Z) < 1e-6 and abs(bb.max.Z - L) < 1e-6, "length wrong"
    print(
        f"BARREL_OD {od}: collar OK  grip d={2 * k['bore_r']:.2f} x {p.GRIP_LENGTH:.1f}  "
        f"guide d={2 * k['guide_r']:.2f} x {p.BARREL_GAP:.1f}  shoulder {shoulder:.2f}  "
        f"sockets at x={sides[0]:+.2f}/{sides[1]:+.2f} on y={y0:+.2f} z={z0:.2f}  "
        f"min socket wall {min(walls):.2f}  min window wall {min(shoulder_walls):.2f}  "
        f"ring wall by window {window_wall:.2f}  groove wall {groove_wall:.2f}  "
        f"size {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}  vol {part.volume:.0f} mm3"
    )


def check_knob(kind: str) -> None:
    p.KNOB_BORE = kind
    part = build.encoder_knob()
    k = build.knob_layout()
    assert part.is_valid, "knob is not a valid solid"
    assert len(part.solids()) == 1, f"knob has {len(part.solids())} solids"
    H, R = p.KNOB_HEIGHT, k["outer_r"]
    bb = part.bounding_box()
    assert abs(bb.min.Z) < 1e-6 and abs(bb.max.Z - H) < 1e-6, "knob height wrong"
    # The ridge tops are flattened by the fillets, so the widest one reaches a little under R.
    assert 2 * R - 0.1 < max(bb.size.X, bb.size.Y) <= 2 * R + 1e-3, f"knob OD wrong: {bb.size}"

    # Bore: one cylinder of the right radius whose axis is the Z axis.
    bores = [f for f in cylinders(part) if abs(f.radius - k["bore_r"]) < 1e-6]
    assert bores, "no bore cylinder"
    for f in bores:
        axis = f.axis_of_rotation
        assert abs(abs(axis.direction.Z) - 1) < 1e-6, "bore not vertical"
        assert abs(axis.position.X) < 1e-6 and abs(axis.position.Y) < 1e-6, "bore off the axis"

    # Probe the bore all round at mid-depth: hollow inside, solid outside, flat on +X.
    r, z = k["bore_r"], k["bore_end"] + k["bore_depth"] / 2
    flat_x = k["flat_x"]
    for deg in range(0, 360, 15):
        c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        if flat_x is not None and (r + EPS) * c > flat_x - EPS:
            continue  # Cut off by the flat, probed below.
        assert not solid_at(part, (r - EPS) * c, (r - EPS) * s, z), f"bore too small at {deg} deg"
        assert solid_at(part, (r + EPS) * c, (r + EPS) * s, z), f"bore too large at {deg} deg"
    if flat_x is not None:
        assert not solid_at(part, flat_x - EPS, 0, z), "flat too deep"
        assert solid_at(part, flat_x + EPS, 0, z), "flat missing"
        width = flat_x + r
        assert abs(width - (p.SHAFT_FLAT + p.SHAFT_TOLERANCE)) < 1e-6, f"flat at {width:.2f}"

    # Depth: hollow just above the bore end, solid just below (the cap).
    assert not solid_at(part, 0, 0, k["bore_end"] + EPS), "bore too short"
    assert solid_at(part, 0, 0, k["bore_end"] - EPS), "bore too deep"
    assert k["bore_end"] >= p.MIN_WALL, "cap thinner than MIN_WALL"
    assert abs(k["bore_depth"] - (p.SHAFT_FREE_LENGTH - p.KNOB_SHAFT_GAP)) < 1e-6, "bore depth wrong"

    # Recess: hollow just inside its radius, solid just outside, open at Z=H.
    zr = H - k["recess_depth"] / 2
    for deg in range(0, 360, 30):
        c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        rr = k["recess_r"]
        assert not solid_at(part, (rr - EPS) * c, (rr - EPS) * s, zr), "recess too small"
        assert solid_at(part, (rr + EPS) * c, (rr + EPS) * s, zr), "recess too large"
    assert k["recess_r"] > p.ENCODER_NUT_AF / math.sqrt(3), "recess does not clear the nut corners"
    assert not solid_at(part, k["recess_r"] - EPS, 0, k["recess_top"] + EPS), "recess too shallow"
    assert solid_at(part, k["recess_r"] - EPS, 0, k["recess_top"] - EPS), "recess too deep"

    # Ridges: a groove centre is hollow halfway down the groove, the land between two is solid.
    zm = H / 2
    half = math.pi / p.KNOB_RIDGES
    assert not solid_at(part, R - p.KNOB_RIDGE_DEPTH / 2, 0, zm), "groove missing"
    assert solid_at(part, (R - EPS) * math.cos(half), (R - EPS) * math.sin(half), zm), "ridge missing"
    # Top chamfer: the rim corner on the bed (Z=0) is cut away.
    edge = p.KNOB_TOP_CHAMFER / 2
    assert not solid_at(part, (R - edge) * math.cos(half), (R - edge) * math.sin(half), edge / 2), "no chamfer"
    print(
        f"knob {kind}: OK  bore d={2 * r:.2f}"
        + (f" flat {flat_x + r:.2f}" if flat_x is not None else "")
        + f" depth {k['bore_depth']:.1f}  recess d={2 * k['recess_r']:.1f} x {k['recess_depth']:.1f}"
        f"  cap {k['bore_end']:.1f}  vol {part.volume:.0f} mm3"
    )


def check_coupon(od: float) -> None:
    p.BARREL_OD = od
    part = build.fit_coupon()
    k = build.coupon_layout()
    assert part.is_valid and len(part.solids()) == 1, "coupon is not one valid solid"
    radii = sorted(
        round(f.radius * 2, 3)
        for f in cylinders(part)
        if abs(f.axis_of_rotation.direction.Z) > 0.99
        and abs(f.radius - p.EDGE_FILLET) > 1e-6
        and abs(f.center().Y - k["bore_y"]) < 1e-3
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

    # Knob bores: one row of D-flats, one of round ones, each through the thicker strip.
    def row(y: float) -> list:
        return sorted(
            round(f.radius * 2, 3)
            for f in cylinders(part)
            if abs(f.axis_of_rotation.direction.Z) > 0.99 and abs(f.axis_of_rotation.position.Y - y) < 1e-3
        )

    guides = row(k["guide_y"])
    want_g = sorted(round(p.BB_GUIDE_D + o, 3) for o in p.COUPON_GUIDE_OFFSETS)
    assert guides == want_g, f"coupon BB guide bores {guides} != {want_g}"
    dflat, press = row(k["dflat_y"]), row(k["press_y"])
    want_d = sorted(round(p.SHAFT_D + o, 3) for o in p.COUPON_SHAFT_OFFSETS)
    want_p = sorted(round(p.SHAFT_D + o, 3) for o in p.COUPON_PRESS_OFFSETS)
    assert dflat == want_d, f"coupon D-flat bores {dflat} != {want_d}"
    assert press == want_p, f"coupon round bores {press} != {want_p}"
    z = p.COUPON_KNOB_THICKNESS / 2
    for i, o in enumerate(p.COUPON_SHAFT_OFFSETS):
        x = -k["width"] / 2 + k["width"] / len(p.COUPON_SHAFT_OFFSETS) * (i + 0.5)
        r = (p.SHAFT_D + o) / 2
        flat_x = x - r + p.SHAFT_FLAT + o
        assert not solid_at(part, flat_x - EPS, k["dflat_y"], z), f"D-flat {o} flat too deep"
        assert solid_at(part, flat_x + EPS, k["dflat_y"], z), f"D-flat {o} flat missing"
        assert not solid_at(part, x - r + EPS, k["dflat_y"], z), f"D-flat {o} too small"
        assert solid_at(part, x - r - EPS, k["dflat_y"], z), f"D-flat {o} too large"
    bb = part.bounding_box()
    assert abs(bb.max.Z - max(p.COUPON_KNOB_THICKNESS, p.IR_LED_DIAMETER + max(p.COUPON_SOCKET_OFFSETS) + 2 * p.MIN_WALL)) < 1e-6
    print(
        f"BARREL_OD {od}: coupon OK  bores {radii}  guides {guides}  sockets {sockets}  "
        f"D-flats {dflat}  round {press}"
    )


if __name__ == "__main__":
    original = p.BARREL_OD
    for od in BARREL_ODS:
        check_collar(od)
        check_coupon(od)
    p.BARREL_OD = original
    bore = p.KNOB_BORE
    for kind in ("dflat", "round"):
        check_knob(kind)
    p.KNOB_BORE = bore
    print("all checks passed")
