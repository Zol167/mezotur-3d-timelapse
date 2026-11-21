"""Blender-specifikus részek: gyűjtemény, objektumok, anyagok, fény, kamera.

Szabály: a szkript CSAK a "Generalt" gyűjteményt írja felül. Minden mást
(kamerák, fények, kézi modellek, anyagbeállítások) békén hagy, így azokon
szabadon dolgozhatsz Blenderben.
"""
import math

import bpy


def is_new_file():
    return not bpy.data.filepath


def remove_startup_objects():
    """Új fájlnál az alap kocka/fény/kamera eltávolítása."""
    for name in ("Cube", "Light", "Camera"):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def reset_collection(name):
    """A gyűjtemény tartalmának törlése (a gyűjtemény maga megmarad)."""
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
    for obj in list(coll.objects):
        data = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if isinstance(data, bpy.types.Mesh) and data.users == 0:
            bpy.data.meshes.remove(data)
    return coll


def material(name, rgba):
    """Meglévő anyagot újrahasznál és NEM írja felül – Blenderben szabadon állíthatod.
    Csak akkor kap alapszínt, ha most jön létre."""
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Roughness"].default_value = 0.9
    mat.diffuse_color = rgba  # viewport Solid módban is ez a szín látszik
    return mat


def mesh_object(name, verts, faces, collection, mat=None, attributes=None):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    mesh.update()
    for attr_name, values in (attributes or {}).items():
        if not values or len(values) != len(mesh.polygons):
            continue  # üres réteg, vagy a validate() eldobott hibás lapokat
        kind = "INT" if isinstance(values[0], int) else "FLOAT"
        attr = mesh.attributes.new(attr_name, kind, "FACE")
        attr.data.foreach_set("value", values)
    if mat:
        mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.hide_select = True  # véletlenül se lehessen kézzel átírni
    return obj


def ensure_sun():
    """Napfény – csak ha még nincs, a meglévőt nem bántja."""
    if bpy.data.objects.get("Nap"):
        return
    light = bpy.data.lights.new("Nap", type="SUN")
    light.energy = 3.0
    light.angle = math.radians(2)
    obj = bpy.data.objects.new("Nap", light)
    obj.rotation_euler = (math.radians(50), 0, math.radians(135))
    bpy.context.scene.collection.objects.link(obj)


def ensure_camera(size_m):
    """Áttekintő kamera – csak ha még nincs."""
    if bpy.data.objects.get("Kamera"):
        return
    target = bpy.data.objects.new("Kamera_cel", None)
    bpy.context.scene.collection.objects.link(target)

    cam_data = bpy.data.cameras.new("Kamera")
    cam_data.clip_start = 5.0
    cam_data.clip_end = size_m * 5
    cam = bpy.data.objects.new("Kamera", cam_data)
    d = size_m * 0.6
    cam.location = (d, -d, d * 0.8)
    bpy.context.scene.collection.objects.link(cam)

    track = cam.constraints.new("TRACK_TO")
    track.target = target
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
    bpy.context.scene.camera = cam


def initial_render_setup():
    """Csak új fájlnál – utána a render-beállítás a te dolgod."""
    scene = bpy.context.scene
    for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.55, 0.65, 0.75)


def fix_viewport_clipping(size_m):
    """Az alap 1000 m-es látótávolság kevés egy városhoz; a nagyobb clip_start
    csökkenti a lapos rétegek (út, víz) villódzását messziről."""
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        space.clip_start = 5.0
                        space.clip_end = size_m * 5
