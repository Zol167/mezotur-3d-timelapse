"""Tetők: tetőtípus kiválasztása és a tető geometriája – tiszta Python, bpy nélkül.

Az alaprajzra egy elforgatott befoglaló téglalapot (OBB) illesztünk, és arra
teszünk nyereg- vagy sátortetőt. Ha az alaprajz nem eléggé téglalap alakú
(pl. L alakú polgárház), vagy túl nagy, lapos tetőt kap.
"""
import math

import geo

MAT_WALL, MAT_ROOF, MAT_FLAT = 0, 1, 2


def convex_hull(pts):
    pts = sorted(set(pts))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def obb(pts):
    """Legkisebb területű elforgatott befoglaló téglalap.

    Visszaad: (cx, cy, ux, uy, L, W) – u a hosszabbik tengely egységvektora, L >= W.
    """
    hull = convex_hull(pts)
    best = None
    for i in range(len(hull)):
        x1, y1 = hull[i]
        x2, y2 = hull[(i + 1) % len(hull)]
        length = math.hypot(x2 - x1, y2 - y1)
        if length < 1e-9:
            continue
        ux, uy = (x2 - x1) / length, (y2 - y1) / length
        vx, vy = -uy, ux
        s = [p[0] * ux + p[1] * uy for p in hull]
        t = [p[0] * vx + p[1] * vy for p in hull]
        area = (max(s) - min(s)) * (max(t) - min(t))
        if best is None or area < best[0]:
            best = (area, ux, uy, min(s), max(s), min(t), max(t))
    _, ux, uy, s0, s1, t0, t1 = best
    vx, vy = -uy, ux
    sm, tm = (s0 + s1) / 2, (t0 + t1) / 2
    cx, cy = ux * sm + vx * tm, uy * sm + vy * tm
    L, W = s1 - s0, t1 - t0
    if W > L:  # u legyen a hosszabbik tengely
        ux, uy = vx, vy
        L, W = W, L
    return cx, cy, ux, uy, L, W


def _cluster(values, tol):
    """Közeli koordináták összevonása: rendezett reprezentánsok listája."""
    vals = sorted(values)
    groups = [[vals[0]]]
    for v in vals[1:]:
        if v - groups[-1][-1] < tol:
            groups[-1].append(v)
        else:
            groups.append([v])
    return [sum(g) / len(g) for g in groups]


def _merge_runs(inside, nx, ny):
    """Rácscellákból téglalapok: soronként futamok, majd az azonos futamok
    összevonása függőlegesen. Visszaad: [(i0, i1, j0, j1)]."""
    rects, active = [], {}
    for j in range(ny):
        runs, i = set(), 0
        while i < nx:
            if inside[i][j]:
                i0 = i
                while i < nx and inside[i][j]:
                    i += 1
                runs.add((i0, i))
            else:
                i += 1
        for key in list(active):
            if key not in runs:
                rects.append((key[0], key[1], active.pop(key), j))
        for key in runs:
            active.setdefault(key, j)
    rects += [(k[0], k[1], j0, ny) for k, j0 in active.items()]
    return rects


def rect_partition(ring, box, cfg):
    """Közel derékszögű alaprajz (L, T, U alak) felbontása téglalapokra.

    Visszaad: téglalapok listája (cx, cy, ux, uy, L, W) formában, vagy None,
    ha az alaprajz nem derékszögű, vagy túl sok darabra esne szét.
    """
    cx, cy, ux, uy, _L, _W = box
    vx, vy = -uy, ux
    local = [((x - cx) * ux + (y - cy) * uy, (x - cx) * vx + (y - cy) * vy) for x, y in ring]

    max_dev = math.sin(math.radians(cfg.RECTILINEAR_TOLERANCE_DEG))
    for i in range(len(local)):
        (x1, y1), (x2, y2) = local[i], local[(i + 1) % len(local)]
        length = math.hypot(x2 - x1, y2 - y1)
        if length > 0.5 and min(abs(x2 - x1), abs(y2 - y1)) / length > max_dev:
            return None

    xs = _cluster([p[0] for p in local], cfg.SNAP_TOLERANCE)
    ys = _cluster([p[1] for p in local], cfg.SNAP_TOLERANCE)
    nx, ny = len(xs) - 1, len(ys) - 1
    if nx < 1 or ny < 1:
        return None
    inside = [[geo.point_in_ring((xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2, local)
               for j in range(ny)] for i in range(nx)]

    by_rows = _merge_runs(inside, nx, ny)
    transposed = [[inside[i][j] for i in range(nx)] for j in range(ny)]
    by_cols = [(i0, i1, j0, j1) for j0, j1, i0, i1 in _merge_runs(transposed, ny, nx)]
    best = min((by_rows, by_cols), key=len)
    if not best or len(best) > cfg.MAX_ROOF_PARTS:
        return None

    out = []
    for i0, i1, j0, j1 in best:
        x0, x1, y0, y1 = xs[i0], xs[i1], ys[j0], ys[j1]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        wx, wy = cx + ux * mx + vx * my, cy + uy * mx + vy * my
        lx, ly = x1 - x0, y1 - y0
        if lx >= ly:
            out.append((wx, wy, ux, uy, lx, ly))
        else:
            out.append((wx, wy, vx, vy, ly, lx))
    return out


def choose(kind, src, wall_h, area, has_holes, ring, cfg, override=None):
    """Tetőterv egy épülethez.

    Visszaad: (típus, hajlásszög, darabok). Típus: 'flat' | 'pitched';
    darabok: [(box, 'gable'|'hip'|'flat')] – minden téglalap darab külön tetőt kap.
    override (zónából): 'lapos' | 'nyereg' | 'sator' | None (automatikus).
    """
    if override == "lapos" or has_holes or src == "meres":
        return "flat", 0, None
    if override is None and (kind in cfg.FLAT_ROOF_CLASSES or
                             (src == "zona" and wall_h >= cfg.FLAT_ZONE_HEIGHT)):
        return "flat", 0, None

    pitch = None
    for limit, _h, p in cfg.AREA_CLASSES:
        if area < limit:
            pitch = p
            break
    if pitch is None:
        return "flat", 0, None

    box = obb(ring)
    L, W = box[4], box[5]
    if L * W <= 0:
        return "flat", 0, None
    rects = [box] if area / (L * W) >= cfg.ROOF_MIN_RECT else rect_partition(ring, box, cfg)
    if not rects:
        return "flat", 0, None

    parts = []
    for r in rects:
        rl, rw = r[4], r[5]
        if rw < cfg.ROOF_MIN_PART_WIDTH or rw > cfg.ROOF_MAX_WIDTH:
            parts.append((r, "flat"))
        elif override == "sator" or (override is None and rl / rw < cfg.HIP_RATIO):
            parts.append((r, "hip"))
        else:
            parts.append((r, "gable"))
    if all(k == "flat" for _r, k in parts):
        return "flat", 0, None
    return "pitched", pitch, parts


def add_flat_rect(verts, faces, mats, box, z):
    """Lapos tetőlap egy téglalap darabra (túl keskeny vagy túl széles szárny)."""
    cx, cy, ux, uy, L, W = box
    vx, vy = -uy, ux
    a, b = L / 2, W / 2
    base = len(verts)
    for s, t in ((-a, -b), (a, -b), (a, b), (-a, b)):
        verts.append((cx + ux * s + vx * t, cy + uy * s + vy * t, z))
    faces.append((base, base + 1, base + 2, base + 3))
    mats.append(MAT_FLAT)


def add_roof(verts, faces, mats, box, wall_h, kind, pitch, cfg):
    """Tetőlapok hozzáadása. Nyeregtetőnél az oromfal fal-anyagot kap."""
    cx, cy, ux, uy, L, W = box
    vx, vy = -uy, ux
    o = cfg.ROOF_OVERHANG
    a = L / 2 + (o if kind == "hip" else 0.0)  # nyeregtetőnél az oromfal a fal síkjában
    b = W / 2 + o
    if kind == "hip":
        pitch -= cfg.HIP_PITCH_DELTA  # a sátortető laposabb
    rise = min(b * math.tan(math.radians(pitch)), cfg.ROOF_MAX_RISE)
    h, top = wall_h, wall_h + rise

    def p(s, t, z):
        return (cx + ux * s + vx * t, cy + uy * s + vy * t, z)

    base = len(verts)
    verts += [p(-a, -b, h), p(a, -b, h), p(a, b, h), p(-a, b, h)]
    p0, p1, p2, p3 = range(base, base + 4)

    e = a if kind == "gable" else max(a - b, 0.0)  # gerinc félhossza
    if e < 0.05:  # sátortető gerinc nélkül: gúla
        verts.append(p(0, 0, top))
        apex = base + 4
        for f in ((p0, p1, apex), (p1, p2, apex), (p2, p3, apex), (p3, p0, apex)):
            faces.append(f)
            mats.append(MAT_ROOF)
        return 4

    verts += [p(-e, 0, top), p(e, 0, top)]
    r0, r1 = base + 4, base + 5
    side = MAT_WALL if kind == "gable" else MAT_ROOF
    for f, m in (((p0, p1, r1, r0), MAT_ROOF), ((p2, p3, r0, r1), MAT_ROOF),
                 ((p1, p2, r1), side), ((p3, p0, r0), side)):
        faces.append(f)
        mats.append(m)
    return 4
