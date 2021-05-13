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
    if dataset == 'gibsonv2':
        return gibsonv2.GibsonV2()
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
    import gibsonv2
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
    imp.reload(gibsonv2)
    
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
    usage_text = (
        "This script renders popular indoors 3D datasets using a spherical camera."
        "Usage:  blender --background --python " + __file__ + " -- [options],"
        "   with [options]:"
    )
    parser = argparse.ArgumentParser(description=usage_text)
    parser.add_argument('-v','--verbose', help='Log script flow details.', default=True, action='store_true')
    parser.add_argument('--input_file', help='File containing the 3D scene to be imported', \
        default='..\\..\\Data\\GibsonV2\\meshes\\Allensville_mesh_texture.obj')
    parser.add_argument('--output_path', help='The path where the rendered output will be saved at.',\
        default="..\\..\\\Data\\GibsonV2\\rendered\\")
    parser.add_argument('--camera_path', help='The path where the camera position will be parsed from.',\
        default="..\\..\\Data\\GibsonV2\\gibson_tiny\\Allensville")
    parser.add_argument('--labels_path', help='The path where the category information will be parsed from.',\
        default="..\\..\\Data\\Semantic2D3D\\my_labels.json")
    parser.add_argument('--samples', help='Number of samples to be used when ray-tracing.', type=int, default=256)
    parser.add_argument('--emission', help='Light emission value.', type=float, default=250.0)
    parser.add_argument('--device_type', help='Compute device.', default='GPU', choices=['CPU', 'GPU'])
    parser.add_argument('--device_id', help='Compute device ID.', default=2)
    parser.add_argument('--width', help='Rendered images width.', default=512, type=int)
    parser.add_argument('--dataset', help='Which dataset this sample belongs to.', \
        default='gibsonv2', \
        choices=['suncg','scenenet', 'scannet', 'scenenn', 'matterport3d', 'stanford2d3d', 'gibsonv2', 'zurich'])
    parser.add_argument('--eye_dist', help='Interocular distance.', default=0.26, type=float)
    parser.add_argument('--far_dist', help='Convergence (far plane) distance.', default=8.0, type=float)
    primary_render_group = parser.add_mutually_exclusive_group()
    primary_render_group.add_argument('-c','--color', help='Render and save color image.', default=False, action='store_true')
    primary_render_group.add_argument('-r','--raw', help='Render and save emission image.', default=False, action='store_true')
    parser.add_argument('-d','--depth', help='Render and save depth map.', default=False, action='store_true')
    primary_render_group.add_argument('-n','--normals', help='Render and save rendered normals.', default=False, action='store_true')
    parser.add_argument('--normal_map', help='Render and save normal map.', default=False, action='store_true')
    parser.add_argument('-l','--labels', help='Render and save label map.', default=False, action='store_true')
    parser.add_argument('-p','--pretty_labels', help='Render and save pretty (colorized) label map.', default=False, action='store_true')
    parser.add_argument('-m','--mask', help='Render and save occlusion mask.', default=False, action='store_true')
    parser.add_argument('--positions', help='Position types to render, accepts one of [center, right, left, up, down].', \
        default='center', choices=['center', 'right', 'left', 'up', 'down'], nargs='*')
    parser.add_argument('--angles', help='Rotation angles around the vertical axis to render at.', \
        default=[], nargs='*', type=int) # called like: --angles 0 90 180 270
    parser.add_argument('--cameras', help='Camera types that will be used to render content.', \
        default=[], nargs='*', choices=['spherical', 'perspective']) # called like --cameras spherical perspective
    parser.add_argument('--log_sheet', help='The path where processing information will be logged at.',\
        default="..\\..\\Data\\test_renders\\test.xlsx")
    parser.add_argument('--suncg_lights', help='The path that the SunCG light metadata json file is located at.',\
        default="..\\..\\Data\\SunCG\\code\\suncgModelLights.json")
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
    import gibsonv2
    
    deleters.delete_all()
    deleters.delete_materials()

    dataset = get_dataset(args.dataset)
    dataset.import_model(args.input_file)        
    base_filename = dataset.get_instance_name(args.input_file)    

    render_engine = engine.Cycles28(args.device_type, args.device_id, 
        args.samples, args.depth, args.normals or args.normal_map,
        args.labels or args.pretty_labels, args.raw, False,
    )
    nodes, links, compositor = render_engine.get_scene_nodes()

    output_nodes = []

    if os.path.isdir(args.output_path) and not os.path.exists(args.output_path):
        print(f"Creating folder {args.output_path}")
        os.mkdir(args.output_path)

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
    if args.labels:
        semantic_map_out = dataset.get_semantic_map_output(args.labels_path, \
            args.output_path, base_filename, nodes, links, compositor)
        output_nodes.append(engine.OutputNode(semantic_map_out, base_filename, 'semantic_map'))
    if args.pretty_labels:
        pretty_semantic_map_out = dataset.get_pretty_semantic_map_output(args.labels_path, \
            args.output_path, base_filename, nodes, links, compositor)
        output_nodes.append(engine.OutputNode(pretty_semantic_map_out, base_filename, 'pretty_semantic_map'))
    
    if in_blender:
        print("Running from inside blender ...")
        args.cameras = ['spherical']        
        args.angles = [0]
        args.positions = ['center']
    
    camera_positions = dataset.get_camera_position_generator(args.camera_path)\
        if os.path.isdir(args.camera_path) else [dataset.get_camera_position(args.camera_path)]
    
    camera_pos_index = 0
    for camera_center_pos in camera_positions:
        for camera_type in args.cameras:
            dataset.set_render_settings()
            camera = render_engine.get_camera(camera_type, args.width, args.width // 2)
            camera.location = camera_center_pos
            camera.rotation_euler = dataset.get_camera_rotation()
            camera.data.stereo.interocular_distance = args.eye_dist
            camera.data.stereo.convergence_distance = args.far_dist
            bpy.context.scene.camera = camera

            for angle in args.angles:
                for position in args.positions:
                    print("Rendering with {0} camera in {1} position at {2} angle.".format(camera_type, position, angle))
                    for node in output_nodes:
                        node.prepare_render(position, angle, camera_type, camera_pos_index)
                    camera.rotation_euler = dataset.get_camera_rotation(angle)
                    camera.location = camera_center_pos + dataset.get_camera_offset(position, args.eye_dist, angle)
                    bpy.ops.render.render(write_still=True)
        camera_pos_index += 1        
        if in_blender and camera_pos_index >= 2:
            break

    if args.log_sheet:
        print("Updating %s" % args.log_sheet)
        data = pyexcel.get_sheet(file_name=args.log_sheet)
        count = len(data.to_array())
        data[count, 0] = base_filename
        data.save_as(args.log_sheet)
