import bpy
import os
import re
import random
import string
import tempfile

def load_lightmap_info(filepath):
    with open(filepath, 'r') as file:
        content = file.read()
    return content

def parse_info(content):
    sections = content.split('Object: ')[1:]
    info = []
    for section in sections:
        lines = section.split('\n')
        obj_info = {'name': lines[0].strip()}
        for line in lines[1:]:
            if line.startswith('Lightmap Index:'):
                obj_info['lightmap_index'] = int(line.split(': ')[1].strip())
            elif line.startswith('Lightmap Texture:'):
                obj_info['lightmap_texture'] = line.split(': ')[1].strip()
            elif line.startswith('Tiling X:'):
                obj_info['tiling_x'] = float(line.split(': ')[1].strip().replace(',', '.'))
            elif line.startswith('Tiling Y:'):
                obj_info['tiling_y'] = float(line.split(': ')[1].strip().replace(',', '.'))
            elif line.startswith('Offset X:'):
                obj_info['offset_x'] = float(line.split(': ')[1].strip().replace(',', '.'))
            elif line.startswith('Offset Y:'):
                obj_info['offset_y'] = float(line.split(': ')[1].strip().replace(',', '.'))
            elif line.startswith('Directional Lightmap Texture:'):
                obj_info['directional_lightmap_texture'] = line.split(': ')[1].strip()
            elif line.startswith('Reflection Probe Texture:'):
                obj_info['reflection_probe_texture'] = line.split(': ')[1].strip()
            elif line.startswith('Path:'):
                obj_info['path'] = line.split(': ')[1].strip()
        if 'lightmap_texture' in obj_info:
            info.append(obj_info)
    return info

def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

import tempfile

def process_exr_image(image_path, original_width, original_height):
    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree
    for node in tree.nodes:
        tree.nodes.remove(node)

    image_node = tree.nodes.new('CompositorNodeImage')
    image_node.image = bpy.data.images.load(image_path)
    
    # Set the view transform to 'Standard'
    bpy.context.scene.view_settings.view_transform = 'Standard'

    # Set the render resolution to match the original image resolution
    bpy.context.scene.render.resolution_x = original_width
    bpy.context.scene.render.resolution_y = original_height

    gamma_node = tree.nodes.new('CompositorNodeGamma')
    gamma_node.inputs[1].default_value = 0.45454545

    separate_color_node = tree.nodes.new('CompositorNodeSepRGBA')

    math_nodes = []
    for _ in range(3):
        math_node = tree.nodes.new('CompositorNodeMath')
        math_node.operation = 'DIVIDE'
        math_node.inputs[1].default_value = 2.0
        math_nodes.append(math_node)

    combine_color_node = tree.nodes.new('CompositorNodeCombRGBA')

    gamma_node_2 = tree.nodes.new('CompositorNodeGamma')
    gamma_node_2.inputs[1].default_value = 3.3

    composite_node = tree.nodes.new('CompositorNodeComposite')

    tree.links.new(image_node.outputs['Image'], gamma_node.inputs['Image'])
    tree.links.new(gamma_node.outputs['Image'], separate_color_node.inputs['Image'])
    tree.links.new(separate_color_node.outputs[0], math_nodes[0].inputs[0])
    tree.links.new(separate_color_node.outputs[1], math_nodes[1].inputs[0])
    tree.links.new(separate_color_node.outputs[2], math_nodes[2].inputs[0])
    tree.links.new(math_nodes[0].outputs['Value'], combine_color_node.inputs[0])
    tree.links.new(math_nodes[1].outputs['Value'], combine_color_node.inputs[1])
    tree.links.new(math_nodes[2].outputs['Value'], combine_color_node.inputs[2])
    tree.links.new(combine_color_node.outputs['Image'], gamma_node_2.inputs['Image'])
    tree.links.new(gamma_node_2.outputs['Image'], composite_node.inputs['Image'])

    # Get the OS's temporary directory
    temp_dir = tempfile.gettempdir()

    # Set the output path to the temporary directory
    output_path = os.path.join(temp_dir, os.path.splitext(os.path.basename(image_path))[0] + "_processed.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)

    return output_path

def create_materials(obj_info):
    materials = []
    is_exr = False

    for info in obj_info:
        image_path = os.path.join(info['path'], info['lightmap_texture'])

        if image_path.lower().endswith('.exr'):
            is_exr = True
            original_image = bpy.data.images.load(image_path)
            original_width, original_height = original_image.size
            bpy.data.images.remove(original_image)
            image_path = process_exr_image(image_path, original_width, original_height)

        random_string = generate_random_string(16)
        
        mat_name = f"vircadia_lightmapData_{random_string}"
        
        if mat_name in bpy.data.materials:
            mat = bpy.data.materials[mat_name]
        else:
            mat = bpy.data.materials.new(name=mat_name)
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes.get('Principled BSDF')
            tex_image = mat.node_tree.nodes.new('ShaderNodeTexImage')
            tex_image.label = "BASE COLOR"
            
            image_name = random_string
            
            if image_name in bpy.data.images:
                tex_image.image = bpy.data.images[image_name]
            else:
                loaded_image = bpy.data.images.load(image_path)
                loaded_image.name = image_name
                tex_image.image = loaded_image
            
            mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])
        
        materials.append(mat)
    
    return materials, is_exr

def adjust_uv_maps(obj_info):
    for info in obj_info:
        obj = bpy.data.objects.get(info['name'])
        if obj and obj.data and 'lightmap_texture' in info and 'tiling_x' in info and 'tiling_y' in info and 'offset_x' in info and 'offset_y' in info:
            if len(obj.data.uv_layers) < 2:
                obj.data.uv_layers.new(name="LightmapUV")
            uv_layer = obj.data.uv_layers[1].data
            
            for poly in obj.data.polygons:
                for loop_index in poly.loop_indices:
                    loop_uv = uv_layer[loop_index]
                    loop_uv.uv[0] = (loop_uv.uv[0] * info['tiling_x']) + info['offset_x']
                    loop_uv.uv[1] = (loop_uv.uv[1] * info['tiling_y']) + info['offset_y']

def create_and_join_planes(materials):
    created_objects = []
    for i, mat in enumerate(materials):
        bpy.ops.mesh.primitive_plane_add(size=2)
        plane = bpy.context.active_object
        plane.name = f"merge.{str(i+1).zfill(3)}"
        plane.data.materials.append(mat)
        created_objects.append(plane)

    bpy.ops.object.select_all(action='DESELECT')
    for obj in created_objects:
        obj.select_set(True)

    bpy.context.view_layer.objects.active = created_objects[0]

    bpy.ops.object.join()
    bpy.context.active_object.name = "vircadia_lightmapData"
    return bpy.context.active_object

def add_custom_properties(obj_info, materials, lightmap_data_obj, is_exr):
    for info in obj_info:
        obj = bpy.data.objects.get(info['name'])
        if obj:
            try:
                mat = materials[obj_info.index(info)]
                mat_name = mat.name
                obj['vircadia_lightmap'] = mat_name
                obj['vircadia_lightmap_texcoord'] = 1
            except (ValueError, IndexError):
                print(f"Warning: Material not found for object {info['name']}")
    
    if is_exr:
        lightmap_data_obj['vircadia_lightmap_mode'] = 'shadowsOnly'

def make_materials_single_user(obj_info):
    for info in obj_info:
        obj = bpy.data.objects.get(info['name'])
        if obj:
            for slot in obj.material_slots:
                if slot.material:
                    slot.material = slot.material.copy()

def import_lightmap_info(filepath):
    content = load_lightmap_info(filepath)
    obj_info = parse_info(content)
    materials, is_exr = create_materials(obj_info)
    adjust_uv_maps(obj_info)
    lightmap_data_obj = create_and_join_planes(materials)
    add_custom_properties(obj_info, materials, lightmap_data_obj, is_exr)
    make_materials_single_user(obj_info)
    

class GetLightmapInfo(bpy.types.Operator):
    """Get Lightmap Information"""
    bl_idname = "import.lightmap_info"
    bl_label = "Import Lightmap Info"
    
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.txt", options={'HIDDEN'})

    def execute(self, context):
        import_lightmap_info(self.filepath)
        return {'FINISHED'}
    
    def invoke(self, context, event):
        self.filepath = "LightmapInfo.txt"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def register():
    bpy.utils.register_class(GetLightmapInfo)

def unregister():
    bpy.utils.unregister_class(GetLightmapInfo)

if __name__ == "__main__":
    register()