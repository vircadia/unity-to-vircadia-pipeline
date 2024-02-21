import bpy

def clear_parents_and_keep_transformation():
    for obj in bpy.data.objects:
        obj.select_set(True)
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
        obj.select_set(False)

def set_uniform_scale():
    for obj in bpy.data.objects:
        obj.scale = (100, 100, 100)

def apply_scale_and_make_unique_data():
    for obj in bpy.data.objects:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        if obj.data:
            obj.data = obj.data.copy()
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        obj.select_set(False)

def identify_and_link_originals_duplicates():
    originals = {}
    duplicates = []

    for obj in bpy.data.objects:
        if "(" in obj.name and ")" in obj.name:
            base_name = obj.name.split("(")[0].strip()
            duplicates.append((base_name, obj))
        else:
            originals[obj.name] = obj

    for base_name, duplicate in duplicates:
        if base_name in originals:
            duplicate.data = originals[base_name].data

    bpy.context.view_layer.update()

def correct_scale():
    clear_parents_and_keep_transformation()
    set_uniform_scale()
    apply_scale_and_make_unique_data()
    identify_and_link_originals_duplicates()

class CorrectScale(bpy.types.Operator):
    """Correct Scale"""
    bl_idname = "object.correct_scale"
    bl_label = "Correct Scale"

    def execute(self, context):
        correct_scale()
        return {'FINISHED'}
