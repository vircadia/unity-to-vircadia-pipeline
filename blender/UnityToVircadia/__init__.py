import bpy
import os

from . import makeObjectsSingleUserFixScale
from . import getLightmapInformation
from . import fixMappingNodesRemoveExtras

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

class UnityToVircadiaPanel(bpy.types.Panel):
    bl_label = "UnityToVircadia"
    bl_idname = "OBJECT_PT_UnityToVircadia"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'UnityToVircadia'

    def draw(self, context):
        layout = self.layout

        # Add the new button for importing glTF 2.0 at the top
        layout.operator("import_scene.gltf", text="Import glTF 2.0")

        # Existing buttons
        layout.operator("object.correct_scale")
        layout.operator("import.lightmap_info")
        layout.operator("object.adjust_shaders")
        layout.operator("export_scene.gltf")

def register():
    bpy.utils.register_class(UnityToVircadiaPanel)
    bpy.utils.register_class(makeObjectsSingleUserFixScale.CorrectScale)
    bpy.utils.register_class(getLightmapInformation.GetLightmapInfo)
    bpy.utils.register_class(fixMappingNodesRemoveExtras.AdjustShaders)

def unregister():
    bpy.utils.unregister_class(UnityToVircadiaPanel)
    bpy.utils.unregister_class(makeObjectsSingleUserFixScale.CorrectScale)
    bpy.utils.unregister_class(getLightmapInformation.GetLightmapInfo)
    bpy.utils.unregister_class(fixMappingNodesRemoveExtras.AdjustShaders)

if __name__ == "__main__":
    register()
