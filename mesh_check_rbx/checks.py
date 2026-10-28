# SPDX-License-Identifier: GPL-3.0-or-later
"""Checks a Blender scene against Roblox's mesh requirements.

Geometry is read from the evaluated mesh (modifiers applied), because that is
what an FBX export contains. Nothing here changes the scene.
"""

from dataclasses import dataclass

import bmesh
import bpy

from . import limits

ERROR = "ERROR"
WARNING = "WARNING"

EPSILON = 1e-4
CAGE_SUFFIXES = (limits.INNER_CAGE_SUFFIX, limits.OUTER_CAGE_SUFFIX)


@dataclass
class Issue:
    severity: str  # ERROR or WARNING
    code: str  # short id, e.g. "TRIS"
    obj: str  # object name, "" for scene-wide issues
    message: str
    doc: str = "modeling"  # key into limits.DOCS


@dataclass
class Settings:
    preset: str = "MESH"  # key into limits.PRESETS
    body_scale: str = "NORMAL"  # key into limits.ACCESSORY_SIZES
    accessory_type: str = "NONE"  # "NONE" or a key of limits.ACCESSORY_TYPE_LABELS


def is_cage(name):
    return name.endswith(CAGE_SUFFIXES)


def cage_base(name):
    for suffix in CAGE_SUFFIXES:
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return None


def count_triangles(obj, depsgraph):
    """Triangles in the evaluated mesh, which is what Roblox imports."""
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        mesh.calc_loop_triangles()
        return len(mesh.loop_triangles)
    finally:
        evaluated.to_mesh_clear()


def _armature_bones(obj):
    bones = set()
    for mod in obj.modifiers:
        if mod.type == "ARMATURE" and mod.object is not None and mod.object.type == "ARMATURE":
            bones.update(b.name for b in mod.object.data.bones)
    if obj.parent is not None and obj.parent.type == "ARMATURE":
        bones.update(b.name for b in obj.parent.data.bones)
    return bones


def _images(obj):
    seen = set()
    for slot in obj.material_slots:
        mat = slot.material
        if mat is None or not getattr(mat, "use_nodes", True) or mat.node_tree is None:
            continue
        for node in mat.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image is not None and node.image.name not in seen:
                seen.add(node.image.name)
                yield node.image


def check_scene(scene):
    issues = []
    units = scene.unit_settings
    if units.system != "NONE" or abs(units.scale_length - 1.0) > EPSILON:
        issues.append(Issue(
            WARNING, "UNITS", "",
            f"Scene units are {units.system.title()} (scale {units.scale_length:g}). Roblox's Blender guide sets "
            "Unit System to None so 1 Blender unit = 1 stud.",
            "blender",
        ))
    return issues


def check_object(obj, depsgraph, settings):
    """Issues for one mesh object. Cage meshes only get naming checks (see check_cages)."""
    preset = limits.PRESETS[settings.preset]
    issues = []
    name = obj.name

    def add(severity, code, message, doc=preset["doc"]):
        issues.append(Issue(severity, code, name, message, doc))

    if is_cage(name):
        return issues

    # Triangle budget.
    tris = count_triangles(obj, depsgraph)
    if tris > preset["tris"]:
        add(ERROR, "TRIS", f"{tris:,} triangles; {preset['label']} limit is {preset['tris']:,}.")

    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        bm = bmesh.new()
        try:
            bm.from_mesh(mesh)
            ngons = sum(1 for f in bm.faces if len(f.verts) > 4)
            open_edges = sum(1 for e in bm.edges if e.is_boundary)
            bad_edges = sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary)
        finally:
            bm.free()

        if ngons:
            add(WARNING, "NGONS", f"{ngons} n-gon(s) (faces with more than 4 sides). Roblox asks for quads where possible.", "modeling")
        if open_edges or bad_edges:
            parts = []
            if open_edges:
                parts.append(f"{open_edges} open edge(s)")
            if bad_edges:
                parts.append(f"{bad_edges} non-manifold edge(s)")
            add(WARNING, "WATERTIGHT", f"Not watertight: {', '.join(parts)}. Roblox requires no exposed holes or backfaces.", "modeling")

        # UVs.
        uv_layers = mesh.uv_layers
        if len(uv_layers) == 0:
            add(WARNING, "NO_UV", "No UV map, so textures can't be applied.", "textures")
        else:
            if len(uv_layers) > 1:
                add(WARNING, "UV_SETS", f"{len(uv_layers)} UV maps; Studio allows a single UV set.", "textures")
            active = uv_layers.active or uv_layers[0]
            outside = sum(
                1 for d in active.data
                if d.uv[0] < -EPSILON or d.uv[0] > 1 + EPSILON or d.uv[1] < -EPSILON or d.uv[1] > 1 + EPSILON
            )
            if outside:
                add(WARNING, "UV_RANGE", f"{outside} UV point(s) outside 0-1; Roblox requires UVs in 0:1 space.", "textures")
    finally:
        evaluated.to_mesh_clear()

    # Thickness and size use the evaluated, transformed bounding box.
    dims = obj.dimensions
    if min(dims) < EPSILON:
        add(ERROR, "FLAT", "Zero thickness on at least one axis. Roblox meshes must have volume.", "modeling")

    if settings.preset == "RIGID" and settings.accessory_type != "NONE":
        max_x, max_y, max_z = limits.ACCESSORY_SIZES[settings.body_scale][settings.accessory_type]
        # Blender X = Roblox X (width), Blender Z = Roblox Y (height), Blender Y = Roblox Z (depth).
        size = (dims.x, dims.z, dims.y)
        over = [
            f"{axis} {value:.2f} > {limit:g}"
            for axis, value, limit in zip(("width", "height", "depth"), size, (max_x, max_y, max_z))
            if value > limit + EPSILON
        ]
        if over:
            label = limits.ACCESSORY_TYPE_LABELS[settings.accessory_type]
            scale = limits.BODY_SCALE_LABELS[settings.body_scale]
            add(ERROR, "SIZE", f"Too big for {label}, {scale} body scale (studs): {'; '.join(over)}.", "rigid")

    # Transforms.
    rotated = any(abs(v) > EPSILON for v in obj.rotation_euler) if obj.rotation_mode not in {"QUATERNION", "AXIS_ANGLE"} else (
        any(abs(a - b) > EPSILON for a, b in zip(obj.rotation_quaternion, (1, 0, 0, 0)))
        if obj.rotation_mode == "QUATERNION"
        else abs(obj.rotation_axis_angle[0]) > EPSILON
    )
    scaled = any(abs(v - 1) > EPSILON for v in obj.scale)
    if rotated or scaled:
        what = " and ".join(w for w, on in (("rotation", rotated), ("scale", scaled)) if on)
        add(WARNING, "TRANSFORM", f"Unapplied {what}. Apply it (Ctrl+A) so Studio imports the size and orientation you see.", "modeling")

    # Materials.
    used = [s.material for s in obj.material_slots if s.material is not None]
    if len(used) > 1:
        add(WARNING, "MATERIALS", f"{len(used)} materials; Roblox mesh objects can only have one material.", "textures")

    # Textures.
    for image in _images(obj):
        width, height = image.size
        if max(width, height) > preset["texture"]:
            severity = ERROR if preset["texture_hard"] else WARNING
            add(severity, "TEXTURE", f"Texture '{image.name}' is {width}x{height}; limit is {preset['texture']}x{preset['texture']}.", "textures")

    # Bone influences.
    bones = _armature_bones(obj)
    if bones:
        group_is_bone = {g.index: g.name in bones for g in obj.vertex_groups}
        over = 0
        for v in obj.data.vertices:
            if sum(1 for g in v.groups if g.weight > 0 and group_is_bone.get(g.group, False)) > limits.MAX_INFLUENCES:
                over += 1
        if over:
            add(ERROR, "INFLUENCES", f"{over} vertex/vertices influenced by more than {limits.MAX_INFLUENCES} bones.", "modeling")

    return issues


def check_cages(objects, settings, names=None):
    """Cage naming: each cage needs its primary mesh; layered accessories need both cages.
    `names` is every object name in the scene, so cages that aren't being checked still count."""
    issues = []
    names = names if names is not None else {o.name for o in objects}
    for obj in objects:
        base = cage_base(obj.name)
        if base is not None and base not in names:
            issues.append(Issue(
                WARNING, "CAGE_NAME", obj.name,
                f"Cage has no mesh named '{base}'. Cages must be named after their mesh plus "
                f"{limits.INNER_CAGE_SUFFIX} or {limits.OUTER_CAGE_SUFFIX}.",
                "modeling",
            ))
    if limits.PRESETS[settings.preset]["cages"]:
        for obj in objects:
            if is_cage(obj.name):
                continue
            missing = [s for s in CAGE_SUFFIXES if obj.name + s not in names]
            if missing:
                issues.append(Issue(
                    ERROR, "CAGES", obj.name,
                    f"Layered accessories need an inner and outer cage; missing {' and '.join(obj.name + s for s in missing)}.",
                    "layered",
                ))
    return issues


def run(context_or_scene, objects=None, settings=None):
    """All issues for `objects` (default: every mesh in the scene), errors first."""
    scene = context_or_scene.scene if hasattr(context_or_scene, "scene") else context_or_scene
    settings = settings or Settings()
    meshes = [o for o in (objects if objects is not None else scene.objects) if o.type == "MESH"]
    depsgraph = bpy.context.evaluated_depsgraph_get()
    issues = check_scene(scene)
    issues += check_cages(meshes, settings, {o.name for o in scene.objects})
    for obj in meshes:
        issues += check_object(obj, depsgraph, settings)
    issues.sort(key=lambda i: (i.severity != ERROR, i.obj, i.code))
    return issues
