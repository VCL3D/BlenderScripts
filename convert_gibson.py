import glob
import tqdm
import os

GIBSON_V2_MESHES = r'PATH_TO_GIBSONV2_MESHES'
MESHLABSERVER_EXE = r'PATH_TO_MESHLABSERVER_EXE'

ply_files = glob.glob(os.path.join(GIBSON_V2_MESHES, '*.ply'))

for ply_file in tqdm.tqdm(ply_files, desc='Converting GibsonV2'):
    if os.path.exists(ply_file.replace('ply', 'obj')):
        continue
    cmd = f"\"{MESHLABSERVER_EXE}\" -i {ply_file} -o {ply_file.replace('ply', 'obj')} -m vn vt wt"
    os.system(cmd)