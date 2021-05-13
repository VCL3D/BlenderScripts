import bpy

import itertools

def find_center():
    vcos = []
    objs = [o for o in bpy.data.objects if o.type == 'MESH']
    for o in objs:
      vcos.extend([o.matrix_world * v.co for v in o.data.vertices])    
    findCenter = lambda l: (max(l) + min(l)) / 2
    x, y, z = [[v[i] for v in vcos] for i in range(3)]
    center = [findCenter(axis) for axis in [x, y, z]]
    return center

def find_model_center(model):
    vcos = []    
    vcos.extend([model.matrix_world * v.co for v in model.data.vertices])    
    findCenter = lambda l: (max(l) + min(l)) / 2
    x, y, z = [[v[i] for v in vcos] for i in range(3)]
    center = [findCenter(axis) for axis in [x, y, z]]
    return center

def find_bbox_center(min, max):
    minvals = [float(s) for s in min]
    maxvals = [float(s) for s in max]
    return (minvals[0] + (maxvals[0] - minvals[0]) / 2, \
      minvals[1] + (maxvals[1] - minvals[1]) / 2, \
      minvals[2] + (maxvals[2] - minvals[2]) / 2)

def calc_floor_area(min, max):
    minvals = [float(s) for s in min]
    maxvals = [float(s) for s in max]
    return (maxvals[0] - minvals[0]) * (maxvals[2] - minvals[2])

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)

def distinct(iterable, keyfunc=None):
    seen = set()
    for item in iterable:
        key = item if keyfunc is None else keyfunc(item)
        if key not in seen:
            seen.add(key)
            yield item
	