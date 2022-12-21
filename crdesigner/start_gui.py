"""
This file is just a helper to start the GUI easily.
"""
import yaml
from crdesigner.ui.gui.mwindow.service_layer import config

from crdesigner.ui.gui.gui import start_gui_new


def transfer_yaml_to_config(yaml_file: str, config: any):
    with open(yaml_file) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    for key, value in data.items():
        setattr(config, key.upper(), value)

if __name__ == '__main__':

    transfer_yaml_to_config('crdesigner/configurations/custom_settings.yaml', config)
    from crdesigner.map_conversion.osm2cr import config
    transfer_yaml_to_config('crdesigner/configurations/custom_settings_osm2cr.yaml', config)
    start_gui_new()
