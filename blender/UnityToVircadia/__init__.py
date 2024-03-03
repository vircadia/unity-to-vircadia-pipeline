import bpy
import os

from . import makeObjectsSingleUserFixScale
from . import getLightmapInformation
from . import fixMappingNodesRemoveExtras
# Assuming the combined script is saved as 'previewLightmaps.py' in the same addon directory
from . import previewLightmaps

bl_info = {
    "name": "UnityToVircadia",
    "blender": (4, 0, 2),
    "category": "Object",
    "description": "Tools for converting Unity assets to Vircadia",
    "author": "Ben Brennan, Vircadia",
    "version": (1, 0),
    "location": "View3D > Sidebar > UnityToVircadia Tab",
}

def get_script_path(script_name):
    addon_dir = os.path.dirname(__file__)
    return os.path.join(addon_dir, script_name)

class ToggleLightmapsOperator(bpy.types.Operator):
    """Toggle Lightmaps"""
    bl_idname = "object.toggle_lightmaps"
    bl_label = "Preview Lightmaps"
    bl_description = "Toggle lightmap textures on objects"

    def execute(self, context):
        previewLightmaps.main(context.scene.lightmaps_applied)
        context.scene.lightmaps_applied = not context.scene.lightmaps_applied
        return {'FINISHED'}

class UnityToVircadiaPanel(bpy.types.Panel):
    bl_label = "UnityToVircadia"
    bl_idname = "OBJECT_PT_UnityToVircadia"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'UnityToVircadia'

    def draw(self, context):
        layout = self.layout

        layout.operator("import_scene.gltf", text="Import glTF 2.0")
        # layout.operator("object.correct_scale") # TODO later
        layout.operator("import.lightmap_info")
        layout.operator("object.adjust_shaders")

        # Toggle button for applying/clearing lightmaps
        if context.scene.lightmaps_applied:
            layout.operator("object.toggle_lightmaps", text="Clear Lightmaps")
        else:
            layout.operator("object.toggle_lightmaps", text="Preview Lightmaps")

        layout.operator("export_scene.gltf", text="Export glTF 2.0")

def register():
    bpy.utils.register_class(ToggleLightmapsOperator)
    bpy.utils.register_class(UnityToVircadiaPanel)
    bpy.utils.register_class(makeObjectsSingleUserFixScale.CorrectScale)
    bpy.utils.register_class(getLightmapInformation.GetLightmapInfo)
    bpy.utils.register_class(fixMappingNodesRemoveExtras.AdjustShaders)
    bpy.types.Scene.lightmaps_applied = bpy.props.BoolProperty(default=False)

def unregister():
    bpy.utils.unregister_class(ToggleLightmapsOperator)
    bpy.utils.unregister_class(UnityToVircadiaPanel)
    bpy.utils.unregister_class(makeObjectsSingleUserFixScale.CorrectScale)
    bpy.utils.unregister_class(getLightmapInformation.GetLightmapInfo)
    bpy.utils.unregister_class(fixMappingNodesRemoveExtras.AdjustShaders)
    del bpy.types.Scene.lightmaps_applied

if __name__ == "__main__":
    register()