"""Mezőtúr 3D jelenet felépítése a QGIS-exportokból.

Futtatás a repó gyökeréből:
    blender --python blender/scripts/build_scene.py          # megnyitja a Blendert a kész jelenettel
    blender -b --python blender/scripts/build_scene.py       # háttérben, csak elmenti a .blend-et
"""
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config
import geo
import heights
import meshgen
import scene

for mod in (config, geo, heights, meshgen, scene):  # újrafuttatáskor a friss kód töltődjön be
    importlib.reload(mod)

import bpy
from mathutils.geometry import tessellate_polygon


def load_optional(key):
    path = config.FILES[key]
    if path.exists():
        return geo.load_features(path)
    print(f"  (nincs {path.name}, kihagyva)")
    return []


def road_width(p):
    return config.ROAD_WIDTHS.get(p.get("highway"))


def is_unpaved(p):
    return p.get("highway") == "track" or p.get("surface") in config.UNPAVED_SURFACES


def main():
    scene.clear_scene()

    # Terület és origó
    terulet = geo.load_features(config.FILES["terulet"])
    origin = geo.origin_from(terulet)
    x0, y0, x1, y1 = geo.bbox(terulet)
    size = max(x1 - x0, y1 - y0)
    bpy.context.scene["eov_origo"] = origin
    print(f"Origó (EOV): {origin}, terület mérete: {size:.0f} m")

    mat = {k: scene.material(k.capitalize(), rgba) for k, rgba in config.COLORS.items()}

    # Talaj
    v, f = geo.flat_polygons(terulet, origin, config.Z_GROUND)
    scene.mesh_object("Talaj", v, f, mat["talaj"])

    # Víz: felületek + vonalas vízfolyások
    v, f = geo.flat_polygons(load_optional("vizfeluletek"), origin, config.Z_WATER, min_area=10)
    scene.mesh_object("Vizfeluletek", v, f, mat["viz"])
    v, f, n = meshgen.ribbons(
        load_optional("vizfolyasok"), origin, config.Z_WATERWAY,
        lambda p: None if p.get("tunnel") in ("culvert", "yes")
        else config.WATERWAY_WIDTHS.get(p.get("waterway")),
    )
    scene.mesh_object("Vizfolyasok", v, f, mat["viz"])
    print(f"Vízfolyások: {n}")

    # Utak – szilárd burkolatú és földút külön objektumban
    utak = load_optional("utak")
    v, f, n1 = meshgen.ribbons(utak, origin, config.Z_ROAD,
                               lambda p: None if is_unpaved(p) else road_width(p))
    scene.mesh_object("Utak", v, f, mat["ut"])
    v, f, n2 = meshgen.ribbons(utak, origin, config.Z_ROAD_DIRT,
                               lambda p: road_width(p) if is_unpaved(p) else None)
    scene.mesh_object("Foldutak", v, f, mat["foldut"])
    print(f"Utak: {n1} szilárd, {n2} földút")

    # Vasút – csak a működő vonalak (a megszűntek majd az idővonalhoz kellenek)
    v, f, n = meshgen.ribbons(load_optional("vasut"), origin, config.Z_RAIL,
                              lambda p: config.RAIL_WIDTHS.get(p.get("railway")))
    scene.mesh_object("Vasut", v, f, mat["vasut"])
    print(f"Vasútvonal-szakaszok: {n}")

    # Épületek – egyetlen mesh, laponként building_id / height / height_src attribútummal
    zones = heights.load_zones(load_optional("magassag_zonak"), origin)
    epuletek = geo.load_features(config.FILES["epuletek"]) + load_optional("kezi_epuletek")
    v, f, attrs, count, stats = meshgen.buildings(epuletek, origin, zones, config, tessellate_polygon)
    scene.mesh_object("Epuletek", v, f, mat["epulet"], attrs)
    print(f"Épületek: {count} ({len(v)} csúcs, {len(f)} lap)")
    print("  magasság forrása: " + ", ".join(f"{k}: {n}" for k, n in stats.most_common()))

    scene.add_sun()
    scene.add_camera(size)
    scene.setup_render()
    scene.fix_viewport_clipping(size)

    bpy.ops.wm.save_as_mainfile(filepath=str(config.OUTPUT_BLEND))
    print(f"Mentve: {config.OUTPUT_BLEND}")


main()
