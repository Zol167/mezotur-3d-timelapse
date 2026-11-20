"""Épületmagasság becslése, ha nincs mért adat.

Sorrend (az első, ami ad értéket, nyer):
  1. kézi zóna a QGIS `magassag_zonak` rétegéből (emelet vagy magassag mező)
  2. mért adat: Overture `height`, majd `num_floors`
  3. épülettípus (class / building mező) a config.CLASS_HEIGHTS alapján
  4. alapterület a config.AREA_HEIGHTS alapján
Végül egy kis, helyhez kötött véletlen eltérés, hogy ne legyen minden ház egyforma.
"""
import zlib

import geo


def _num(v):
    if isinstance(v, (int, float)) and v > 0:
        return float(v)
    if isinstance(v, str):
        try:
            f = float(v.replace(",", "."))
            return f if f > 0 else None
        except ValueError:
            return None
    return None


def load_zones(features, origin):
    """Zónák: (gyűrű, magasság) párok, a kisebb területű zóna előbb (az nyer)."""
    zones = []
    for feat in features:
        props = feat.get("properties") or {}
        h = _num(props.get("magassag"))
        if h is None:
            floors = _num(props.get("emelet"))
            h = floors * 3.2 if floors else None
        if h is None:
            continue
        for rings in geo.iter_polygons(feat["geometry"]):
            ring = geo.shift(geo.clean_ring(rings[0]), origin)
            if len(ring) >= 3:
                zones.append((abs(geo.signed_area(ring)), ring, h))
    zones.sort(key=lambda z: z[0])
    return [(ring, h) for _, ring, h in zones]


def _bucket(area, table):
    for limit, h in table:
        if area < limit:
            return h
    return table[-1][1]


def _jitter(cx, cy, amount):
    """Determinisztikus ±amount szorzó a hely alapján (minden futásnál ugyanaz)."""
    seed = zlib.crc32(f"{cx:.0f},{cy:.0f}".encode())
    return 1.0 + amount * ((seed % 2001) / 1000.0 - 1.0)


def estimate(props, ring_local, zones, cfg):
    """Visszaad: (magasság, forrás) – a forrás a hibakereséshez hasznos."""
    cx, cy = geo.centroid(ring_local)

    for zring, h in zones:
        if geo.point_in_ring(cx, cy, zring):
            return h, "zona"

    h = _num(props.get("height"))
    if h:
        return h, "meres"
    floors = _num(props.get("num_floors")) or _num(props.get("building:levels"))
    if floors:
        return floors * cfg.FLOOR_HEIGHT, "emelet"

    kind = (props.get("class") or props.get("building") or "").strip().lower()
    h = cfg.CLASS_HEIGHTS.get(kind)
    area = abs(geo.signed_area(ring_local))
    if h is None:
        h, src = _bucket(area, cfg.AREA_HEIGHTS), "terulet"
    else:
        src = "tipus"
    return h * _jitter(cx, cy, cfg.HEIGHT_VARIATION), src
