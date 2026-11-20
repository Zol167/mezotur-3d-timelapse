"""Mesh-adatok (csúcsok, lapok, attribútumok) előállítása – bpy nélkül.

A háromszögelést (udvaros épületek teteje) kívülről kapjuk meg: Blenderben a
mathutils.geometry.tessellate_polygon, tesztben egy helyettesítő függvény.
"""
from collections import Counter

import geo
import heights

SOURCE_CODES = {"zona": 0, "meres": 1, "emelet": 2, "tipus": 3, "terulet": 4}


def buildings(features, origin, zones, cfg, tessellate):
    verts, faces = [], []
    attrs = {"building_id": [], "height": [], "height_src": []}
    stats = Counter()
    bid = 0
    for feat in features:
        props = feat.get("properties") or {}
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

            h, src = heights.estimate(props, outer, zones, cfg)
            stats[src] += 1
            n_faces = _extrude(verts, faces, outer, holes, h, tessellate)
            attrs["building_id"] += [bid] * n_faces
            attrs["height"] += [h] * n_faces
            attrs["height_src"] += [SOURCE_CODES[src]] * n_faces
            bid += 1
    return verts, faces, attrs, bid, stats


def _extrude(verts, faces, outer, holes, h, tessellate):
    """Falak minden gyűrűre + tetőlap. Visszaadja a létrehozott lapok számát."""
    start_faces = len(faces)
    top_index = []  # a tető csúcsainak indexei, gyűrűnként összefűzve
    for ring in [outer] + holes:
        n, b = len(ring), len(verts)
        verts += [(x, y, 0.0) for x, y in ring]
        verts += [(x, y, h) for x, y in ring]
        for i in range(n):
            j = (i + 1) % n
            faces.append((b + i, b + j, b + n + j, b + n + i))
        top_index += list(range(b + n, b + 2 * n))

    if not holes:
        faces.append(tuple(top_index))
    else:
        flat = [p for ring in [outer] + holes for p in ring]
        try:
            tris = tessellate([outer] + holes)
        except Exception:
            tris = []
        if not tris:  # hibás geometria: udvar nélküli tető
            faces.append(tuple(top_index[: len(outer)]))
        for tri in tris:
            a, b, c = tri
            pa, pb, pc = flat[a], flat[b], flat[c]
            if geo.signed_area([pa, pb, pc]) < 0:  # felfelé nézzen a normál
                b, c = c, b
            faces.append((top_index[a], top_index[b], top_index[c]))
    return len(faces) - start_faces


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
