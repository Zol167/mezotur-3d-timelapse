"""Blender-specifikus részek: objektumok, anyagok, fény, kamera."""
import math

import bpy


def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def material(name, rgba):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Roughness"].default_value = 0.9
    mat.diffuse_color = rgba  # viewport Solid módban is ez a szín látszik
    return mat


def mesh_object(name, verts, faces, mat=None, attributes=None):
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
    bpy.context.scene.collection.objects.link(obj)
    return obj


def add_sun():
    light = bpy.data.lights.new("Nap", type="SUN")
    light.energy = 3.0
    light.angle = math.radians(2)
    obj = bpy.data.objects.new("Nap", light)
    obj.rotation_euler = (math.radians(50), 0, math.radians(135))
    bpy.context.scene.collection.objects.link(obj)


def add_camera(size_m):
    """Ferde madártávlati kamera délkelet felől, a terület közepére nézve."""
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


def setup_render():
    scene = bpy.context.scene
    # Az Eevee belső neve verziónként eltér (4.2–4.x: BLENDER_EEVEE_NEXT)
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
