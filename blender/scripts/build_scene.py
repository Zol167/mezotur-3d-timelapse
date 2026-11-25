"""Mezőtúr 3D jelenet felépítése a QGIS-exportokból.

A szkript CSAK a "Generalt" gyűjteményt építi újra, minden más (kamerák, fények,
kézi modellek, anyagok) megmarad a fájlban.

Első futtatás (még nincs blender/mezotur.blend):
    blender --python blender/scripts/build_scene.py
Utána mindig a meglévő fájllal:
    blender blender/mezotur.blend --python blender/scripts/build_scene.py
"""
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config
import geo
import heights
import meshgen
import roofs
import scene

for mod in (config, geo, heights, roofs, meshgen, scene):  # újrafuttatáskor a friss kód töltődjön be
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
    if scene.is_new_file():
        if config.MAIN_BLEND.exists():
            raise SystemExit(
                f"\n!!! {config.MAIN_BLEND} már létezik – nem írom felül.\n"
                f"    Futtasd így: blender {config.MAIN_BLEND.relative_to(config.ROOT)} "
                f"--python blender/scripts/build_scene.py\n"
            )
        scene.remove_startup_objects()
        scene.initial_render_setup()

    coll = scene.reset_collection(config.GENERATED_COLLECTION)

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
    scene.mesh_object("Talaj", v, f, coll, mat["talaj"])

    # Víz: felületek + vonalas vízfolyások
    v, f = geo.flat_polygons(load_optional("vizfeluletek"), origin, config.Z_WATER, min_area=10)
    scene.mesh_object("Vizfeluletek", v, f, coll, mat["viz"])
    v, f, n = meshgen.ribbons(
        load_optional("vizfolyasok"), origin, config.Z_WATERWAY,
        lambda p: None if p.get("tunnel") in ("culvert", "yes")
        else config.WATERWAY_WIDTHS.get(p.get("waterway")),
    )
    scene.mesh_object("Vizfolyasok", v, f, coll, mat["viz"])
    print(f"Vízfolyások: {n}")

    # Utak – szilárd burkolatú és földút külön objektumban
    utak = load_optional("utak")
    v, f, n1 = meshgen.ribbons(utak, origin, config.Z_ROAD,
                               lambda p: None if is_unpaved(p) else road_width(p))
    scene.mesh_object("Utak", v, f, coll, mat["ut"])
    v, f, n2 = meshgen.ribbons(utak, origin, config.Z_ROAD_DIRT,
                               lambda p: road_width(p) if is_unpaved(p) else None)
    scene.mesh_object("Foldutak", v, f, coll, mat["foldut"])
    print(f"Utak: {n1} szilárd, {n2} földút")

    # Vasút – csak a működő vonalak (a megszűntek majd az idővonalhoz kellenek)
    v, f, n = meshgen.ribbons(load_optional("vasut"), origin, config.Z_RAIL,
                              lambda p: config.RAIL_WIDTHS.get(p.get("railway")))
    scene.mesh_object("Vasut", v, f, coll, mat["vasut"])
    print(f"Vasútvonal-szakaszok: {n}")

    # Épületek – egyetlen mesh, laponként building_id / height / height_src attribútummal
    zones = heights.load_zones(load_optional("magassag_zonak"), origin)
    kezi = load_optional("kezi_epuletek")
    auto, dropped = geo.replace_with_manual(geo.load_features(config.FILES["epuletek"]), kezi)
    epuletek = auto + kezi
    if kezi:
        print(f"Kézi épületek: {len(kezi)}, ezek {dropped} automatikus épületet váltottak ki")
    v, f, attrs, count, stats, roof_stats = meshgen.buildings(
        epuletek, origin, zones, config, tessellate_polygon)
    building_mats = [
        scene.palette_material("Fal", "rnd", config.WALL_PALETTE),
        scene.palette_material("Teto", "rnd2", config.ROOF_PALETTE, roughness=0.7),
        scene.material("Lapos_teto", scene.hex_to_linear(config.FLAT_ROOF_COLOR)),
    ]
    scene.mesh_object("Epuletek", v, f, coll, building_mats, attrs)
    print(f"Épületek: {count} ({len(v)} csúcs, {len(f)} lap)")
    print("  magasság forrása: " + ", ".join(f"{k}: {n}" for k, n in stats.most_common()))
    print("  tetők: " + ", ".join(f"{k}: {n}" for k, n in roof_stats.most_common()))

    scene.ensure_sun()
    scene.ensure_camera(size)
    scene.fix_viewport_clipping(size)

    bpy.ops.wm.save_as_mainfile(filepath=str(config.MAIN_BLEND))
    print(f"Mentve: {config.MAIN_BLEND}")


main()
