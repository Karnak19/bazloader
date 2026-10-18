"""Build every part and export it as STL and STEP into out/.

Add a part: write a function returning a build123d shape, then add it to PARTS.
"""

import math
from pathlib import Path

from build123d import (
    Align,
    Box,
    Circle,
    Cylinder,
    Part,
    Plane,
    Pos,
    Rectangle,
    RegularPolygon,
    Rot,
    SlotOverall,
    Text,
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

    Frame: the tube axis is Z, the collar sits on Z=0 (its print face), the beam
    runs along X through the tube centre at mid-length, the clamp slot is on +Y.
    """
    bore_r = (p.BARREL_OD + p.FIT_TOLERANCE) / 2
    led_r = (p.IR_LED_DIAMETER + p.SOCKET_TOLERANCE) / 2
    photo_r = (p.PHOTOTRANSISTOR_DIAMETER + p.SOCKET_TOLERANCE) / 2
    socket_r = max(led_r, photo_r)
    shoulder_x = bore_r + p.APERTURE_LEN  # Both stop shoulders sit this far from the axis.
    nut_r = (p.M3_NUT_AF + p.NUT_TOLERANCE) / math.sqrt(3)  # Hexagon corner radius.
    screw_y = bore_r + p.MIN_WALL + nut_r  # Nut trap clears the bore by MIN_WALL.
    return {
        "bore_r": bore_r,
        "outer_r": bore_r + p.COLLAR_WALL,
        "beam_z": p.COLLAR_LENGTH / 2,
        "led_r": led_r,  # LED socket, on -X.
        "photo_r": photo_r,  # Phototransistor socket, on +X.
        "socket_r": socket_r,
        "shoulder_x": shoulder_x,
        "back_x": shoulder_x + p.SOCKET_DEPTH,  # Back face, where the leads come out.
        "bar_hw": max(socket_r + p.SOCKET_WALL, p.WIRE_CHANNEL_W / 2 + p.MIN_WALL),
        "nut_r": nut_r,
        "screw_y": screw_y,
        "ear_y": screw_y + nut_r + p.MIN_WALL,  # Outer face of the clamp ears.
        "ear_hx": p.CLAMP_SLOT / 2 + p.M3_NUT_THICKNESS + p.NUT_TOLERANCE + p.MIN_WALL,
        "channel_top": p.COLLAR_LENGTH / 2 - socket_r - p.MIN_WALL / 2,
    }


def _yz_plane(x: float, y: float, z: float, into: float) -> Plane:
    """Plane facing along X (into = +1 or -1), local x = global Y."""
    return Plane(origin=(x, y, z), x_dir=(0, 1, 0), z_dir=(into, 0, 0))


def ir_collar() -> Part:
    """Clamp-on collar that holds the IR LED and phototransistor face to face across the barrel.

    One piece, so both sockets come out of the same print layers and stay coaxial.
    It is a C-clamp: a slot on +Y and one M3 screw through two ears, nut in a trap.
    Print it standing on its end face (Z=0): every hole across the tube is then
    horizontal and small, and the nut trap has a corner on top, so no supports.
    """
    assert p.SOCKET_DEPTH < p.IR_BODY_LENGTH, "the flange would hit the back before the shoulder"
    k = collar_layout()
    assert max(p.APERTURE_D, p.APERTURE_W) < 2 * min(k["led_r"], k["photo_r"]) - p.SOCKET_TOLERANCE, (
        "the aperture must be narrower than the component, or there is no shoulder to stop it"
    )
    assert k["channel_top"] > p.MIN_WALL, "collar too short for the wire channels"
    L, z0 = p.COLLAR_LENGTH, k["beam_z"]

    # Outer outline, seen from above: ring + bar holding the sockets + clamp ears.
    outline = (
        Circle(k["outer_r"])
        + Rectangle(2 * k["back_x"], 2 * k["bar_hw"])
        + Pos(0, k["ear_y"] / 2) * Rectangle(2 * k["ear_hx"], k["ear_y"])
    )
    outline = fillet(outline.vertices(), p.EDGE_FILLET)
    body = extrude(outline, L)

    # Bore and clamp slot.
    body -= Cylinder(k["bore_r"], L, align=(Align.CENTER, Align.CENTER, Align.MIN))
    body -= Pos(0, k["ear_y"] / 2, L / 2) * Box(p.CLAMP_SLOT, k["ear_y"] + 1, L + 1)

    # Sockets: LED on -X, phototransistor on +X, open at the back for insertion.
    # Each ends on a flat shoulder at shoulder_x, the same on both sides.
    socket_len = p.SOCKET_DEPTH + 1  # Runs 1 mm past the back face for a clean cut.
    for side, r in ((-1, k["led_r"]), (1, k["photo_r"])):
        x_mid = side * (k["shoulder_x"] + socket_len / 2)
        body -= Pos(x_mid, 0, z0) * Rot(0, 90, 0) * Cylinder(r, socket_len)

    # Aperture: one window straight through both walls, so the two cannot drift apart.
    if p.APERTURE_W > p.APERTURE_D:
        window = SlotOverall(p.APERTURE_W, p.APERTURE_D)
    else:
        window = Circle(p.APERTURE_D / 2)
    reach = k["shoulder_x"] + 0.5
    body -= extrude(_yz_plane(-reach, 0, z0, 1) * window, 2 * reach)

    # Wire channels: a groove on each back face, from under the socket to the bottom end.
    for side in (-1, 1):
        x = side * (k["back_x"] - p.WIRE_CHANNEL_DEPTH / 2)
        h = k["channel_top"] + 1
        body -= Pos(x, 0, h / 2 - 1) * Box(p.WIRE_CHANNEL_DEPTH + 0.01, p.WIRE_CHANNEL_W, h)

    # M3 screw across the ears, head on -X, nut trapped in the +X ear.
    ear_span = 2 * k["ear_hx"] + 2
    body -= Pos(0, k["screw_y"], z0) * Rot(0, 90, 0) * Cylinder(p.M3_CLEARANCE / 2, ear_span)
    nut_depth = p.M3_NUT_THICKNESS + p.NUT_TOLERANCE
    # rotation=90 puts a hexagon corner on top (+Z), so the pocket roof prints without support.
    hexagon = RegularPolygon(k["nut_r"], 6, rotation=90)
    body -= extrude(_yz_plane(k["ear_hx"] + 1, k["screw_y"], z0, -1) * hexagon, nut_depth + 1)
    return body


def fit_coupon() -> Part:
    """Thin plate to print first: barrel bores and horizontal sockets at several tolerances.

    Each hole is labelled with the offset it adds. Slide it on the barrel and push
    in the components, then copy the best offsets into FIT_TOLERANCE and SOCKET_TOLERANCE.
    The socket holes are horizontal, in a rib, like in the printed collar.
    """
    t, gap, text = p.COUPON_THICKNESS, p.COUPON_GAP, p.COUPON_TEXT_SIZE
    bores = [p.BARREL_OD + o for o in p.COUPON_BORE_OFFSETS]
    sockets = [p.IR_LED_DIAMETER + o for o in p.COUPON_SOCKET_OFFSETS]
    pitch = max(bores) + gap
    width = pitch * len(bores) + gap
    bore_row_y = 0.0
    bore_label_y = -(max(bores) / 2 + gap / 2 + text / 2)
    socket_label_y = max(bores) / 2 + gap / 2 + text / 2
    rib_y0 = socket_label_y + text / 2 + gap / 2
    rib_h = max(sockets) + 2 * p.MIN_WALL
    y_min = bore_label_y - text / 2 - gap / 2
    y_max = rib_y0 + p.SOCKET_DEPTH

    outline = Pos(0, (y_min + y_max) / 2) * Rectangle(width, y_max - y_min)
    outline = fillet(outline.vertices(), p.EDGE_FILLET)
    rib_outline = outline & Pos(0, (rib_y0 + y_max) / 2 + 1) * Rectangle(width + 2, y_max - rib_y0 + 2)
    part = extrude(outline, t) + extrude(rib_outline, rib_h)

    def label(value: float) -> str:
        return "0" if abs(value) < 1e-9 else f"{value:+.1f}".replace("0.", ".")

    def engrave(s: str, x: float, y: float) -> Part:
        return Pos(x, y, t - p.COUPON_TEXT_DEPTH) * extrude(Text(s, text), p.COUPON_TEXT_DEPTH + 0.1)

    x0 = -width / 2 + gap + max(bores) / 2
    for i, (d, offset) in enumerate(zip(bores, p.COUPON_BORE_OFFSETS)):
        x = x0 + i * pitch
        part -= Pos(x, bore_row_y, t / 2) * Cylinder(d / 2, t + 1)
        part -= engrave(label(offset), x, bore_label_y)

    s_pitch = width / len(sockets)
    for i, (d, offset) in enumerate(zip(sockets, p.COUPON_SOCKET_OFFSETS)):
        x = -width / 2 + s_pitch * (i + 0.5)
        hole_len = p.SOCKET_DEPTH + 2
        part -= Pos(x, (rib_y0 + y_max) / 2, rib_h / 2) * Rot(90, 0, 0) * Cylinder(d / 2, hole_len)
        part -= engrave(label(offset), x, socket_label_y)
    return part


PARTS = {
    "test_ring": test_ring,
    "ir_collar": ir_collar,
    "fit_coupon": fit_coupon,
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
