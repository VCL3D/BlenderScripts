import os
import argparse
import sys
import subprocess
import multiprocessing
import pyexcel
import itertools
import nvgpu

DEFAULT_M3D_PATH = r'PATH_TO_MATTERPORT3D'
DEFAULT_DRONE_TRAJECTORIES = r'PATH_TO_TRAJECTORY_FOLDERS'
DEFAULT_BLENDER_PATH = r'PATH_TO_BLENDER_EXE'
DEFAULT_OUTPUT_PATH = r'PATH_TO_DUMP_RESULTS'
DEFAULT_RENDER_SCRIPT_PATH = ".\\render\\DroneRender.py"
DEFAULT_RENDERED_TRAJECTORIES_PATH = ".\\drone.xlsx"

def parse_arguments(args):
    usage_text = (
        "This script renders egocentric viewpoint pairs from Matterport3D using sampled play-generated trajectories."
        "Usage:  egocentric_render.py --m3d PATH_TO_MATTERPORT3D --generated trajectories PATH_TO_TRAJECTORY_FOLDERS"
        "   --blender PATH_TO_BLENDER_EXE --rendered_path PATH_TO_DUMP_RESULTS --render_script PATH_TO_RENDER_SCRIPT"
        "   --rendered_trajectories PATH_TO_DUMP_COMPLETED_JOBS"
    )
    parser = argparse.ArgumentParser(description=usage_text)
    parser.add_argument('--m3d', type=str, help='Matterport3D root path.',\
        default=DEFAULT_M3D_PATH)
    parser.add_argument('--generated_trajectories', type=str, help='Root path for the generated trajectories.',\
        default=DEFAULT_DRONE_TRAJECTORIES) #TODO: add code
    parser.add_argument("--blender", type=str, help="Blender executable path.",\
        default=DEFAULT_BLENDER_PATH)
    parser.add_argument("--rendered_path", type=str, help="Output folder.",\
        default=DEFAULT_OUTPUT_PATH)
    parser.add_argument('--render_script', type=str, help='The render script path.',\
        default=DEFAULT_RENDER_SCRIPT_PATH)
    parser.add_argument('--rendered_trajectories', type=str, 
        help='The .xlsx file with the already rendered Matterport3D buildings that will be appended to during rendering.',\
        default=DEFAULT_RENDERED_TRAJECTORIES_PATH)
    return parser.parse_known_args(args)

COMMAND = (
    "{0} --background --python {1} -- " # use blender's exe and render script's path
    "--samples {2} --scene_model {3} --output_path {4} " # 
    "--camera_path {5} --device_type {6} --dataset matterport3d " # use \pose path and input flag
    "--log_sheet {7} " # use primary render group flag
    )

def render_trajectory(t):
    command, queue = t
    gpu_id = queue.get()
    try:
        command += "--device_id " + str(gpu_id)
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
    gpus = len(nvgpu.available_gpus(max_used_percent=30.0))
    args, unknown = parse_arguments(sys.argv)
    buildings_root = os.path.join(args.m3d, "v1", "scans")
    print("Working on M3D buildings @ %s" % buildings_root)    
    rendered_trajectories = [] 
    if args.rendered_trajectories is not None and os.path.exists(args.rendered_trajectories):
        data = pyexcel.get_sheet(file_name=args.rendered_trajectories)
        rendered_trajectories.extend(data.column_at(0))
    commands = []
    building_hashes = {}
    for building_folder in os.listdir(buildings_root):
        building_hash = os.path.join(buildings_root, building_folder, building_folder, "matterport_mesh")
        for root, dirs, files in os.walk(building_hash, topdown = False):
            obj = next((s for s in files if 'obj' in s), None)
            mesh = os.path.join(root, obj)            
            building_hashes.update({building_folder: mesh})
            if obj is not None:
                break
    for traj in os.listdir(args.generated_trajectories):
        mesh = building_hashes[traj]
        trajectory_folder = os.path.join(args.generated_trajectories, traj)
        for trajectory_date in os.listdir(trajectory_folder):
            if trajectory_date in rendered_trajectories:
                print("Skipping already rendered building (%s)" % building_hash)
                continue
            for root, dirs, files in os.walk(os.path.join(trajectory_folder, trajectory_date), topdown = False):
                txt = next((s for s in files if 'airsim_rec_blender' in s), None)
                trajectory_file = os.path.join(root, txt)
                if txt is None:
                    break
            cmd = COMMAND.format(
                    args.blender, #1
                    args.render_script, #2
                    256, #3
                    mesh, #4
                    args.rendered_path, #5
                    trajectory_file, #6
                    'GPU', #7
                    args.rendered_trajectories, #8,
                ) + " -d --normal_map -f -r "
            commands.extend([cmd])

    pool = multiprocessing.Pool(processes=gpus)
    m = multiprocessing.Manager()
    q = m.Queue()
    for gpu_ids in range(gpus):
        q.put(gpu_ids)    
    pool.map(render_trajectory, zip(commands, itertools.repeat(q, len(commands))))
    pool.close()
    pool.join()