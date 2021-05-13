import bpy

def hide_all():
    for o in bpy.data.objects:
        o.cycles_visibility.camera = False

def show_all():
    for o in bpy.data.objects:
        o.cycles_visibility.camera = True

def toggle_visibility_all(flag:bool):
    for o in bpy.data.objects:
        o.cycles_visibility.camera = flag

def merge_all():        
    bpy.context.view_layer.objects.active = bpy.data.objects[0]
    for o in bpy.data.objects:
        o.select_set(True)
    bpy.ops.object.join()