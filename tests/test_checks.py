# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for mesh_check_rbx.checks, run inside real Blender.

    python tests/test_checks.py          (with the bpy module from PyPI installed)
    blender -b --python tests/test_checks.py
"""

import os
import sys

import bpy

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from mesh_check_rbx import checks  # noqa: E402

passed, failed = 0, 0


def test(fn):
    global passed, failed
    reset()
    try:
        fn()
        passed += 1
    except Exception as e:  # report and keep going
        failed += 1
        print(f"FAIL  {fn.__name__}: {type(e).__name__}: {e}")
    return fn


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "NONE"
    scene.unit_settings.scale_length = 1.0


def codes(objects=None, **settings):
    return {(i.obj, i.code) for i in checks.run(bpy.context, objects, checks.Settings(**settings))}


def severity(code, **settings):
    return {i.severity for i in checks.run(bpy.context, None, checks.Settings(**settings)) if i.code == code}


def cube(name="Cube", size=1.0, location=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name
    return obj


@test
def clean_cube_passes():
    cube()
    found = codes()
    assert found == set(), found


@test
def scene_units_warning():
    cube()
    bpy.context.scene.unit_settings.system = "METRIC"
    assert ("", "UNITS") in codes()
    bpy.context.scene.unit_settings.system = "NONE"
    bpy.context.scene.unit_settings.scale_length = 0.01
    assert ("", "UNITS") in codes()


@test
def plane_is_flat_and_open():
    bpy.ops.mesh.primitive_plane_add()
    found = codes()
    name = bpy.context.active_object.name
    assert (name, "FLAT") in found, found
    assert (name, "WATERTIGHT") in found, found


@test
def triangle_budget_counts_modifiers():
    obj = cube("Ball")
    mod = obj.modifiers.new("Subsurf", "SUBSURF")
    mod.levels = 4  # 6 faces * 4^4 quads * 2 = 3,072 triangles
    assert checks.count_triangles(obj, bpy.context.evaluated_depsgraph_get()) == 3072
    assert ("Ball", "TRIS") not in codes(preset="RIGID")
    mod.levels = 5  # 12,288 triangles
    assert ("Ball", "TRIS") in codes(preset="RIGID"), "over the 4k accessory budget"
    assert ("Ball", "TRIS") not in codes(preset="MESH"), "under the 20k mesh budget"
    mod.levels = 6  # 49,152 triangles
    assert ("Ball", "TRIS") in codes(preset="MESH")


@test
def ngons_are_warned():
    bpy.ops.mesh.primitive_cylinder_add(vertices=8)  # caps are 8-sided n-gons
    name = bpy.context.active_object.name
    assert (name, "NGONS") in codes()
    assert severity("NGONS") == {checks.WARNING}


@test
def unapplied_transforms():
    obj = cube()
    obj.scale = (2, 2, 2)
    assert ("Cube", "TRANSFORM") in codes()
    obj.scale = (1, 1, 1)
    obj.rotation_euler = (0, 0, 0.5)
    assert ("Cube", "TRANSFORM") in codes()
    obj.rotation_euler = (0, 0, 0)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = (1, 0, 0, 0)
    assert ("Cube", "TRANSFORM") not in codes()


@test
def uv_problems():
    obj = cube()
    obj.data.uv_layers.new(name="Second")
    assert ("Cube", "UV_SETS") in codes()
    obj.data.uv_layers.remove(obj.data.uv_layers["Second"])
    obj.data.uv_layers.active.data[0].uv = (1.5, 0.2)
    obj.data.update()
    assert ("Cube", "UV_RANGE") in codes()
    while obj.data.uv_layers:
        obj.data.uv_layers.remove(obj.data.uv_layers[0])
    obj.data.update()
    assert ("Cube", "NO_UV") in codes()


@test
def one_material_only():
    obj = cube()
    for n in ("A", "B"):
        obj.data.materials.append(bpy.data.materials.new(n))
    assert ("Cube", "MATERIALS") in codes()


@test
def texture_size_by_preset():
    obj = cube("Hatty", size=1.0)
    mat = bpy.data.materials.new("Mat")
    if bpy.app.version < (5, 0, 0):
        mat.use_nodes = True
    node = mat.node_tree.nodes.new("ShaderNodeTexImage")
    node.image = bpy.data.images.new("Big", 4096, 4096)
    obj.data.materials.append(mat)
    assert severity("TEXTURE", preset="MESH") == {checks.WARNING}
    assert severity("TEXTURE", preset="RIGID") == {checks.ERROR}
    node.image = bpy.data.images.new("Ok", 2048, 1024)
    assert severity("TEXTURE", preset="RIGID") == set(), "2048 is allowed for accessories"
    assert severity("TEXTURE", preset="MESH") == {checks.WARNING}, "above 1024 for a plain mesh"


@test
def bone_influences():
    obj = cube()
    bpy.ops.object.armature_add()
    arm = bpy.context.active_object
    bpy.ops.object.mode_set(mode="EDIT")
    for i in range(4):
        bone = arm.data.edit_bones.new(f"B{i}")
        bone.head = (i, 0, 0)
        bone.tail = (i, 0, 1)
    bpy.ops.object.mode_set(mode="OBJECT")
    mod = obj.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    names = [b.name for b in arm.data.bones]
    assert len(names) == 5
    for n in names[:4]:
        obj.vertex_groups.new(name=n).add([0, 1], 0.25, "REPLACE")
    assert ("Cube", "INFLUENCES") not in codes(), "4 bones is fine"
    obj.vertex_groups.new(name=names[4]).add([0], 0.2, "REPLACE")
    obj.vertex_groups.new(name="NotABone").add([1, 2], 1.0, "REPLACE")
    found = [i for i in checks.run(bpy.context) if i.code == "INFLUENCES"]
    assert len(found) == 1 and found[0].message.startswith("1 vertex"), found


@test
def cages_for_layered_accessories():
    cube("Shirt")
    assert ("Shirt", "CAGES") in codes(preset="LAYERED")
    assert ("Shirt", "CAGES") not in codes(preset="RIGID")
    cube("Shirt_InnerCage", location=(3, 0, 0))
    cube("Shirt_OuterCage", location=(6, 0, 0))
    found = codes(preset="LAYERED")
    assert ("Shirt", "CAGES") not in found, found
    assert not any(obj.endswith("Cage") for obj, _ in found), "cages get no geometry checks"
    cube("Pants_OuterCage", location=(9, 0, 0))
    assert ("Pants_OuterCage", "CAGE_NAME") in codes()


@test
def cages_count_even_when_only_the_mesh_is_checked():
    shirt = cube("Shirt")
    cube("Shirt_InnerCage", location=(3, 0, 0))
    cube("Shirt_OuterCage", location=(6, 0, 0))
    assert ("Shirt", "CAGES") not in codes([shirt], preset="LAYERED")


@test
def accessory_size_limits():
    obj = cube("Hat", size=2.0)  # 2 x 2 x 2 studs
    found = codes(preset="RIGID", accessory_type="HAT", body_scale="NORMAL")
    assert ("Hat", "SIZE") in found, "2 > 1.87 wide"
    assert ("Hat", "SIZE") not in codes(preset="RIGID", accessory_type="HAT", body_scale="CLASSIC"), "classic hat is 3x4x3"
    assert ("Hat", "SIZE") not in codes(preset="RIGID"), "no accessory type, no size check"
    obj.dimensions = (1.8, 1.8, 2.4)  # Blender Z is Roblox height
    assert ("Hat", "SIZE") not in codes(preset="RIGID", accessory_type="HAT", body_scale="NORMAL")
    obj.dimensions = (1.8, 2.4, 1.8)  # 2.4 deep > 1.87
    msgs = [i.message for i in checks.run(bpy.context, None, checks.Settings("RIGID", "NORMAL", "HAT")) if i.code == "SIZE"]
    assert msgs and "depth 2.40 > 1.87" in msgs[0], msgs


@test
def errors_sort_first():
    cube()
    bpy.ops.mesh.primitive_plane_add(location=(3, 0, 0))
    bpy.context.scene.unit_settings.system = "METRIC"
    issues = checks.run(bpy.context)
    seen_warning = False
    for i in issues:
        if i.severity == checks.WARNING:
            seen_warning = True
        assert not (seen_warning and i.severity == checks.ERROR), "an error came after a warning"


@test
def addon_registers_and_runs():
    import mesh_check_rbx

    mesh_check_rbx.register()
    try:
        cube()
        bpy.ops.mesh.primitive_plane_add(location=(3, 0, 0))
        bpy.context.scene.mesh_check_rbx.preset = "RIGID"
        assert bpy.ops.mesh_check_rbx.run() == {"FINISHED"}
        assert any(i.code == "FLAT" for i in mesh_check_rbx._results)
        assert mesh_check_rbx._last_run["tris"]["Cube"] == 12
        assert bpy.ops.mesh_check_rbx.select(name="Cube") == {"FINISHED"}
        assert bpy.context.view_layer.objects.active.name == "Cube"
    finally:
        mesh_check_rbx.unregister()


print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
