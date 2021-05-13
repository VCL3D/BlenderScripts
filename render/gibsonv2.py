import os
import csv
import math

import bpy
import bmesh
from mathutils import Vector, Euler

from dataset import Dataset

class GibsonV2(Dataset):
    def __init__(self):
        super(GibsonV2, self).__init__(__name__)

    def __str__(self):
        return self.name

    def import_model(self, filepath):
        _, ext = os.path.os.path.splitext(filepath)
        if ext == '.obj':            
            bpy.ops.import_scene.obj("EXEC_DEFAULT", filepath=filepath,
                axis_forward='Y', axis_up='Z')
        else:
            print("error loading incorrect matterport mesh, unknown extension: " + ext)

    def get_instance_name(self, filepath, id = 0):
        return os.path.basename(filepath).split('_')[0]

    def get_camera_position(self, filepath):
        position = []        
        print("Reading camera pose from %s" % filepath)
        with open(filepath, 'r') as f:            
            for line in f.readlines():
                position.append(float(line.split(" ")[3]))
        return Vector(position[0:3])

    def get_camera_position_generator(self, folder):
        csv_filename = os.path.join(folder, 'camera_poses.csv')
        with open(csv_filename) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                yield Vector(list(map(lambda s: float(s), row[1:4])))

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
        depth_out.base_path = os.path.join(output_path)
        depth_out.file_slots.remove(depth_out.inputs[0])
        depth_out.file_slots.new("depth")
        depth_out.file_slots[0].path = base_filename + "#_depth_0"
        links.new(compositor.outputs['Depth'], depth_out.inputs["depth"])
        return depth_out

    def get_color_output(self, output_path, base_filename, nodes, links, compositor):
        image_out = nodes.new('CompositorNodeOutputFile')
        image_out.format.file_format = 'PNG'
        image_out.format.quality = 100
        image_out.format.color_mode = 'RGB'
        image_out.base_path = os.path.join(output_path)
        image_out.file_slots.remove(image_out.inputs[0])
        image_out.file_slots.new("color")
        image_out.file_slots[0].path = base_filename + "#_color_0"
        links.new(compositor.outputs['Image'], image_out.inputs["color"])
        return image_out

    def get_emission_output(self, output_path, base_filename, nodes, links, compositor):
        for m in bpy.data.materials:
            m.node_tree.links.remove(m.node_tree.nodes["Image Texture"].outputs['Color'].links[0])
            m.node_tree.links.new(
                m.node_tree.nodes["Image Texture"].outputs['Color'],
                m.node_tree.nodes["Principled BSDF"].inputs['Emission']
            )
        emission_out = nodes.new('CompositorNodeOutputFile')
        emission_out.format.file_format = 'PNG'
        emission_out.format.quality = 100
        emission_out.format.color_mode = 'RGB'
        emission_out.base_path = os.path.join(output_path)
        emission_out.file_slots.remove(emission_out.inputs[0])
        emission_out.file_slots.new("emission")
        emission_out.file_slots[0].path = base_filename + "#_emission_0"
        links.new(compositor.outputs['Emit'], emission_out.inputs["emission"])
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
        normals_out.base_path = os.path.join(output_path)
        normals_out.file_slots.remove(normals_out.inputs[0])
        normals_out.file_slots.new("normals")
        normals_out.file_slots[0].path = base_filename + "#_normals_0"
        links.new(compositor.outputs['Image'], normals_out.inputs["normals"])
        return normals_out

    def get_normal_map_output(self, output_path, base_filename, nodes, links, compositor):
        normal_map_out = nodes.new('CompositorNodeOutputFile')
        normal_map_out.format.file_format = 'OPEN_EXR'
        normal_map_out.format.color_depth = '32'
        normal_map_out.base_path = os.path.join(output_path)
        normal_map_out.file_slots.remove(normal_map_out.inputs[0])
        normal_map_out.file_slots.new("normal_map")
        normal_map_out.file_slots[0].path = base_filename + "#_normal_map_0"
        links.new(compositor.outputs['Normal'], normal_map_out.inputs["normal_map"])
        return normal_map_out

    def get_flow_map_output(self, output_path, base_filename, nodes, links, compositor):
        flow_map_out = nodes.new('CompositorNodeOutputFile')
        flow_map_out.format.file_format = 'OPEN_EXR'
        flow_map_out.format.color_depth = '32'
        flow_map_out.base_path = os.path.join(output_path)
        flow_map_out.file_slots.remove(flow_map_out.inputs[0])
        flow_map_out.file_slots.new("flow_map")
        flow_map_out.file_slots[0].path = base_filename + "#_flow_map_0"
        links.new(compositor.outputs['Speed'], flow_map_out.inputs["flow_map"])
        return flow_map_out

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
        bpy.context.scene.display_settings.display_device = 'sRGB'
        bpy.context.scene.view_settings.view_transform = 'Raw'
