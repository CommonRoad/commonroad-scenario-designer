"""
This file is just a helper to start the GUI easily.
"""
import yaml
from crdesigner.ui.gui.mwindow.service_layer import config
from crdesigner.ui.gui.gui import start_gui_new


if __name__ == '__main__':

    with open('crdesigner/configurations/custom_settings.yaml') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    for key, value in data.items():
        setattr(config, key.upper(), value)

    start_gui_new()
