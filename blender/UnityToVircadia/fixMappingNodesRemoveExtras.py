import bpy
import os
import re
import math
from mathutils import Color

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
                   value = line.split(": ")[1].replace(',', '.')
                   material_tiling[current_material]['x'] = float(value)
               elif line.startswith("Tiling Y:"):
                   value = line.split(": ")[1].replace(',', '.')
                   material_tiling[current_material]['y'] = float(value)
               elif line.startswith("Smoothness:"):
                   value = line.split(": ")[1].replace(',', '.')
                   material_tiling[current_material]['smoothness'] = float(value)
               elif line.startswith("Base Color R:"):
                   material_tiling[current_material]['r'] = int(line.split(": ")[1])
               elif line.startswith("Base Color G:"):
                   material_tiling[current_material]['g'] = int(line.split(": ")[1])
               elif line.startswith("Base Color B:"):
                   material_tiling[current_material]['b'] = int(line.split(": ")[1])

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

   # Find or create a UV Map node
   uv_map_node = None
   for node in nodes:
       if node.type == 'UVMAP':
           uv_map_node = node
           break
   if not uv_map_node:
       uv_map_node = nodes.new(type='ShaderNodeUVMap')

   for mapping_node in mapping_nodes:
       # Connect the UV Map node to the mapping node
       if not any(link.from_node == uv_map_node and link.to_node == mapping_node for link in links):
           links.new(uv_map_node.outputs['UV'], mapping_node.inputs['Vector'])

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

       # Remove Roughness Factor node if connected to Separate_color
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
               if not any(link.from_node == target_texture_node and link.to_socket == node.inputs['Specular'] for link in links):
                   links.new(target_texture_node.outputs['Color'], node.inputs['Specular'])

   # Find the metallic roughness texture node
   metallic_roughness_node = None
   for node in nodes:
       if node.type == 'TEX_IMAGE' and node.label == "METALLIC ROUGHNESS":
           metallic_roughness_node = node
           break

   if metallic_roughness_node:
       # Find the Principled BSDF node
       principled_node = None
       for node in nodes:
           if node.type == 'BSDF_PRINCIPLED':
               principled_node = node
               break

       if principled_node:
           # Disconnect nodes connected to the roughness input of the Principled BSDF
           for link in principled_node.inputs['Roughness'].links:
               links.remove(link)

           # Connect the metallic roughness texture to the metallic input of Principled BSDF
           links.new(metallic_roughness_node.outputs['Color'], principled_node.inputs['Metallic'])

   # Set the roughness value based on the smoothness value from the MaterialsCheckReport.txt file for all materials
   material_name_without_suffix = remove_numbered_suffix(material.name)
   for mat_name, tiling_info in material_tiling.items():
       if remove_numbered_suffix(mat_name) == material_name_without_suffix and 'smoothness' in tiling_info:
           roughness_value = 1.0 - tiling_info['smoothness']
           for node in nodes:
               if node.type == 'BSDF_PRINCIPLED':
                   node.inputs['Roughness'].default_value = roughness_value
                   break

def switch_to_newer_textures(material):
   if not material.node_tree:
       return

   nodes = material.node_tree.nodes

   # Find all image texture nodes in the material
   image_nodes = [node for node in nodes if node.type == 'TEX_IMAGE']

   for image_node in image_nodes:
       if image_node.image:
           # Get the base name of the current texture
           current_texture_name = image_node.image.name
           base_name = remove_numbered_suffix(current_texture_name)

           # Find the highest numbered version of the texture in the scene
           highest_version = current_texture_name
           highest_suffix = 0
           for image in bpy.data.images:
               if image.name.startswith(base_name):
                   suffix_match = re.search(r'\.(\d+)$', image.name)
                   if suffix_match:
                       suffix = int(suffix_match.group(1))
                       if suffix > highest_suffix:
                           highest_version = image.name
                           highest_suffix = suffix

           # Switch to the highest numbered version of the texture
           if highest_version != current_texture_name:
               image_node.image = bpy.data.images[highest_version]

def convert_srgb_to_linear(srgb_value):
   if srgb_value <= 0.04045:
       linear_value = srgb_value / 12.92
   else:
       linear_value = ((srgb_value + 0.055) / 1.055) ** 2.4
   return linear_value

def swap_materials_with_suffixes_and_set_vertex_colors(material_tiling):
   # Get all mesh objects in the scene
   mesh_objects = [obj for obj in bpy.data.objects if obj.type == 'MESH']

   # Dictionary to store color values for each material
   material_colors = {}

   # Iterate over each material in the material_tiling dictionary
   for material_name, tiling_info in material_tiling.items():
       # Get the RGB values from the text file for the material
       r = tiling_info.get('r', 255)
       g = tiling_info.get('g', 255)
       b = tiling_info.get('b', 255)

       # Convert sRGB values to linear
       r_linear = convert_srgb_to_linear(r / 255.0)
       g_linear = convert_srgb_to_linear(g / 255.0)
       b_linear = convert_srgb_to_linear(b / 255.0)

       # Store the color values for the material
       material_colors[material_name] = (r_linear, g_linear, b_linear, 1.0)

   # Iterate over each mesh object
   for obj in mesh_objects:
       # Iterate over each material slot in the object
       for slot in obj.material_slots:
           material = slot.material
           if material:
               # Check if the material has a counterpart in the text file
               if material.name in material_tiling:
                   # Find the similar material with suffix and not in text file
                   material_name_without_suffix = remove_numbered_suffix(material.name)
                   for mat in bpy.data.materials:
                       if remove_numbered_suffix(mat.name) == material_name_without_suffix and mat.name not in material_tiling:
                           # Swap the material in the slot with the similar material that has a suffix
                           slot.material = mat

                           # Get the color values for the original material
                           color_values = material_colors.get(material.name)

                           # Create a new vertex color layer with the name "Col" if it doesn't exist
                           color_attribute_name = "Col"
                           if color_attribute_name not in obj.data.vertex_colors:
                               obj.data.vertex_colors.new(name=color_attribute_name)

                           # Set the color values for each loop in the mesh object
                           for poly in obj.data.polygons:
                               for loop_index in poly.loop_indices:
                                   obj.data.vertex_colors[color_attribute_name].data[loop_index].color = color_values

                           break

def apply_gamma_correction(srgb_value):
   linear_value = pow(srgb_value / 255.0, 2.2)
   return linear_value

def set_base_color_from_rgb(material_tiling):
   # Get all mesh objects in the scene
   mesh_objects = [obj for obj in bpy.data.objects if obj.type == 'MESH']

   # Iterate over each mesh object
   for obj in mesh_objects:
       # Iterate over each material slot in the object
       for slot in obj.material_slots:
           material = slot.material
           if material and material.node_tree:
               nodes = material.node_tree.nodes
               links = material.node_tree.links

               # Find the Principled BSDF shader
               principled_node = next((node for node in nodes if node.type == 'BSDF_PRINCIPLED'), None)

               if principled_node:
                   base_color_input = principled_node.inputs['Base Color']

                   # Check if the base color input is not connected
                   if not base_color_input.is_linked:
                       # Check if the material has a counterpart in the text file with RGB values
                       if material.name in material_tiling and 'r' in material_tiling[material.name] and 'g' in material_tiling[material.name] and 'b' in material_tiling[material.name]:
                           r = apply_gamma_correction(material_tiling[material.name]['r'])
                           g = apply_gamma_correction(material_tiling[material.name]['g'])
                           b = apply_gamma_correction(material_tiling[material.name]['b'])

                           # Set the base color of the Principled BSDF shader
                           base_color_input.default_value = (r, g, b, 1.0)  # Assuming alpha is 1.0

def adjust_shaders(context, file_path):
   material_tiling = read_material_tiling_from_file(file_path)

   # Iterate over all materials in scene
   for material in bpy.data.materials:
       connect_mapping_to_textures_and_adjust_gloss_and_spec(material, material_tiling)
       switch_to_newer_textures(material)

   swap_materials_with_suffixes_and_set_vertex_colors(material_tiling)
   set_base_color_from_rgb(material_tiling)

def register():
   pass

def unregister():
   pass