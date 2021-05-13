class Dataset(object):
    def __init__(self, name=None):
        self.name = name        

    def __str__(self):
        return self.name

    def get_instance_name(self, filepath, id):
        raise NotImplementedError("Abstract class")

    def import_model(self, filepath):
        raise NotImplementedError("Abstract class")

    def get_camera_position(self, filepath):
        raise NotImplementedError("Abstract class")
    
    def get_camera_position_generator(self, folder):
        raise NotImplementedError("Abstract class")

    def get_camera_rotation(self, degrees = 0):
        raise NotImplementedError("Abstract class")

    def get_camera_offset(self, direction, distance, degrees):
        raise NotImplementedError("Abstract class")

    def get_depth_output(self, output_path, base_filename, nodes, links, compositor):
        raise NotImplementedError("Abstract class")

    def get_color_output(self, output_path, base_filename, nodes, links, compositor):
        raise NotImplementedError("Abstract class")

    def get_emission_output(self, output_path, base_filename, nodes, links, compositor):
        raise NotImplementedError("Abstract class")

    def get_normals_output(self, output_path, base_filename, nodes, links, compositor):
        raise NotImplementedError("Abstract class")

    def get_normal_map_output(self, output_path, base_filename, nodes, links, compositor):
        raise NotImplementedError("Abstract class")

    def get_flow_map_output(self, output_path, base_filename, nodes, links, compositor):
        raise NotImplementedError("Abstract class")

    def get_semantic_map_output(self, labels_path, output_path, base_filename, nodes, links, compositor):
        raise NotImplementedError("Abstract class")

    def get_pretty_semantic_map_output(self, labels_path, output_path, base_filename, nodes, links, compositor):
        raise NotImplementedError("Abstract class")

    def set_render_settings(self):
        raise NotImplementedError("Abstract class")

	
	
	
	