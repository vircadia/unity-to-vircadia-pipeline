import bpy
import os

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
            elif line.startswith('Path:'):
                obj_info['path'] = line.split(': ')[1].strip()
        info.append(obj_info)
    return info

def create_materials(obj_info):
    materials = []
    for info in obj_info:
        mat_name = f"vircadia_lightmapData_{os.path.splitext(info['lightmap_texture'])[0]}"
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get('Principled BSDF')
        tex_image = mat.node_tree.nodes.new('ShaderNodeTexImage')
        tex_image.image = bpy.data.images.load(os.path.join(info['path'], info['lightmap_texture']))
        mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])
        materials.append(mat)
    return materials

def create_and_join_planes(materials):
    created_objects = []
    for i, mat in enumerate(materials):
        bpy.ops.mesh.primitive_plane_add(size=2)
        plane = bpy.context.active_object
        plane.name = f"merge.{str(i+1).zfill(3)}"
        plane.data.materials.append(mat)
        created_objects.append(plane)

    # Ensure all created planes are selected
    bpy.ops.object.select_all(action='DESELECT')
    for obj in created_objects:
        obj.select_set(True)

    # Set one of the planes as the active object
    bpy.context.view_layer.objects.active = created_objects[0]

    # Join the planes into a single object
    bpy.ops.object.join()
    bpy.context.active_object.name = "vircadia_lightmapData"

def add_custom_properties(obj_info, materials):
    for info in obj_info:
        obj = bpy.data.objects.get(info['name'])
        if obj:
            mat_name = f"vircadia_lightmapData_{os.path.splitext(info['lightmap_texture'])[0]}"
            obj['vircadia_lightmap'] = mat_name
            obj['vircadia_lightmap_texcoord'] = 1  # Default value set to 1

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
    create_and_join_planes(materials)
    add_custom_properties(obj_info, materials)
    make_materials_single_user(obj_info)  # Make specified object materials single-user

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
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
