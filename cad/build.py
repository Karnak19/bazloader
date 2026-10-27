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
    Pos,
    Rectangle,
    RectangleRounded,
    RegularPolygon,
    Rot,
    SlotOverall,
    Sketch,
    Text,
    chamfer,
    export_step,
    export_stl,
    extrude,
    fillet,
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


def box_interior(z: float) -> tuple[float, float]:
    """Interior length and width of the Plano box at height z above its floor (the walls lean out)."""
    return p.BOX_FLOOR_L + p.BOX_TAPER_L * z, p.BOX_FLOOR_W + p.BOX_TAPER_W * z


def seat_layout() -> dict[str, float]:
    """Outline of a part resting on the box ledge: ledge_gauge now, the top plate (#18) later.

    Box frame: floor at Z=0, interior centred on X=0, Y=0, X along the length. The part's
    underside is at z = BOX_LEDGE_Z1. Outside: the box there minus WALL_CLEARANCE per side.
    Inside: the ledge opening minus SEAT_INSET per side, so it covers the whole ledge.
    """
    box_l, box_w = box_interior(p.BOX_LEDGE_Z1)
    return {
        "z": p.BOX_LEDGE_Z1,
        "outer_l": box_l - 2 * p.WALL_CLEARANCE,
        "outer_w": box_w - 2 * p.WALL_CLEARANCE,
        "inner_l": p.BOX_LEDGE_OPEN_L - 2 * p.SEAT_INSET,
        "inner_w": p.BOX_LEDGE_OPEN_W - 2 * p.SEAT_INSET,
    }


def floor_layout() -> dict[str, float]:
    """Outline of floor_gauge, in the box frame: on the floor (z=0), WALL_CLEARANCE off every wall."""
    box_l, box_w = box_interior(0.0)
    outer_l, outer_w = box_l - 2 * p.WALL_CLEARANCE, box_w - 2 * p.WALL_CLEARANCE
    return {
        "z": 0.0,
        "outer_l": outer_l,
        "outer_w": outer_w,
        "inner_l": outer_l - 2 * p.GAUGE_WALL,
        "inner_w": outer_w - 2 * p.GAUGE_WALL,
    }


def _mm(v: float) -> str:
    """228.0 -> "228", 235.64 -> "235.6"."""
    return f"{v:.1f}".removesuffix(".0")


def gauge_label(k: dict[str, float], name: str) -> str:
    return f"{name} {_mm(k['outer_l'])}x{_mm(k['outer_w'])}"


def box_gauge(k: dict[str, float], name: str) -> Part:
    """Thin closed frame: outer outline k["outer_l"] x k["outer_w"] with CORNER_R corners, hollow
    k["inner_l"] x k["inner_w"]. A tab inside the -Y long side carries the engraved name and outer
    size. Printed flat, Z=0 on the bed; in the box it sits at k["z"].
    """
    wall = min(k["outer_l"] - k["inner_l"], k["outer_w"] - k["inner_w"]) / 2
    assert wall >= p.MIN_WALL, f"{name} gauge wall only {wall:.2f}"
    inner_r = max(p.CORNER_R - wall, 1.0)
    outline = RectangleRounded(k["outer_l"], k["outer_w"], p.CORNER_R) - RectangleRounded(
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


PARTS = {
    "test_ring": test_ring,
    "ir_collar": ir_collar,
    "fit_coupon": fit_coupon,
    "encoder_knob": encoder_knob,
    "floor_gauge": floor_gauge,
    "ledge_gauge": ledge_gauge,
}


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    for name, build in PARTS.items():
        part = build()
        for path, export in (
            (OUT_DIR / f"{name}.stl", export_stl),
            (OUT_DIR / f"{name}.step", export_step),
        ):
            if not export(part, str(path)) or path.stat().st_size == 0:
                raise SystemExit(f"export failed: {path}")
            print(f"wrote out/{path.name}")


if __name__ == "__main__":
    main()
