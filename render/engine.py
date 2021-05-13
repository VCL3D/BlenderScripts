import bpy

from math import radians

class Cycles28(object):
    
    def __init__(self, 
        device_type: str='CUDA',
        device_id: int=0,
        samples: int=128,
        depth_pass: bool=False,
        normal_pass: bool=False,
        label_pass: bool=False,
        raw_pass: bool=False,
        flow_pass: bool=False,
        object_pass: bool=False
    ):
        print(f"Setting device to {device_type}:{device_id}")
        bpy.context.scene.render.engine = 'CYCLES' 
        # bpy.ops.xps_tools.convert_to_cycles_all()
        bpy.context.preferences.addons['cycles'].preferences.get_devices()
        bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'        
        bpy.context.scene.cycles.device = device_type
        if device_type == 'GPU':
            bpy.context.scene.cycles.feature_set = "EXPERIMENTAL"        
        for i, device in enumerate(bpy.context.preferences.addons['cycles'].preferences.devices):
            enable = (i == int(device_id))
            device.use = enable
            print(f"Setting device {device} ({i}) to {device.use} ({enable})")
        # bpy.context.preferences.addons['cycles'].preferences.devices[0].use = True        
        # bpy.context.preferences.addons['cycles'].preferences.devices[device_id].use = True
        #print(f"Setting device {device_id} to {bpy.context.preferences.addons['cycles'].preferences.devices[device_id].use}")
        bpy.context.scene.render.threads_mode = 'AUTO' if device_type == 'GPU' else 'FIXED'
        bpy.context.scene.render.threads = 1 if device_type == 'GPU' else 4
        bpy.context.scene.render.image_settings.color_mode = 'RGB'
        bpy.context.scene.render.image_settings.use_zbuffer = depth_pass
        bpy.context.scene.view_layers[0].use_pass_normal = normal_pass
        bpy.context.scene.view_layers[0].use_pass_material_index = label_pass
        bpy.context.scene.view_layers[0].use_pass_emit = raw_pass
        bpy.context.scene.view_layers[0].use_pass_vector = flow_pass
        bpy.context.scene.view_layers[0].use_pass_object_index = object_pass        
        bpy.context.scene.render.resolution_percentage = 100
        #bpy.context.scene.view_settings.view_transform = 'Raw'
        bpy.context.scene.render.tile_x = 128 if device_type == 'GPU' else 64
        bpy.context.scene.render.tile_y = 128 if device_type == 'GPU' else 64
        bpy.context.scene.cycles.debug_bvh_type = 'STATIC_BVH'
        bpy.data.scenes[0].cycles.samples = samples
        self.spherical_camera = None
        self.perspective_camera = None
        print(f"Blender Cycles Device set to {bpy.context.scene.cycles.device}")

    def get_scene_nodes(self):
        bpy.context.scene.use_nodes = True
        tree = bpy.context.scene.node_tree                
        for n in tree.nodes: # clear default nodes
            tree.nodes.remove(n)
        compositor = tree.nodes.new('CompositorNodeRLayers')
        return tree.nodes, tree.links, compositor

    def get_camera(self, camera_type, render_width, render_height, fov_h=90.0):
        if camera_type == 'spherical':
            if self.spherical_camera is None:
                bpy.ops.object.camera_add(align='WORLD', enter_editmode=False, \
                    location=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0))        
                self.spherical_camera = bpy.context.object
                self.spherical_camera.name = 'Spherical'
                self.spherical_camera.data.name = self.spherical_camera.name
                cam = bpy.data.cameras[self.spherical_camera.name]      
                cam.type = 'PANO'
                cam.cycles.panorama_type = 'EQUIRECTANGULAR'
                bpy.context.scene.render.resolution_x = render_width
                bpy.context.scene.render.resolution_y = render_width // 2
            return self.spherical_camera
        elif camera_type == 'perspective':
            if self.perspective_camera is None:
                bpy.ops.object.camera_add(align='WORLD', enter_editmode=False, \
                    location=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0))        
                self.perspective_camera = bpy.context.object
                self.perspective_camera.name = 'Perspective'
                self.perspective_camera.data.name = self.perspective_camera.name
                cam = bpy.data.cameras[self.perspective_camera.name]      
                cam.type = 'PERSP'
                cam.lens_unit = 'FOV'
                cam.angle = radians(fov_h)
                bpy.context.scene.render.resolution_x = render_width
                bpy.context.scene.render.resolution_y = render_height
            return self.perspective_camera
        else:
            return None

    def get_point_light(self, emission):
        bpy.ops.object.light_add()
        obj = bpy.context.object
        obj.data.node_tree.nodes["Emission"].inputs[1].default_value = emission
        return obj

class OutputNode(object):
    def __init__(self, output_layer, base_filename, output_type):
        self.output_layer = output_layer
        self.base_filename = base_filename
        self.output_type = output_type        

    def prepare_render(self, position_type, degrees, camera_type, index=0):
        self.output_layer.file_slots[0].path = "%d_%s_#_%s_%s_%d" \
            % (index, camera_type, self.output_type, position_type, degrees)