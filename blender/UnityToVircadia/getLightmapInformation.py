import bpy
import os
import re
import random
import string

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
            if line.startswith('Lightmap Texture:'):
                obj_info['lightmap_texture'] = line.split(': ')[1].strip()
            elif line.startswith('Tiling X:'):
                obj_info['tiling_x'] = float(line.split(': ')[1].strip().replace(',', '.'))
            elif line.startswith('Tiling Y:'):
                obj_info['tiling_y'] = float(line.split(': ')[1].strip().replace(',', '.'))
            elif line.startswith('Offset X:'):
                obj_info['offset_x'] = float(line.split(': ')[1].strip().replace(',', '.'))
            elif line.startswith('Offset Y:'):
                obj_info['offset_y'] = float(line.split(': ')[1].strip().replace(',', '.'))
            elif line.startswith('Path:'):
                obj_info['path'] = line.split(': ')[1].strip()
        if 'lightmap_texture' in obj_info:
            info.append(obj_info)
    return info

def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def create_materials(obj_info):
    materials = []
    for info in obj_info:
        # Generate a random string of 16 characters
        random_string = generate_random_string(16)
        
        # Remove the file extension for the lightmap texture name
        lightmap_texture_name_without_extension = os.path.splitext(info['lightmap_texture'])[0]
        mat_name = f"vircadia_lightmapData_{random_string}"
        
        if mat_name in bpy.data.materials:
            mat = bpy.data.materials[mat_name]
        else:
            mat = bpy.data.materials.new(name=mat_name)
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes.get('Principled BSDF')
            tex_image = mat.node_tree.nodes.new('ShaderNodeTexImage')
            tex_image.label = "BASE COLOR"  # Set the label to "BASE COLOR"
            
            image_path = os.path.join(info['path'], info['lightmap_texture'])
            image_name = random_string  # Use the random string as the image name
            
            if image_name in bpy.data.images:
                tex_image.image = bpy.data.images[image_name]
            else:
                # Load the image and set its name to the random string
                loaded_image = bpy.data.images.load(image_path)
                loaded_image.name = image_name
                tex_image.image = loaded_image
            
            mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])
        
        materials.append(mat)
    return materials

def adjust_uv_maps(obj_info):
    for info in obj_info:
        obj = bpy.data.objects.get(info['name'])
        if obj and 'tiling_x' in info and 'tiling_y' in info and 'offset_x' in info and 'offset_y' in info:
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

def add_custom_properties(obj_info, materials):
    for info in obj_info:
        obj = bpy.data.objects.get(info['name'])
        if obj:
            mat = materials[obj_info.index(info)]
            mat_name = mat.name
            obj['vircadia_lightmap'] = mat_name
            obj['vircadia_lightmap_texcoord'] = 1

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
    materials = create_materials(obj_info)
    adjust_uv_maps(obj_info)
    create_and_join_planes(materials)
    add_custom_properties(obj_info, materials)
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
        self.filepath = "LightmapInfo.txt"  # Set the default file name
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def register():
    bpy.utils.register_class(GetLightmapInfo)

def unregister():
    bpy.utils.unregister_class(GetLightmapInfo)

if __name__ == "__main__":
    register()