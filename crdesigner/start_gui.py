"""
This file is just a helper to start the GUI easily.
"""
import yaml
from crdesigner.ui.gui.mwindow.service_layer import config

from crdesigner.ui.gui.gui import start_gui_new
from crdesigner.ui.gui.mwindow.service_layer import transfer
import os
from crdesigner.configurations.definition import ROOT_DIR




if __name__ == '__main__':
    path_to_custom_settings = os.path.join(ROOT_DIR, 'custom_settings.yaml')
    transfer.transfer_yaml_to_config(path_to_custom_settings, config)
    from crdesigner.map_conversion.osm2cr import config
    path_to_custom_settings_osm2cr = os.path.join(ROOT_DIR, 'custom_settings_osm2cr.yaml')
    transfer.transfer_yaml_to_config(path_to_custom_settings_osm2cr, config)
    start_gui_new()
