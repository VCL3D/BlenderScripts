import colour
import csv
import os

# https://github.com/ScanNet/ScanNet/blob/master/BenchmarkScripts/util.py
def __create_color_palette(): # color palette for nyu40 labels
    return [
       (0, 0, 0),
       (174, 199, 232),		# wall
       (152, 223, 138),		# floor
       (31, 119, 180), 		# cabinet
       (255, 187, 120),		# bed
       (188, 189, 34), 		# chair
       (140, 86, 75),  		# sofa
       (255, 152, 150),		# table
       (214, 39, 40),  		# door
       (197, 176, 213),		# window
       (148, 103, 189),		# bookshelf
       (196, 156, 148),		# picture
       (23, 190, 207), 		# counter
       (178, 76, 76),  
       (247, 182, 210),		# desk
       (66, 188, 102), 
       (219, 219, 141),		# curtain
       (140, 57, 197), 
       (202, 185, 52), 
       (51, 176, 203), 
       (200, 54, 131), 
       (92, 193, 61),  
       (78, 71, 183),  
       (172, 114, 82), 
       (255, 127, 14), 		# refrigerator
       (91, 163, 138), 
       (153, 98, 156), 
       (140, 153, 101),
       (158, 218, 229),		# shower curtain
       (100, 125, 154),
       (178, 127, 135),
       (120, 185, 128),
       (146, 111, 194),
       (44, 160, 44),  		# toilet
       (112, 128, 144),		# sink
       (96, 207, 209), 
       (227, 119, 194),		# bathtub
       (213, 92, 176), 
       (94, 106, 211), 
       (82, 84, 163),  		# otherfurn
       (100, 85, 144)
    ]

class Label(object):
    def __init__(self, id = -1, name=None, color=colour.Color("black")):
        self.name = name
        self.color = color
        self.id = id

    def is_valid(self):
        return self.id >= 0

    def get_id(self):
        return self.id

    def get_color(self):
        return self.color

    def get_color_hex(self):
        return self.color.get_hex_l()

    def get_color_rgb(self):
        return self.color.get_rgb()

    def get_color_bgr(self):
        r, g, b = self.color.get_rgb()
        return b, g, r

    def get_name(self):
        return self.name if isinstance(self.name, str) else "error"

    def __str__(self):
        return "[" + str(self.get_id()) + "," + self.get_name() + "]"

class NYU40Label(Label):
    def __init__(self, id = -1, name=None, color=colour.Color("black")):
        super(NYU40Label, self).__init__(id, name, color)

class NYU40LabelFactory(object):
    def __init__(self, nyu40csv):
        self.__labels = []
        with open(nyu40csv) as f:
            for row in csv.DictReader(f, delimiter=','):
                r = float(row['r']) / 255
                g = float(row['g']) / 255
                b = float(row['b']) / 255
                id = int(row['nyu40id'])
                category = row['nyu40class']
                self.__labels.append(NYU40Label(id=id, name=category, \
                    color=colour.Color(red=r, green=g, blue=b)))
        self.__id_to_label = dict((l.get_id(), l) for l in self.__labels)
        self.__name_to_label = dict((l.get_name(), l) for l in self.__labels)

    def create_from_id(self, id):
        return self.__id_to_label[id] if id in self.__id_to_label else NYU40Label()

    def create_from_name(self, name):
        return self.__name_to_label[name] if self.__name_to_label.has_key(name) else NYU40Label()