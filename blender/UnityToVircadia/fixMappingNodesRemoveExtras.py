import bpy

def connect_mapping_to_textures_and_adjust_gloss(material):
    if not material.node_tree:
        return

    nodes = material.node_tree.nodes
    mapping_node = None
    gloss_texture_node = None

    # Find the mapping node
    for node in nodes:
        if node.type == 'MAPPING':
            mapping_node = node

    # Connect the mapping node to all image texture nodes
    if mapping_node:
        for node in nodes:
            if node.type == 'TEX_IMAGE':
                material.node_tree.links.new(mapping_node.outputs['Vector'], node.inputs['Vector'])

    # Find the texture node with "GLOSS" in its name
    for node in nodes:
        if node.type == 'TEX_IMAGE' and "gloss" in node.image.name.lower():
            gloss_texture_node = node
            break

    if gloss_texture_node:
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
            for link in material.node_tree.links:
                if link.from_node == separate_color_node and link.to_node == roughness_factor_node:
                    nodes.remove(roughness_factor_node)
                    break

        # Remove Separate Color node
        if separate_color_node:
            nodes.remove(separate_color_node)

        # Find the Principled BSDF node and connect gloss texture
        for node in nodes:
            if node.type == 'BSDF_PRINCIPLED':
                material.node_tree.links.new(gloss_texture_node.outputs['Color'], node.inputs['Specular IOR Level'])

def adjust_shaders():
    # Iterate over all materials in the scene
    for material in bpy.data.materials:
        connect_mapping_to_textures_and_adjust_gloss(material)

class AdjustShaders(bpy.types.Operator):
    """Adjust Shaders"""
    bl_idname = "object.adjust_shaders"
    bl_label = "Adjust Shaders"

    def execute(self, context):
        adjust_shaders()
        return {'FINISHED'}
