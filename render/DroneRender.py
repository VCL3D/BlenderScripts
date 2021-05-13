import bpy

from math import radians

import sys
import os
import argparse

import pyexcel

def get_dataset(dataset):
    if dataset == 'suncg':
        return suncg.SunCG()
    if dataset == 'matterport3d':
        return matterport3d.Matterport3D()
    if dataset == 'stanford2d3d':
        return stanford2d3d.Stanford2D3D()
    else:
        print("!!! - Erroneous dataset selection.")
         
def init_script():
    arguments_vector = sys.argv
    in_blender = False
    if "--" not in arguments_vector: # running from inside blender
        arguments_vector = []  # as if no args are passed
        module_path = bpy.context.space_data.text.filepath # all modules in same path as the script
        os.chdir(os.path.dirname(module_path))
        in_blender = True
    else: # running as cli-like background blender script
        arguments_vector = arguments_vector[arguments_vector.index("--") + 1:]# get all args after "--"
        module_path = os.path.abspath(__file__) # all modules in same path as the script
    return arguments_vector, module_path, in_blender


def import_modules(module_path, verbose):
    if verbose:
        print("Adding module path: %s" % module_path)
    sys.path.append(os.path.dirname(module_path))
    import deleters
    import utils
    import engine
    import dataset
    import colour
    import semantics
    import suncg
    import matterport3d
    import stanford2d3d
    import airsim
    import imp # force a reload
    imp.reload(deleters)
    imp.reload(utils)
    imp.reload(engine)
    imp.reload(dataset)
    imp.reload(colour)
    imp.reload(semantics)
    imp.reload(suncg)
    imp.reload(matterport3d)
    imp.reload(stanford2d3d)
    imp.reload(airsim)
    
def print_arguments(args):
    print("Supplied arguments:")
    for arg in vars(args):
        print("\t", arg, ":", getattr(args, arg))
    if len(unknown) > 0:
        print("Unknown arguments:")
        for arg in unknown:
            print("\t", arg,)
    print("Current working directory : %s" % os.getcwd())
    print("Bleder data filepath : %s" % bpy.data.filepath)
            
def parse_arguments(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('-v','--verbose', help='Log script flow details.', default=True, action='store_true')
    parser.add_argument('--scene_model', help='File containing the 3D scene to be imported', \
        default='..\\..\\Data\\Matterport3D\\Data\\1pXnuDYAj8r\\1pXnuDYAj8r\\matterport_mesh\\2e84c97e728d46babd3270f4e1a0ae3a\\2e84c97e728d46babd3270f4e1a0ae3a.obj')
    parser.add_argument('--output_path', help='The path where the rendered output will be saved at.',\
        default="..\\..\\Data\\test_renders\\renders\\")
    parser.add_argument('--camera_path', help='The path where the camera position will be parsed from.',\
        default="..\\..\\Data\\test_renders\\poses\\test\\1pXnuDYAj8r\\2019-12-24-13-30-23\\airsim_rec_blender.txt")
    parser.add_argument('--samples', help='Number of samples to be used when ray-tracing.', type=int, default=256)
    parser.add_argument('--device_type', help='Compute device type.', default='GPU', choices=['CPU', 'GPU'])
    parser.add_argument('--device_id', help='Compute device ID.', default=1, type=int)
    parser.add_argument('--width', help='Rendered images width.', default=320, type=int)
    parser.add_argument('--height', help='Rendered images height.', default=180, type=int)
    parser.add_argument('--dataset', help='Which dataset this sample belongs to.', \
        default='matterport3d', \
        choices=['matterport3d', 'stanford2d3d', 'gibson'])
    parser.add_argument('--ego_fov_h', help='Egocentric camera horizontal field-of-view (in degrees).', default=85.0, type=float)
    parser.add_argument('--far_dist', help='Convergence (far plane) distance.', default=8.0, type=float)
    primary_render_group = parser.add_mutually_exclusive_group()
    primary_render_group.add_argument('-c','--color', help='Render and save color image.', default=False, action='store_true')
    primary_render_group.add_argument('-r','--raw', help='Render and save emission image.', default=True, action='store_true')
    parser.add_argument('-d','--depth', help='Render and save depth map.', default=True, action='store_true')
    primary_render_group.add_argument('-n','--normals', help='Render and save rendered normals.', default=False, action='store_true')
    parser.add_argument('--normal_map', help='Render and save normal map.', default=True, action='store_true')    
    parser.add_argument('-f','--flow', help='Render and save optical flow map.', default=True, action='store_true')
    parser.add_argument('-m','--mask', help='Render and save occlusion mask.', default=False, action='store_true')
    parser.add_argument('--log_sheet', help='The path where processing information will be logged at.',\
        default="..\\..\\Data\\test_renders\\drone.xlsx")    
    return parser.parse_known_args(args)
    
if __name__ == "__main__":
    arguments_vector, module_path, in_blender = init_script()    
    args, unknown = parse_arguments(arguments_vector)
    if args.verbose:
        print_arguments(args)
    import_modules(module_path, args.verbose)
    import deleters
    import utils
    import engine
    import dataset
    import colour
    import semantics
    import suncg
    import matterport3d
    import stanford2d3d
    import airsim
    
    deleters.delete_all()
    deleters.delete_materials()

    dataset = get_dataset(args.dataset)
    dataset.import_model(args.scene_model)        
    base_filename = dataset.get_instance_name(args.scene_model)
    
    render_engine = engine.Cycles28(
        args.device_type, args.device_id, args.samples, 
        args.depth, args.normals or args.normal_map, 
        False, args.raw, args.flow)
    nodes, links, compositor = render_engine.get_scene_nodes()

    output_nodes = []

    if args.depth:        
        depth_out = dataset.get_depth_output(args.output_path, base_filename, \
            nodes, links, compositor)
        output_nodes.append(engine.OutputNode(depth_out, base_filename, 'depth'))
    if args.color:        
        image_out = dataset.get_color_output(args.output_path, base_filename, \
            nodes, links, compositor)
        output_nodes.append(engine.OutputNode(image_out, base_filename, 'color'))
    elif args.normals:
        normals_out = dataset.get_normals_output(args.output_path, base_filename, \
            nodes, links, compositor)
        output_nodes.append(engine.OutputNode(normals_out, base_filename, 'normals'))        
    if args.raw:
        emission_out = dataset.get_emission_output(args.output_path, base_filename, \
            nodes, links, compositor)
        output_nodes.append(engine.OutputNode(emission_out, base_filename, 'emission'))
    if args.normal_map:
        normal_map_out = dataset.get_normal_map_output(args.output_path, base_filename, \
            nodes, links, compositor)
        output_nodes.append(engine.OutputNode(normal_map_out, base_filename, 'normal_map'))
    if args.flow:
        flow_map_out = dataset.get_flow_map_output(args.output_path, base_filename, \
            nodes, links, compositor)
        output_nodes.append(engine.OutputNode(flow_map_out, base_filename, 'flow_map'))
    
    if in_blender:
        print("Running from inside blender ...")
    
    camera_positions = airsim.load_camera_tuples(args.camera_path)
    
    trajectory_date = os.path.basename(os.path.dirname(args.camera_path))

    camera_pos_index = 0
    for ego_pos_rot_t, ego_pos_rot_tp1, exo_pos_rot in camera_positions:        
        camera = render_engine.get_camera('perspective', args.width, args.height)
        camera.data.stereo.convergence_distance = args.far_dist
        camera.data.clip_start = 0.1
        camera.data.clip_end = args.far_dist
        camera.data.lens_unit = 'FOV'
        camera.data.angle = radians(args.ego_fov_h)

        dataset.set_render_settings()
       
        camera.rotation_mode = 'QUATERNION'

        bpy.context.scene.frame_set(0)
        camera.location = ego_pos_rot_t[0]
        camera.rotation_quaternion = ego_pos_rot_t[1]
        camera.keyframe_insert('location',group="LocRot")
        camera.keyframe_insert('rotation_quaternion',group="LocRot")

        bpy.context.scene.frame_set(1)
        camera.location = ego_pos_rot_tp1[0]
        camera.rotation_quaternion = ego_pos_rot_tp1[1]
        camera.keyframe_insert('location',group="LocRot")
        camera.keyframe_insert('rotation_quaternion',group="LocRot")

        bpy.context.scene.camera = camera
        
        for fid in range(2):
            for node in output_nodes:                
                node.prepare_render("egocentric", fid, trajectory_date, camera_pos_index)
            bpy.context.scene.frame_set(fid)
            bpy.ops.render.render(write_still=True)
        camera_pos_index += 1

        if in_blender and camera_pos_index >= 3:
            break

    if args.log_sheet:
        print("Updating %s" % args.log_sheet)
        data = pyexcel.get_sheet(file_name=args.log_sheet)
        count = len(data.to_array())
        data[count, 0] = trajectory_date
        data.save_as(args.log_sheet)
