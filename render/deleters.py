import bpy

import os

def delete_cameras_lights():
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_by_type(type='CAMERA')
    bpy.ops.object.delete(use_global=False)
    # bpy.ops.object.select_by_type(type='LAMP')
    bpy.ops.object.select_by_type(type='LIGHT')
    bpy.ops.object.delete(use_global=False)
    bpy.ops.object.select_by_type(type='CAMERA')
    bpy.ops.object.delete(use_global=False)
    # bpy.ops.object.select_by_type(type='LAMP')
    bpy.ops.object.select_by_type(type='LIGHT')
    bpy.ops.object.delete(use_global=False)
    for item in bpy.data.cameras:
        bpy.data.cameras.remove(item, do_unlink=True)   
    for item in bpy.data.lamps:
        bpy.data.lamps.remove(item, do_unlink=True)   
        
def delete_all():
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete(use_global=False)
    bpy.ops.object.select_by_type(type='ARMATURE')
    bpy.ops.object.delete(use_global=False)
    bpy.ops.object.select_by_type(type='CAMERA')
    bpy.ops.object.delete(use_global=False)
    # bpy.ops.object.select_by_type(type='LAMP')
    bpy.ops.object.select_by_type(type='LIGHT')
    bpy.ops.object.delete(use_global=False)
    
    for item in bpy.data.meshes:
        bpy.data.meshes.remove(item, do_unlink=True)
    for item in bpy.data.armatures:
        bpy.data.armatures.remove(item, do_unlink=True)
    for item in bpy.data.actions:
        bpy.data.actions.remove(item, do_unlink=True)   
    for item in bpy.data.cameras:
        bpy.data.cameras.remove(item, do_unlink=True)   
    for item in bpy.data.lights:
        bpy.data.lights.remove(item, do_unlink=True) 


def delete_textureless():
    bpy.ops.object.select_all(action='DESELECT')
    for mesh in bpy.data.meshes:
        slot = mesh.materials[0].texture_slots[0]
        if slot is None or not os.path.isfile(mesh.materials[0].texture_slots[0].texture.image.filepath):
            bpy.data.objects[mesh.name].select = True
            bpy.ops.object.delete(use_global=False)

def delete_materials():
    while len(bpy.data.materials):
        bpy.data.materials.remove(bpy.data.materials[0], do_unlink=True)
    for obj in bpy.data.objects:
        if obj.data is not None:
            obj.data.materials.clear()
	
	
	
	