import bpy

def clear_lightmap_materials():
    for obj in bpy.data.objects:
        for mat_slot in obj.material_slots:
            mat = mat_slot.material
            if mat and mat.use_nodes:
                # Find the Mix node added for the lightmap
                mix_nodes = [node for node in mat.node_tree.nodes if node.name.startswith("LM_Mix")]
                for mix_node in mix_nodes:
                    # Assuming the original texture/color is connected to the first input of the Mix node
                    if mix_node.inputs[1].is_linked:
                        original_input = mix_node.inputs[1].links[0].from_socket
                        bsdf = mat.node_tree.nodes.get('Principled BSDF')
                        if bsdf:
                            # Reconnect the original texture/color to the Principled BSDF's 'Base Color'
                            mat.node_tree.links.new(original_input, bsdf.inputs['Base Color'])
                    
                    # Remove the Mix node and any other lightmap-specific nodes
                    mat.node_tree.nodes.remove(mix_node)
                
                uv_map_nodes = [node for node in mat.node_tree.nodes if node.name.startswith("LM_UVMap")]
                tex_image_nodes = [node for node in mat.node_tree.nodes if node.name.startswith("LM_TexImage")]
                separate_color_nodes = [node for node in mat.node_tree.nodes if node.name.startswith("LM_SeparateColor")]
                math_nodes = [node for node in mat.node_tree.nodes if node.name.startswith("LM_Math")]
                combine_color_nodes = [node for node in mat.node_tree.nodes if node.name.startswith("LM_CombineColor")]
                gamma_nodes = [node for node in mat.node_tree.nodes if node.name.startswith("LM_Gamma")]
                for node in uv_map_nodes + tex_image_nodes + separate_color_nodes + math_nodes + combine_color_nodes + gamma_nodes:
                    mat.node_tree.nodes.remove(node)

                print(f"Reverted material {mat.name} on object {obj.name}.")

def add_lightmap_to_materials():
    for obj in bpy.data.objects:
        if "vircadia_lightmap" not in obj or not obj.data or len(obj.data.uv_layers) < 2:
            continue

        lightmap_mat_name = obj["vircadia_lightmap"]
        lightmap_mat = bpy.data.materials.get(lightmap_mat_name)
        if not (lightmap_mat and lightmap_mat.use_nodes):
            continue

        lightmap_texture_node = next((node for node in lightmap_mat.node_tree.nodes if node.type == 'TEX_IMAGE'), None)
        if not lightmap_texture_node:
            continue

        for mat_slot in obj.material_slots:
            mat = mat_slot.material
            if not (mat and mat.use_nodes):
                continue

            bsdf = mat.node_tree.nodes.get('Principled BSDF')
            if not bsdf:
                continue

            uv_map_node = mat.node_tree.nodes.new('ShaderNodeUVMap')
            uv_map_node.name = "LM_UVMap"
            uv_map_node.uv_map = obj.data.uv_layers[1].name

            new_tex_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
            new_tex_node.name = "LM_TexImage"
            new_tex_node.image = lightmap_texture_node.image

            gamma_node_input = mat.node_tree.nodes.new('ShaderNodeGamma')
            gamma_node_input.name = "LM_Gamma_Input"
            gamma_node_input.inputs[1].default_value = 0.3

            separate_color_node = mat.node_tree.nodes.new('ShaderNodeSeparateColor')
            separate_color_node.name = "LM_SeparateColor"

            math_nodes = []
            for i in range(3):
                math_node = mat.node_tree.nodes.new('ShaderNodeMath')
                math_node.name = f"LM_Math_{i}"
                math_node.operation = 'MULTIPLY'
                math_node.inputs[1].default_value = 2.0
                math_nodes.append(math_node)

            combine_color_node = mat.node_tree.nodes.new('ShaderNodeCombineColor')
            combine_color_node.name = "LM_CombineColor"

            gamma_node = mat.node_tree.nodes.new('ShaderNodeGamma')
            gamma_node.name = "LM_Gamma"
            gamma_node.inputs[1].default_value = 2.2

            mix_node = mat.node_tree.nodes.new('ShaderNodeMixRGB')
            mix_node.name = "LM_Mix"
            mix_node.blend_type = 'MULTIPLY'
            mix_node.inputs[0].default_value = 1.0

            mat.node_tree.links.new(uv_map_node.outputs[0], new_tex_node.inputs[0])
            mat.node_tree.links.new(new_tex_node.outputs[0], gamma_node_input.inputs[0])
            mat.node_tree.links.new(gamma_node_input.outputs[0], separate_color_node.inputs[0])

            for i in range(3):
                mat.node_tree.links.new(separate_color_node.outputs[i], math_nodes[i].inputs[0])
                mat.node_tree.links.new(math_nodes[i].outputs[0], combine_color_node.inputs[i])

            mat.node_tree.links.new(combine_color_node.outputs[0], gamma_node.inputs[0])

            if bsdf.inputs['Base Color'].is_linked:
                original_input = bsdf.inputs['Base Color'].links[0].from_socket
                mat.node_tree.links.new(original_input, mix_node.inputs[1])
            else:
                mix_node.inputs[1].default_value = bsdf.inputs['Base Color'].default_value

            mat.node_tree.links.new(gamma_node.outputs[0], mix_node.inputs[2])
            mat.node_tree.links.new(mix_node.outputs[0], bsdf.inputs['Base Color'])

            print(f"Updated material {mat.name} on object {obj.name} with lightmap texture.")

def main(applied):
    if applied:
        clear_lightmap_materials()
    else:
        add_lightmap_to_materials()

if __name__ == "__main__":
    main(False)