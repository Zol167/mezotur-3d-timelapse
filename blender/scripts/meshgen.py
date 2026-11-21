"""Mesh-adatok (csúcsok, lapok, attribútumok) előállítása – bpy nélkül.

A háromszögelést (udvaros épületek teteje) kívülről kapjuk meg: Blenderben a
mathutils.geometry.tessellate_polygon, tesztben egy helyettesítő függvény.
"""
from collections import Counter

import geo
import heights
import roofs

SOURCE_CODES = {"zona": 0, "meres": 1, "emelet": 2, "tipus": 3, "terulet": 4}
ROOF_CODES = {"flat": 0, "gable": 1, "hip": 2, "osszetett": 3}


def buildings(features, origin, zones, cfg, tessellate):
    """Épületek falakkal és tetővel.

    Laponkénti attribútumok: building_id, height (falmagasság), height_src,
    roof_type, rnd / rnd2 (0..1, a fal- és tetőszín kiválasztásához),
    material_index (0 fal, 1 cseréptető, 2 lapos tető).
    """
    verts, faces, mats = [], [], []
    attrs = {k: [] for k in ("building_id", "height", "height_src", "roof_type", "rnd", "rnd2")}
    stats, roof_stats = Counter(), Counter()
    bid = 0
    for feat in features:
        props = feat.get("properties") or {}
        kind = (props.get("class") or props.get("building") or "").strip().lower()
        for rings in geo.iter_polygons(feat["geometry"]):
            outer = geo.clean_ring(rings[0])
            if len(outer) < 3 or abs(geo.signed_area(outer)) < cfg.MIN_AREA:
                continue
            outer = geo.ccw(geo.shift(outer, origin))
            holes = []
            for r in rings[1:]:
                r = geo.clean_ring(r)
                if len(r) >= 3 and abs(geo.signed_area(r)) >= 1.0:
                    holes.append(geo.cw(geo.shift(r, origin)))

            h, src, override = heights.estimate(props, outer, zones, cfg)
            area = abs(geo.signed_area(outer))
            plan, pitch, parts = roofs.choose(kind, src, h, area, bool(holes), outer, cfg, override)
            if plan == "flat":
                roof = "flat"
            elif len(parts) > 1:
                roof = "osszetett"
            else:
                roof = parts[0][1]
            stats[src] += 1
            roof_stats[roof] += 1

            start = len(faces)
            _walls(verts, faces, mats, outer, holes, h, flat_top=(plan == "flat"), tessellate=tessellate)
            if plan != "flat":
                for box, kind_part in parts:
                    if kind_part == "flat":
                        roofs.add_flat_rect(verts, faces, mats, box, h)
                    else:
                        roofs.add_roof(verts, faces, mats, box, h, kind_part, pitch, cfg)
            n = len(faces) - start

            cx, cy = geo.centroid(outer)
            attrs["building_id"] += [bid] * n
            attrs["height"] += [h] * n
            attrs["height_src"] += [SOURCE_CODES[src]] * n
            attrs["roof_type"] += [ROOF_CODES[roof]] * n
            attrs["rnd"] += [heights.stable_random(cx, cy, "fal")] * n
            attrs["rnd2"] += [heights.stable_random(cx, cy, "teto")] * n
            bid += 1
    attrs["material_index"] = mats
    return verts, faces, attrs, bid, stats, roof_stats


def _walls(verts, faces, mats, outer, holes, h, flat_top, tessellate):
    """Falak minden gyűrűre; lapos tetőnél felső lap is (udvarral, ha van)."""
    top_index = []  # a felső csúcsok indexei, gyűrűnként összefűzve
    for ring in [outer] + holes:
        n, b = len(ring), len(verts)
        verts += [(x, y, 0.0) for x, y in ring]
        verts += [(x, y, h) for x, y in ring]
        for i in range(n):
            j = (i + 1) % n
            faces.append((b + i, b + j, b + n + j, b + n + i))
            mats.append(roofs.MAT_WALL)
        top_index += list(range(b + n, b + 2 * n))

    if not flat_top:
        return
    if not holes:
        faces.append(tuple(top_index))
        mats.append(roofs.MAT_FLAT)
        return
    flat = [p for ring in [outer] + holes for p in ring]
    try:
        tris = tessellate([outer] + holes)
    except Exception:
        tris = []
    if not tris:  # hibás geometria: udvar nélküli tető
        faces.append(tuple(top_index[: len(outer)]))
        mats.append(roofs.MAT_FLAT)
    for tri in tris:
        a, b, c = tri
        if geo.signed_area([flat[a], flat[b], flat[c]]) < 0:  # felfelé nézzen a normál
            b, c = c, b
        faces.append((top_index[a], top_index[b], top_index[c]))
        mats.append(roofs.MAT_FLAT)


def ribbons(features, origin, z, width_of):
    """Vonalas elemekből szalagok. width_of(props) -> szélesség vagy None (kihagyás)."""
    verts, faces = [], []
    count = 0
    for feat in features:
        props = feat.get("properties") or {}
        w = width_of(props)
        if not w:
            continue
        for line in geo.iter_lines(feat["geometry"]):
            pts = geo.dedup(geo.shift(line, origin))
            if len(pts) < 2:
                continue
            left, right = geo.ribbon(pts, w / 2.0)
            b = len(verts)
            for (lx, ly), (rx, ry) in zip(left, right):
                verts += [(lx, ly, z), (rx, ry, z)]
            for i in range(len(pts) - 1):
                l0, r0, l1, r1 = b + 2 * i, b + 2 * i + 1, b + 2 * i + 2, b + 2 * i + 3
                faces.append((l0, r0, r1, l1))
            count += 1
    return verts, faces, count
