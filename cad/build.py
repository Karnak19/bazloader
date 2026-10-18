"""Build every part and export it as STL and STEP into out/.

Add a part: write a function returning a build123d shape, then add it to PARTS.
"""

from pathlib import Path

from build123d import Cylinder, Part, export_step, export_stl

import params as p

OUT_DIR = Path(__file__).parent / "out"


def test_ring() -> Part:
    """Plain ring that should slide onto the inner barrel. M0 smoke test."""
    inner_d = p.BARREL_OD + p.FIT_TOLERANCE
    outer_d = inner_d + 2 * max(p.RING_WALL, p.MIN_WALL)
    return Cylinder(outer_d / 2, p.RING_HEIGHT) - Cylinder(inner_d / 2, p.RING_HEIGHT)


PARTS = {
    "test_ring": test_ring,
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
