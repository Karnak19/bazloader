"""Pack the feed bench rig into one Bambu Studio project, one plate per print group.

Run: uv run python pack_3mf.py  (writes out/feed_rig.3mf, then reads it back and checks it)

The parts come from build.PARTS, already the right way up, and are only moved, never
rotated. Plates follow Bambu Studio's layout for project files: plate i sits at column
i % cols, row i // cols, cols = ceil(sqrt(plate count)), one step being the bed size
× 1.2 along +X for columns and along -Y for rows. Plate 1's bed is [0, BED] × [0, BED].

Bambu Studio only reads the plates of a project that carries its full print profile
(without one it loads the geometry alone and drops the plates). Missing keys fall back
to generic defaults, not to the printer's, so the profile can't be written by hand:
bambu_project_settings.json is one Bambu Studio 2.08 saved itself, for a P2S 0.4 nozzle
on "0.20mm High Quality @BBL P2S" with its filament list as it was, the process reset to
the system values. SETTINGS goes on top of it, and on every object as a per-object
override so it survives a change of printer or process. To refresh the profile, save
any project from Bambu Studio and copy its Metadata/project_settings.config here.
"""

import json
import math
import re
import uuid
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import build

BED = 256.0  # X1C / P1S / P2S / A1 bed, mm.
PLATE_STEP = BED * 1.2  # Bambu's gap between plates is a fifth of the bed.
MARGIN = 5.0  # Minimum gap between two objects, and from an object to the bed edge.
TOLERANCE = 1e-3  # Same mesh tolerance as build.py's STL export.
SETTINGS = {"layer_height": "0.2", "wall_loops": "4"}

PLATES = [
    ("Essentiel PETG", ["feed_disc", "feed_cover_skew30", "feed_elbow_r30_a", "feed_elbow_r30_b"]),
    ("Base", ["feed_base", "feed_drive", "feed_servo_bracket"]),
    ("Grandes pièces", ["feed_hopper", "feed_chimney"]),
    ("Variantes couvercle (si besoin)", ["feed_cover_radial", "feed_cover_skew45"]),
    ("Variantes coude (si besoin)", [f"feed_elbow_r{r}_{h}" for r in (25, 40) for h in ("a", "b")]),
]

OUT = build.OUT_DIR / "feed_rig.3mf"
PROFILE = Path(__file__).parent / "bambu_project_settings.json"
NS_ID = uuid.UUID("6b1f4a52-3c0e-4b8e-9d55-0f3ed0a1b54e")  # Fixed, so the UUIDs repeat run to run.


def mesh(name: str) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    """Tessellate a part and weld the vertices that faces share, so the mesh is closed."""
    verts, tris = build.meshable(build.PARTS[name]()).tessellate(TOLERANCE)
    index: dict[tuple[float, float, float], int] = {}
    welded: list[tuple[float, float, float]] = []
    remap = []
    for v in verts:
        key = (round(v.X, 5), round(v.Y, 5), round(v.Z, 5))
        if key not in index:
            index[key] = len(welded)
            welded.append(key)
        remap.append(index[key])
    faces = [(remap[a], remap[b], remap[c]) for a, b, c in tris]
    return welded, [f for f in faces if len(set(f)) == 3]


def bbox(verts) -> tuple[float, float, float, float, float, float]:
    xs, ys, zs = zip(*verts)
    return min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)


def plate_origin(i: int, count: int) -> tuple[float, float]:
    cols = math.ceil(math.sqrt(count))
    return (i % cols) * PLATE_STEP, -(i // cols) * PLATE_STEP


def layout(sizes: dict[str, tuple[float, float]]) -> dict[str, tuple[float, float]]:
    """Centre of each footprint on a BED × BED plate: shelves filled deepest first, spaced evenly."""
    todo = sorted(sizes, key=lambda n: -sizes[n][1])
    rows: list[list[str]] = []
    while todo:
        row: list[str] = []
        for n in list(todo):
            widths = [sizes[m][0] for m in row + [n]]
            if sum(widths) + MARGIN * (len(widths) + 1) <= BED:
                row.append(n)
                todo.remove(n)
        if not row:
            raise SystemExit(f"{todo[0]} does not fit on a {BED:g} mm bed")
        rows.append(row)
    depths = [max(sizes[n][1] for n in row) for row in rows]
    gap_y = (BED - sum(depths)) / (len(rows) + 1)
    if gap_y < MARGIN:
        raise SystemExit(f"plate too full: {rows}")
    centres = {}
    y = BED - gap_y
    for row, depth in zip(rows, depths):
        gap_x = (BED - sum(sizes[n][0] for n in row)) / (len(row) + 1)
        x = gap_x
        for n in row:
            centres[n] = (x + sizes[n][0] / 2, y - depth / 2)
            x += sizes[n][0] + gap_x
        y -= depth + gap_y
    return centres


def fmt(x: float) -> str:
    return f"{x:.5f}".rstrip("0").rstrip(".")


def object_model(oid: int, name: str, verts, faces) -> str:
    vs = "\n".join(f'     <vertex x="{fmt(x)}" y="{fmt(y)}" z="{fmt(z)}"/>' for x, y, z in verts)
    ts = "\n".join(f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in faces)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">
 <metadata name="BambuStudio:3mfVersion">1</metadata>
 <resources>
  <object id="{oid}" p:UUID="{uuid.uuid5(NS_ID, 'mesh/' + name)}" type="model">
   <mesh>
    <vertices>
{vs}
    </vertices>
    <triangles>
{ts}
    </triangles>
   </mesh>
  </object>
 </resources>
 <build/>
</model>
"""


def pack() -> None:
    placed = []  # (plate index, name, mesh object id, wrapper object id, verts, faces, x, y)
    for i, (_, names) in enumerate(PLATES):
        meshes = {}
        for n in names:
            verts, faces = mesh(n)
            x0, y0, z0, x1, y1, _ = bbox(verts)
            # Centre the footprint on the object's origin, base on Z = 0.
            meshes[n] = ([(x - (x0 + x1) / 2, y - (y0 + y1) / 2, z - z0) for x, y, z in verts], faces)
        sizes = {}
        for n, (v, _) in meshes.items():
            x0, y0, _, x1, y1, _ = bbox(v)
            sizes[n] = (x1 - x0, y1 - y0)
        centres = layout(sizes)
        ox, oy = plate_origin(i, len(PLATES))
        for n in names:
            k = len(placed)
            cx, cy = centres[n]
            placed.append((i, n, 2 * k + 1, 2 * k + 2, *meshes[n], ox + cx, oy + cy))

    files: dict[str, str] = {}
    objects, items, rels, settings = [], [], [], []
    for i, n, mid, oid, verts, faces, x, y in placed:
        path = f"3D/Objects/{n}.model"
        files[path] = object_model(mid, n, verts, faces)
        rels.append(f' <Relationship Target="/{path}" Id="rel-{mid}" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>')
        objects.append(
            f'  <object id="{oid}" p:UUID="{uuid.uuid5(NS_ID, "object/" + n)}" type="model">\n'
            f"   <components>\n"
            f'    <component p:path="/{path}" objectid="{mid}" p:UUID="{uuid.uuid5(NS_ID, "component/" + n)}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n'
            f"   </components>\n"
            f"  </object>"
        )
        items.append(
            f'  <item objectid="{oid}" p:UUID="{uuid.uuid5(NS_ID, "item/" + n)}" '
            f'transform="1 0 0 0 1 0 0 0 1 {fmt(x)} {fmt(y)} 0" printable="1"/>'
        )
        extra = "".join(f'\n    <metadata key="{k}" value="{v}"/>' for k, v in SETTINGS.items())
        settings.append(
            f'  <object id="{oid}">\n'
            f'    <metadata key="name" value="{escape(n)}"/>\n'
            f'    <metadata key="extruder" value="1"/>{extra}\n'
            f'    <metadata face_count="{len(faces)}"/>\n'
            f'    <part id="{mid}" subtype="normal_part">\n'
            f'      <metadata key="name" value="{escape(n)}"/>\n'
            f'      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n'
            f"    </part>\n"
            f"  </object>"
        )
    for i, (title, _) in enumerate(PLATES):
        instances = "".join(
            f"\n    <model_instance>\n"
            f'      <metadata key="object_id" value="{oid}"/>\n'
            f'      <metadata key="instance_id" value="0"/>\n'
            f'      <metadata key="identify_id" value="{100 + oid}"/>\n'
            f"    </model_instance>"
            for j, _, _, oid, *_ in placed
            if j == i
        )
        settings.append(
            f"  <plate>\n"
            f'    <metadata key="plater_id" value="{i + 1}"/>\n'
            f'    <metadata key="plater_name" value="{escape(title)}"/>\n'
            f'    <metadata key="locked" value="false"/>{instances}\n'
            f"  </plate>"
        )

    nl = "\n"
    files["3D/3dmodel.model"] = f"""<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">
 <metadata name="Application">BambuStudio-02.08.02.61</metadata>
 <metadata name="BambuStudio:3mfVersion">1</metadata>
 <metadata name="Title">BazLoader feed bench rig</metadata>
 <resources>
{nl.join(objects)}
 </resources>
 <build p:UUID="{uuid.uuid5(NS_ID, 'build')}">
{nl.join(items)}
 </build>
</model>
"""
    files["3D/_rels/3dmodel.model.rels"] = f"""<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
{nl.join(rels)}
</Relationships>
"""
    files["Metadata/model_settings.config"] = f"""<?xml version="1.0" encoding="UTF-8"?>
<config>
{nl.join(settings)}
</config>
"""
    profile = json.loads(PROFILE.read_text())
    # The first entry lists the process keys that differ from the system preset (the profile has none).
    changed = {k for k, v in SETTINGS.items() if profile[k] != v}
    profile.update(SETTINGS)
    profile["different_settings_to_system"][0] = ";".join(sorted(changed))
    files["Metadata/project_settings.config"] = json.dumps(profile, indent=4, ensure_ascii=False) + "\n"
    files["_rels/.rels"] = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>
"""
    files["[Content_Types].xml"] = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
 <Default Extension="png" ContentType="image/png"/>
</Types>
"""
    OUT.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for path in ["[Content_Types].xml", "_rels/.rels", *sorted(set(files) - {"[Content_Types].xml", "_rels/.rels"})]:
            z.writestr(zipfile.ZipInfo(path, (2026, 1, 1, 0, 0, 0)), files[path], zipfile.ZIP_DEFLATED)
    print(f"wrote out/{OUT.name}")


def mesh_faults(name: str, verts, faces) -> list[str]:
    """How a mesh read back from the file differs from the build123d solid it was made from."""
    edges: dict[tuple[int, int], int] = {}
    for a, b, c in faces:
        for e in ((a, b), (b, c), (c, a)):
            key = (min(e), max(e))
            edges[key] = edges.get(key, 0) + 1
    volume = 0.0
    for a, b, c in faces:
        (ax, ay, az), (bx, by, bz), (cx, cy, cz) = verts[a], verts[b], verts[c]
        volume += (ax * (by * cz - bz * cy) - ay * (bx * cz - bz * cx) + az * (bx * cy - by * cx)) / 6
    solid = build.PARTS[name]()
    size = solid.bounding_box().size
    x0, y0, z0, x1, y1, z1 = bbox(verts)
    faults = []
    if any(n != 2 for n in edges.values()):
        faults.append(f"not closed: {sum(n != 2 for n in edges.values())} edges not used exactly twice")
    if abs(volume - solid.volume) > 0.005 * solid.volume:
        faults.append(f"volume {volume:.1f}, the solid has {solid.volume:.1f}")
    if max(abs(x1 - x0 - size.X), abs(y1 - y0 - size.Y), abs(z1 - z0 - size.Z)) > 0.05:
        faults.append(f"size {x1 - x0:.2f} x {y1 - y0:.2f} x {z1 - z0:.2f}, the solid is {size.X:.2f} x {size.Y:.2f} x {size.Z:.2f}")
    print(f"  {name:22s} volume {solid.volume:9.1f} solid, {volume:9.1f} mesh, {len(faces):6d} triangles")
    return faults


def verify(path: Path = OUT) -> None:
    """Read the 3MF back: every mesh matches its solid (closed, same volume within 0.5 %, same size
    within 0.05 mm), and every object sits on its own plate, MARGIN clear of the edges and of each other."""
    z = zipfile.ZipFile(path)
    model = z.read("3D/3dmodel.model").decode()
    config = z.read("Metadata/model_settings.config").decode()
    names = dict(re.findall(r'<object id="(\d+)">\s*<metadata key="name" value="([^"]+)"', config))
    paths = dict(re.findall(r'<object id="(\d+)"[^>]*>\s*<components>\s*<component p:path="/([^"]+)"', model))
    moves = {o: tuple(map(float, t.split()[9:12])) for o, t in re.findall(r'<item objectid="(\d+)"[^>]*transform="([^"]+)"', model)}
    plates = re.findall(r"<plate>(.*?)</plate>", config, re.S)
    if len(plates) != len(PLATES):
        raise SystemExit(f"{len(plates)} plates in the file, expected {len(PLATES)}")
    faults = []
    for i, plate in enumerate(plates):
        ox, oy = plate_origin(i, len(plates))
        title = re.search(r'"plater_name" value="([^"]*)"', plate).group(1)
        print(f"plate {i + 1} '{title}':")
        boxes = []
        for oid in re.findall(r'"object_id" value="(\d+)"', plate):
            text = z.read(paths[oid]).decode()
            verts = [tuple(map(float, v)) for v in re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', text)]
            faces = [tuple(map(int, t)) for t in re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', text)]
            faults += [f"{names[oid]}: {f}" for f in mesh_faults(names[oid], verts, faces)]
            dx, dy, dz = moves[oid]
            x0, y0, z0, x1, y1, z1 = bbox(verts)
            box = (x0 + dx - ox, y0 + dy - oy, x1 + dx - ox, y1 + dy - oy)
            if min(box) < MARGIN - 1e-6 or max(box) > BED - MARGIN + 1e-6 or abs(z0 + dz) > 1e-6 or z1 + dz > BED:
                faults.append(f"{names[oid]} is not inside plate {i + 1}: {box}")
            for other, b in boxes:
                if box[0] < b[2] + MARGIN and b[0] < box[2] + MARGIN and box[1] < b[3] + MARGIN and b[1] < box[3] + MARGIN:
                    faults.append(f"{names[oid]} is closer than {MARGIN:g} mm to {other} on plate {i + 1}")
            boxes.append((names[oid], box))
    if faults:
        raise SystemExit("FAILED:\n" + "\n".join(faults))
    print(f"ok: every mesh matches its solid, every object inside its plate, {MARGIN:g} mm clear of the edges and of each other")


if __name__ == "__main__":
    import sys

    if sys.argv[1:]:  # uv run python pack_3mf.py some.3mf: only check that file.
        verify(Path(sys.argv[1]))
    else:
        pack()
        verify()
