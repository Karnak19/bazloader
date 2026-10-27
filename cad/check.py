"""Sanity checks on the IR collar, the encoder knob, the fit coupon, the box fit gauges and the feed rig.

Run: uv run python check.py
Probes points just inside and just outside each feature, so a wrong bore, a missing
shoulder, a socket off its axis, two sockets that are not coaxial or a knob bore off
its axis fail loudly.
"""

import math

from build123d import Align, Box, GeomType, Pos, Vector

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


def wall_gap(x: float, y: float, z: float) -> float:
    """Distance from a point inside the box (box frame) to the nearest wall at height z.

    The box is modelled with CORNER_R corners, the worst case: its real corners are tighter,
    which only leaves more room for an R10 part.
    """
    box_l, box_w = build.box_interior(z)
    r = p.CORNER_R
    qx, qy = abs(x) - (box_l / 2 - r), abs(y) - (box_w / 2 - r)
    outside = math.hypot(max(qx, 0.0), max(qy, 0.0)) + min(max(qx, qy), 0.0) - r  # Signed distance, < 0 inside.
    return -outside


def check_box() -> None:
    """The hand measurements agree with each other: the ledge opening, measured directly, matches
    the box at the ledge (from the draft) minus the ledge on both sides, within the +/- 1 mm of each."""
    assert 0 < p.BOX_LEDGE_Z0 < p.BOX_LEDGE_Z1 < p.BOX_HEIGHT, "ledge heights out of order"
    box_l, box_w = build.box_interior(p.BOX_LEDGE_Z1)
    dl = box_l - 2 * p.BOX_LEDGE_DEPTH - p.BOX_LEDGE_OPEN_L
    dw = box_w - 2 * p.BOX_LEDGE_DEPTH - p.BOX_LEDGE_OPEN_W
    assert abs(dl) <= 2 and abs(dw) <= 2, f"ledge opening disagrees with box minus ledge by {dl:+.1f} / {dw:+.1f}"
    print(
        f"box: floor {p.BOX_FLOOR_L:g} x {p.BOX_FLOOR_W:g}  at ledge top {box_l:.1f} x {box_w:.1f}  "
        f"draft {p.BOX_TAPER_L:.3f} / {p.BOX_TAPER_W:.3f} per mm  ledge opening measured "
        f"{p.BOX_LEDGE_OPEN_L:g} x {p.BOX_LEDGE_OPEN_W:g}, derived {dl:+.1f} / {dw:+.1f} off"
    )


def check_gauge(name: str, part, k: dict) -> float:
    """Common checks: one valid frame, fits the bed, WALL_CLEARANCE to the box all round at its height.
    Returns the smallest wall gap found."""
    assert part.is_valid and len(part.solids()) == 1, f"{name} is not one valid solid"
    bb = part.bounding_box()
    assert max(bb.size.X, bb.size.Y, bb.size.Z) <= p.BED_SIZE, f"{name} does not fit the bed: {bb.size}"
    assert abs(bb.size.X - k["outer_l"]) < 1e-3 and abs(bb.size.Y - k["outer_w"]) < 1e-3, f"{name} size {bb.size}"
    assert abs(bb.min.Z) < 1e-6 and abs(bb.max.Z - p.GAUGE_HEIGHT) < 1e-6, f"{name} height wrong"
    assert k["z"] + p.GAUGE_HEIGHT < p.BOX_HEIGHT, f"{name} sticks out over the rim"
    # Every point of its outline, bottom and top, keeps WALL_CLEARANCE to the box at that height.
    gaps = []
    for edge in part.edges():
        for i in range(21):
            pt = edge.position_at(i / 20)
            gaps.append(wall_gap(pt.X, pt.Y, k["z"] + pt.Z))
    gap = min(gaps)
    assert gap >= p.WALL_CLEARANCE - 1e-6, f"{name} only {gap:.2f} from a wall"
    # A closed frame: hollow in the middle, solid across each side.
    z = p.GAUGE_HEIGHT / 2
    assert not solid_at(part, 0, 0, z), f"{name} is not hollow"
    mx, my = (k["outer_l"] + k["inner_l"]) / 4, (k["outer_w"] + k["inner_w"]) / 4
    for x, y in ((mx, 0), (-mx, 0), (0, my), (0, -my), (mx * 0.5, my), (-mx * 0.5, -my)):
        assert solid_at(part, x, y, z), f"{name} frame open at ({x:.1f}, {y:.1f})"
    return gap


def check_floor_gauge() -> None:
    part, k = build.floor_gauge(), build.floor_layout()
    gap = check_gauge("floor_gauge", part, k)
    assert abs(gap - p.WALL_CLEARANCE) < 0.01, f"floor gauge gap {gap:.2f}, want exactly WALL_CLEARANCE"
    print(
        f"floor_gauge: OK  {k['outer_l']:.1f} x {k['outer_w']:.1f} x {p.GAUGE_HEIGHT:g}  "
        f"wall {p.GAUGE_WALL:g}  min wall gap {gap:.2f}  label {build.gauge_label(k, 'FLOOR')!r}"
    )


def check_ledge_gauge() -> None:
    part, k = build.ledge_gauge(), build.seat_layout()
    gap = check_gauge("ledge_gauge", part, k)
    # Rests on the ledge: on each side the frame reaches at least SEAT_MIN_REST past the ledge edge
    # toward the wall, so it cannot fall through flat.
    rest_l = (k["outer_l"] - p.BOX_LEDGE_OPEN_L) / 2
    rest_w = (k["outer_w"] - p.BOX_LEDGE_OPEN_W) / 2
    assert min(rest_l, rest_w) >= p.SEAT_MIN_REST, f"rests on only {rest_l:.2f} / {rest_w:.2f} of ledge"
    # And it is solid over the whole ledge edge, from the opening outward: the frame's inner edge is
    # inside the opening, all along each side (probed away from the corners, whose radius we do not know).
    ol, ow = p.BOX_LEDGE_OPEN_L / 2, p.BOX_LEDGE_OPEN_W / 2
    z = p.GAUGE_HEIGHT / 2
    for f in (-0.8, -0.4, 0.0, 0.4, 0.8):
        for d in (-EPS, rest_l / 2):
            assert solid_at(part, ol + d, f * ow, z) and solid_at(part, -ol - d, f * ow, z), "not resting on an end ledge"
        for d in (-EPS, rest_w / 2):
            assert solid_at(part, f * ol, ow + d, z) and solid_at(part, f * ol, -ow - d, z), "not resting on a side ledge"
    assert k["inner_l"] < p.BOX_LEDGE_OPEN_L and k["inner_w"] < p.BOX_LEDGE_OPEN_W, "inner opening wider than the ledge"
    print(
        f"ledge_gauge: OK  {k['outer_l']:.1f} x {k['outer_w']:.1f} x {p.GAUGE_HEIGHT:g}  "
        f"opening {k['inner_l']:.1f} x {k['inner_w']:.1f}  sits at Z={k['z']:g}  "
        f"rests on {rest_l:.1f} (ends) / {rest_w:.1f} (sides) of ledge  min wall gap {gap:.2f}  "
        f"label {build.gauge_label(k, 'LEDGE')!r}"
    )


# --- Feed mechanism bench rig (#54) ------------------------------------------------------


def feed_bridges(name: str) -> tuple:
    """Documented bridges of a feed part: heights, in its print orientation, of the horizontal
    ceilings the printer has to span (all short). Anything else facing down flatter than 45 deg fails."""
    k = build.feed_layout()
    nut_d = p.M3_NUT_THICKNESS + p.NUT_TOLERANCE
    if name == "feed_base":
        return (nut_d,)  # Nut trap ceilings.
    if name == "feed_drive_hub":
        return (p.FEED_SHAFT_ENGAGE + k["chamber_h"],)  # Ceiling of the screw-head chamber.
    if name.startswith("feed_cover_"):
        return (p.FEED_HOPPER_SEAT, p.FEED_TEXT_DEPTH)  # Hopper groove and label, on the bed side.
    if name == "feed_servo_bracket":
        return (p.FEED_BRACKET_T,)  # Ends of the 2.5 mm ear holes where they meet the house wall.
    if name.startswith("feed_elbow_") and name.endswith("_b"):
        return (nut_d,)  # Nut trap ceilings.
    return ()


def overhangs(part, bridges: tuple = (), small_hole_r: float = 2.0) -> list:
    """Points of downward faces flatter than 45 deg, off the bed, that are neither a documented
    bridge (horizontal face at one of the `bridges` heights) nor the top of a small horizontal hole.
    Each face is sampled on a 5 x 5 grid."""
    bad = []
    for f in part.faces():
        small = f.geom_type == GeomType.CYLINDER and f.radius is not None and f.radius <= small_hole_r
        for i in range(5):
            for j in range(5):
                n = f.normal_at(0.1 + 0.2 * i, 0.1 + 0.2 * j)
                q = f.position_at(0.1 + 0.2 * i, 0.1 + 0.2 * j)
                if n.Z > -0.7072 or q.Z < 0.01 or small:
                    continue
                if f.geom_type == GeomType.PLANE and n.Z < -0.999 and any(abs(q.Z - z) < 0.02 for z in bridges):
                    continue
                bad.append((str(f.geom_type), round(q.X, 1), round(q.Y, 1), round(q.Z, 2), round(n.Z, 3)))
    return bad


def check_feed_numbers() -> None:
    """One BB per notch, one layer under the cover, nothing a BB can bind in."""
    k = build.feed_layout()
    big = p.BB_D + p.FIT_TOLERANCE  # Largest BB, or a passage printed FIT_TOLERANCE small.
    R, N, w = p.FEED_BB_CIRCLE_R, p.FEED_POCKETS, p.FEED_NOTCH_W
    pitch = 2 * math.pi * R / N
    land_angle = 2 * math.pi / N - 2 * math.asin(w / 2 / R)
    land = 2 * R * math.sin(land_angle / 2)  # Straight across the land, on the BB circle.
    assert land >= p.FEED_MIN_LAND, f"land only {land:.2f} between notches"
    assert w >= big, f"notch {w} binds a {big:.2f} BB"
    assert w < 2 * p.BB_MIN_D, "two BBs fit side by side in a notch"
    assert k["shroud_r"] - k["notch_end_r"] < 2 * p.BB_MIN_D, "two BBs fit one behind the other in a notch"
    assert k["shroud_r"] >= R + big / 2, "the shroud pinches the largest BB in its notch"
    assert k["shroud_r"] - k["disc_r"] >= p.FIT_TOLERANCE, "disc rim rubs the shroud"
    assert k["disc_r"] > R, "notch centres beyond the rim"
    assert p.FEED_SLOT_H - p.FIT_TOLERANCE >= p.BB_D, f"slot {p.FEED_SLOT_H} binds a BB if it prints low"
    assert p.FEED_SLOT_H + p.FIT_TOLERANCE < 2 * p.BB_MIN_D, "two small BBs could stack under the cover"
    # A BB riding on the disc (not in a notch) never gets under the cover: the cut-off edge holds it.
    assert p.FEED_DISC_T + p.BB_MIN_D > p.FEED_SLOT_H + p.FIT_TOLERANCE, "a BB on the disc fits under the cover"
    # The notch walls push the BB at its centre, the tongue catches its top.
    assert p.FEED_DISC_T > p.BB_D / 2, "disc too thin: its notch walls push the BB below the centre"
    grip = p.BB_MIN_D - (k["tongue_bottom"] - k["floor"])
    assert grip >= 1.0, f"the tongue catches only {grip:.2f} of the smallest BB"
    assert p.FEED_RUN_GAP >= p.FIT_TOLERANCE, "running gap under FIT_TOLERANCE"
    assert p.BB_GUIDE_D - p.FIT_TOLERANCE >= p.BB_D, "channel and elbow bore bind a BB if they print small"
    # Reverse: past the tongue, full slot height for at least 2 pockets before the window starts.
    free = (k["start"] + 360) - p.FEED_TONGUE_ARC
    assert free >= 2 * 360 / N, f"only {free:.0f} deg of full slot before the window, a reverse meets the tongue"
    assert abs(p.FEED_WINDOW_ARC + p.FEED_CARRY_ARC + free + p.FEED_TONGUE_ARC - 360) < 1e-9
    assert p.FEED_WINDOW_R_IN > k["sleeve_ro"] + p.MIN_WALL / 2, "the sleeve does not stand over solid cover"
    assert p.FEED_WINDOW_R_IN < k["notch_end_r"], "window does not open the notches down to their end"
    print(
        f"feed numbers: OK  {N} notches w={w} on R{R:g}, pitch {pitch:.2f}, land {land:.2f}  "
        f"slot {p.FEED_SLOT_H} (2 x min BB = {2 * p.BB_MIN_D:.1f})  tongue grips {grip:.2f}  "
        f"shroud R{k['shroud_r']:.2f} (disc R{k['disc_r']:.2f})  inlet {k['inlet']:.1f} over the floor, "
        f"{k['cover_top']:.1f} over the table  full slot before the window {free:.0f} deg"
    )


def check_feed_disc() -> None:
    part = build.feed_disc()
    k = build.feed_layout()
    assert part.is_valid and len(part.solids()) == 1, "disc is not one valid solid"
    R, N, w, z = p.FEED_BB_CIRCLE_R, p.FEED_POCKETS, p.FEED_NOTCH_W, k["floor"] + p.FEED_DISC_T / 2
    # Count the notches round the BB circle, and check they are evenly spaced.
    runs, prev = [], solid_at(part, R, 0, z)
    for i in range(1, 3601):
        a = math.radians(i / 10)
        now = solid_at(part, R * math.cos(a), R * math.sin(a), z)
        if prev and not now:
            runs.append(i / 10)
        prev = now
    assert len(runs) == N, f"{len(runs)} notches, want {N}"
    steps = [(runs[(i + 1) % N] - runs[i]) % 360 for i in range(N)]
    assert max(steps) - min(steps) < 0.25, f"notches unevenly spaced: {steps}"
    for i in range(N):
        a = 2 * math.pi * i / N
        c, s = math.cos(a), math.sin(a)
        # Hollow across the notch up to w/2, solid past it; hollow up to the round end, solid past it.
        for side in (-1, 1):
            x, y = R * c - side * (w / 2 - EPS) * s, R * s + side * (w / 2 - EPS) * c
            assert not solid_at(part, x, y, z), f"notch {i} narrower than {w}"
            x, y = R * c - side * (w / 2 + EPS) * s, R * s + side * (w / 2 + EPS) * c
            assert solid_at(part, x, y, z), f"notch {i} wider than {w}"
        re = k["notch_end_r"]
        assert not solid_at(part, (re + EPS) * c, (re + EPS) * s, z), f"notch {i} end too close in"
        assert solid_at(part, (re - EPS) * c, (re - EPS) * s, z), f"notch {i} end too deep"
        # Notch walls vertical: through from just over the floor to just under the top.
        for zz in (k["floor"] + EPS, k["disc_top"] - EPS):
            assert not solid_at(part, R * c, R * s, zz), f"notch {i} not through at z={zz:.2f}"
    # Hub: pin bore underneath, hex socket on top, solid between.
    pr = k["pin_bore_r"]
    zp = k["floor"] + 1
    assert not solid_at(part, pr - EPS, 0, zp) and solid_at(part, pr + EPS, 0, zp), "pin bore size"
    assert solid_at(part, 0, 0, k["floor"] + k["pin_bore_depth"] + pr + EPS), "no wall between pin bore and hex socket"
    zh = k["hub_top"] - p.FEED_HEX_DEPTH / 2
    af = (p.FEED_SHAFT_AF + p.FEED_HEX_TOLERANCE) / 2
    assert not solid_at(part, af - EPS, 0, zh) and solid_at(part, af + EPS, 0, zh), "hex socket across flats"
    bb = part.bounding_box()
    assert abs(max(bb.size.X, bb.size.Y) - p.FEED_DISC_OD) < 0.01, f"disc OD {bb.size}"
    print(
        f"feed_disc: OK  {N} notches every {360 / N:.2f} deg, OD {p.FEED_DISC_OD}, t {p.FEED_DISC_T}, "
        f"hub {k['hub_h']:.1f} tall"
    )


def check_feed_cover(skew: float, assembly: dict) -> None:
    k = build.feed_layout()
    cover, base, disc = assembly["cover"], assembly["base"], assembly["disc"]
    assert cover.is_valid and len(cover.solids()) == 1, f"cover {skew} is not one valid solid"
    R, zu = p.FEED_BB_CIRCLE_R, k["block_top"]

    def pt(a: float, r: float = R) -> tuple:
        return (r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))

    # Slot: floor to cover underside is FEED_SLOT_H, under the cover past the cut-off edge.
    x, y = pt(k["cut"] + 20)
    assert solid_at(base, x, y, k["floor"] - EPS) and not solid_at(base, x, y, k["floor"] + EPS), "floor height"
    assert solid_at(cover, x, y, zu + EPS) and not solid_at(cover, x, y, zu - EPS), "cover underside height"
    # Window: open through the cover over the whole notch band, at its middle.
    mid = k["cut"] - p.FEED_WINDOW_ARC / 2
    for r in (p.FEED_WINDOW_R_IN + EPS, k["notch_end_r"], R, k["shroud_r"] - EPS):
        for zz in (zu + EPS, k["cover_top"] - EPS):
            assert not solid_at(cover, *pt(mid, r), zz), f"window closed at r={r:.2f}"
    # Edges through the BB circle at their angles, at the underside (where the chamfer is nil).
    for a, inside in ((k["cut"], -1), (k["start"], 1)):
        assert not solid_at(cover, *pt(a + inside * 1.0), zu + EPS), f"window short of its edge at {a}"
        assert solid_at(cover, *pt(a - inside * 1.0), zu + EPS), f"window past its edge at {a}"
    # Lift chamfer: half way in, solid low down, cut away higher up. And the tilt of each edge.
    c = p.FEED_LIFT_CHAMFER
    for a, side in ((k["cut"], 1), (k["start"], -1)):
        e = build.feed_edge(a, skew, side)
        d = (e[2][0] - e[1][0], e[2][1] - e[1][1])
        L = math.hypot(*d)
        n = (-side * d[1] / L, side * d[0] / L)
        x, y = pt(a)
        assert solid_at(cover, x + n[0] * c / 2, y + n[1] * c / 2, zu + c / 4), f"chamfer too big at {a}"
        assert not solid_at(cover, x + n[0] * c / 2, y + n[1] * c / 2, zu + 3 * c / 4), f"no lift chamfer at {a}"
        tilt = math.degrees(math.atan2(abs(d[0] * y - d[1] * x), d[0] * x + d[1] * y))
        assert abs(tilt - skew) < 1e-6, f"edge tilt {tilt:.2f}, want {skew}"
        # Tilted the right way: the outer end set back toward the window.
        diff = (math.degrees(math.atan2(e[2][1], e[2][0])) - a + 180) % 360 - 180
        assert skew == 0 or diff * side < 0, f"edge at {a} tilted the wrong way"
    # Tongue: hangs to FEED_RUN_GAP over the disc, its edge on the channel's inner wall.
    x0, zt = k["channel_x0"], k["tongue_bottom"]
    assert solid_at(cover, x0 - EPS, 5, zt + EPS) and not solid_at(cover, x0 + EPS, 5, zt + EPS), "tongue edge"
    assert not solid_at(cover, x0 - 1, 5, zt - EPS), "tongue too low"
    assert not solid_at(cover, *pt(p.FEED_TONGUE_ARC + 5), zt + EPS), "tongue runs past FEED_TONGUE_ARC"
    # The sleeve stands over solid cover all round; the hopper wall sits in its groove.
    rs = (k["sleeve_ri"] + k["sleeve_ro"]) / 2
    for a in range(0, 360, 10):
        assert solid_at(cover, *pt(a, rs), k["cover_top"] - EPS), f"no cover under the sleeve at {a} deg"
    gm = (k["hop_in"] + k["hop_out"]) / 2
    assert not solid_at(cover, gm, 0, k["cover_top"] - EPS), "no hopper groove"
    assert solid_at(cover, gm, 0, k["hop_bottom"] - EPS), "hopper groove too deep"
    # Clear of the turning disc by FEED_RUN_GAP, never touching it.
    gap = cover.distance_to(disc)
    assert gap >= p.FIT_TOLERANCE - 1e-6, f"cover only {gap:.3f} from the disc"
    assert (cover & base).volume < 1e-3, "cover and base overlap"
    print(
        f"feed_cover skew {skew:g}: OK  window {p.FEED_WINDOW_ARC:g} deg, edges tilted {skew:g} deg, "
        f"chamfer {c}, disc gap {gap:.2f}"
    )


def check_feed_assembly(assembly: dict) -> None:
    k = build.feed_layout()
    a = assembly
    for n, s in a.items():
        assert s.is_valid and len(s.solids()) == 1, f"{n} is not one valid solid"

    def overlap(m: str, n: str) -> None:
        v = (a[m] & a[n]).volume
        assert v < 1e-3, f"{m} and {n} overlap by {v:.3f} mm3"

    def clear(m: str, n: str, want: float) -> float:
        d = a[m].distance_to(a[n])
        assert d >= want - 1e-6, f"{m} only {d:.3f} from {n}, want {want}"
        return d

    pairs = (
        ("disc", "base"),
        ("shaft", "disc"),
        ("shaft", "drive_hub"),
        ("hopper", "cover"),
        ("hopper", "bracket"),
        ("elbow_a", "base"),
        ("elbow_b", "base"),
        ("elbow_a", "elbow_b"),
        ("elbow_a", "cover"),
        ("elbow_b", "cover"),
    )
    for m, n in pairs:
        overlap(m, n)
    clear("shaft", "cover", p.FIT_TOLERANCE)
    clear("shaft", "bracket", p.FIT_TOLERANCE)
    clear("disc", "bracket", p.FIT_TOLERANCE)
    clear("drive_hub", "bracket", p.FIT_TOLERANCE)
    clear("disc", "hopper", p.FIT_TOLERANCE)
    # The disc's rim clears the shroud all round (outside the exit, where the shroud opens).
    r = k["shroud_r"]
    for deg in range(0, 360, 5):
        c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        if not solid_at(a["base"], (r + EPS) * c, (r + EPS) * s, k["floor"] + 1):
            continue  # The channel.
        assert not solid_at(a["base"], (r - EPS) * c, (r - EPS) * s, k["floor"] + 1), f"shroud inside R{r} at {deg}"
    # Servo case: through the plate with FIT_TOLERANCE, clear of the house below.
    xc = (k["case_x0"] + k["case_x1"]) / 2
    h = k["ears"] - k["case_face"]
    up = (Align.CENTER, Align.CENTER, Align.MIN)
    case = Pos(xc, 0, k["case_face"]) * Box(p.SERVO_BODY_L, p.SERVO_BODY_W, h, align=up)
    d = case.distance_to(a["bracket"])
    assert d >= p.FIT_TOLERANCE - 1e-6, f"servo case {d:.2f} from the bracket"
    # Shaft: sits on the floor of the disc's socket, goes up into the drive hub with room to float.
    engage = k["shaft_top"] - k["dhub_bottom"]
    assert engage >= p.FEED_SHAFT_ENGAGE / 2, f"shaft only {engage:.1f} into the drive hub"
    assert p.FEED_SHAFT_FLOAT > 0
    assert 0 < p.FEED_SLEEVE_GAP < p.BB_MIN_D / 2, "a BB gets under the sleeve"
    assert k["hop_top"] - k["cover_top"] >= 100, "hopper under 10 cm"
    print(
        f"feed assembly: OK  no overlaps  servo case gap {d:.2f}  shaft {k['shaft_top'] - k['shaft_bottom']:.1f} long, "
        f"{engage:.1f} into the drive hub (float {p.FEED_SHAFT_FLOAT})  "
        f"hopper {k['hop_top'] - k['cover_top']:.0f} over the cover"
    )


def check_feed_elbow(R: float) -> None:
    k = build.feed_layout()
    e = build.elbow_layout(R)
    a, b = build.feed_elbow_half(R, "a", placed=False), build.feed_elbow_half(R, "b", placed=False)
    for h in (a, b):
        assert h.is_valid and len(h.solids()) == 1, f"elbow R{R} half is not one valid solid"
    both = a + b
    assert R >= p.FEED_ELBOW_MIN_R, f"elbow R{R} under FEED_ELBOW_MIN_R {p.FEED_ELBOW_MIN_R}"
    r, cu, cv = e["bore_r"], e["cu"], e["cv"]

    def ring(center, n1, n2, radius: float, hollow: bool, skip_split: bool = False) -> None:
        for deg in range(0, 360, 30):
            if skip_split and deg % 180 == 0:
                continue
            c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
            q = Vector(*center) + Vector(*n1) * (radius * c) + Vector(*n2) * (radius * s)
            what = "closed" if hollow else "open"
            assert both.is_inside(q) != hollow, f"elbow R{R}: bore {what} at {center} {deg} deg"

    # Bore continuous along the path: hollow just inside bore_r, solid just outside, all along.
    stations = [((u, 0, 0), (0, 1, 0), (0, 0, 1)) for u in (p.FEED_MOUTH_CHAMFER + 0.3, p.FEED_ELBOW_RUN / 2)]
    for deg in range(0, 91, 10):
        t = math.radians(-90 + deg)
        stations.append(((cu + R * math.cos(t), cv + R * math.sin(t), 0), (math.cos(t), math.sin(t), 0), (0, 0, 1)))
    stations.append(((e["ue"], (cv + e["vs"]) / 2, 0), (1, 0, 0), (0, 0, 1)))
    for ctr, n1, n2 in stations:
        ring(ctr, n1, n2, r - EPS, True)
        ring(ctr, n1, n2, r + EPS, False)
    # Mouth: every point a BB can reach at the channel exit (resting on the floor, anywhere across the
    # channel) is open just inside the elbow, even with the elbow FIT_TOLERANCE off in any direction.
    off_z = p.BB_D / 2 - p.BB_GUIDE_D / 2  # BB centre below the bore axis.
    for dx in (-(p.BB_GUIDE_D - p.BB_D) / 2, (p.BB_GUIDE_D - p.BB_D) / 2):
        for mx in (-p.FIT_TOLERANCE, 0, p.FIT_TOLERANCE):
            for mz in (-p.FIT_TOLERANCE, 0, p.FIT_TOLERANCE):
                for deg in range(0, 360, 15):
                    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
                    q = Vector(0.05, off_z + mz + (p.BB_D / 2) * s, dx + mx + (p.BB_D / 2) * c)
                    where = f"({dx:+.1f},{mx:+.1f},{mz:+.1f})"
                    assert not both.is_inside(q), f"elbow R{R}: a BB catches on the mouth {where}"
    # And it lines up: bore bottom on the channel floor, bore as wide as the channel, on its axis.
    assert abs(e["z0"] - r - k["floor"]) < 1e-9, "elbow bore bottom not on the channel floor"
    assert abs(2 * r - (k["channel_x1"] - k["channel_x0"])) < 1e-9, "elbow bore not as wide as the channel"
    assert abs(e["x"] - (k["channel_x0"] + k["channel_x1"]) / 2) < 1e-9, "elbow off the channel axis"
    # Barrel socket and its shoulder.
    vm = (e["vs"] + e["vt"]) / 2
    ring((e["ue"], vm, 0), (1, 0, 0), (0, 0, 1), e["sock_r"] - EPS, True)
    ring((e["ue"], vm, 0), (1, 0, 0), (0, 0, 1), e["sock_r"] + EPS, False, skip_split=True)
    rs = (r + e["sock_r"]) / 2
    assert both.is_inside(Vector(e["ue"], e["vs"] - EPS, rs)), "no shoulder under the barrel"
    assert not both.is_inside(Vector(e["ue"], e["vs"] + EPS, rs)), "shoulder too high"
    # The clamp gap: the halves stand apart round the socket.
    assert not both.is_inside(Vector(e["ue"] + e["sock_r"] + 1, vm, 0)), "no clamp gap round the socket"
    # Screws keep MIN_WALL to every edge; nut traps in half b, MIN_WALL round them too.
    for u, v, nut in e["screws"]:
        for deg in range(0, 360, 30):
            c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
            rr = p.M3_CLEARANCE / 2 + p.MIN_WALL - EPS
            q = Vector(u + rr * c, v + rr * s, e["t"] / 2)
            assert a.is_inside(q), f"elbow R{R}: screw at ({u:.1f},{v:.1f}) near an edge"
            if nut:
                rn = e["nut_r"] + p.MIN_WALL - EPS
                q = Vector(u + rn * c, v + rn * s, -e["t"] + e["nut_d"] / 2)
                assert b.is_inside(q), f"elbow R{R}: nut trap at ({u:.1f},{v:.1f}) near an edge"
        assert not b.is_inside(Vector(u, v, -e["t"] + 0.5)), "screw hole missing"
    print(
        f"feed_elbow R{R:g}: OK  bore d={2 * r:.2f} continuous, mouth takes a {p.FIT_TOLERANCE} misfit  "
        f"barrel socket d={2 * e['sock_r']:.2f} from Z={e['socket_z']:.1f} to {e['top_z']:.1f} over the table, "
        f"barrel {e['barrel_y'] - p.FEED_BLOCK_HALF:.1f} out from the base block"
    )


def check_feed_coupon() -> None:
    part = build.feed_coupon()
    k = build.feed_coupon_layout()
    assert part.is_valid and len(part.solids()) == 1, "feed coupon is not one valid solid"
    T, W = p.FEED_COUPON_T, k["width"]

    def xs(n: int) -> list:
        return [-W / 2 + W / n * (i + 0.5) for i in range(n)]

    for x, o in zip(xs(len(p.FEED_COUPON_SLOT_OFFSETS)), p.FEED_COUPON_SLOT_OFFSETS):
        depth = p.FEED_SLOT_H + o
        assert not solid_at(part, x, k["y_pocket"], T - depth + EPS), f"slot pocket {o} too shallow"
        assert solid_at(part, x, k["y_pocket"], T - depth - EPS), f"slot pocket {o} too deep"
        assert T - depth >= p.MIN_WALL - 1e-9, "slot pocket floor thinner than MIN_WALL"
    for x, o in zip(xs(len(p.FEED_COUPON_PIN_OFFSETS)), p.FEED_COUPON_PIN_OFFSETS):
        r = (p.FEED_PIN_D + o) / 2
        y = k["y_pin"]
        assert not solid_at(part, x + r - EPS, y, T / 2) and solid_at(part, x + r + EPS, y, T / 2), f"pin bore {o}"
    for x, o in zip(xs(len(p.FEED_COUPON_HEX_OFFSETS)), p.FEED_COUPON_HEX_OFFSETS):
        af, y = (p.FEED_SHAFT_AF + o) / 2, k["y_hex"]
        assert not solid_at(part, x + af - EPS, y, T / 2) and solid_at(part, x + af + EPS, y, T / 2), f"hex {o}"
    print(
        f"feed_coupon: OK  slot pockets {[round(p.FEED_SLOT_H + o, 2) for o in p.FEED_COUPON_SLOT_OFFSETS]}  "
        f"pin bores {[round(p.FEED_PIN_D + o, 2) for o in p.FEED_COUPON_PIN_OFFSETS]}  "
        f"hex {[round(p.FEED_SHAFT_AF + o, 2) for o in p.FEED_COUPON_HEX_OFFSETS]}"
    )


def check_feed_print() -> None:
    """Every feed part, as exported: fits the bed, sits on it, and nothing needs supports."""
    for name, make in build.PARTS.items():
        if not name.startswith("feed_"):
            continue
        part = make()
        bb = part.bounding_box()
        assert max(bb.size.X, bb.size.Y, bb.size.Z) <= p.BED_SIZE, f"{name} does not fit the bed: {bb.size}"
        assert abs(bb.min.Z) < 1e-6, f"{name} not on the bed"
        bad = overhangs(part, feed_bridges(name))
        assert not bad, f"{name} has overhangs flatter than 45 deg: {bad[:5]}"
    print("feed print: OK  every feed part fits the bed, no overhang flatter than 45 deg except the documented bridges")


if __name__ == "__main__":
    check_box()
    check_floor_gauge()
    check_ledge_gauge()
    original = p.BARREL_OD
    for od in BARREL_ODS:
        check_collar(od)
        check_coupon(od)
    p.BARREL_OD = original
    bore = p.KNOB_BORE
    for kind in ("dflat", "round"):
        check_knob(kind)
    p.KNOB_BORE = bore
    check_feed_numbers()
    check_feed_disc()
    check_feed_coupon()
    for skew in p.FEED_CUTOFF_SKEWS:
        assembly = build.feed_assembly(skew=skew)
        check_feed_cover(skew, assembly)
    check_feed_assembly(assembly)
    for radius in p.FEED_ELBOW_RADII:
        check_feed_elbow(radius)
    check_feed_print()
    print("all checks passed")
