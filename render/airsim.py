import csv

from typing import Tuple, List

from mathutils import Vector
from mathutils import Quaternion

def load_camera_tuple(row: str) -> Tuple[Tuple[Vector, Quaternion], Tuple[Vector, Quaternion], Tuple[Vector, Quaternion]]:
    drone_pos_t = Vector(float(v) for v in (row["Position(x)_t1"], row["Position(y)_t1"], row["Position(z)_t1"]))
    drone_ori_t = Quaternion(float(v) for v in (row["Orientation(w)_t1"], row["Orientation(x)_t1"], row["Orientation(y)_t1"], row["Orientation(z)_t1"]))
    drone_pos_tp1 = Vector(float(v) for v in (row["Position(x)_t2"], row["Position(y)_t2"], row["Position(z)_t2"]))
    drone_ori_tp1 = Quaternion(float(v) for v in (row["Orientation(w)_t2"], row["Orientation(x)_t2"], row["Orientation(y)_t2"], row["Orientation(z)_t2"]))
    pilot_pos = Vector(float(v) for v in (row["Pilot(x)"], row["Pilot(y)"], row["Pilot(z)"]))
    pilot_ori = Quaternion(float(v) for v in (row["PilotRot(w)"], row["PilotRot(x)"], row["PilotRot(y)"], row["PilotRot(z)"]))
    return (drone_pos_t, drone_ori_t), (drone_pos_tp1, drone_ori_tp1), (pilot_pos, pilot_ori)

def load_camera_tuples(
    path: str
) -> List[Tuple[Tuple[Vector, Quaternion], Tuple[Vector, Quaternion], Tuple[Vector, Quaternion]]]:
    return [load_camera_tuple(row) 
        for i, row in enumerate(csv.DictReader(open(path, mode='r'), delimiter='\t'))]