
class Drone(object):
    def __init__(self, name: str=None):
        self.name = name        

    def __str__(self):
        return self.name

    def get_instance_name(self, filepath: str, id: int):
        raise NotImplementedError("Abstract class")

    def import_model(self, filepath:str):
        raise NotImplementedError("Abstract class")

    def show(self):
        raise NotImplementedError("Abstract class")

    def hide(self):
        raise NotImplementedError("Abstract class")

    def get_mask_output(self, output_path, base_filename, nodes, links, compositor):
        raise NotImplementedError("Abstract class")

    def get_combined_output(self, output_path, base_filename, nodes, links, compositor):
        raise NotImplementedError("Abstract class")

    def set_render_settings(self):
        raise NotImplementedError("Abstract class")

    def set_random_lighting(self):
        raise NotImplementedError("Abstract class")