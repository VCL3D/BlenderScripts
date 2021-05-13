import bpy
from mathutils import Vector, Euler

import json
import math
import os
import itertools
import random

from dataset import Dataset
import utils

class SunCG(Dataset):
  def __init__(self):
    super(SunCG, self).__init__(__name__)

  def __str__(self):
    return self.name

  def import_model(self, filepath):
    bpy.ops.import_scene.obj("EXEC_DEFAULT", filepath=filepath,\
      axis_forward='-Z', axis_up='Y')

  def get_instance_name(self, filepath, id = 0):
    return os.path.split(os.path.dirname(filepath))[1]

  def get_camera_position(self, filepath):
    if os.path.exists(filepath):        
        print("Reading best viewpoint from %s." % filepath)
        lines = [line.strip() for line in open(filepath, 'r')]
        if len(lines) > 0:
          best_viewpoint_text = lines[0]
          splitted = best_viewpoint_text.split()          
          return Vector((float(splitted[0]), -float(splitted[2]), float(splitted[1])))
        else:
          print("No lines found in %s, switching to central viewpoint." % filepath)
          return Vector(utils.find_center())
    else:
      print("Invalid path (%s), switching to central viewpoint." % filepath)
      return Vector(utils.find_center())

  def get_camera_position_generator(self, folder):
      viewpoints_filename = os.path.join(folder, "viewpoints.txt")
      if not os.path.exists(viewpoints_filename):
          print("Viewpoints file (%s) does not exist, switching to central viewpoint." % viewpoints_filename)
          yield Vector(utils.find_center())
      else:
        lines = [line.strip() for line in open(viewpoints_filename, 'r')]
        pos_wt = [(line.split()[0], line.split()[1], line.split()[2], line.split()[-1]) for line in lines]
        if not any(itertools.takewhile(lambda x: float(x[3]) > 15.0, itertools.islice(pos_wt, 3))):
          yield Vector(utils.find_center())
        for poswt in itertools.takewhile(lambda x: float(x[3]) > 15.0, itertools.islice(pos_wt, 3)):
            yield Vector((float(poswt[0]), -float(poswt[2]), float(poswt[1])))

  def get_camera_rotation(self, degrees = 0):
    return Euler((math.radians(90), math.radians(0), math.radians(degrees)), 'XYZ')

  def get_camera_offset(self, direction, distance, degrees):
    if direction == 'right' or direction == 'left':
      return Vector((math.trunc(math.cos(math.radians(degrees))) * distance,\
        math.trunc(math.sin(math.radians(degrees))) * distance,\
        0))
    elif direction == 'up':
      return Vector((0, 0, distance))
    elif direction == 'down':
      return Vector((0, 0, -distance))
    else:
      return Vector((0, 0, 0))

  def get_depth_output(self, output_path, base_filename, nodes, links, compositor):
    depth_out = nodes.new('CompositorNodeOutputFile')
    depth_out.format.file_format = 'OPEN_EXR'
    depth_out.format.color_depth = '32'
    depth_out.base_path = os.path.join(output_path, base_filename)
    depth_out.file_slots.remove(depth_out.inputs[0])
    depth_out.file_slots.new("depth")
    depth_out.file_slots[0].path = "#_depth_0"
    links.new(compositor.outputs['Depth'], depth_out.inputs["depth"])
    return depth_out

  def get_color_output(self, output_path, base_filename, nodes, links, compositor):
    image_out = nodes.new('CompositorNodeOutputFile')
    image_out.format.file_format = 'PNG'
    image_out.format.quality = 100
    image_out.format.color_mode = 'RGB'
    image_out.base_path = os.path.join(output_path, base_filename)
    image_out.file_slots.remove(image_out.inputs[0])
    image_out.file_slots.new("color")
    image_out.file_slots[0].path = "#_color_0"
    links.new(compositor.outputs['Image'], image_out.inputs["color"])
    return image_out

  def get_emission_output(self, output_path, base_filename, nodes, links, compositor):
    for m in bpy.data.materials:
        if 'Color Mult' not in m.node_tree.nodes.keys():
            continue
        if m.node_tree.nodes.get("Color Mult", None) is not None and m.node_tree.nodes.get("Material Output", None) is not None:
            m.node_tree.links.remove(m.node_tree.nodes["Color Mult"].outputs[0].links[0])
            emission = m.node_tree.nodes.new(type="ShaderNodeEmission")
            m.node_tree.links.new(m.node_tree.nodes["Color Mult"].outputs[0], emission.inputs[0])
            m.node_tree.links.new(emission.outputs[0], m.node_tree.nodes["Material Output"].inputs[0])
    emission_out = nodes.new('CompositorNodeOutputFile')
    emission_out.format.file_format = 'PNG'
    emission_out.format.quality = 100
    emission_out.format.color_mode = 'RGB'
    emission_out.base_path = os.path.join(output_path, base_filename)
    emission_out.file_slots.remove(emission_out.inputs[0])
    emission_out.file_slots.new("emission")
    emission_out.file_slots[0].path = "#_emission_0"
    links.new(compositor.outputs['Emit'], emission_out.inputs["emission"])
    return emission_out

  def get_normals_output(self, output_path, base_filename, nodes, links, compositor):
    meshes = [mesh for mesh in bpy.data.objects if mesh.type == 'MESH']
    for mesh in meshes:
      for slot in mesh.material_slots:
        if slot.material.node_tree.nodes.find("Diffuse Texture") > 0:
          material = slot.material
          material.node_tree.nodes.new('ShaderNodeMapping')          
          material.node_tree.nodes['Mapping'].vector_type = 'NORMAL'
          material.node_tree.nodes['Mapping'].rotation[0] = math.radians(90) # X
          material.node_tree.nodes['Mapping'].rotation[1] = math.radians(0) # Y
          material.node_tree.nodes['Mapping'].rotation[2] = math.radians(90) # Z
          material.node_tree.nodes.new('ShaderNodeVectorTransform')          
          material.node_tree.nodes['Vector Transform'].vector_type = 'NORMAL'
          material.node_tree.nodes['Vector Transform'].convert_to = 'CAMERA'
          material.node_tree.links.new(\
            material.node_tree.nodes['Texture Coordinate'].outputs['Normal'], \
            material.node_tree.nodes['Mapping'].inputs['Vector'])
          material.node_tree.links.new(\
            material.node_tree.nodes['Mapping'].outputs['Vector'], \
            material.node_tree.nodes['Vector Transform'].inputs['Vector'])
          material.node_tree.links.new(\
            material.node_tree.nodes['Vector Transform'].outputs['Vector'],\
            material.node_tree.nodes['Diffuse BSDF'].inputs['Color'])
    normals_out = nodes.new('CompositorNodeOutputFile')
    normals_out.format.file_format = 'OPEN_EXR'
    normals_out.format.color_depth = '32'
    normals_out.base_path = os.path.join(output_path, base_filename)
    normals_out.file_slots.remove(normals_out.inputs[0])
    normals_out.file_slots.new("normals")
    normals_out.file_slots[0].path = "#_normals_0"
    links.new(compositor.outputs['Image'], normals_out.inputs["normals"])
    return normals_out

  def get_normal_map_output(self, output_path, base_filename, nodes, links, compositor):
    normal_map_out = nodes.new('CompositorNodeOutputFile')
    normal_map_out.format.file_format = 'OPEN_EXR'
    normal_map_out.format.color_depth = '32'
    normal_map_out.base_path = os.path.join(output_path, base_filename)
    normal_map_out.file_slots.remove(normal_map_out.inputs[0])
    normal_map_out.file_slots.new("normal_map")
    normal_map_out.file_slots[0].path = "#_normal_map_0"
    links.new(compositor.outputs['Normal'], normal_map_out.inputs["normal_map"])
    return normal_map_out

  def get_flow_map_output(self, output_path, base_filename, nodes, links, compositor):
      flow_map_out = nodes.new('CompositorNodeOutputFile')
      flow_map_out.format.file_format = 'OPEN_EXR'
      flow_map_out.format.color_depth = '32'
      flow_map_out.base_path = os.path.join(output_path, base_filename)
      flow_map_out.file_slots.remove(flow_map_out.inputs[0])
      flow_map_out.file_slots.new("flow_map")
      flow_map_out.file_slots[0].path = "#_flow_map_0"
      links.new(compositor.outputs['Vector'], flow_map_out.inputs["flow_map"])
      return flow_map_out

  def get_semantic_map_output(self, labels_path, output_path, base_filename, nodes, links, compositor):
    with open(labels_path) as f:
        categories = json.load(f)
    for material in bpy.data.materials:
        material.pass_index = categories[material.name]['id']
    # material id output
    material_out = nodes.new('CompositorNodeOutputFile')
    material_out.name = material_out.label = 'material_out'
    material_out.format.file_format = 'OPEN_EXR'    
    material_out.format.color_depth = '32'    
    material_out.base_path = os.path.join(output_path, base_filename)
    material_out.file_slots.remove(material_out.inputs[0])
    material_out.file_slots.new("category")
    material_out.file_slots[0].path = "#_labels_0"
    links.new(compositor.outputs['IndexMA'], material_out.inputs["category"])
    return material_out

  def get_pretty_semantic_map_output(self, labels_path, output_path, base_filename, nodes, links, compositor):
      with open(labels_path) as f:
          categories = json.load(f)
      for material in bpy.data.materials:
          material.pass_index = categories[material.name]['id']        
      for material in bpy.data.materials:
          name = material.name
          index = material.pass_index
          mask = nodes.new("CompositorNodeIDMask")
          mask.index = index
          mask.name = mask.label = 'mask_' + str(name)
          mask.use_antialiasing = True
          links.new(compositor.outputs['IndexMA'], mask.inputs[0])
          color = material.diffuse_color
          rgb = nodes.new("CompositorNodeRGB")
          rgb.name = rgb.label = 'rgb_' + str(name)            
          rgb.outputs[0].default_value = (color[0], color[1], color[2], 255.0)                      
      sorted_materials = sorted(bpy.data.materials, key=lambda m: m.pass_index, reverse=False)
      first_index = sorted_materials[0].pass_index
      for first, second in utils.pairwise(sorted_materials):
          mix = nodes.new("CompositorNodeMixRGB")
          mix.name = 'mix_' + str(second.pass_index)
          mix.label = 'mix_' + first.name + '_' + second.name
          mix.use_clamp = True
          mask = nodes['mask_' + second.name]
          rgb1 = nodes['rgb_' + first.name] if first.pass_index == first_index else nodes['mix_' + str(first.pass_index)]
          rgb2 = nodes['rgb_' + second.name]            
          links.new(mask.outputs[0], mix.inputs[0])
          links.new(rgb1.outputs[0], mix.inputs[1])
          links.new(rgb2.outputs[0], mix.inputs[2])
      # material pretty output
      pretty_out = nodes.new('CompositorNodeOutputFile')
      pretty_out.name = pretty_out.label = 'pretty_out'
      pretty_out.format.quality = 100
      pretty_out.format.color_mode = 'RGB'
      pretty_out.base_path = os.path.join(output_path, base_filename)
      pretty_out.file_slots.remove(pretty_out.inputs[0])
      pretty_out.file_slots.new("pretty")
      pretty_out.file_slots[0].path = "#_labels_pretty"
      links.new(mix.outputs[0], pretty_out.inputs["pretty"])
      return pretty_out

  def set_render_settings(self):
      bpy.context.scene.cycles.sample_clamp_direct = 2.0
      bpy.context.scene.cycles.sample_clamp_indirect = 1.0
      bpy.context.scene.cycles.caustics_reflective = False
      bpy.context.scene.cycles.caustics_refractive = False
      bpy.context.scene.cycles.max_bounces = 5
      bpy.context.scene.cycles.min_bounces = 4
      bpy.context.scene.cycles.diffuse_bounces = 4
      bpy.data.worlds["World"].color = (0.0, 0.0, 0.0)
      bpy.data.worlds["World"].light_settings.use_ambient_occlusion = True
      bpy.data.worlds["World"].cycles_visibility.glossy = False
      bpy.data.worlds["World"].cycles_visibility.transmission = False
      bpy.data.worlds["World"].cycles_visibility.scatter = False
      bpy.data.worlds["World"].cycles.sample_map_resolution = 2048
      bpy.data.worlds["World"].cycles.max_bounces = 2048
      bpy.context.scene.cycles.debug_use_hair_bvh = False
      bpy.context.scene.display_settings.display_device = 'sRGB'
      bpy.context.scene.view_settings.view_transform = random.choice(['Raw', 'Film'])
      bpy.context.scene.view_settings.exposure = random.uniform(0.8, 1.2)
      bpy.context.scene.view_settings.gamma = random.uniform(0.8, 1.2)
      bpy.context.scene.cycles.film_exposure = random.uniform(0.8, 1.2)
      bpy.context.scene.cycles.progressive = 'BRANCHED_PATH'
      bpy.context.scene.cycles.aa_samples = 64
      bpy.context.scene.cycles.diffuse_samples = 64

  def create_lights(self, lights_metadata_path):
      with open(lights_metadata_path) as f:
          metadata = json.load(f)            
          light_ids = metadata.keys()
      success = False
      for m in bpy.data.meshes:
          if "Model#" in m.name and m.name.split("#")[1] in light_ids:
              success = True
              light_metadata = metadata[m.name.split("#")[1]][0]              
              light_type = light_metadata['type']
              model_position = utils.find_model_center(bpy.data.objects[m.name])
              if light_type == "PointLight" or light_type == "LineLight":
                  bpy.ops.object.lamp_add(location=model_position)
                  obj = bpy.context.object
                  obj.data.node_tree.nodes["Emission"].inputs[1].default_value = random.uniform(2.0, 4.0) * light_metadata["power"]
                  light_offset = light_metadata['position']                  
                  obj.location += Vector((float(light_offset[0]), -float(light_offset[2]), float(light_offset[1])))
                  obj.data.shadow_soft_size = 1.5
              elif light_type == "SpotLight":
                  success = True
                  light_direction = light_metadata['direction']
                  direction = Vector(model_position) + Vector((float(light_direction[0]), -float(light_direction[2]), float(light_direction[1])))
                  rot_quat = direction.to_track_quat('X', 'Z') # point the cameras '-Z' and use its 'Y' as up
                  bpy.ops.object.lamp_add(type='SPOT', location=model_position,\
                      rotation=rot_quat.to_euler())
                  obj = bpy.context.object
                  obj.data.node_tree.nodes["Emission"].inputs[1].default_value = random.uniform(5.0, 15.0) * light_metadata["power"]
                  light_offset = light_metadata['position']
                  obj.location += Vector((float(light_offset[0]), -float(light_offset[2]), float(light_offset[1])))
                  cutoffAngle = float(light_metadata['cutoffAngle'])                    
                  obj.data.spot_size = random.uniform(0.5, 1.0) * cutoffAngle
                  obj.data.shadow_soft_size = 1.0
      return success