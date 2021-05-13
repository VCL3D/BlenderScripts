import os
import argparse
import sys
import subprocess
import multiprocessing
import pyexcel
import itertools
import glob

DEFAULT_GV2_PATH = r'PATH_TO_GIBSONV2'
DEFAULT_BLENDER_PATH = r'PATH_TO_BLENDER_EXE'
DEFAULT_OUTPUT_PATH = r'PATH_TO_DUMP_RESULTS'
DEFAULT_RENDER_SCRIPT_PATH = ".\\render\\OmniRender.py"
DEFAULT_RENDERED_TRAJECTORIES_PATH = ".\\fullplus.xlsx"

def parse_arguments(args):
    usage_text = (
        "This script renders panorama viewpoints from GibsonV2 using the captured poses."
        "Usage:  gibson_render.py --gibson PATH_TO_GIBSONV2 "
        "   --blender PATH_TO_BLENDER_EXE --rendered_path PATH_TO_DUMP_RESULTS --render_script PATH_TO_RENDER_SCRIPT "
        "   --rendered_meshes PATH_TO_DUMP_COMPLETED_JOBS"
    )
    parser = argparse.ArgumentParser(description=usage_text)
    parser.add_argument('--gibson', type=str, help='GibsonV2 root path.',\
        default=DEFAULT_GV2_PATH)
    parser.add_argument('--split', type=str, help='GibsonV2 split.',\
        choices=['gibson_fullplus', 'gibson_full', 'gibson_medium', 'gibson_tiny'],
        default="gibson_fullplus")
    parser.add_argument('--width', type=int, help='Panorama width.',\
        type=int, default=512)        
    parser.add_argument("--blender", type=str, help="Blender executable path.",\
        default=DEFAULT_BLENDER_PATH)
    parser.add_argument("--rendered_path", type=str, help="Output folder.",\
        default=DEFAULT_OUTPUT_PATH)
    parser.add_argument('--render_script', help='The render script path.',\
        default=DEFAULT_RENDER_SCRIPT_PATH)
    parser.add_argument('--rendered_meshes', type=str, help='The .xlsx file contained already rendered GibsonV2 meshes.',\
        default=DEFAULT_RENDERED_TRAJECTORIES_PATH)
    return parser.parse_known_args(args)

COMMAND = (
    "{0} --background --python {1} -- " # use blender's exe and render script's path
    "--samples {2} --input_file {3} --output_path {4} " # 
    "--camera_path {5} --device_type {6} --dataset gibsonv2 " 
    "--width {7} --normal_map --raw --depth --angles 0 " 
    "--log_sheet {8} --positions center --cameras spherical " # use primary render group flag
    #"--log_sheet {8} --positions center right left up down --cameras spherical " # use primary render group flag
    )

def render_mesh(t):
    command, queue = t
    gpu_id = queue.get()
    try:
        command += "--device_id 2 " #TODO: careful hardcoded GPU
        print(command)
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=None, shell=True)
        output = process.communicate()
        print(output[0])
    finally:
        queue.put(gpu_id)

def process(t):
    command, queue = t
    gpu_id = queue.get()
    try:
        command += "--device_id " + str(gpu_id)
    finally:
        queue.put(gpu_id)

if __name__ == "__main__":
    if 'PROGRAMFILES' in os.environ.keys():
        nvidia_smi_path = os.path.join(
            os.environ['PROGRAMFILES'],
            'NVIDIA Corporation',
            'NVSMI'
        )
        if nvidia_smi_path not in os.environ['PATH']:
            os.environ['PATH'] = os.environ['PATH'] + ";" + nvidia_smi_path
    gpus = 1 # len(nvgpu.available_gpus(max_used_percent=30.0))
    args, unknown = parse_arguments(sys.argv)
    meshes_root = os.path.join(args.gibson, "meshes")
    poses_root = os.path.join(args.gibson, args.split)
    print("Working on GibsonV2 meshes @ %s" % meshes_root)    
    rendered_meshes = [] 
    if args.rendered_meshes is not None and os.path.exists(args.rendered_meshes):
        data = pyexcel.get_sheet(file_name=args.rendered_meshes)
        if next(data.columns(), None) is not None:
            rendered_meshes.extend(data.column_at(0))
    commands = []
    mesh_poses = {}
    for mesh in glob.glob(os.path.join(meshes_root, '*.obj')):
        mesh_name = os.path.basename(mesh).split('_')[0]
        pose_filename = os.path.join(poses_root, mesh_name, 'camera_poses.csv')
        if os.path.exists(pose_filename) and mesh_name not in rendered_meshes:
            mesh_poses.update({mesh: pose_filename})
            cmd = COMMAND.format(
                    args.blender, #1
                    args.render_script, #2
                    256, #3
                    mesh, #4
                    os.path.join(args.rendered_path, mesh_name), #5
                    os.path.dirname(pose_filename), #6
                    'GPU', #7
                    args.width, #8
                    args.rendered_meshes, #9,
                )
            commands.extend([cmd])
        else:
            print(f"Skipping {mesh_name}.")

    pool = multiprocessing.Pool(processes=gpus)
    m = multiprocessing.Manager()
    q = m.Queue()
    for gpu_ids in range(gpus):
        q.put(gpu_ids)    
    pool.map(render_mesh, zip(commands, itertools.repeat(q, len(commands))))
    pool.close()
    pool.join()