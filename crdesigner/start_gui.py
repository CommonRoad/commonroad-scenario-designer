"""
This file is just a helper to start the GUI easily.
"""
import os

from crdesigner.ui.gui.mwindow.service_layer import config
from crdesigner.ui.gui.gui import start_gui_new
from crdesigner.ui.gui.mwindow.service_layer import transfer


if __name__ == '__main__':

    transfer.transfer_yaml_to_config(
            os.path.dirname(os.path.realpath(__file__)) + '/configurations/custom_settings.yaml', config)
    from crdesigner.map_conversion.osm2cr import config
    transfer.transfer_yaml_to_config(os.path.dirname(
            os.path.realpath(__file__)) + '/configurations/custom_settings_osm2cr.yaml', config)
    start_gui_new()
