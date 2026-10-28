# SPDX-License-Identifier: GPL-3.0-or-later
"""Mesh Check for Roblox: checks meshes against Roblox's import limits.

Sidebar (N) > Roblox tab in the 3D Viewport. The Pro edition adds fix
buttons and a Roblox-ready FBX export; the free edition only checks.
"""

bl_info = {
    "name": "Mesh Check for Roblox",
    "author": "Kettlewick Tools",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "3D Viewport > Sidebar > Roblox",
    "description": "Checks triangle budgets, watertightness, UVs, textures, bone influences, cages and accessory sizes against Roblox's limits",
    "category": "Import-Export",
}

import bpy
from bpy.props import BoolProperty, EnumProperty, PointerProperty, StringProperty

from . import checks, limits

try:  # Present only in the Pro edition.
    from . import pro
except ImportError:
    pro = None

STORE_URL = "https://kettlewick.gumroad.com/l/mesh-check-pro-roblox"
MAX_ROWS = 40

_results = []  # Issues from the last run, shown in the panel.
_last_run = {"objects": 0, "tris": {}}


def _preset_items(_self, _context):
    return [(k, v["label"], f"{v['tris']:,} triangle budget") for k, v in limits.PRESETS.items()]


def _scale_items(_self, _context):
    return [(k, v, "") for k, v in limits.BODY_SCALE_LABELS.items()]


def _type_items(_self, _context):
    return [("NONE", "Any (skip size check)", "")] + [(k, v, "") for k, v in limits.ACCESSORY_TYPE_LABELS.items()]


class MeshCheckSettings(bpy.types.PropertyGroup):
    preset: EnumProperty(name="Asset type", items=_preset_items)
    body_scale: EnumProperty(name="Body scale", items=_scale_items)
    accessory_type: EnumProperty(name="Accessory", items=_type_items)
    selected_only: BoolProperty(name="Selected only", default=False, description="Check only the selected meshes")


def settings_from(props):
    return checks.Settings(preset=props.preset, body_scale=props.body_scale, accessory_type=props.accessory_type)


def target_objects(context, props):
    pool = context.selected_objects if props.selected_only else context.scene.objects
    return [o for o in pool if o.type == "MESH"]


class MESHCHECK_OT_run(bpy.types.Operator):
    bl_idname = "mesh_check_rbx.run"
    bl_label = "Check for Roblox"
    bl_description = "Check meshes against Roblox's limits"

    def execute(self, context):
        props = context.scene.mesh_check_rbx
        objects = target_objects(context, props)
        _results[:] = checks.run(context, objects, settings_from(props))
        depsgraph = context.evaluated_depsgraph_get()
        _last_run["objects"] = len(objects)
        _last_run["tris"] = {o.name: checks.count_triangles(o, depsgraph) for o in objects if not checks.is_cage(o.name)}
        errors = sum(1 for i in _results if i.severity == checks.ERROR)
        warnings = len(_results) - errors
        self.report({"WARNING" if errors else "INFO"}, f"{len(objects)} mesh(es): {errors} error(s), {warnings} warning(s)")
        return {"FINISHED"}


class MESHCHECK_OT_select(bpy.types.Operator):
    bl_idname = "mesh_check_rbx.select"
    bl_label = "Select"
    bl_description = "Select this object"
    bl_options = {"REGISTER", "UNDO"}

    name: StringProperty()

    def execute(self, context):
        obj = context.scene.objects.get(self.name)
        if obj is None:
            return {"CANCELLED"}
        if context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        for o in context.selected_objects:
            o.select_set(False)
        obj.select_set(True)
        context.view_layer.objects.active = obj
        return {"FINISHED"}


class MESHCHECK_OT_open_doc(bpy.types.Operator):
    bl_idname = "mesh_check_rbx.open_doc"
    bl_label = "Open Roblox docs"
    bl_description = "Open the Roblox page this limit comes from"

    doc: StringProperty()

    def execute(self, _context):
        bpy.ops.wm.url_open(url=limits.DOCS.get(self.doc, limits.DOCS["modeling"]))
        return {"FINISHED"}


class MESHCHECK_PT_panel(bpy.types.Panel):
    bl_label = "Mesh Check for Roblox"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Roblox"

    def draw(self, context):
        layout = self.layout
        props = context.scene.mesh_check_rbx
        layout.prop(props, "preset")
        if props.preset == "RIGID":
            layout.prop(props, "accessory_type")
            if props.accessory_type != "NONE":
                layout.prop(props, "body_scale")
        layout.prop(props, "selected_only")
        layout.operator(MESHCHECK_OT_run.bl_idname, icon="CHECKMARK")

        if _last_run["objects"]:
            total = sum(_last_run["tris"].values())
            box = layout.box()
            errors = sum(1 for i in _results if i.severity == checks.ERROR)
            warnings = len(_results) - errors
            if not _results:
                box.label(text=f"{_last_run['objects']} mesh(es) passed", icon="CHECKMARK")
            else:
                box.label(text=f"{errors} error(s), {warnings} warning(s)", icon="ERROR" if errors else "INFO")
            box.label(text=f"{total:,} triangles in total")
            for issue in _results[:MAX_ROWS]:
                col = box.column(align=True)
                row = col.row(align=True)
                row.alert = issue.severity == checks.ERROR
                icon = "CANCEL" if issue.severity == checks.ERROR else "ERROR"
                if issue.obj:
                    op = row.operator(MESHCHECK_OT_select.bl_idname, text=issue.obj, icon=icon, emboss=False)
                    op.name = issue.obj
                else:
                    row.label(text="Scene", icon=icon)
                row.operator(MESHCHECK_OT_open_doc.bl_idname, text="", icon="HELP").doc = issue.doc
                for line in _wrap(issue.message, 46):
                    col.label(text=line)
                if pro is not None:
                    pro.draw_fix(col, issue)
            if len(_results) > MAX_ROWS:
                box.label(text=f"... and {len(_results) - MAX_ROWS} more")

        if pro is not None:
            pro.draw_panel(layout, context)
        else:
            col = layout.column(align=True)
            col.label(text="Pro: one-click fixes + Roblox FBX export")
            col.operator("wm.url_open", text="Get Pro", icon="URL").url = STORE_URL


def _wrap(text, width):
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}" if line else word
    if line:
        lines.append(line)
    return lines


CLASSES = (MeshCheckSettings, MESHCHECK_OT_run, MESHCHECK_OT_select, MESHCHECK_OT_open_doc, MESHCHECK_PT_panel)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.mesh_check_rbx = PointerProperty(type=MeshCheckSettings)
    if pro is not None:
        pro.register()


def unregister():
    if pro is not None:
        pro.unregister()
    del bpy.types.Scene.mesh_check_rbx
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
