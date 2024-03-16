import bpy
import os
import re

def read_material_tiling_from_file(file_path):
    material_tiling = {}
    with open(file_path, 'r') as file:
        lines = file.readlines()
        current_material = None
        for line in lines:
            line = line.strip()
            if line.startswith("Material:"):
                current_material = line.split(": ")[1]
                material_tiling[current_material] = {}
            elif current_material and line:
                if line.startswith("Tiling X:"):
                    material_tiling[current_material]['x'] = float(line.split(": ")[1])
                elif line.startswith("Tiling Y:"):
                    material_tiling[current_material]['y'] = float(line.split(": ")[1])
    return material_tiling

def remove_numbered_suffix(name):
    return re.sub(r'\.\d+$', '', name)

def connect_mapping_to_textures_and_adjust_gloss_and_spec(material, material_tiling):
    if not material.node_tree:
        return

    nodes = material.node_tree.nodes
    links = material.node_tree.links

    # Find all mapping nodes in the material
    mapping_nodes = [node for node in nodes if node.type == 'MAPPING']

    # Create a new mapping node if none exist
    if not mapping_nodes:
        mapping_node = nodes.new(type='ShaderNodeMapping')
        mapping_nodes.append(mapping_node)

    for mapping_node in mapping_nodes:
        # Adjust the scaling of the mapping node based on the material tiling information
        material_name_without_suffix = remove_numbered_suffix(material.name)
        for mat_name, tiling_info in material_tiling.items():
            if remove_numbered_suffix(mat_name) == material_name_without_suffix:
                mapping_node.inputs['Scale'].default_value = (
                    tiling_info['x'],
                    tiling_info['y'],
                    1.0  # Set the Z-scale to 1
                )
                mapping_node.inputs['Scale'].keyframe_insert(data_path='default_value')
                break

    # Create a new texture coordinate node if it doesn't exist
    if 'Texture Coordinate' not in nodes:
        tex_coord_node = nodes.new(type='ShaderNodeTexCoord')
    else:
        tex_coord_node = nodes['Texture Coordinate']

    for mapping_node in mapping_nodes:
        # Connect the texture coordinate node to the mapping node
        if not any(link.from_node == tex_coord_node and link.to_node == mapping_node for link in links):
            links.new(tex_coord_node.outputs['UV'], mapping_node.inputs['Vector'])

        # Connect the mapping node to all texture nodes
        for node in nodes:
            if node.type == 'TEX_IMAGE':
                if not any(link.from_node == mapping_node and link.to_socket == node.inputs['Vector'] for link in links):
                    links.new(mapping_node.outputs['Vector'], node.inputs['Vector'])

    # Update the node tree to apply the changes
    material.node_tree.nodes.update()

    # Find the texture node with "GLOSS" or "SPEC" in its name
    target_texture_node = None
    for node in nodes:
        if node.type == 'TEX_IMAGE' and ("gloss" in node.image.name.lower() or "spec" in node.image.name.lower()):
            target_texture_node = node
            break

    if target_texture_node:
        # Check for Separate Color and Roughness Factor nodes
        separate_color_node = None
        roughness_factor_node = None
        for node in nodes:
            if node.name == "Separate Color":
                separate_color_node = node
            elif node.type == 'MATH' and node.label == "Roughness Factor":
                roughness_factor_node = node

        # Remove Roughness Factor node if connected to Separate Color node
        if roughness_factor_node and separate_color_node:
            for link in links:
                if link.from_node == separate_color_node and link.to_node == roughness_factor_node:
                    nodes.remove(roughness_factor_node)
                    break

        # Remove Separate Color node
        if separate_color_node:
            nodes.remove(separate_color_node)

        # Find the Principled BSDF node and connect gloss/spec texture
        for node in nodes:
            if node.type == 'BSDF_PRINCIPLED':
                if not any(link.from_node == target_texture_node and link.to_socket == node.inputs['Specular IOR Level'] for link in links):
                    links.new(target_texture_node.outputs['Color'], node.inputs['Specular IOR Level'])

def adjust_shaders(context, file_path):
    material_tiling = read_material_tiling_from_file(file_path)

    # Iterate over all materials in the scene
    for material in bpy.data.materials:
        connect_mapping_to_textures_and_adjust_gloss_and_spec(material, material_tiling)

class AdjustShaders(bpy.types.Operator):
    """Adjust Shaders"""
    bl_idname = "object.adjust_shaders"
    bl_label = "Adjust Shaders"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        adjust_shaders(context, self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.filepath = "MaterialsCheckReport.txt"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def register():
    bpy.utils.register_class(AdjustShaders)

def unregister():
    bpy.utils.unregister_class(AdjustShaders)