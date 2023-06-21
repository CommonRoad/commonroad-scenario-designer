import os

import yaml

from crdesigner.configurations.definition import ROOT_DIR
from crdesigner.ui.gui.utilities import transfer

""" Configuration of the Scenario Designer """


class GuiSettingsModel:

    def __init__(self):
        super().__init__()

        # focus on the selection
        self.AUTOFOCUS = False
        self.MWINDOW_TMP_FOLDER_PATH = "/tmp/cr_designer/"
        # default values in default_draw_params
        self.DRAW_TRAJECTORY = False
        self.DRAW_INTERSECTIONS = False
        self.DRAW_OBSTACLE_LABELS = True
        self.DRAW_OBSTACLE_ICONS = False
        self.DRAW_OBSTACLE_DIRECTION = False
        self.DRAW_OBSTACLE_SIGNALS = True
        self.DRAW_OCCUPANCY = False
        self.DRAW_TRAFFIC_SIGNS = False
        self.DRAW_TRAFFIC_LIGHTS = True
        self.DRAW_INCOMING_LANELETS = True
        self.DRAW_SUCCESSORS = True
        self.DRAW_INTERSECTION_LABELS = False
        self.DARKMODE = False
        self.AXIS_VISIBLE = 'All'
        self.LEGEND = True
        # The key to access bing maps
        self.BING_MAPS_KEY = ""
        # Username and password to access LDBV maps
        self.LDBV_USERNAME = ""
        self.LDBV_PASSWORD = ""

    def apply_set_to_default(self):
        '''
        the variables in config.py will be changed back to the default values, not the file itself
        '''
        path_to_default_settings = os.path.join(ROOT_DIR, 'default_settings.yaml')
        transfer.transfer_yaml_to_config(path_to_default_settings, gui_settings)
        with open(path_to_default_settings) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)

        path_to_custom_settings = os.path.join(ROOT_DIR, 'custom_settings.yaml')
        with open(path_to_custom_settings, 'w') as yaml_file:
            yaml_file.write(yaml.dump(data, default_flow_style=False))

    def save_config_to_custom_settings(self):
        '''
        when clicking on ok button the changed settings will be written into the custom_settings.yaml file
        '''
        path_to_custom_settings = os.path.join(ROOT_DIR, 'custom_settings.yaml')
        with open(path_to_custom_settings) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
        for key in dir(self):
            yaml_key = key.lower()
            if yaml_key in data:
                data[yaml_key] = getattr(self, key)
        with open(path_to_custom_settings, 'w') as yaml_file:
            yaml_file.write(yaml.dump(data, default_flow_style=False))


gui_settings = GuiSettingsModel()
