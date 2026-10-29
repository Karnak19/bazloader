"""Sanity checks on the IR collar, the encoder knob, the fit coupon, the box fit gauges and the feed rig.

Run: uv run python check.py
Probes points just inside and just outside each feature, so a wrong bore, a missing
shoulder, a socket off its axis, two sockets that are not coaxial or a knob bore off
its axis fail loudly.
"""

import math

from build123d import Align, Box, Cylinder, GeomType, Pos, Vector, extrude

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

    The box is modelled with CORNER_R corners above the ledge and FLOOR_CORNER_R below it, the
    worst case: its real corners are tighter, which only leaves more room for a part with that radius.
    """
    box_l, box_w = build.box_interior(z)
    r = p.FLOOR_CORNER_R if z < p.BOX_LEDGE_Z0 else p.CORNER_R
    qx, qy = abs(x) - (box_l / 2 - r), abs(y) - (box_w / 2 - r)
    outside = math.hypot(max(qx, 0.0), max(qy, 0.0)) + min(max(qx, qy), 0.0) - r  # Signed distance, < 0 inside.
    return -outside


def check_box() -> None:
    """The hand measurements agree with each other: the ledge heights are in order, and the step
    from the upper part to the lower part is wide enough on every side for a part to rest on."""
    assert 0 < p.BOX_LEDGE_Z0 < p.BOX_LEDGE_Z1 < p.BOX_HEIGHT, "ledge heights out of order"
    rim_l, rim_w = build.box_interior(p.BOX_HEIGHT)
    assert abs(rim_l - p.BOX_RIM_L) < 1e-6 and abs(rim_w - p.BOX_RIM_W) < 1e-6, "upper part does not meet the rim"
    box_l, box_w = build.box_interior(p.BOX_LEDGE_Z1)
    low_l, low_w = build.box_lower(p.BOX_LEDGE_Z1)
    need = p.WALL_CLEARANCE + p.SEAT_MIN_REST
    assert min(p.BOX_STEP_L, p.BOX_STEP_W) >= need, f"step only {p.BOX_STEP_L:.1f} / {p.BOX_STEP_W:.1f}, want {need:g}"
    print(
        f"box: floor {p.BOX_FLOOR_L:g} x {p.BOX_FLOOR_W:g}  draft {p.BOX_TAPER_L:.3f} / {p.BOX_TAPER_W:.3f} per mm  "
        f"at ledge top: lower {low_l:.1f} x {low_w:.1f}, upper {box_l:.1f} x {box_w:.1f}  "
        f"rim {rim_l:g} x {rim_w:g}  step {p.BOX_STEP_L:.1f} (ends) / {p.BOX_STEP_W:.1f} (sides)"
    )


def bed_fit(l: float, w: float) -> str | None:
    """How an l x w footprint fits the square bed: "straight", "diagonal" (turned 1 to 89 deg), or
    None. The bounding rectangle is used, so the rounded corners only make it a little safer."""
    for deg in range(90):
        a = math.radians(deg)
        c, s = math.cos(a), math.sin(a)
        if l * c + w * s <= p.BED_SIZE and l * s + w * c <= p.BED_SIZE:
            return "straight" if deg == 0 else f"diagonal ({deg} deg)"
    return None


def check_gauge(name: str, part, k: dict) -> float:
    """Common checks: one valid frame, fits the bed, WALL_CLEARANCE to the box all round at its height.
    Returns the smallest wall gap found."""
    assert part.is_valid and len(part.solids()) == 1, f"{name} is not one valid solid"
    bb = part.bounding_box()
    assert bb.size.Z <= p.BED_SIZE and bed_fit(bb.size.X, bb.size.Y), f"{name} does not fit the bed: {bb.size}"
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


def check_corner_gauges() -> None:
    for r in p.CORNER_GAUGE_RADII:
        part = build.corner_gauge(r)
        assert part.is_valid and len(part.solids()) == 1, f"corner_gauge_r{r:g}: not one valid solid"
        size = part.bounding_box().size
        assert abs(size.X - p.CORNER_GAUGE_SIZE) < 1e-3 and abs(size.Y - p.CORNER_GAUGE_SIZE) < 1e-3, f"R{r:g} tab is {size}"
        assert r < p.CORNER_GAUGE_SIZE / 2, f"R{r:g} too big for the tab"
    radii = ", ".join(f"R{r:g}" for r in p.CORNER_GAUGE_RADII)
    print(f"corner gauges: OK  {len(p.CORNER_GAUGE_RADII)} tabs ({radii}), {p.CORNER_GAUGE_SIZE:g} mm square, one file each")


def check_ledge_gauge() -> None:
    part, k = build.ledge_gauge(), build.seat_layout()
    gap = check_gauge("ledge_gauge", part, k)
    # check_gauge made sure it keeps WALL_CLEARANCE to the upper walls (mid-wall numbers; it is sized
    # smaller, for the corners).
    # It cannot drop into the lower part: it is bigger than the lower part at the ledge, both ways,
    # and rests on at least SEAT_MIN_REST of step on every side.
    low_l, low_w = build.box_lower(p.BOX_LEDGE_Z1)
    assert k["outer_l"] > low_l and k["outer_w"] > low_w, "ledge gauge would drop into the lower part"
    rest_l = (k["outer_l"] - low_l) / 2
    rest_w = (k["outer_w"] - low_w) / 2
    assert min(rest_l, rest_w) >= p.SEAT_MIN_REST, f"rests on only {rest_l:.2f} / {rest_w:.2f} of step"
    # And it is solid over the whole step, from the lower wall outward: the frame's inner edge is
    # inside the lower part, all along each side (probed away from the corners, whose radius we do not know).
    ol, ow = low_l / 2, low_w / 2
    z = p.GAUGE_HEIGHT / 2
    for f in (-0.8, -0.4, 0.0, 0.4, 0.8):
        for d in (-EPS, rest_l / 2):
            assert solid_at(part, ol + d, f * ow, z) and solid_at(part, -ol - d, f * ow, z), "not resting on an end step"
        for d in (-EPS, rest_w / 2):
            assert solid_at(part, f * ol, ow + d, z) and solid_at(part, f * ol, -ow - d, z), "not resting on a side step"
    assert k["inner_l"] < low_l and k["inner_w"] < low_w, "inner opening wider than the lower part"
    bb = part.bounding_box()
    print(
        f"ledge_gauge: OK  {k['outer_l']:.1f} x {k['outer_w']:.1f} x {p.GAUGE_HEIGHT:g}  "
        f"opening {k['inner_l']:.1f} x {k['inner_w']:.1f}  sits at Z={k['z']:g}  "
        f"rests on {rest_l:.1f} (ends) / {rest_w:.1f} (sides) of step  min wall gap {gap:.2f}  "
        f"bed {bed_fit(bb.size.X, bb.size.Y)}  label {build.gauge_label(k, 'LEDGE')!r}"
    )


# --- Feed mechanism bench rig (#54) ------------------------------------------------------


def feed_bridges(name: str) -> tuple:
    """Documented bridges of a feed part: heights, in its print orientation, of the horizontal
    ceilings the printer has to span (all short). Anything else facing down flatter than 45 deg fails."""
    k = build.feed_layout()
    nut_d = p.M3_NUT_THICKNESS + p.NUT_TOLERANCE
    if name == "feed_base":
        return (nut_d,)  # Nut trap ceilings.
    if name == "feed_drive":
        return (k["socket_depth"] + k["chamber_h"],)  # Ceiling of the screw-head chamber.
    if name.startswith("feed_cover_"):
        return (p.FEED_HOPPER_SEAT, p.FEED_TEXT_DEPTH)  # Hopper and chimney grooves, label, on the bed side.
    if name == "feed_servo_bracket":
        return (p.FEED_SELF_TAP_DEPTH, k["rib_groove_d"])  # Ends of the pilot holes in the leg, ear rib groove.
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
    # Hub: pin bore underneath, solid over it, round up to the cover top, then the hex boss.
    pr = k["pin_bore_r"]
    zp = k["floor"] + 1
    assert not solid_at(part, pr - EPS, 0, zp) and solid_at(part, pr + EPS, 0, zp), "pin bore size"
    assert solid_at(part, 0, 0, k["floor"] + k["pin_bore_depth"] + pr + EPS), "no solid over the pin bore"
    zr = k["hub_round_top"] - 1
    assert solid_at(part, p.FEED_HUB_R - EPS, 0, zr) and not solid_at(part, p.FEED_HUB_R + EPS, 0, zr), "hub radius"
    zh = (k["hub_round_top"] + k["boss_top"]) / 2
    af = p.FEED_HEX_AF / 2
    assert solid_at(part, af - EPS, 0, zh) and not solid_at(part, af + EPS, 0, zh), "hex boss across flats"
    assert solid_at(part, 0, 0, k["boss_top"] - EPS) and not solid_at(part, 0, 0, k["boss_top"] + EPS), "boss top"
    bb = part.bounding_box()
    assert abs(max(bb.size.X, bb.size.Y) - p.FEED_DISC_OD) < 0.01, f"disc OD {bb.size}"
    print(
        f"feed_disc: OK  {N} notches every {360 / N:.2f} deg, OD {p.FEED_DISC_OD}, t {p.FEED_DISC_T}, "
        f"hex boss AF{p.FEED_HEX_AF:g} up to {k['boss_top'] - k['cover_top']:.1f} over the cover"
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
    # Window: open through the cover over the whole notch band, all along, except where the chimney
    # stands; and the BB circle itself never under the chimney.
    foot = build.feed_chimney_footprint(p.FIT_TOLERANCE, zu - 1, p.FEED_COVER_T + 2)
    a = k["start"] + 12  # Clear of the skewed edges, which lean into the window at the rim.
    while a <= k["cut"] - 12:
        assert not foot.is_inside(Vector(*pt(a), zu + 1)), f"the BB circle runs under the chimney at {a:.0f} deg"
        for r in (k["notch_end_r"] + EPS, R, k["shroud_r"] - EPS):
            if foot.is_inside(Vector(*pt(a, r), zu + 1)):
                continue
            for zz in (zu + EPS, k["cover_top"] - EPS):
                assert not solid_at(cover, *pt(a, r), zz), f"window closed at {a:.0f} deg, r={r:.2f}"
        a += 3
    # Edges through the BB circle at their angles, at the underside (where the chamfer is nil).
    for a, inside in ((k["cut"], -1), (k["start"], 1)):
        assert not solid_at(cover, *pt(a + inside * 1.0), zu + EPS), f"window short of its edge at {a}"
        assert solid_at(cover, *pt(a - inside * 1.0), zu + EPS), f"window past its edge at {a}"
    # Lift chamfer: half way in, solid low down, cut away higher up. And the tilt of each edge. The
    # cut-off edge keeps its whole chamfer over the notches, clear of the wall; the start edge only
    # matters on a reverse, and the wall's line takes its inner corner.
    c = p.FEED_LIFT_CHAMFER
    for a, side in ((k["cut"], 1), (k["start"], -1)):
        e = build.feed_edge(a, skew, side)
        d = (e[2][0] - e[1][0], e[2][1] - e[1][1])
        L = math.hypot(*d)
        n = (-side * d[1] / L, side * d[0] / L)
        rs = (k["shroud_r"] - 1,) if side < 0 else (k["notch_end_r"] + EPS, R, k["shroud_r"] - 1)
        jx, jy = e[1]
        for r in rs:
            # Point of the edge at radius r: from the joint, along it.
            ju = (jx * d[0] + jy * d[1]) / L
            t = -ju + math.sqrt(ju * ju - jx * jx - jy * jy + r * r)
            x, y = jx + d[0] / L * t, jy + d[1] / L * t
            qx, qy = x + n[0] * c / 2, y + n[1] * c / 2
            assert solid_at(cover, qx, qy, zu + c / 4), f"chamfer too big at {a}, r={r:.1f}"
            assert not solid_at(cover, qx, qy, zu + 3 * c / 4), f"no lift chamfer at {a}, r={r:.1f}"
        x, y = pt(a)
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
    # The hopper and the chimney sit in their grooves; the bracket's pegs go through.
    gm = (k["hop_in"] + k["hop_out"]) / 2
    t = p.FEED_CHIMNEY_T
    probes = ((0, -gm, "hopper"), ((k["hop_x1_in"] + k["hop_x1_out"]) / 2, 30, "hopper +X"),
              (k["ch_x0"] + t / 2, 0, "chimney nose"), (25, k["ch_in_y_low"] + t / 2, "chimney side"))
    for x, y, what in probes:
        assert not solid_at(cover, x, y, k["cover_top"] - EPS), f"no {what} groove"
        assert solid_at(cover, x, y, k["hop_bottom"] - EPS), f"{what} groove too deep"
    for y in p.FEED_PEG_YS:
        for dx in (-1, 1):
            xe = k["peg_x"] + dx * (p.FEED_PEG_L / 2 + p.FEED_SERVO_TRAVEL_X - EPS)
            assert not solid_at(cover, xe, y, k["cover_top"] - 1), f"peg slot at y={y} too short"
    # Clear of the turning disc by FEED_RUN_GAP, never touching it.
    gap = cover.distance_to(disc)
    assert gap >= p.FIT_TOLERANCE - 1e-6, f"cover only {gap:.3f} from the disc"
    assert (cover & base).volume < 1e-3, "cover and base overlap"
    print(
        f"feed_cover skew {skew:g}: OK  window {p.FEED_WINDOW_ARC:g} deg, edges tilted {skew:g} deg, "
        f"chamfer {c}, disc gap {gap:.2f}"
    )


def servo_model(k: dict, dz: float = 0.0) -> dict:
    """The servo as boxes, in the rig frame: the case below the ears (it moves dz with the unmeasured
    heights), the ears, the ribs under them, and the case above them."""
    up = (Align.CENTER, Align.CENTER, Align.MIN)
    xc, L, W = k["servo_xc"], p.SERVO_BODY_L, p.SERVO_BODY_W
    face = k["case_face"] + dz
    top = k["case_face"] + p.SERVO_BODY_H
    e1 = k["ears"] + p.SERVO_EAR_T
    rib_l = (p.SERVO_EAR_SPAN - L) / 2
    ribs = [Pos(xc + s * (L + rib_l) / 2, 0, k["ears"] - p.SERVO_EAR_RIB_H) * Box(rib_l, p.SERVO_EAR_RIB_W, p.SERVO_EAR_RIB_H, align=up) for s in (-1, 1)]
    return {
        "ear ribs": ribs[0] + ribs[1],
        "case below the ears": Pos(xc, 0, face) * Box(L, W, k["ears"] - face, align=up),
        "ears": Pos(xc, 0, k["ears"]) * Box(p.SERVO_EAR_SPAN, p.SERVO_EAR_W, p.SERVO_EAR_T, align=up),
        "case above the ears": Pos(xc, 0, e1) * Box(L, W, top - e1, align=up),
    }


def outline_points(sketch, step: float = 1.0) -> list:
    """Points every `step` mm along the edges of a sketch (its outline)."""
    pts = []
    for e in sketch.edges():
        n = max(2, int(e.length / step))
        pts += [e.position_at(i / n) for i in range(n)]
    return pts


def check_feed_assembly(assembly: dict) -> None:
    k = build.feed_layout()
    a = assembly
    for n, s in a.items():
        assert s.is_valid and len(s.solids()) == 1, f"{n} is not one valid solid"
    up = (Align.CENTER, Align.CENTER, Align.MIN)
    tol = p.FIT_TOLERANCE

    def overlap(m, n, what: str) -> None:
        v = (m & n).volume
        assert v < 1e-3, f"{what} overlap by {v:.3f} mm3"

    def clear(m, n, want: float, what: str) -> float:
        d = m.distance_to(n)
        assert d >= want - 1e-6, f"{what}: only {d:.3f} apart, want {want}"
        return d

    names = list(a)
    for i, m in enumerate(names):
        for n in names[i + 1 :]:
            overlap(a[m], a[n], f"{m} and {n}")
    for n in ("cover", "chimney", "hopper", "bracket"):  # It lies on the base.
        clear(a["disc"], a[n], tol, f"disc and {n}")
    # The disc's rim clears the shroud all round (outside the exit, where the shroud opens).
    r = k["shroud_r"]
    for deg in range(0, 360, 5):
        c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        if not solid_at(a["base"], (r + EPS) * c, (r + EPS) * s, k["floor"] + 1):
            continue  # The channel.
        assert not solid_at(a["base"], (r - EPS) * c, (r - EPS) * s, k["floor"] + 1), f"shroud inside R{r} at {deg}"

    # Drive: the boss slides in the socket. Servo FEED_SERVO_TRAVEL_Z low, the boss still clears the
    # socket's top (the screw-head chamber) and the piece clears the cover; high, it still goes
    # FEED_DRIVE_MIN_ENGAGE in. The hex holds the piece on the disc axis: it only moves up and down.
    tz, tx, play = p.FEED_SERVO_TRAVEL_Z, p.FEED_SERVO_TRAVEL_X, k["ear_play"]
    engage = k["boss_top"] - k["drive_bottom"]
    assert abs(engage - p.FEED_DRIVE_ENGAGE) < 1e-9
    assert p.FEED_DRIVE_FLOAT > tz, f"servo {tz} low would bottom the boss in the socket (float {p.FEED_DRIVE_FLOAT})"
    assert engage - tz >= p.FEED_DRIVE_MIN_ENGAGE, f"servo {tz} high, the boss is only {engage - tz:.1f} in"
    assert p.SERVO_HORN_GAP >= p.FEED_HORN_HUB_H, "the horn's hub does not fit between the case and the drive piece"
    drive_min = {}
    for dz in (-tz, 0, tz):
        d = Pos(0, 0, dz) * a["drive"]
        overlap(d, a["disc"], f"drive {dz:+g} high and disc")
        for n in ("cover", "chimney"):
            drive_min[n] = min(drive_min.get(n, 1e9), clear(d, a[n], p.FEED_RUN_GAP, f"drive {dz:+g} high and {n}"))
        for bx in (-tx, 0, tx):
            g = clear(d, Pos(bx, 0, 0) * a["bracket"], p.FEED_RUN_GAP, f"drive and bracket at {bx:+g}")
            drive_min["bracket"] = min(drive_min.get("bracket", 1e9), g)

    # The bracket slides FEED_SERVO_TRAVEL_X either way along its slots: its pegs stay in them, and
    # it stays clear of the chimney.
    bracket_min = 1e9
    for bx in (-tx, tx):
        b = Pos(bx, 0, 0) * a["bracket"]
        overlap(b, a["base"], f"bracket at {bx:+g} and base")
        overlap(b, a["cover"], f"bracket at {bx:+g} and cover")
        for n in ("chimney", "hopper"):
            bracket_min = min(bracket_min, clear(b, a[n], tol, f"bracket at {bx:+g} and {n}"))
    # The servo, wherever the unmeasured numbers put it: along the servo with the bracket (the spline
    # offset), the ear holes' play both ways on the bracket, and the case below the ears up or down.
    servo_min = {}
    for bx in (-tx, 0, tx):
        b = Pos(bx, 0, 0) * a["bracket"]
        for px in (-play, play):
            for py in (-play, play):
                for dz in (-tz, tz):
                    for part, box in servo_model(k, dz).items():
                        s = Pos(bx + px, py, 0) * box
                        for n in ("chimney", "cover"):
                            g = clear(s, a[n], tol, f"servo {part} ({bx + px:+.2f}, {py:+.2f}, {dz:+g}) and {n}")
                            servo_min[n] = min(servo_min.get(n, 1e9), g)
                        if part != "ears":  # The ears rest on the shelf.
                            g = clear(s, b, tol, f"servo {part} and its bracket")
                            servo_min["bracket"] = min(servo_min.get("bracket", 1e9), g)
    # The ear pilot holes sit on the measured pitch.
    z = k["ears"] - p.FEED_BRACKET_T / 2
    for ex in (k["servo_xc"] - p.SERVO_EAR_PITCH_L / 2, k["servo_xc"] + p.SERVO_EAR_PITCH_L / 2):
        for ey in (-p.SERVO_EAR_PITCH_W / 2, p.SERVO_EAR_PITCH_W / 2):
            r = p.FEED_SELF_TAP_D / 2
            assert not solid_at(a["bracket"], ex, ey, z), f"no ear hole at ({ex:.2f}, {ey:.2f})"
            for q in ((r + EPS, 0), (-r - EPS, 0), (0, r + EPS), (0, -r - EPS)):
                assert solid_at(a["bracket"], ex + q[0], ey + q[1], z), f"ear hole at ({ex:.2f}, {ey:.2f}) too big"

    # Seal: no BB (BB_MIN_D) gets from the pile to the inside of the chimney, nor to the elbow.
    rb = p.BB_MIN_D / 2
    t = p.FEED_CHIMNEY_T
    foot = build.feed_chimney_footprint(tol, k["block_top"] - 1, p.FEED_COVER_T + 2)
    (ho, hi) = build.feed_hopper_rects()
    for skew in p.FEED_CUTOFF_SKEWS:
        w = build.feed_window(skew)
        v = (w & foot).volume
        assert v < 1e-3, f"window {skew} runs under the chimney ({v:.2f} mm3)"
        bb = w.bounding_box()
        assert hi[0] < bb.min.X and bb.max.X < hi[2] and hi[1] < bb.min.Y and bb.max.Y < hi[3], "window outside the hopper"
    assert k["hole_r"] + tol < k["ch_in_r_drive"], "the hub hole is not inside the chimney"
    for y in p.FEED_PEG_YS:
        assert abs(y) + p.FEED_PEG_W / 2 + tol < k["ch_in_y_low"], "a peg slot is outside the chimney"
    for n in ("elbow_a", "elbow_b"):
        assert a[n].bounding_box().min.Y > ho[3], f"{n} is in the hopper"
    assert p.FEED_CABLE_W < p.BB_MIN_D - tol, "the cable notch lets a BB through"
    barrier = a["chimney"] + a["hopper"] + a["cover"]

    def blocked(q) -> bool:
        return barrier.distance_to(Vector(q.X, q.Y, q.Z)) < rb

    n_probe = 0
    # (1) The walls are whole: the middle of the chimney's wall (narrow part, and wide part over the
    # flare) and of the hopper's is solid on a 3 mm grid, from inside their grooves in the cover up to
    # the pile top. Any hole a BB could pass holds a point of that grid.
    assert k["ch_bottom"] < k["cover_top"] and k["hop_bottom"] < k["cover_top"], "a wall does not sit in a groove"
    assert k["ch_top"] > k["hop_top"], "the pile can spill over the chimney"
    step = 3.0
    z0 = k["cover_top"] - p.FEED_HOPPER_SEAT / 2

    def zs(lo: float, hi_: float) -> list:
        return [lo + step * j for j in range(int((hi_ - lo) / step) + 1)]

    mid = build._rect((ho[0] + hi[0]) / 2, (ho[1] + hi[1]) / 2, (ho[2] + hi[2]) / 2, (ho[3] + hi[3]) / 2)
    walls = (
        ("chimney", build.chimney_plan(t / 2), zs(z0, k["ch_z_a"])),
        ("chimney", build.chimney_plan(t / 2, up=True), zs(k["ch_z_b"], k["hop_top"])),
        ("hopper", mid, zs(z0, k["hop_top"])),
    )
    for n, plan, heights in walls:
        for q in outline_points(plan, step):
            for zz in heights:
                assert a[n].is_inside(Vector(q.X, q.Y, zz)), f"hole in the {n} at ({q.X:.1f}, {q.Y:.1f}, {zz:.1f})"
                n_probe += 1
    # The flare: the middle of the wall moves out linearly from the narrow part to the wide one
    # (sampled on its flat faces).
    za, zb = k["ch_z_a"], k["ch_z_b"]
    for zz in zs(za + 0.5, zb - 0.5):
        f = (zz - za) / (zb - za)
        x0 = k["ch_in_x0_low"] + f * (k["ch_in_x0_up"] - k["ch_in_x0_low"]) - t / 2
        y1 = k["ch_in_y_low"] + f * (k["ch_in_y_up"] - k["ch_in_y_low"]) + t / 2
        x1 = k["ch_in_x1"] + t / 2
        pts = [(x0, y) for y in zs(-y1 + t, y1 - t)] + [(x, s * y1) for x in zs(x0 + t, x1 - t) for s in (-1, 1)]
        pts += [(x1, y) for y in zs(-y1 + t, y1 - t)]
        for x, y in pts:
            assert a["chimney"].is_inside(Vector(x, y, zz)), f"hole in the chimney's flare at ({x:.1f}, {y:.1f}, {zz:.1f})"
            n_probe += 1
    # (2) Where the chimney's +X face meets the hopper's +X wall, top to bottom: a BB centred anywhere
    # in that joint touches one or the other.
    xj = (k["ch_x1"] + k["hop_x1_in"]) / 2
    hy = k["ch_in_y_up"] + t + 3
    for i in range(int(2 * hy) + 1):
        for zz in zs(k["cover_top"] + 0.3, k["hop_top"] - rb):
            assert blocked(Vector(xj, -hy + i, zz)), f"a BB gets between the chimney and the hopper at y={-hy + i:.0f}, z={zz:.0f}"
            n_probe += 1
    # (4) Inside the chimney, the cover is solid but for the hub hole (0.4 round the hub) and the peg
    # slots, which end in solid base.
    inside = build.chimney_plan(-tol)
    inner = Pos(0, 0, k["hop_bottom"] - 2) * extrude(inside, 0.1)
    bbi = inner.bounding_box()
    slot_x = p.FEED_PEG_L / 2 + tx + tol
    for ix in range(int(bbi.min.X) - 1, int(bbi.max.X) + 2):
        for iy in range(int(bbi.min.Y) - 1, int(bbi.max.Y) + 2):
            x, y, zc = float(ix), float(iy), k["hop_bottom"] - 1.95
            if not inner.is_inside(Vector(x, y, zc)) or solid_at(a["cover"], x, y, zc):
                continue
            hole = math.hypot(x, y) < k["hole_r"] + EPS
            peg = abs(x - k["peg_x"]) < slot_x + EPS and any(abs(y - py) < p.FEED_PEG_W / 2 + tol + EPS for py in p.FEED_PEG_YS)
            assert hole or peg, f"the cover is open inside the chimney at ({x}, {y})"
    for py in p.FEED_PEG_YS:
        assert solid_at(a["base"], k["peg_x"], py, k["peg_bottom"] - p.FEED_RUN_GAP - EPS), "peg slot through the base"
    assert k["hole_r"] - p.FEED_HUB_R < p.BB_MIN_D, "a BB fits round the hub"
    assert k["hop_top"] - k["cover_top"] >= 100, "hopper under 10 cm"
    # How many BBs the pile side holds at 10 cm: the hopper's inside less the chimney's outside, at
    # 64 % packing (random close packing of spheres).
    h10 = 100.0
    area = (hi[2] - hi[0]) * (hi[3] - hi[1]) - build.chimney_plan(t, up=True).area
    bbs = area * h10 * 0.64 / (math.pi / 6 * p.BB_D**3)
    corner_r = math.hypot(k["ch_x0"] + t, k["ch_in_y_low"]) + t + tol
    print(
        f"feed assembly: OK  no overlaps  drive: boss {engage:.1f} into the socket (float {p.FEED_DRIVE_FLOAT}), "
        f"{engage - tz:.1f} to {engage + tz:.1f} over servo height +-{tz:g}; bracket slides +-{tx:g} along the servo  "
        f"min gaps: drive to cover {drive_min['cover']:.2f}, chimney {drive_min['chimney']:.2f}, bracket {drive_min['bracket']:.2f}; "
        f"servo to chimney {servo_min['chimney']:.2f}, bracket {servo_min['bracket']:.2f}; bracket to chimney {bracket_min:.2f}"
    )
    print(
        f"feed seal: OK  window {p.FEED_WINDOW_ARC:g} deg, clear of the chimney (its narrow end's corners "
        f"{corner_r:.1f} from the axis)  {n_probe} probes: chimney and hopper walls whole on a 3 mm grid, "
        f"no BB through their joint  cable notch {p.FEED_CABLE_W:g}, hub gap {k['hole_r'] - p.FEED_HUB_R:.1f}  "
        f"pile {k['hop_top'] - k['cover_top']:.0f} over the cover (~{bbs:.0f} BBs at 10 cm), inlet {k['inlet']:.1f}"
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
        af, y = (p.FEED_HEX_AF + o) / 2, k["y_hex"]
        assert not solid_at(part, x + af - EPS, y, T / 2) and solid_at(part, x + af + EPS, y, T / 2), f"hex {o}"
    print(
        f"feed_coupon: OK  slot pockets {[round(p.FEED_SLOT_H + o, 2) for o in p.FEED_COUPON_SLOT_OFFSETS]}  "
        f"pin bores {[round(p.FEED_PIN_D + o, 2) for o in p.FEED_COUPON_PIN_OFFSETS]}  "
        f"hex {[round(p.FEED_HEX_AF + o, 2) for o in p.FEED_COUPON_HEX_OFFSETS]}"
    )


def check_feed_drive() -> None:
    """The 4 horn screws reach the horn straight from the bottom face: head and key fit up each well."""
    k = build.feed_layout()
    part = build.feed_drive()
    assert part.is_valid and len(part.solids()) == 1, "feed drive is not one valid solid"
    up = (Align.CENTER, Align.CENTER, Align.MIN)
    zb, rr = k["drive_bottom"], p.FEED_HORN_HOLE_CIRCLE / 2
    z_pl = zb + k["socket_depth"] + k["chamber_h"]  # Plate underside: the heads seat here.
    for i in range(4):
        a = math.radians(90 * i)
        x, y = rr * math.cos(a), rr * math.sin(a)
        head = Pos(x, y, zb - 1) * Cylinder(p.M3_HEAD_D / 2, z_pl - zb + 1 - EPS, align=up)
        v = (part & head).volume
        assert v < 1e-3, f"horn screw {i}: the head does not pass from below ({v:.3f} mm3 in the way)"
        assert not solid_at(part, x, y, z_pl + p.FEED_HUB_PLATE_T / 2), f"horn screw {i}: no hole in the plate"
    wall = k["drive_r"] - rr - k["well_r"]
    assert wall >= 0.8 - 1e-9, f"screw wells leave {wall:.2f} to the outside, under 2 perimeters"
    print(f"feed_drive: OK  4 screw wells d={2 * k['well_r']:.2f}, head d={p.M3_HEAD_D} passes from below, wall {wall:.2f}")


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
    check_corner_gauges()
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
    check_feed_drive()
    for skew in p.FEED_CUTOFF_SKEWS:
        assembly = build.feed_assembly(skew=skew)
        check_feed_cover(skew, assembly)
    check_feed_assembly(assembly)
    for radius in p.FEED_ELBOW_RADII:
        check_feed_elbow(radius)
    check_feed_print()
    print("all checks passed")
