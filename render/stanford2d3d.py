import json
import os
import math

import bpy
import bmesh
from mathutils import Vector
from mathutils import Euler

from dataset import Dataset
import utils

class Stanford2D3D(Dataset):
    def __init__(self):
        super(Stanford2D3D, self).__init__(__name__)

    def __str__(self):
        return self.name

    def import_model(self, filepath):
        bpy.ops.import_scene.obj("EXEC_DEFAULT", filepath=filepath, \
            axis_forward='-Z', axis_up='Y')

    def get_instance_name(self, filepath, id = 0):        
        return os.path.basename(os.path.dirname(os.path.dirname(filepath)))

    def get_camera_position(self, filepath):
        with open(os.path.join(filepath), 'r') as f: 
            data = json.load(f)
            position = data['camera_location']
        return Vector(position)

    def get_camera_position_generator(self, folder):
        hashes_w_filenames = [(fp.split("_")[1], os.path.join(folder, fp)) for fp in os.listdir(folder)]
        for h_fn in utils.distinct(hashes_w_filenames):
            yield self.get_camera_position(h_fn[1])

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
        emission_out.file_slots.new("raw")
        emission_out.file_slots[0].path = "#_emission_0"
        links.new(compositor.outputs['Emit'], emission_out.inputs["raw"])
        return emission_out

    def get_normals_output(self, output_path, base_filename, nodes, links, compositor):
        meshes = [mesh for mesh in bpy.data.objects if mesh.type == 'MESH']
        bm = bmesh.new()     
        for mesh in meshes:
            bm.from_mesh(mesh.data)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            bm.to_mesh(mesh.data)
            bm.clear()
            mesh.data.update()
            mesh.data.use_auto_smooth = True
            for slot in mesh.material_slots:
                if slot.material.node_tree.nodes.find("Diffuse Texture") > 0:
                    material = slot.material
                    material.node_tree.nodes.new('ShaderNodeMapping')          
                    material.node_tree.nodes['Mapping'].vector_type = 'NORMAL'
                    material.node_tree.nodes['Mapping'].rotation[0] = math.radians(0) # X
                    material.node_tree.nodes['Mapping'].rotation[1] = math.radians(0) # Y
                    material.node_tree.nodes['Mapping'].rotation[2] = math.radians(0) # Z
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
        bm.free()
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
        bpy.data.worlds["World"].color = (0.0, 0.0, 0.0)
        bpy.data.worlds["World"].light_settings.use_ambient_occlusion = True
        bpy.data.worlds["World"].cycles_visibility.glossy = False
        bpy.data.worlds["World"].cycles_visibility.transmission = False
        bpy.data.worlds["World"].cycles_visibility.scatter = False
        bpy.context.scene.cycles.debug_use_spatial_splits = True
        bpy.context.scene.cycles.debug_use_hair_bvh = False
        bpy.context.scene.cycles.caustics_reflective = False
        bpy.context.scene.cycles.caustics_refractive = False
        bpy.context.scene.display_settings.display_device = 'None'
        # bpy.context.scene.view_settings.view_transform = 'Raw'