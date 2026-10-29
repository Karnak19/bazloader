"""Build every part and export it as STL and STEP into out/.

Add a part: write a function returning a build123d shape, then add it to PARTS.
"""

import math
from pathlib import Path

from build123d import (
    Align,
    Axis,
    Box,
    Circle,
    Cone,
    Cylinder,
    Part,
    Plane,
    Polygon,
    Pos,
    Rectangle,
    RectangleRounded,
    RegularPolygon,
    Rot,
    SlotOverall,
    Sketch,
    Text,
    Torus,
    chamfer,
    export_step,
    export_stl,
    extrude,
    fillet,
    loft,
)

import params as p

OUT_DIR = Path(__file__).parent / "out"


def test_ring() -> Part:
    """Plain ring that should slide onto the inner barrel. M0 smoke test."""
    inner_d = p.BARREL_OD + p.FIT_TOLERANCE
    outer_d = inner_d + 2 * max(p.RING_WALL, p.MIN_WALL)
    return Cylinder(outer_d / 2, p.RING_HEIGHT) - Cylinder(inner_d / 2, p.RING_HEIGHT)


def collar_layout() -> dict[str, float]:
    """Key positions of the IR collar, shared by ir_collar() and check.py.

    Frame: the tube axis is Z, the collar sits on Z=0 (its print face). From Z=0 up:
    the bottom grip bore, the ring (BB guide, beam at its mid-height), the top grip
    bore. The beam runs along X, BEAM_OFFSET off the axis on -Y; the clamp slots and
    screws are on +Y, away from it.
    """
    bore_r = (p.BARREL_OD + p.FIT_TOLERANCE) / 2  # Grip bores, one per barrel half.
    guide_r = p.BB_GUIDE_D / 2
    led_r = (p.IR_LED_DIAMETER + p.SOCKET_TOLERANCE) / 2
    photo_r = (p.PHOTOTRANSISTOR_DIAMETER + p.SOCKET_TOLERANCE) / 2
    socket_r = max(led_r, photo_r)
    beam_y = -p.BEAM_OFFSET
    # Off-axis, the guide surface along the beam is at sqrt(guide_r^2 - y^2), furthest out where y is
    # nearest the axis. Measured at the socket edge nearest the axis (wider than the window), the
    # wall in front of each shoulder is at least APERTURE_LEN everywhere.
    near_y = max(0.0, abs(beam_y) - socket_r)
    shoulder_x = math.sqrt(guide_r**2 - near_y**2) + p.APERTURE_LEN  # Both stop shoulders sit at this |X|.
    # On a thick barrel, push the sockets out so the wire grooves on the back faces keep MIN_WALL
    # to the grip bore (the window just gets longer).
    groove_y = max(0.0, abs(beam_y) - p.WIRE_CHANNEL_W / 2)  # Groove edge nearest the axis.
    groove_x = math.sqrt((bore_r + p.MIN_WALL) ** 2 - groove_y**2) + p.WIRE_CHANNEL_DEPTH
    shoulder_x = max(shoulder_x, groove_x - p.SOCKET_DEPTH)
    nut_r = (p.M3_NUT_AF + p.NUT_TOLERANCE) / math.sqrt(3)  # Hexagon corner radius.
    screw_y = bore_r + p.MIN_WALL + nut_r  # Nut trap clears the bore by MIN_WALL.
    ring_z0 = p.GRIP_LENGTH
    ring_z1 = p.GRIP_LENGTH + p.BARREL_GAP
    length = ring_z1 + p.GRIP_LENGTH
    return {
        "bore_r": bore_r,
        "guide_r": guide_r,
        "outer_r": bore_r + p.COLLAR_WALL,
        "length": length,
        "ring_z0": ring_z0,  # Shoulder the bottom half stops on.
        "ring_z1": ring_z1,  # Shoulder the top half stops on.
        "beam_z": (ring_z0 + ring_z1) / 2,
        "beam_y": beam_y,
        "led_r": led_r,  # LED socket, on -X.
        "photo_r": photo_r,  # Phototransistor socket, on +X.
        "socket_r": socket_r,
        "shoulder_x": shoulder_x,
        "back_x": shoulder_x + p.SOCKET_DEPTH,  # Back face, where the leads come out.
        "bar_hw": max(socket_r + p.SOCKET_WALL, p.WIRE_CHANNEL_W / 2 + p.MIN_WALL),
        "nut_r": nut_r,
        "screw_y": screw_y,
        "screw_z": (p.GRIP_LENGTH / 2, length - p.GRIP_LENGTH / 2),  # One screw per grip, at mid-grip.
        "ear_y": screw_y + nut_r + p.MIN_WALL,  # Outer face of the clamp ears.
        "ear_hx": p.CLAMP_SLOT / 2 + p.M3_NUT_THICKNESS + p.NUT_TOLERANCE + p.MIN_WALL,
        "channel_top": (ring_z0 + ring_z1) / 2 - socket_r - p.MIN_WALL / 2,
    }


def _yz_plane(x: float, y: float, z: float, into: float) -> Plane:
    """Plane facing along X (into = +1 or -1), local x = global Y."""
    return Plane(origin=(x, y, z), x_dir=(0, 1, 0), z_dir=(into, 0, 0))


def ir_collar() -> Part:
    """Sleeve that joins the two halves of the cut barrel and holds the IR LED and phototransistor.

    Each end is a grip bore for one barrel half, closed by its own C-clamp (slot on +Y,
    one M3 screw through two ears, nut in a trap). Between them, a closed ring: its faces
    are the stops both halves butt against, its bore guides the BBs across the gap, and
    the beam crosses it through the sockets' window. The slots stop at the ring, so the
    screws never squeeze the BB guide. One piece, so both sockets come out of the same
    print layers and stay coaxial. Print it standing on its end face (Z=0): every hole
    across the tube is then horizontal and small, the nut traps have a corner on top,
    and the ring overhang is short, so no supports.
    """
    assert p.SOCKET_DEPTH < p.IR_BODY_LENGTH, "the flange would hit the back before the shoulder"
    k = collar_layout()
    assert max(p.APERTURE_D, p.APERTURE_W) < 2 * min(k["led_r"], k["photo_r"]) - p.SOCKET_TOLERANCE, (
        "the aperture must be narrower than the component, or there is no shoulder to stop it"
    )
    assert k["channel_top"] > p.MIN_WALL, "collar too short for the wire channels"
    assert p.BEAM_OFFSET + p.APERTURE_W / 2 < k["guide_r"], "the window pokes past the BB guide"
    assert p.BARREL_ID < p.BB_GUIDE_D < p.BARREL_OD, "BB guide must be over the barrel bore, under its OD"
    assert k["guide_r"] + p.RING_CHAMFER < k["bore_r"], "chamfer eats the whole shoulder"
    assert p.BARREL_GAP / 2 >= k["socket_r"] + p.SOCKET_WALL - 1e-9, "sockets break into the grip bores"
    L, z0, y0 = k["length"], k["beam_z"], k["beam_y"]

    # Outer outline, seen from above: ring + bar holding the sockets (on the beam line) + clamp ears.
    outline = (
        Circle(k["outer_r"])
        + Pos(0, y0) * Rectangle(2 * k["back_x"], 2 * k["bar_hw"])
        + Pos(0, k["ear_y"] / 2) * Rectangle(2 * k["ear_hx"], k["ear_y"])
    )
    # Round the outer corners only: those where the ring meets the bar or the ears are concave,
    # not sharp in the hand, and the short edges next to them make the 2D fillet fail.
    corners = [v for v in outline.vertices() if abs(math.hypot(v.X, v.Y) - k["outer_r"]) > 1e-6]
    outline = fillet(corners, p.EDGE_FILLET)
    body = extrude(outline, L)

    # BB guide through the whole length, then a grip bore and a clamp slot from each end up to
    # the ring. The slots stop at the ring, so it stays a closed circle whatever the screws do.
    body -= Pos(0, 0, -1) * Cylinder(k["guide_r"], L + 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    c = p.RING_CHAMFER
    for z_start, z_ring, up in ((-1, k["ring_z0"], 1), (L + 1, k["ring_z1"], -1)):
        grip = abs(z_ring - z_start)
        z_mid = (z_start + z_ring) / 2
        body -= Pos(0, 0, z_mid) * Cylinder(k["bore_r"], grip)
        body -= Pos(0, k["ear_y"] / 2, z_mid) * Box(p.CLAMP_SLOT, k["ear_y"] + 1, grip)
        # 45 deg chamfer on the guide edge: radius guide_r + c at the ring face, guide_r c into the ring.
        cone = Cone(k["guide_r"] + c + 0.01, k["guide_r"] - 0.01, c + 0.02)
        body -= Pos(0, 0, z_ring + up * (c / 2 + 0.005)) * (cone if up > 0 else Rot(180, 0, 0) * cone)

    # Sockets: LED on -X, phototransistor on +X, both on the beam line y0, open at the back.
    # Each ends on a flat shoulder at shoulder_x, the same on both sides.
    socket_len = p.SOCKET_DEPTH + 1  # Runs 1 mm past the back face for a clean cut.
    for side, r in ((-1, k["led_r"]), (1, k["photo_r"])):
        x_mid = side * (k["shoulder_x"] + socket_len / 2)
        body -= Pos(x_mid, y0, z0) * Rot(0, 90, 0) * Cylinder(r, socket_len)

    # Aperture: one window straight through both sides of the ring, so the two cannot drift apart.
    # It is a chord of the BB guide.
    if p.APERTURE_W > p.APERTURE_D:
        window = SlotOverall(p.APERTURE_W, p.APERTURE_D)
    else:
        window = Circle(p.APERTURE_D / 2)
    reach = k["shoulder_x"] + 0.5
    body -= extrude(_yz_plane(-reach, y0, z0, 1) * window, 2 * reach)

    # Wire channels: a groove on each back face, from under the socket to the bottom end.
    for side in (-1, 1):
        x = side * (k["back_x"] - p.WIRE_CHANNEL_DEPTH / 2)
        h = k["channel_top"] + 1
        body -= Pos(x, y0, h / 2 - 1) * Box(p.WIRE_CHANNEL_DEPTH + 0.01, p.WIRE_CHANNEL_W, h)

    # One M3 screw across the ears of each clamp, head on -X, nut trapped in the +X ear.
    ear_span = 2 * k["ear_hx"] + 2
    nut_depth = p.M3_NUT_THICKNESS + p.NUT_TOLERANCE
    # rotation=90 puts a hexagon corner on top (+Z), so the pocket roof prints without support.
    hexagon = RegularPolygon(k["nut_r"], 6, rotation=90)
    for zs in k["screw_z"]:
        body -= Pos(0, k["screw_y"], zs) * Rot(0, 90, 0) * Cylinder(p.M3_CLEARANCE / 2, ear_span)
        body -= extrude(_yz_plane(k["ear_hx"] + 1, k["screw_y"], zs, -1) * hexagon, nut_depth + 1)
    return body


def shaft_bore_profile(kind: str, offset: float) -> Sketch:
    """Cross-section of a hole for the encoder shaft, centred on the origin.

    kind "dflat": SHAFT_D + offset round, with the flat on +X at SHAFT_FLAT + offset
    from the opposite side. kind "round": a plain SHAFT_D + offset circle.
    """
    r = (p.SHAFT_D + offset) / 2
    if kind == "round":
        return Circle(r)
    assert kind == "dflat", f"unknown bore kind {kind!r}"
    flat_x = -r + p.SHAFT_FLAT + offset
    assert -r < flat_x < r, "SHAFT_FLAT must be smaller than SHAFT_D"
    w = flat_x + r + 1  # From 1 mm past the round side to the flat.
    return Circle(r) & Pos(flat_x - w / 2, 0) * Rectangle(w, 2 * r + 2)


def knob_layout() -> dict[str, float]:
    """Key sizes of the encoder knob, shared by encoder_knob() and check.py.

    Frame (print orientation): the axis is Z, the top face lies on Z=0 (the bed),
    the recess opens at Z=KNOB_HEIGHT and the bore goes down from the recess.
    """
    offset = p.SHAFT_TOLERANCE if p.KNOB_BORE == "dflat" else p.KNOB_PRESS_FIT
    bore_r = (p.SHAFT_D + offset) / 2
    nut_corner_r = p.ENCODER_NUT_AF / math.sqrt(3)
    # Pushed fully down, the shaft tip touches the bore end. The recess ceiling then
    # sits KNOB_SHAFT_GAP above the nut, and the skirt KNOB_PANEL_GAP above the panel.
    recess_depth = p.ENCODER_TOP_HEIGHT + p.KNOB_SHAFT_GAP - p.KNOB_PANEL_GAP
    bore_depth = p.SHAFT_FREE_LENGTH - p.KNOB_SHAFT_GAP
    recess_top = p.KNOB_HEIGHT - recess_depth  # Z of the recess ceiling (its floor while printing).
    return {
        "outer_r": p.KNOB_OD / 2,
        "bore_offset": offset,
        "bore_r": bore_r,
        "flat_x": -bore_r + p.SHAFT_FLAT + offset if p.KNOB_BORE == "dflat" else None,
        "bore_depth": bore_depth,
        "bore_end": recess_top - bore_depth,  # Z of the bore end, i.e. the cap thickness.
        "recess_r": nut_corner_r + p.KNOB_RECESS_CLEARANCE,
        "recess_depth": recess_depth,
        "recess_top": recess_top,
        "groove_r": (p.KNOB_RIDGE_WIDTH**2 / 4 + p.KNOB_RIDGE_DEPTH**2) / (2 * p.KNOB_RIDGE_DEPTH),
    }


def encoder_knob() -> Part:
    """Big ridged knob for the KY-040 encoder, to turn with gloves on.

    Print it top face down (Z=0 on the bed). The recess for the nut and the shaft
    bore both open upward, so every layer sits on the one below: no supports.
    The top-edge chamfer is a 45 deg slope at the bed, which also hides elephant's foot.
    """
    k = knob_layout()
    R, H = k["outer_r"], p.KNOB_HEIGHT
    assert k["bore_end"] >= p.MIN_WALL, "knob too short for the bore, the recess and a MIN_WALL cap: raise KNOB_HEIGHT"
    assert k["recess_depth"] > 0, "KNOB_PANEL_GAP leaves no recess"
    assert R - p.KNOB_RIDGE_DEPTH - k["recess_r"] >= p.MIN_WALL, "skirt wall too thin round the recess"
    pitch = 2 * math.pi * R / p.KNOB_RIDGES
    assert p.KNOB_RIDGE_WIDTH + 2 * p.KNOB_RIDGE_FILLET < pitch, "grooves too wide for their number"

    # Side: a circle with KNOB_RIDGES round grooves, every edge rounded.
    gr = k["groove_r"]
    outline = Circle(R)
    for i in range(p.KNOB_RIDGES):
        a = 2 * math.pi * i / p.KNOB_RIDGES
        d = R + gr - p.KNOB_RIDGE_DEPTH
        outline -= Pos(d * math.cos(a), d * math.sin(a)) * Circle(gr)
    outline = fillet(outline.vertices(), p.KNOB_RIDGE_FILLET)
    body = extrude(outline, H)

    # Top-edge chamfer: intersect with a cylinder chamfered at Z=0.
    blank = Cylinder(R + 0.01, H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    blank = chamfer(blank.edges().sort_by(Axis.Z)[0], p.KNOB_TOP_CHAMFER)
    body &= blank

    # Recess for the nut and bushing, open at Z=H.
    body -= Pos(0, 0, H) * Cylinder(k["recess_r"], 2 * k["recess_depth"])

    # Shaft bore, down from the recess ceiling, with a lead-in cone.
    profile = shaft_bore_profile(p.KNOB_BORE, k["bore_offset"])
    body -= Pos(0, 0, k["bore_end"]) * extrude(profile, k["bore_depth"] + 0.5)
    c = p.KNOB_BORE_CHAMFER
    body -= Pos(0, 0, k["recess_top"] - c) * Cone(
        k["bore_r"], k["bore_r"] + c + 0.01, c + 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    return body


def coupon_layout() -> dict[str, float]:
    """Row positions of the fit coupon, shared by fit_coupon() and check.py.

    From +Y to -Y: socket rib, socket labels, barrel bores, their labels, BB guide
    bores, their labels, then a thicker strip with the D-flat knob bores, their labels,
    the round ones, their labels.
    """
    gap, text = p.COUPON_GAP, p.COUPON_TEXT_SIZE
    bore_d = p.BARREL_OD + max(p.COUPON_BORE_OFFSETS)
    knob_d = p.SHAFT_D + max(p.COUPON_SHAFT_OFFSETS + p.COUPON_PRESS_OFFSETS)
    row = knob_d / 2 + gap / 2 + text / 2  # From a knob bore row to its label row.
    bore_label_y = -(bore_d / 2 + gap / 2 + text / 2)
    guide_d = p.BB_GUIDE_D + max(p.COUPON_GUIDE_OFFSETS)
    guide_y = bore_label_y - text / 2 - gap / 2 - guide_d / 2
    guide_label_y = guide_y - guide_d / 2 - gap / 2 - text / 2
    strip_y = guide_label_y - text / 2 - gap / 2
    dflat_y = strip_y - gap / 2 - knob_d / 2
    press_y = dflat_y - 2 * row  # Below the D-flat labels.
    socket_label_y = bore_d / 2 + gap / 2 + text / 2
    rib_y0 = socket_label_y + text / 2 + gap / 2
    return {
        "width": (bore_d + gap) * len(p.COUPON_BORE_OFFSETS) + gap,
        "bore_d": bore_d,
        "bore_y": 0.0,
        "bore_label_y": bore_label_y,
        "guide_y": guide_y,
        "guide_label_y": guide_label_y,
        "socket_label_y": socket_label_y,
        "rib_y0": rib_y0,
        "strip_y": strip_y,  # The knob strip covers everything below this.
        "dflat_y": dflat_y,
        "press_y": press_y,
        "knob_label_dy": row,  # Each knob label sits this far below its hole.
        "y_min": press_y - row - text / 2 - gap / 2,
        "y_max": rib_y0 + p.SOCKET_DEPTH,
    }


def fit_coupon() -> Part:
    """Thin plate to print first: test holes for every fit, at several tolerances.

    Each hole is labelled with the offset it adds. Slide it on the barrel, push in the
    IR components and the encoder shaft, then copy the best offsets into FIT_TOLERANCE,
    SOCKET_TOLERANCE, SHAFT_TOLERANCE and KNOB_PRESS_FIT. Drop a BB through the BB
    guide row: it must fall through the 0 hole freely, or BB_GUIDE_D goes up.
    The socket holes are horizontal, in a rib, like in the printed collar. The knob
    bores are vertical, in a thicker strip, like in the knob.
    """
    t, text = p.COUPON_THICKNESS, p.COUPON_TEXT_SIZE
    k = coupon_layout()
    width, y_min, y_max, rib_y0 = k["width"], k["y_min"], k["y_max"], k["rib_y0"]
    sockets = [p.IR_LED_DIAMETER + o for o in p.COUPON_SOCKET_OFFSETS]
    rib_h = max(sockets) + 2 * p.MIN_WALL
    tk = p.COUPON_KNOB_THICKNESS

    outline = Pos(0, (y_min + y_max) / 2) * Rectangle(width, y_max - y_min)
    outline = fillet(outline.vertices(), p.EDGE_FILLET)
    rib_outline = outline & Pos(0, (rib_y0 + y_max) / 2 + 1) * Rectangle(width + 2, y_max - rib_y0 + 2)
    strip_outline = outline & Pos(0, (y_min + k["strip_y"]) / 2 - 1) * Rectangle(width + 2, k["strip_y"] - y_min + 2)
    part = extrude(outline, t) + extrude(rib_outline, rib_h) + extrude(strip_outline, tk)

    def label(value: float) -> str:
        return "0" if abs(value) < 1e-9 else f"{value:+.1f}".replace("0.", ".")

    def engrave(s: str, x: float, y: float, top: float = t) -> Part:
        return Pos(x, y, top - p.COUPON_TEXT_DEPTH) * extrude(Text(s, text), p.COUPON_TEXT_DEPTH + 0.1)

    x0 = -width / 2 + p.COUPON_GAP + k["bore_d"] / 2
    pitch = k["bore_d"] + p.COUPON_GAP
    for i, offset in enumerate(p.COUPON_BORE_OFFSETS):
        x = x0 + i * pitch
        part -= Pos(x, k["bore_y"], t / 2) * Cylinder((p.BARREL_OD + offset) / 2, t + 1)
        part -= engrave(label(offset), x, k["bore_label_y"])

    # BB guide bores: vertical, like the ring in the collar printed standing.
    for i, offset in enumerate(p.COUPON_GUIDE_OFFSETS):
        x = -width / 2 + width / len(p.COUPON_GUIDE_OFFSETS) * (i + 0.5)
        part -= Pos(x, k["guide_y"], t / 2) * Cylinder((p.BB_GUIDE_D + offset) / 2, t + 1)
        part -= engrave(label(offset), x, k["guide_label_y"])

    s_pitch = width / len(sockets)
    for i, (d, offset) in enumerate(zip(sockets, p.COUPON_SOCKET_OFFSETS)):
        x = -width / 2 + s_pitch * (i + 0.5)
        hole_len = p.SOCKET_DEPTH + 2
        part -= Pos(x, (rib_y0 + y_max) / 2, rib_h / 2) * Rot(90, 0, 0) * Cylinder(d / 2, hole_len)
        part -= engrave(label(offset), x, k["socket_label_y"])

    # Knob bores: D-flat ones (flat on +X) then round press-fit ones, through the strip.
    for kind, y, offsets in (
        ("dflat", k["dflat_y"], p.COUPON_SHAFT_OFFSETS),
        ("round", k["press_y"], p.COUPON_PRESS_OFFSETS),
    ):
        for i, offset in enumerate(offsets):
            x = -width / 2 + width / len(offsets) * (i + 0.5)
            part -= Pos(x, y, -0.5) * extrude(shaft_bore_profile(kind, offset), tk + 1)
            part -= engrave(label(offset), x, y - k["knob_label_dy"], tk)
    return part


def box_lower(z: float) -> tuple[float, float]:
    """Interior length and width of the box's lower part (under the ledge) at height z, from its draft."""
    return p.BOX_FLOOR_L + p.BOX_TAPER_L * z, p.BOX_FLOOR_W + p.BOX_TAPER_W * z


def box_interior(z: float) -> tuple[float, float]:
    """Interior length and width of the Plano box at height z above its floor (the walls lean out).

    Above the top of the ledge (z >= BOX_LEDGE_Z1), the wide upper part; under it, the narrower
    lower part. On the sloped ledge itself the lower part is returned, the safe (narrower) answer.
    """
    l, w = box_lower(z)
    if z >= p.BOX_LEDGE_Z1:
        return l + 2 * p.BOX_STEP_L, w + 2 * p.BOX_STEP_W
    return l, w


def seat_layout() -> dict[str, float]:
    """Outline of a part resting on the box ledge: ledge_gauge now, the top plate (#18) later.

    Box frame: floor at Z=0, interior centred on X=0, Y=0, X along the length. The part's
    underside is at z = BOX_LEDGE_Z1. Outside: SEAT_L x SEAT_W with SEAT_CORNER_R corners, sized
    for the box corners. Inside: the lower part there minus SEAT_INSET per side, so it covers the
    whole step.
    """
    low_l, low_w = box_lower(p.BOX_LEDGE_Z1)
    return {
        "z": p.BOX_LEDGE_Z1,
        "outer_l": p.SEAT_L,
        "outer_w": p.SEAT_W,
        "corner_r": p.SEAT_CORNER_R,
        "inner_l": low_l - 2 * p.SEAT_INSET,
        "inner_w": low_w - 2 * p.SEAT_INSET,
    }


def floor_layout() -> dict[str, float]:
    """Outline of floor_gauge, in the box frame: on the floor (z=0), WALL_CLEARANCE off every wall."""
    box_l, box_w = box_interior(0.0)
    outer_l, outer_w = box_l - 2 * p.WALL_CLEARANCE, box_w - 2 * p.WALL_CLEARANCE
    return {
        "z": 0.0,
        "outer_l": outer_l,
        "outer_w": outer_w,
        "corner_r": p.FLOOR_CORNER_R,
        "inner_l": outer_l - 2 * p.GAUGE_WALL,
        "inner_w": outer_w - 2 * p.GAUGE_WALL,
    }


def _mm(v: float) -> str:
    """228.0 -> "228", 235.64 -> "235.6"."""
    return f"{v:.1f}".removesuffix(".0")


def gauge_label(k: dict[str, float], name: str) -> str:
    return f"{name} {_mm(k['outer_l'])}x{_mm(k['outer_w'])}"


def box_gauge(k: dict[str, float], name: str) -> Part:
    """Thin closed frame: outer outline k["outer_l"] x k["outer_w"] with k["corner_r"] corners, hollow
    k["inner_l"] x k["inner_w"]. A tab inside the -Y long side carries the engraved name and outer
    size. Printed flat, Z=0 on the bed; in the box it sits at k["z"].
    """
    wall = min(k["outer_l"] - k["inner_l"], k["outer_w"] - k["inner_w"]) / 2
    assert wall >= p.MIN_WALL, f"{name} gauge wall only {wall:.2f}"
    inner_r = max(k["corner_r"] - wall, 1.0)
    outline = RectangleRounded(k["outer_l"], k["outer_w"], k["corner_r"]) - RectangleRounded(
        k["inner_l"], k["inner_w"], inner_r
    )
    label = Text(gauge_label(k, name), p.GAUGE_TEXT_SIZE)
    size = label.bounding_box().size
    tab_l, tab_w = size.X + 2 * p.GAUGE_TAB_MARGIN, size.Y + 2 * p.GAUGE_TAB_MARGIN
    assert tab_l < k["inner_l"] - 2 * inner_r and tab_w < k["inner_w"] / 2, f"{name} label too big for the frame"
    tab_y = -k["inner_w"] / 2 + tab_w / 2
    outline += Pos(0, tab_y - 0.5) * Rectangle(tab_l, tab_w + 1)  # Runs 1 mm into the wall, so they fuse.
    body = extrude(outline, p.GAUGE_HEIGHT)
    body -= Pos(0, tab_y, p.GAUGE_HEIGHT - p.GAUGE_TEXT_DEPTH) * extrude(label, p.GAUGE_TEXT_DEPTH + 0.1)
    return body


def floor_gauge() -> Part:
    """Frame the size of the box floor minus WALL_CLEARANCE: dropped on the floor, it lies flat, loose."""
    return box_gauge(floor_layout(), "FLOOR")


def ledge_gauge() -> Part:
    """Frame resting on the box ledge: the outline of the future top plate seat (#18)."""
    return box_gauge(seat_layout(), "LEDGE")


# --- Feed mechanism bench rig (#54, concept B) ----------------------------------------

COVER_VARIANTS = {("radial" if a == 0 else f"skew{a:g}"): a for a in p.FEED_CUTOFF_SKEWS}


def feed_layout() -> dict[str, float]:
    """Key positions of the feed bench rig, shared by every feed part and check.py.

    Rig frame: the table at Z=0, the disc axis on X=0, Y=0. The disc turns counter-clockwise
    seen from above. The strip point is on +X (angle 0): the exit channel leaves there along +Y,
    its axis on X = FEED_BB_CIRCLE_R, and the elbow stands at the end of it, outside the hopper.
    The servo hangs upside down over the disc, spline on the axis, body along +X, inside a closed
    chimney; a short drive piece on its horn slides over the hex boss on the disc's hub. The window
    ends FEED_CARRY_ARC before the strip point and wraps round the chimney's narrow -X end. The
    pile fills the hopper round the chimney; the chimney's +X face sits against the hopper's +X wall.
    """
    floor = p.FEED_BASE_T + p.MIN_WALL  # The elbow stands on the base plate with MIN_WALL under its bore.
    block_top = floor + p.FEED_SLOT_H  # = cover underside.
    cover_top = block_top + p.FEED_COVER_T
    pin_bore_r = (p.FEED_PIN_D + p.FEED_PIN_CLEARANCE) / 2
    pin_bore_depth = p.FEED_PIN_H + p.FEED_RUN_GAP
    hole_r = p.FEED_HUB_R + p.FEED_RUN_GAP  # Cover hole round the disc hub.
    # Drive: the piece's bottom clears the cover top even with the servo FEED_SERVO_TRAVEL_Z low.
    drive_bottom = cover_top + p.FEED_SERVO_TRAVEL_Z + p.FEED_RUN_GAP
    socket_depth = p.FEED_DRIVE_ENGAGE + p.FEED_DRIVE_FLOAT
    chamber_h = p.M3_HEAD_H + 0.5
    drive_h = socket_depth + chamber_h + p.FEED_HUB_PLATE_T + p.FEED_HORN_T
    horn_back = drive_bottom + drive_h  # Top of the drive piece: the horn sits in its recess.
    case_face = horn_back + p.SERVO_HORN_GAP  # Output face of the servo case (facing down).
    ears = case_face + p.SERVO_FACE_TO_EARS  # Underside of the ears = top of the bracket's shelf.
    ear_play = (p.SERVO_EAR_HOLE_D - p.M3_D) / 2  # The servo slides this far on loose ear screws.
    tol, tx = p.FIT_TOLERANCE, p.FEED_SERVO_TRAVEL_X
    drive_r = (p.FEED_HORN_D + tol) / 2 + p.FEED_DRIVE_RIM
    xc = p.SERVO_BODY_L / 2 - p.SERVO_SPLINE_OFFSET  # Middle of the servo body along X.
    case_x0, case_x1 = -p.SERVO_SPLINE_OFFSET, p.SERVO_BODY_L - p.SERVO_SPLINE_OFFSET
    ear_x0, ear_x1 = xc - p.SERVO_EAR_SPAN / 2, xc + p.SERVO_EAR_SPAN / 2
    # Bracket: a shelf ring round the case under the ears (rails beside the case, pads under the
    # ears), on one leg under the +X ears whose pegs key into the base. It slides tx along X.
    case_gap = ear_play + tol  # Room round the case in the shelf (the servo moves only by the ear play on it).
    shelf_bottom = ears - p.FEED_BRACKET_T
    rail_y = p.SERVO_BODY_W / 2 + case_gap  # Inner face of the rails.
    # Chimney, inside faces. Low down it hugs the case and the drive piece; from ch_z_b up it also
    # takes the ears, the shelf and the rails, all of them anywhere in their travel.
    in_y_low = p.SERVO_BODY_W / 2 + ear_play + tol  # Round the case; a round bulge takes the drive piece.
    leg_hy = in_y_low - tol  # The leg stands in the narrow part.
    in_y_up = rail_y + p.FEED_RAIL_W + tol
    in_x0_low = case_x0 - tx - ear_play - tol
    in_x0_up = ear_x0 - tx - ear_play - tol
    in_x1 = ear_x1 + tx + ear_play + tol
    ch_z_b = shelf_bottom - p.FEED_RAIL_H - tol
    flare = max(in_x0_low - in_x0_up, in_y_up - in_y_low) * 1.1  # A bit steeper than 45 deg.
    t = p.FEED_CHIMNEY_T
    # Hopper: a closed ring on the cover; its +X wall right behind the chimney's +X face.
    hop_out = p.FEED_BLOCK_HALF - p.MIN_WALL - tol  # Hopper outer half width on -X, -Y, +Y.
    hop_in = hop_out - p.FEED_HOPPER_WALL
    hop_x1_in = in_x1 + t + tol
    hop_x1_out = hop_x1_in + p.FEED_HOPPER_WALL
    return {
        "floor": floor,
        "disc_top": floor + p.FEED_DISC_T,
        "block_top": block_top,
        "cover_top": cover_top,
        "inlet": cover_top - floor,  # Inlet height over the floor the disc runs on.
        "disc_r": p.FEED_DISC_OD / 2,
        "notch_end_r": p.FEED_BB_CIRCLE_R - p.FEED_NOTCH_W / 2,
        "shroud_r": p.FEED_BB_CIRCLE_R + p.BB_D / 2 + p.FEED_SHROUD_GAP,
        "pin_bore_r": pin_bore_r,
        "pin_bore_depth": pin_bore_depth,
        "hub_round_top": cover_top,  # The hub is round up to the cover top, hex above.
        "boss_top": drive_bottom + p.FEED_DRIVE_ENGAGE,
        "boss_r": p.FEED_HEX_AF / math.sqrt(3),  # Corner radius of the boss.
        "hex_r": (p.FEED_HEX_AF + p.FEED_HEX_TOLERANCE) / math.sqrt(3),  # Corner radius of the hex sockets.
        "hole_r": hole_r,
        "cut": -p.FEED_CARRY_ARC,  # Cut-off edge angle.
        "start": -p.FEED_CARRY_ARC - p.FEED_WINDOW_ARC,  # Window start edge angle.
        "channel_x0": p.FEED_BB_CIRCLE_R - p.BB_GUIDE_D / 2,  # Channel inner wall = the tongue's edge.
        "channel_x1": p.FEED_BB_CIRCLE_R + p.BB_GUIDE_D / 2,
        "axis_z": floor + p.BB_GUIDE_D / 2,  # Channel and elbow bore axis: bore bottom on the floor.
        "tongue_bottom": floor + p.FEED_DISC_T + p.FEED_RUN_GAP,
        "drive_bottom": drive_bottom,
        "drive_r": drive_r,
        "drive_h": drive_h,
        "socket_depth": socket_depth,
        "chamber_r": p.FEED_HORN_HOLE_CIRCLE / 2 + p.M3_HEAD_D / 2 + tol,
        "chamber_h": chamber_h,
        "horn_back": horn_back,
        "case_face": case_face,
        "ears": ears,
        "ear_play": ear_play,
        "case_x0": case_x0,
        "case_x1": case_x1,
        "servo_xc": xc,
        "case_gap": case_gap,
        "shelf_x0": ear_x0,
        "shelf_x1": ear_x1,
        "shelf_bottom": shelf_bottom,
        "rail_y": rail_y,
        "leg_x0": case_x1 + case_gap,
        "leg_x1": ear_x1,
        "leg_hy": leg_hy,
        "peg_x": (case_x1 + case_gap + ear_x1) / 2,
        "peg_bottom": block_top - p.FEED_PEG_DEPTH,
        "ch_in_x0_low": in_x0_low,
        "ch_in_x0_up": in_x0_up,
        "ch_in_x1": in_x1,
        "ch_in_y_low": in_y_low,
        "ch_in_y_up": in_y_up,
        "ch_in_r_drive": drive_r + p.FEED_RUN_GAP,  # The bulge round the drive piece, up to ch_z_b.
        "ch_bottom": cover_top - p.FEED_HOPPER_SEAT,
        "ch_z_a": ch_z_b - flare,  # The flare runs from here...
        "ch_z_b": ch_z_b,  # ...to here.
        "ch_top": cover_top + p.FEED_PILE_H + p.FEED_CHIMNEY_ABOVE,
        # The chimney's footprint on the cover, outside (corners rounded to t): the window stays out of it.
        "ch_x0": in_x0_low - t,
        "ch_x1": in_x1 + t,
        "ch_hy": max(in_y_low, drive_r + p.FEED_RUN_GAP) + t,
        "hop_out": hop_out,
        "hop_in": hop_in,
        "hop_x1_in": hop_x1_in,
        "hop_x1_out": hop_x1_out,
        "hop_bottom": cover_top - p.FEED_HOPPER_SEAT,
        "hop_top": cover_top + p.FEED_PILE_H,
        "block_x1": hop_x1_out + tol + p.MIN_WALL,  # Base block and cover, +X edge.
        "screw_xy": p.FEED_BLOCK_HALF - p.FEED_COVER_SCREW_INSET,  # Cover screws at (+-, +-) this.
    }


def on_bed(part: Part, flip: bool = False) -> Part:
    """Print orientation: optionally upside down (flip), then centred on X/Y and set on Z=0."""
    if flip:
        part = Rot(180, 0, 0) * part
    bb = part.bounding_box()
    return Pos(-bb.center().X, -bb.center().Y, -bb.min.Z) * part


def _hex(r: float) -> Sketch:
    """Hexagon of corner radius r, flats on +-X."""
    return RegularPolygon(r, 6, rotation=30)


def feed_disc() -> Part:
    """Pocket disc: FEED_POCKETS U-notches open at the rim, lying on the base floor.

    Raised hub in the middle: a bore underneath for the centre pin (its bearing), round up to the
    cover top, then a hex boss the drive piece slides over. Printed as it sits, flat on the bed: the
    notch walls and the boss are vertical, the pin bore ends in a 45 deg cone, so no supports.
    """
    k = feed_layout()
    z0, t = k["floor"], p.FEED_DISC_T
    up = (Align.CENTER, Align.CENTER, Align.MIN)
    disc = Pos(0, 0, z0) * Cylinder(k["disc_r"], t, align=up)
    disc += Pos(0, 0, z0) * Cylinder(p.FEED_HUB_R, k["hub_round_top"] - z0, align=up)
    boss = Pos(0, 0, k["hub_round_top"] - 0.01) * extrude(_hex(k["boss_r"]), k["boss_top"] - k["hub_round_top"] + 0.01)
    disc += chamfer(boss.faces().sort_by(Axis.Z)[-1].edges(), 0.5)  # Lead-in into the socket.
    R, w = p.FEED_BB_CIRCLE_R, p.FEED_NOTCH_W
    notch = Pos(R, 0) * Circle(w / 2) + Pos(R + 10, 0) * Rectangle(20, w)
    for i in range(p.FEED_POCKETS):
        disc -= Pos(0, 0, z0 - 1) * extrude(Rot(0, 0, i * 360 / p.FEED_POCKETS) * notch, t + 2)
    r, d = k["pin_bore_r"], k["pin_bore_depth"]
    disc -= Pos(0, 0, z0 - 1) * Cylinder(r, d + 1, align=up)
    disc -= Pos(0, 0, z0 + d) * Cone(r, 0, r, align=up)
    c = p.BED_HOLE_CHAMFER
    disc -= Pos(0, 0, z0 - 0.01) * Cone(r + c + 0.01, r, c + 0.01, align=up)  # Lead-in, eats elephant's foot.
    return disc


def feed_drive() -> Part:
    """Drive piece screwed to the servo horn, sliding over the hex boss on the disc's hub.

    From the top: the recess the round horn sits in, a plate with the 4 horn holes and a hole for
    the head of the spline screw, a chamber for the 4 screw heads, then the hex socket, as deep as
    FEED_DRIVE_ENGAGE + FEED_DRIVE_FLOAT so the servo height does not matter. The screws go in
    through the socket, up into the horn's threads. Printed socket down, as it sits: the only
    overhang is the chamber ceiling, a short bridge (documented in the README).
    """
    k = feed_layout()
    up = (Align.CENTER, Align.CENTER, Align.MIN)
    zb, zt = k["drive_bottom"], k["horn_back"]
    piece = Pos(0, 0, zb) * Cylinder(k["drive_r"], k["drive_h"], align=up)
    piece -= Pos(0, 0, zb - 1) * extrude(_hex(k["hex_r"]), k["socket_depth"] + 1)
    c = p.BED_HOLE_CHAMFER  # Lead-in on the socket mouth, on the bed: eats elephant's foot.
    piece -= Pos(0, 0, zb - 0.01) * extrude(_hex(k["hex_r"] + c / math.cos(math.pi / 6)), c + 0.01, taper=45)
    z_ch = zb + k["socket_depth"]
    piece -= Pos(0, 0, z_ch) * Cylinder(k["chamber_r"], k["chamber_h"], align=up)
    z_pl = z_ch + k["chamber_h"]
    holes = Circle(p.FEED_HORN_SCREW_HEAD_D / 2)
    for i in range(4):
        a = math.radians(45 + 90 * i)
        rr = p.FEED_HORN_HOLE_CIRCLE / 2
        holes += Pos(rr * math.cos(a), rr * math.sin(a)) * Circle(p.FEED_HORN_HOLE_D / 2)
    piece -= Pos(0, 0, z_pl - 0.5) * extrude(holes, p.FEED_HUB_PLATE_T + 1)
    piece -= Pos(0, 0, zt - p.FEED_HORN_T) * Cylinder(
        (p.FEED_HORN_D + p.FIT_TOLERANCE) / 2, p.FEED_HORN_T + 1, align=up
    )
    return piece


def feed_edge(theta: float, skew: float, side: int) -> list[tuple[float, float]]:
    """One window edge, from the centre out: [inner point, joint, outer point].

    The outer part is a straight line through the BB circle at angle theta, tilted skew degrees
    from radial with its outer end set back toward the window, so the edge pushes a BB inward,
    toward the land, rather than out against the shroud. Inside FEED_EDGE_JOINT_R it turns radial.
    side=+1: the cut-off edge (window on its clockwise side); -1: the start edge (mirror).
    """
    k = feed_layout()
    t, a, R = math.radians(theta), math.radians(skew), p.FEED_BB_CIRCLE_R
    rh, th = (math.cos(t), math.sin(t)), (-math.sin(t), math.cos(t))
    d = tuple(rh[i] * math.cos(a) - side * th[i] * math.sin(a) for i in range(2))

    def at(rho: float) -> tuple[float, float]:
        s = -R * math.cos(a) + math.sqrt((R * math.cos(a)) ** 2 - R * R + rho * rho)
        return (R * rh[0] + s * d[0], R * rh[1] + s * d[1])

    assert R * math.sin(a) < p.FEED_EDGE_JOINT_R, "skew too steep for the joint radius"
    joint = at(p.FEED_EDGE_JOINT_R)
    tj = math.atan2(joint[1], joint[0])
    return [(math.cos(tj), math.sin(tj)), joint, at(k["shroud_r"] + p.FEED_LIFT_CHAMFER + 2)]


def _edge_chamfer(a: tuple, b: tuple, n: tuple, k: dict, ext_a: float, ext_b: float) -> Part:
    """Wedge cut under a window edge from a to b, into the cover on side n (unit, in plan): nothing at
    the underside, FEED_LIFT_CHAMFER wide FEED_LIFT_CHAMFER above it (45 deg), then straight up.
    It runs ext_a past a and ext_b past b (free ends only: the window clip trims those)."""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    d = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    if d[0] * n[1] - d[1] * n[0] > 0:
        origin, zd = (a[0] - ext_a * d[0], a[1] - ext_a * d[1]), d
    else:
        origin, zd = (b[0] + ext_b * d[0], b[1] + ext_b * d[1]), (-d[0], -d[1])
    c, z0, z1 = p.FEED_LIFT_CHAMFER, k["block_top"], k["cover_top"] + 1
    plane = Plane(origin=(origin[0], origin[1], 0), x_dir=(n[0], n[1], 0), z_dir=(zd[0], zd[1], 0))
    profile = Polygon((-0.01, z0 - 0.01), (0, z0 - 0.01), (c, z0 + c), (c, z1), (-0.01, z1))
    return extrude(plane * profile, L + ext_a + ext_b)


def feed_window(skew: float) -> Part:
    """The volume cut out of the cover for the window, lift chamfers included (rig frame)."""
    k = feed_layout()
    e0 = feed_edge(k["start"], skew, -1)
    e1 = feed_edge(k["cut"], skew, 1)
    big = k["shroud_r"] + p.FEED_LIFT_CHAMFER + 2
    a0 = math.degrees(math.atan2(e0[2][1], e0[2][0])) % 360
    a1 = math.degrees(math.atan2(e1[2][1], e1[2][0])) % 360
    if a1 < a0:
        a1 += 360
    arc = [
        (big * math.cos(math.radians(a)), big * math.sin(math.radians(a)))
        for a in (a0 + (a1 - a0) * i / 24 for i in range(1, 24))
    ]
    outline = Polygon(*e0, *arc, *reversed(e1))
    z0, z1 = k["block_top"] - 1, k["cover_top"] + 1
    cut = Pos(0, 0, z0) * extrude(outline, z1 - z0)
    for edge, side in ((e0, -1), (e1, 1)):
        for a, b, ea, eb in ((edge[0], edge[1], 3.0, 0.0), (edge[1], edge[2], 0.0, 3.0)):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            dn = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
            cut += _edge_chamfer(a, b, (-side * dn[1], side * dn[0]), k, ea, eb)
    ring = Pos(0, 0, z0) * (
        Cylinder(k["shroud_r"], z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))
        - Cylinder(p.FEED_WINDOW_R_IN, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    )
    return cut & ring - feed_chimney_footprint(p.FIT_TOLERANCE, z0 - 1, z1 - z0 + 2)


def feed_chimney_footprint(grow: float, z0: float, h: float) -> Part:
    """The chimney's footprint on the cover (outside of its narrow part), grown by `grow`, from z0 up h."""
    return Pos(0, 0, z0) * extrude(chimney_plan(p.FEED_CHIMNEY_T + grow), h)


def chimney_plan(grow: float, up: bool = False, bulge: bool = True) -> Sketch:
    """Plan of the chimney's inside grown by `grow` (its outside for grow=FEED_CHIMNEY_T), corners
    rounded to `grow` when it is positive. Low part (up=False): round the case, plus a round bulge for
    the drive piece; high part: round the ears and the shelf."""
    k = feed_layout()
    x0 = k["ch_in_x0_up"] if up else k["ch_in_x0_low"]
    hy = k["ch_in_y_up"] if up else k["ch_in_y_low"]
    x1 = k["ch_in_x1"]
    w, h = x1 - x0 + 2 * grow, 2 * (hy + grow)
    c = Pos((x0 + x1) / 2, 0)
    plan = c * (RectangleRounded(w, h, grow) if grow > 0 else Rectangle(w, h))
    if bulge and not up:
        plan += Circle(k["ch_in_r_drive"] + grow)
    return plan


def feed_tongue_outline() -> Sketch:
    """Plan of the stripper tongue: from the strip point (angle 0) on for FEED_TONGUE_ARC, inside the
    channel's inner wall, inside the shroud, outside the hub hole."""
    k = feed_layout()
    fan = Polygon(
        (0, 0),
        *[
            (80 * math.cos(math.radians(a)), 80 * math.sin(math.radians(a)))
            for a in range(0, 1 + int(p.FEED_TONGUE_ARC))
        ],
    )
    inner = Pos(k["channel_x0"] - 50, 0) * Rectangle(100, 200)
    return fan & inner & Circle(k["shroud_r"] - p.FEED_RUN_GAP) - Circle(k["hole_r"])


def feed_cover(skew: float) -> Part:
    """Cover over the disc: the window, the cut-off edge tilted skew degrees, the stripper tongue.

    It lies on the base block, so its underside is FEED_SLOT_H over the floor: one layer of BBs in
    the notches, and a BB riding on the disc cannot follow them under it. Both window edges have a
    45 deg lifting chamfer underneath. The tongue hangs FEED_RUN_GAP over the disc and pushes each BB
    out along the channel's inner wall. Grooves in the top locate the hopper and the chimney, two
    slots inside the chimney let the bracket's pegs through to the base. Printed upside down (the STL
    is), so the tongue and the chamfers point up.
    """
    k = feed_layout()
    t = p.FEED_COVER_T
    up = (Align.CENTER, Align.CENTER, Align.MIN)
    body = Pos(0, 0, k["block_top"]) * extrude(feed_block_outline(), t)
    body -= Pos(0, 0, k["block_top"] - 1) * Cylinder(k["hole_r"], t + 2, align=up)
    body -= feed_window(skew)
    tongue_h = k["block_top"] - k["tongue_bottom"]
    body += Pos(0, 0, k["tongue_bottom"]) * extrude(feed_tongue_outline(), tongue_h + 0.01)
    body -= Pos(0, 0, k["cover_top"] - p.FEED_HOPPER_SEAT) * extrude(feed_grooves(), p.FEED_HOPPER_SEAT + 1)
    body -= feed_peg_slots(k["block_top"] - 1, t + 2)
    s = k["screw_xy"]
    for x, y in ((s, s), (-s, s), (s, -s), (-s, -s)):
        body -= Pos(x, y, k["block_top"] - 1) * Cylinder(p.M3_CLEARANCE / 2, t + 2, align=up)
    label = Text(f"CUT {skew:g}", p.FEED_TEXT_SIZE)
    y_label = -(k["shroud_r"] + p.FEED_LIFT_CHAMFER + k["hop_in"]) / 2  # Between the window and the hopper.
    body -= Pos(0, y_label, k["cover_top"] - p.FEED_TEXT_DEPTH) * extrude(label, p.FEED_TEXT_DEPTH + 0.1)
    return body


def feed_block_outline() -> Sketch:
    """Plan of the base block and the cover: FEED_BLOCK_HALF on -X, -Y and +Y, block_x1 on +X."""
    k = feed_layout()
    H, x1 = p.FEED_BLOCK_HALF, k["block_x1"]
    return Pos((x1 - H) / 2, 0) * RectangleRounded(x1 + H, 2 * H, 2.0)


def feed_hopper_rects() -> tuple[tuple[float, float, float, float], tuple[float, float, float, float]]:
    """Plan of the hopper ring (x0, y0, x1, y1): outside, then inside."""
    k = feed_layout()
    o, i = k["hop_out"], k["hop_in"]
    return (-o, -o, k["hop_x1_out"], o), (-i, -i, k["hop_x1_in"], i)


def _rect(x0: float, y0: float, x1: float, y1: float, grow: float = 0.0) -> Sketch:
    return Pos((x0 + x1) / 2, (y0 + y1) / 2) * Rectangle(x1 - x0 + 2 * grow, y1 - y0 + 2 * grow)


def feed_grooves() -> Sketch:
    """The grooves in the cover top the hopper and the chimney stand in: each wall FIT_TOLERANCE
    wider either side."""
    g = p.FIT_TOLERANCE
    (o, i) = feed_hopper_rects()
    t = p.FEED_CHIMNEY_T
    return (_rect(*o, g) - _rect(*i, -g)) + (chimney_plan(t + g) - chimney_plan(-g))


def feed_peg_slots(z0: float, h: float) -> Part:
    """The slots the bracket's pegs slide in, along X, from z0 up h (in the cover and the base)."""
    k = feed_layout()
    g = p.FIT_TOLERANCE
    L, W = p.FEED_PEG_L + 2 * p.FEED_SERVO_TRAVEL_X + 2 * g, p.FEED_PEG_W + 2 * g
    slots = None
    for y in p.FEED_PEG_YS:
        s = Pos(k["peg_x"], y, z0) * Box(L, W, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
        slots = s if slots is None else slots + s
    return slots


def elbow_layout(R: float) -> dict:
    """Sizes of the elbow at bend radius R, shared by feed_elbow_half(), feed_base() and check.py.

    Local frame of the elbow: u along the channel from the mouth (rig +Y), v up from the bore
    axis (rig +Z), w across the split plane (rig +X); half "a" on w >= 0, "b" on w <= 0.
    """
    k = feed_layout()
    bore_r = p.BB_GUIDE_D / 2
    sock_r = (p.BARREL_OD + p.FIT_TOLERANCE) / 2
    t = sock_r + p.FEED_ELBOW_WALL  # Each half's thickness.
    nut_r = (p.M3_NUT_AF + p.NUT_TOLERANCE) / math.sqrt(3)
    nut_d = p.M3_NUT_THICKNESS + p.NUT_TOLERANCE

    def screw_off(r: float) -> float:
        # MIN_WALL from the hole to the cavity in the plane, and from the nut trap (on the outer face) to it.
        return max(
            r + p.MIN_WALL + p.M3_CLEARANCE / 2, nut_r + math.sqrt(max(0.0, (r + p.MIN_WALL) ** 2 - (t - nut_d) ** 2))
        )

    off_b, off_s = screw_off(bore_r), screw_off(sock_r)
    ue, vs = p.FEED_ELBOW_RUN + R, R + p.FEED_ELBOW_RISE
    vt = vs + p.GRIP_LENGTH
    c = math.sqrt(0.5)
    u1 = p.M3_CLEARANCE / 2 + p.MIN_WALL + 0.5  # Dock screw, near the mouth.
    return {
        "R": R,
        "bore_r": bore_r,
        "sock_r": sock_r,
        "t": t,
        "w": p.FEED_ELBOW_HALF_W,
        "nut_r": nut_r,
        "nut_d": nut_d,
        "off_b": off_b,
        "off_s": off_s,
        "ue": ue,  # u of the vertical leg (the barrel axis).
        "vs": vs,  # v of the shoulder the barrel butts on.
        "vt": vt,  # v of the top.
        "vb": p.FEED_BASE_T - k["axis_z"],  # v of the bottom edge, on the base plate.
        "cu": p.FEED_ELBOW_RUN,  # Centre of the bend.
        "cv": R,
        "u1": u1,
        # (u, v, nut): the dock screw goes through the base cheeks with a loose nut; the others have
        # a nut trap in half b.
        "screws": [
            (u1, off_b, False),
            (p.FEED_ELBOW_RUN + (R + off_b) * c, R - (R + off_b) * c, True),
            (p.FEED_ELBOW_RUN + (R - off_b) * c, R - (R - off_b) * c, True),
            (ue - off_s, vs + p.GRIP_LENGTH / 2, True),
            (ue + off_s, vs + p.GRIP_LENGTH / 2, True),
        ],
        "x": p.FEED_BB_CIRCLE_R,  # Rig X of the split plane.
        "y0": p.FEED_BLOCK_HALF,  # Rig Y of the mouth.
        "z0": k["axis_z"],  # Rig Z of the bore axis at the mouth.
        "barrel_y": p.FEED_BLOCK_HALF + ue,
        "socket_z": k["axis_z"] + vs,  # Shoulder height over the table.
        "top_z": k["axis_z"] + vt,
    }


def elbow_plane(e: dict) -> Plane:
    """Maps the elbow's local (u, v, w) to the rig frame."""
    return Plane(origin=(e["x"], e["y0"], e["z0"]), x_dir=(0, 1, 0), z_dir=(1, 0, 0))


def elbow_bore(e: dict) -> Part:
    """The BB path through the elbow (local frame): lead-in, run, bend, rise, barrel socket."""
    r, R, c = e["bore_r"], e["R"], p.FEED_MOUTH_CHAMFER
    run, cu, cv, ue = p.FEED_ELBOW_RUN, e["cu"], e["cv"], e["ue"]
    bore = Pos((run - 1) / 2, 0, 0) * Rot(0, 90, 0) * Cylinder(r, run + 1 + 0.01)
    bore += Pos(-1, 0, 0) * Rot(0, 90, 0) * Cylinder(r + c, 1, align=(Align.CENTER, Align.CENTER, Align.MIN))
    bore += Rot(0, 90, 0) * Cone(r + c, r, c, align=(Align.CENTER, Align.CENTER, Align.MIN))
    quarter = Pos(cu, cv - R - r - 1, -r - 1) * Box(R + r + 1, R + r + 1, 2 * r + 2, align=(Align.MIN,) * 3)
    # Seam of the tube off the split plane (w=0), or the halves do not mesh cleanly.
    bore += Pos(cu, cv, 0) * Torus(R, r, minor_start_angle=90, minor_end_angle=450) & quarter
    bore += (
        Pos(ue, cv - 0.01, 0)
        * Rot(-90, 0, 0)
        * Cylinder(r, e["vs"] - cv + 0.02, align=(Align.CENTER, Align.CENTER, Align.MIN))
    )
    bore += (
        Pos(ue, e["vs"], 0)
        * Rot(-90, 0, 0)
        * Cylinder(e["sock_r"], e["vt"] - e["vs"] + 1, align=(Align.CENTER, Align.CENTER, Align.MIN))
    )
    return bore


def feed_elbow_half(R: float, half: str, placed: bool = True) -> Part:
    """One half of the elbow at bend radius R, split on the plane of the bend.

    Each half is a flat plate with half the BB path cut into its split face: printed split face up,
    the path is an open groove and the layers run along it. Its bottom edge stands on the base plate
    between two cheeks, the mouth against the channel exit. M3 screws hold the halves (nuts trapped
    in half b); round the barrel socket the split faces are set back so the two screws there clamp
    the barrel. placed=False returns it in the elbow's local frame (see elbow_layout).
    """
    e = elbow_layout(R)
    assert R >= p.FEED_ELBOW_MIN_R, f"elbow radius {R} under FEED_ELBOW_MIN_R"
    w, ue, vt, vb, t = e["w"], e["ue"], e["vt"], e["vb"], e["t"]
    assert R - w > p.MIN_WALL, "bend too tight for FEED_ELBOW_HALF_W"
    inner = [
        (e["cu"] + (R - w) * math.cos(math.radians(a)), e["cv"] + (R - w) * math.sin(math.radians(a)))
        for a in range(0, -91, -5)
    ]
    outline = Polygon((0, vb), (ue + w, vb), (ue + w, vt), (ue - w, vt), *inner, (0, w))
    sign = 1 if half == "a" else -1
    body = Pos(0, 0, 0 if sign > 0 else -t) * extrude(outline, t)
    body -= elbow_bore(e)
    gap = p.FEED_ELBOW_CLAMP_GAP / 2
    body -= Pos(ue - w - 1, e["vs"], 0 if sign > 0 else -gap) * Box(
        2 * w + 2, vt - e["vs"] + 1, gap, align=(Align.MIN,) * 3
    )
    hexagon = RegularPolygon(e["nut_r"], 6)
    for u, v, nut in e["screws"]:
        body -= Pos(u, v, 0) * Cylinder(p.M3_CLEARANCE / 2, 2 * t + 2)
        if nut and sign < 0:
            body -= Pos(u, v, -t - 1) * extrude(hexagon, e["nut_d"] + 1)
    return elbow_plane(e) * body if placed else body


def elbow_on_bed(half: str, R: float) -> Part:
    """Print orientation of an elbow half: split face up, outer face on the bed."""
    body = feed_elbow_half(R, half, placed=False)
    if half == "a":
        body = Rot(180, 0, 0) * body
    return on_bed(body)


def feed_base() -> Part:
    """Base: a plate on the table, a block with the round track the disc turns in (its wall is the
    shroud), the centre pin, the exit channel, nut traps for the cover screws, and two cheeks that
    hold the elbow on the channel exit. Printed flat as it sits; the cheek holes are the only
    horizontal holes (small), the nut trap ceilings the only bridges."""
    k = feed_layout()
    H = p.FEED_BLOCK_HALF
    e = elbow_layout(max(p.FEED_ELBOW_RADII))
    y_end = H + e["ue"] + e["w"] + p.MIN_WALL
    bx1 = k["block_x1"]
    body = Pos((bx1 - H) / 2, (y_end - H) / 2, 0) * extrude(RectangleRounded(bx1 + H, y_end + H, 2.0), p.FEED_BASE_T)
    body += Pos(0, 0, p.FEED_BASE_T - 0.01) * extrude(feed_block_outline(), k["block_top"] - p.FEED_BASE_T + 0.01)
    up = (Align.CENTER, Align.CENTER, Align.MIN)
    body -= Pos(0, 0, k["floor"]) * Cylinder(k["shroud_r"], k["block_top"] - k["floor"] + 1, align=up)
    x0, x1 = k["channel_x0"], k["channel_x1"]
    body -= Pos(x0, 0, k["floor"]) * Box(x1 - x0, H + 1, k["block_top"] - k["floor"] + 1, align=(Align.MIN,) * 3)
    body += Pos(0, 0, k["floor"] - 0.01) * Cylinder(p.FEED_PIN_D / 2, p.FEED_PIN_H + 0.01, align=up)
    s = k["screw_xy"]
    hexagon = RegularPolygon(e["nut_r"], 6)
    for x, y in ((s, s), (-s, s), (s, -s), (-s, -s)):
        body -= Pos(x, y, -1) * Cylinder(p.M3_CLEARANCE / 2, k["block_top"] + 2, align=up)
        body -= Pos(x, y, -1) * extrude(hexagon, e["nut_d"] + 1)
    # Cheeks either side of the elbow, with the dock screw hole through both.
    dock_len = e["u1"] + p.M3_CLEARANCE / 2 + p.MIN_WALL
    dock_top = k["axis_z"] + e["off_b"] + p.M3_CLEARANCE / 2 + p.MIN_WALL
    inner = e["t"] + p.FIT_TOLERANCE / 2
    for side in (-1, 1):
        x = e["x"] + side * (inner + p.FEED_DOCK_T / 2)
        body += Pos(x, H, p.FEED_BASE_T - 0.01) * Box(
            p.FEED_DOCK_T, dock_len, dock_top - p.FEED_BASE_T + 0.01, align=(Align.CENTER, Align.MIN, Align.MIN)
        )
    span = 2 * (inner + p.FEED_DOCK_T) + 2
    body -= Pos(e["x"], H + e["u1"], k["axis_z"] + e["off_b"]) * Rot(0, 90, 0) * Cylinder(p.M3_CLEARANCE / 2, span)
    # Slots the servo bracket's pegs key into: it slides along the servo, never sideways or round.
    body -= feed_peg_slots(k["peg_bottom"] - p.FEED_RUN_GAP, k["block_top"])
    return body


def feed_hopper() -> Part:
    """A closed ring round the cover holding the pile round the chimney, standing in the cover's
    groove. The chimney's +X face sits against the inside of its +X wall. Printed as it stands."""
    k = feed_layout()
    o, i = feed_hopper_rects()
    return Pos(0, 0, k["hop_bottom"]) * extrude(_rect(*o) - _rect(*i), k["hop_top"] - k["hop_bottom"])


def _chimney_solid(grow: float) -> Part:
    """The chimney's volume (inside if grow=0, outside if grow=FEED_CHIMNEY_T), bottom to top: the
    narrow part, a 45 deg flare, the wide part."""
    k = feed_layout()
    low, high = chimney_plan(grow, bulge=False), chimney_plan(grow, up=True)
    za, zb = k["ch_z_a"], k["ch_z_b"]
    z0, z1 = k["ch_bottom"] - 1, k["ch_top"] + 1
    body = Pos(0, 0, z0) * extrude(low, za - z0)
    body += loft([Plane.XY.offset(za) * low, Plane.XY.offset(zb) * high])
    body += Pos(0, 0, zb) * extrude(high, z1 - zb)
    body += Pos(0, 0, z0) * Cylinder(k["ch_in_r_drive"] + grow, zb - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return body


def feed_chimney() -> Part:
    """Closed tube round the servo and its bracket, open at the top. It stands in a groove in the
    cover, so no BB gets in at its foot; narrow low down (round the case and the drive piece, so the
    window can wrap round its -X end), it flares out at 45 deg to take the ears and the shelf. A
    notch at the top, above the pile, lets the cables out sideways. Printed as it stands: the flare
    is the only overhang, just steeper than 45 deg."""
    k = feed_layout()
    t = p.FEED_CHIMNEY_T
    up = (Align.CENTER, Align.CENTER, Align.MIN)
    body = _chimney_solid(t) - _chimney_solid(0)
    body &= Pos(0, 0, k["ch_bottom"]) * Box(500, 500, k["ch_top"] - k["ch_bottom"], align=up)
    body -= Pos(k["ch_in_x1"] + t / 2, 0, k["hop_top"]) * Box(t + 2, p.FEED_CABLE_W, 100, align=up)
    return body


def feed_servo_bracket() -> Part:
    """Servo bracket, inside the chimney: a shelf ring round the case the ears are screwed to (side
    rails beside the case, pads under the ears), on one leg under the +X ears whose two pegs key into
    slots in the base.

    The slots run along the servo, so the bracket slides FEED_SERVO_TRAVEL_X either way: the hex
    pulls the spline onto the disc axis whatever SERVO_SPLINE_OFFSET really is. The pegs and the
    chimney's walls stop it turning with the servo's torque. Ear screws cut their thread in pilot
    holes. Printed upside down (the STL is): shelf on the bed, nothing overhangs.
    """
    k = feed_layout()
    up = (Align.CENTER, Align.CENTER, Align.MIN)
    x0, x1, zs = k["shelf_x0"], k["shelf_x1"], k["shelf_bottom"]
    ry, rw = k["rail_y"], p.FEED_RAIL_W
    g = k["case_gap"]
    ring = _rect(x0, -ry - rw, x1, ry + rw) - _rect(k["case_x0"] - g, -ry, k["case_x1"] + g, ry)
    body = Pos(0, 0, zs) * extrude(ring, p.FEED_BRACKET_T)
    rails = _rect(x0, -ry - rw, x1, ry + rw) - _rect(x0 - 1, -ry, x1 + 1, ry)
    body += Pos(0, 0, zs - p.FEED_RAIL_H) * extrude(rails, p.FEED_RAIL_H + 0.01)
    zc = k["cover_top"]
    body += Pos(0, 0, zc) * extrude(_rect(k["leg_x0"], -k["leg_hy"], k["leg_x1"], k["leg_hy"]), zs - zc + 0.01)
    for y in p.FEED_PEG_YS:
        body += Pos(k["peg_x"], y, k["peg_bottom"]) * Box(p.FEED_PEG_L, p.FEED_PEG_W, zc - k["peg_bottom"] + 0.01, align=up)
    xe = p.SERVO_EAR_PITCH_L / 2
    for ex in (k["servo_xc"] - xe, k["servo_xc"] + xe):
        for ey in (-p.SERVO_EAR_PITCH_W / 2, p.SERVO_EAR_PITCH_W / 2):
            body -= Pos(ex, ey, k["ears"] - p.FEED_SELF_TAP_DEPTH) * Cylinder(
                p.FEED_SELF_TAP_D / 2, p.FEED_SELF_TAP_DEPTH + 1, align=up
            )
    return body


def feed_coupon_layout() -> dict:
    """Positions on feed_coupon, shared with check.py. Rows from +Y down: slot pockets, their labels,
    pin bores, labels, hex sockets, labels."""
    gap, text = p.COUPON_GAP, p.COUPON_TEXT_SIZE
    pocket_w, pocket_l = p.BB_D + 2, 20.0
    pin_r = (p.FEED_PIN_D + max(p.FEED_COUPON_PIN_OFFSETS)) / 2
    hex_r = (p.FEED_HEX_AF + max(p.FEED_COUPON_HEX_OFFSETS)) / math.sqrt(3)
    y_pocket = 0.0
    y_pl = -pocket_l / 2 - gap / 2 - text / 2
    y_pin = y_pl - text / 2 - gap / 2 - pin_r
    y_pinl = y_pin - pin_r - gap / 2 - text / 2
    y_hex = y_pinl - text / 2 - gap / 2 - hex_r
    y_hexl = y_hex - hex_r - gap / 2 - text / 2
    n = max(len(p.FEED_COUPON_PIN_OFFSETS), len(p.FEED_COUPON_HEX_OFFSETS))
    return {
        "width": n * (2 * hex_r + gap) + gap,
        "pocket_w": pocket_w,
        "pocket_l": pocket_l,
        "y_pocket": y_pocket,
        "y_pocket_label": y_pl,
        "y_pin": y_pin,
        "y_pin_label": y_pinl,
        "y_hex": y_hex,
        "y_hex_label": y_hexl,
        "y_min": y_hexl - text / 2 - gap / 2,
        "y_max": pocket_l / 2 + gap,
    }


def feed_coupon() -> Part:
    """Test piece for the feed rig fits, labelled with the offset each one adds.

    Slot pockets FEED_SLOT_H + offset deep: lay a straight edge over one, a BB must roll along under
    it freely in the 0 one (and, of course, never two BBs one on the other). Pin bores FEED_PIN_D +
    offset: the base's pin (or a 5 mm drill shank) turns freely without wobble in the right one:
    FEED_PIN_CLEARANCE. Hex sockets FEED_HEX_AF + offset: the printed disc's hex boss slides in
    without turning play in the right one: FEED_HEX_TOLERANCE. Printed flat, everything vertical.
    """
    k = feed_coupon_layout()
    T, text, W = p.FEED_COUPON_T, p.COUPON_TEXT_SIZE, k["width"]
    outline = Pos(0, (k["y_min"] + k["y_max"]) / 2) * Rectangle(W, k["y_max"] - k["y_min"])
    part = extrude(fillet(outline.vertices(), p.EDGE_FILLET), T)

    def label(v: float) -> str:
        return "0" if abs(v) < 1e-9 else f"{v:+.1f}".replace("0.", ".")

    def engrave(s: str, x: float, y: float) -> Part:
        return Pos(x, y, T - p.COUPON_TEXT_DEPTH) * extrude(Text(s, text), p.COUPON_TEXT_DEPTH + 0.1)

    def xs(n: int) -> list[float]:
        return [-W / 2 + W / n * (i + 0.5) for i in range(n)]

    for x, o in zip(xs(len(p.FEED_COUPON_SLOT_OFFSETS)), p.FEED_COUPON_SLOT_OFFSETS):
        depth = p.FEED_SLOT_H + o
        part -= Pos(x, k["y_pocket"], T - depth) * Box(
            k["pocket_w"], k["pocket_l"], depth + 1, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        part -= engrave(label(o), x, k["y_pocket_label"])
    for x, o in zip(xs(len(p.FEED_COUPON_PIN_OFFSETS)), p.FEED_COUPON_PIN_OFFSETS):
        part -= Pos(x, k["y_pin"], T / 2) * Cylinder((p.FEED_PIN_D + o) / 2, T + 1)
        part -= engrave(label(o), x, k["y_pin_label"])
    for x, o in zip(xs(len(p.FEED_COUPON_HEX_OFFSETS)), p.FEED_COUPON_HEX_OFFSETS):
        part -= Pos(x, k["y_hex"], -0.5) * extrude(_hex((p.FEED_HEX_AF + o) / math.sqrt(3)), T + 1)
        part -= engrave(label(o), x, k["y_hex_label"])
    return part


def feed_assembly(skew: float = 0.0, R: float | None = None) -> dict[str, Part]:
    """Every rig part in place (rig frame), for check.py and previews."""
    R = p.FEED_ELBOW_RADII[1] if R is None else R
    return {
        "base": feed_base(),
        "disc": feed_disc(),
        "drive": feed_drive(),
        "cover": feed_cover(skew),
        "elbow_a": feed_elbow_half(R, "a"),
        "elbow_b": feed_elbow_half(R, "b"),
        "hopper": feed_hopper(),
        "chimney": feed_chimney(),
        "bracket": feed_servo_bracket(),
    }


def corner_gauge(r: float) -> Part:
    """A square tab with one corner rounded to r and "R<r>" engraved. Pushed into a bottom corner of
    the box, the tab that touches both walls with no gap in the corner gives the box's corner radius.
    One part per radius in CORNER_GAUGE_RADII, so they can be laid out freely on the bed."""
    s = p.CORNER_GAUGE_SIZE
    # Rounded corner at +X+Y: a square with that corner cut and replaced by a quarter circle.
    outline = Rectangle(s, s) - Pos(s / 2 - r / 2, s / 2 - r / 2) * Rectangle(r, r)
    outline += Pos(s / 2 - r, s / 2 - r) * Circle(r)
    tab = extrude(outline, p.GAUGE_HEIGHT)
    label = Text(f"R{r:g}", p.GAUGE_TEXT_SIZE)
    return tab - Pos(-s / 6, -s / 6, p.GAUGE_HEIGHT - p.GAUGE_TEXT_DEPTH) * extrude(label, p.GAUGE_TEXT_DEPTH + 0.1)


PARTS = {
    "test_ring": test_ring,
    "ir_collar": ir_collar,
    "fit_coupon": fit_coupon,
    "encoder_knob": encoder_knob,
    "floor_gauge": floor_gauge,
    "ledge_gauge": ledge_gauge,
    **{f"corner_gauge_r{r:g}": (lambda r=r: corner_gauge(r)) for r in p.CORNER_GAUGE_RADII},
    "feed_coupon": feed_coupon,
    "feed_base": feed_base,
    "feed_disc": lambda: on_bed(feed_disc()),
    "feed_drive": lambda: on_bed(feed_drive()),
    **{f"feed_cover_{n}": (lambda a=a: on_bed(feed_cover(a), flip=True)) for n, a in COVER_VARIANTS.items()},
    **{f"feed_elbow_r{r:g}_{h}": (lambda r=r, h=h: elbow_on_bed(h, r)) for r in p.FEED_ELBOW_RADII for h in ("a", "b")},
    "feed_hopper": lambda: on_bed(feed_hopper()),
    "feed_chimney": lambda: on_bed(feed_chimney()),
    "feed_servo_bracket": lambda: on_bed(feed_servo_bracket(), flip=True),
}


def meshable(part: Part) -> Part:
    """The same solid without the face wires made only of INTERNAL edges.

    A boolean can leave such a wire on a face: a seam that bounds nothing, e.g. a half circle
    0.01 mm inside the end of the toroidal bore of feed_elbow_r30_b. The solid is still valid,
    but OCC's mesher then triangulates that face wrong: the mesh stays closed, yet a third of
    the bore groove is missing. Dropping the wire changes nothing else, so mesh this instead.
    """
    from OCP.BRep import BRep_Builder
    from OCP.BRepTools import BRepTools_ReShape
    from OCP.TopAbs import TopAbs_EDGE, TopAbs_INTERNAL, TopAbs_WIRE
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopoDS import TopoDS

    def children(shape, kind):  # Every sub-shape, INTERNAL ones included (build123d skips them).
        found = TopExp_Explorer(shape, kind)
        while found.More():
            yield found.Current()
            found.Next()

    reshape = BRepTools_ReShape()
    for face in part.faces():
        wires = list(children(face.wrapped, TopAbs_WIRE))
        keep = [w for w in wires if any(e.Orientation() != TopAbs_INTERNAL for e in children(w, TopAbs_EDGE))]
        if len(keep) < len(wires):
            new = TopoDS.Face(face.wrapped.EmptyCopied())
            for w in keep:
                BRep_Builder().Add(new, w)
            reshape.Replace(face.wrapped, new)
    return Part(reshape.Apply(part.wrapped))


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    for name, build in PARTS.items():
        part = build()
        for path, export, shape in (
            (OUT_DIR / f"{name}.stl", export_stl, meshable(part)),
            (OUT_DIR / f"{name}.step", export_step, part),
        ):
            if not export(shape, str(path)) or path.stat().st_size == 0:
                raise SystemExit(f"export failed: {path}")
            print(f"wrote out/{path.name}")


if __name__ == "__main__":
    main()
