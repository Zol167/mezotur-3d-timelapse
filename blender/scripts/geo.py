"""GeoJSON beolvasás és alap geometria – tiszta Python, bpy nélkül (tesztelhető)."""
import json
import math


def load_features(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)["features"]


def iter_polygons(geometry):
    """Minden (Multi)Polygonból a gyűrűk listáját adja: [külső, lyuk1, ...]."""
    if not geometry:
        return
    t, coords = geometry["type"], geometry["coordinates"]
    if t == "Polygon":
        yield coords
    elif t == "MultiPolygon":
        yield from coords


def iter_lines(geometry):
    """(Multi)LineString -> pontlisták."""
    if not geometry:
        return
    t, coords = geometry["type"], geometry["coordinates"]
    if t == "LineString":
        yield coords
    elif t == "MultiLineString":
        yield from coords


def clean_ring(ring):
    """Lezáró pont eldobása, egymást követő duplikátumok kiszűrése."""
    pts = [(p[0], p[1]) for p in ring]
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts.pop()
    return dedup(pts)


def dedup(pts):
    out = []
    for p in pts:
        p = (p[0], p[1])
        if not out or p != out[-1]:
            out.append(p)
    return out


def signed_area(pts):
    a = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        a += x1 * y2 - x2 * y1
    return a / 2.0


def ccw(pts):
    """Óramutatóval ellentétes irány."""
    return pts if signed_area(pts) >= 0 else pts[::-1]


def cw(pts):
    return pts[::-1] if signed_area(pts) > 0 else pts


def centroid(pts):
    n = len(pts)
    return sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n


def point_in_ring(x, y, ring):
    """Sugárkövetéses pont-a-poligonban teszt."""
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def bbox(features):
    xs, ys = [], []
    for feat in features:
        for rings in iter_polygons(feat["geometry"]):
            for x, y in clean_ring(rings[0]):
                xs.append(x)
                ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


def origin_from(features):
    """Az origó a terület közepe, egész méterre kerekítve."""
    x0, y0, x1, y1 = bbox(features)
    return round((x0 + x1) / 2), round((y0 + y1) / 2)


def shift(pts, origin):
    ox, oy = origin
    return [(x - ox, y - oy) for x, y in pts]


def flat_polygons(features, origin, z, min_area=0.0):
    """Lapos poligonok (talaj, víz) adott magasságban, lyukak nélkül."""
    verts, faces = [], []
    for feat in features:
        for rings in iter_polygons(feat["geometry"]):
            ring = clean_ring(rings[0])
            if len(ring) < 3 or abs(signed_area(ring)) < min_area:
                continue
            ring = ccw(shift(ring, origin))
            b = len(verts)
            verts += [(x, y, z) for x, y in ring]
            faces.append(tuple(range(b, b + len(ring))))
    return verts, faces


def ribbon(pts, half_width, max_miter=2.5):
    """Vonalból szalag (út, csatorna): bal és jobb oldali pontsor.

    A töréspontokban a két szakasz normálisának átlagával tolunk el (miter),
    hegyes szögeknél korlátozva, hogy ne szaladjon ki tüskébe.
    """
    n = len(pts)
    left, right = [], []
    for i in range(n):
        x, y = pts[i]
        normals = []
        if i > 0:
            normals.append(_seg_normal(pts[i - 1], pts[i]))
        if i < n - 1:
            normals.append(_seg_normal(pts[i], pts[i + 1]))
        nx = sum(v[0] for v in normals)
        ny = sum(v[1] for v in normals)
        length = math.hypot(nx, ny)
        if length < 1e-9:  # visszaforduló vonal
            nx, ny = normals[0]
            length = 1.0
        nx, ny = nx / length, ny / length
        cos_half = max(nx * normals[0][0] + ny * normals[0][1], 1.0 / max_miter)
        d = half_width / cos_half
        left.append((x + nx * d, y + ny * d))
        right.append((x - nx * d, y - ny * d))
    return left, right


def _seg_normal(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy) or 1.0
    return -dy / length, dx / length
