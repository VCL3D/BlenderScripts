from drone import Drone

import bpy
from mathutils import Color

import itertools
import random
import os

class DJI(Drone):
    def __init__(self, without_wings: bool=True, prejoined: bool=False):
        super(DJI, self).__init__(__name__)
        self.without_wings = without_wings
        self.prejoined = prejoined
        self.parts = []

    def __str__(self):
        return self.name

    def get_instance_name(self):
        return self.name

    def import_model(self, filepath):
        bpy.ops.import_scene.fbx("EXEC_DEFAULT", filepath=filepath)
        if self.without_wings:
            for o in bpy.data.objects:
                o.select_set(False)
            for o in filter(lambda o: 'Wing8' in o.name, bpy.data.objects):
                if '.004' in o.name or '.005' in o.name or '.006' in o.name\
                    or '.007' in o.name or '.008' in o.name:
                        bpy.data.objects[o.name].select_set(True)
                        bpy.ops.object.delete(use_global=False)
        for o in filter(lambda o: 'Wing8' in o.name, bpy.data.objects):
            if len(o.material_slots[0].material.node_tree.nodes["Principled BSDF"].inputs['Alpha'].links) == 0:
                continue
            o.material_slots[0].material.node_tree.links.remove(
                o.material_slots[0].material.node_tree.nodes["Principled BSDF"].inputs['Alpha'].links[0]
            )
            value_node = o.material_slots[0].material.node_tree.nodes.new('ShaderNodeValue')
            value_node.outputs[0].default_value = 1.0
            o.material_slots[0].material.node_tree.links.new(
                value_node.outputs[0],
                o.material_slots[0].material.node_tree.nodes["Principled BSDF"].inputs['Alpha']
            )
            o.material_slots[0].material.node_tree.nodes["Principled BSDF"].inputs[12].default_value = 0.7
            o.material_slots[0].material.node_tree.nodes["Principled BSDF"].inputs[13].default_value = 0.7
            o.material_slots[0].material.node_tree.nodes["Principled BSDF"].inputs[7].default_value = 0.7
            o.material_slots[0].material.node_tree.nodes["Principled BSDF"].inputs[4].default_value = 0.6
        if not self.prejoined:
            wings = list(w for w in bpy.data.objects if 'Wing' in w.name)
            bpy.context.view_layer.objects.active = wings[0]
            for w in wings: 
                w.select_set(True)
            bpy.ops.object.join()
        self.model = next(itertools.dropwhile(lambda o: 'Wing' not in o.name, bpy.data.objects))
        return self.model

    def show(self):
        self.model.cycles_visibility.camera = True

    def hide(self):
        self.model.cycles_visibility.camera = False

    def get_mask_output(self, output_path, base_filename, nodes, links, compositor):
        self.model.pass_index = 1
        mask_out = nodes.new("CompositorNodeOutputFile")
        mask_out.format.file_format = 'PNG' #'OPEN_EXR'
        mask_out.format.color_depth = '8' #'32'
        mask_out.base_path = os.path.join(output_path, base_filename)
        mask_out.file_slots.remove(mask_out.inputs[0])
        mask_out.file_slots.new("silhouette")
        mask_out.file_slots[0].path = "#_silhouette_0"
        links.new(compositor.outputs['IndexOB'], mask_out.inputs["silhouette"])
        return mask_out

    def set_render_settings(self):
        bpy.data.worlds["World"].color = (0.0, 0.0, 0.0)
        bpy.data.worlds["World"].light_settings.use_ambient_occlusion = True
        bpy.data.worlds["World"].cycles_visibility.glossy = True
        bpy.data.worlds["World"].cycles_visibility.transmission = True
        bpy.data.worlds["World"].cycles_visibility.scatter = True
        bpy.context.scene.cycles.debug_use_spatial_splits = True
        bpy.context.scene.cycles.debug_use_hair_bvh = False
        bpy.context.scene.cycles.caustics_reflective = True
        bpy.context.scene.cycles.caustics_refractive = True
        bpy.context.scene.display_settings.display_device = 'None'
        # bpy.context.scene.view_layers[0].cycles.use_pass_crypto_object = True
        bpy.context.scene.view_layers[0].cycles.use_pass_crypto_asset = True
        bpy.context.scene.view_layers[0].cycles.use_denoising = True

    def set_random_lighting(self):
        if 'Environment Texture' in bpy.context.scene.world.node_tree.nodes.keys():
            bpy.context.scene.world.node_tree.nodes.remove(bpy.context.scene.world.node_tree.nodes['Environment Texture'])
        env = bpy.context.scene.world.node_tree.nodes.new("ShaderNodeTexEnvironment")
        env.interpolation = 'Cubic'
        env.image = bpy.data.images[random.randint(0, len(bpy.data.images) - 1)]
        # env.image = bpy.data.images["Render Result"]
        bpy.context.scene.world.node_tree.links.new(
            bpy.context.scene.world.node_tree.nodes['Environment Texture'].outputs['Color'],
            bpy.context.scene.world.node_tree.nodes['Background'].inputs['Color']
        )
        bpy.context.scene.world.node_tree.nodes['Background'].inputs[1].default_value = random.uniform(0.001, 0.2)

    def get_combined_output(self, output_path, base_filename, nodes, links, compositor):
        mix = nodes.new("CompositorNodeMixRGB")
        crypto_mask = nodes.new("CompositorNodeCryptomatte")
        # crypto_mask.matte_id = '<9.48593618e+29>'
        crypto_mask.matte_id = 'Wing8'
        links.new(compositor.outputs['Image'], crypto_mask.inputs['Image'])
        # links.new(compositor.outputs['CryptoObject00'], crypto_mask.inputs['Crypto 00'])
        links.new(compositor.outputs['CryptoAsset00'], crypto_mask.inputs['Crypto 00'])
        links.new(crypto_mask.outputs['Matte'], mix.inputs['Fac'])

        links.new(compositor.outputs['Emit'], mix.inputs[1])
        links.new(compositor.outputs['Image'], mix.inputs[2])

        combined_out = nodes.new("CompositorNodeOutputFile")
        combined_out.format.file_format = 'PNG'
        combined_out.format.color_depth = '8'
        combined_out.base_path = os.path.join(output_path, base_filename)
        combined_out.file_slots.remove(combined_out.inputs[0])
        combined_out.file_slots.new("combined")
        combined_out.file_slots[0].path = "#_combined_0"
        links.new(mix.outputs[0], combined_out.inputs["combined"])
        return combined_out

class Photogrammetry(Drone):
    def __init__(self):
        super(Photogrammetry, self).__init__(__name__)        

    def __str__(self):
        return self.name

    def get_instance_name(self):
        return self.name

    def import_model(self, filepath):
        bpy.ops.import_scene.fbx("EXEC_DEFAULT", filepath=filepath)                
        self.model = next(itertools.dropwhile(lambda o: 'Wing' not in o.name, bpy.data.objects))
        self.model.material_slots[0].material.node_tree.nodes["Principled BSDF"].inputs[4].default_value = 0.8 # Metallic
        self.model.material_slots[0].material.node_tree.nodes["Principled BSDF"].inputs[5].default_value = 0.8 # Specular
        self.model.material_slots[0].material.node_tree.nodes["Principled BSDF"].inputs[6].default_value = 1.0 # Specular Tint
        self.model.material_slots[0].material.node_tree.nodes["Principled BSDF"].inputs[7].default_value = 0.9 # Roughness
        self.model.material_slots[0].material.node_tree.nodes["Principled BSDF"].inputs[12].default_value = 0.5 # Clearcoat
        self.model.material_slots[0].material.node_tree.nodes["Principled BSDF"].inputs[13].default_value = 1.0 # Clearcoat Roughness

        return self.model

    def show(self):
        self.model.cycles_visibility.camera = True

    def hide(self):
        self.model.cycles_visibility.camera = False

    def get_mask_output(self, output_path, base_filename, nodes, links, compositor):
        self.model.pass_index = 1
        mask_out = nodes.new("CompositorNodeOutputFile")
        mask_out.format.file_format = 'PNG' #'OPEN_EXR'
        mask_out.format.color_depth = '8' #'32'
        mask_out.base_path = os.path.join(output_path, base_filename)
        mask_out.file_slots.remove(mask_out.inputs[0])
        mask_out.file_slots.new("silhouette")
        mask_out.file_slots[0].path = "#_silhouette_0"
        links.new(compositor.outputs['IndexOB'], mask_out.inputs["silhouette"])
        return mask_out

    def set_render_settings(self):
        bpy.data.worlds["World"].color = (0.0, 0.0, 0.0)
        bpy.data.worlds["World"].light_settings.use_ambient_occlusion = True
        bpy.data.worlds["World"].cycles_visibility.glossy = True
        bpy.data.worlds["World"].cycles_visibility.transmission = True
        bpy.data.worlds["World"].cycles_visibility.scatter = True
        bpy.context.scene.cycles.debug_use_spatial_splits = True
        bpy.context.scene.cycles.debug_use_hair_bvh = False
        bpy.context.scene.cycles.caustics_reflective = True
        bpy.context.scene.cycles.caustics_refractive = True
        bpy.context.scene.display_settings.display_device = 'None'
        # bpy.context.scene.view_layers[0].cycles.use_pass_crypto_object = True
        bpy.context.scene.view_layers[0].cycles.use_pass_crypto_asset = True
        bpy.context.scene.view_layers[0].cycles.use_denoising = True

    def set_random_lighting(self):
        if 'Environment Texture' in bpy.context.scene.world.node_tree.nodes.keys():
            bpy.context.scene.world.node_tree.nodes.remove(bpy.context.scene.world.node_tree.nodes['Environment Texture'])
        env = bpy.context.scene.world.node_tree.nodes.new("ShaderNodeTexEnvironment")
        env.interpolation = 'Cubic'
        env.image = bpy.data.images[random.randint(0, len(bpy.data.images) - 1)]
        # env.image = bpy.data.images["Render Result"]
        bpy.context.scene.world.node_tree.links.new(
            bpy.context.scene.world.node_tree.nodes['Environment Texture'].outputs['Color'],
            bpy.context.scene.world.node_tree.nodes['Background'].inputs['Color']
        )
        bpy.context.scene.world.node_tree.nodes['Background'].inputs[1].default_value = random.uniform(0.001, 0.2)

        c = Color()
        c.hsv = 0.0, 0.0, random.uniform(0.3, 0.7)
        self.model.material_slots[0].material.node_tree.nodes["Principled BSDF"].inputs[0].default_value = c.r, c.g, c.b, 1.0

    def get_combined_output(self, output_path, base_filename, nodes, links, compositor):
        mix = nodes.new("CompositorNodeMixRGB")  
        crypto_mask = nodes.new("CompositorNodeCryptomatte")
        # crypto_mask.matte_id = '<9.48593618e+29>'
        crypto_mask.matte_id = 'Wing8'
        links.new(compositor.outputs['Image'], crypto_mask.inputs['Image'])
        # links.new(compositor.outputs['CryptoObject00'], crypto_mask.inputs['Crypto 00'])
        links.new(compositor.outputs['CryptoAsset00'], crypto_mask.inputs['Crypto 00'])
        links.new(crypto_mask.outputs['Matte'], mix.inputs['Fac'])

        links.new(compositor.outputs['Emit'], mix.inputs[1])
        links.new(compositor.outputs['Image'], mix.inputs[2])

        combined_out = nodes.new("CompositorNodeOutputFile")
        combined_out.format.file_format = 'PNG'
        combined_out.format.color_depth = '8'
        combined_out.base_path = os.path.join(output_path, base_filename)
        combined_out.file_slots.remove(combined_out.inputs[0])
        combined_out.file_slots.new("combined")
        combined_out.file_slots[0].path = "#_combined_0"
        links.new(mix.outputs[0], combined_out.inputs["combined"])
        return combined_out