import yaml

'''
this file contains a functions that will write the settings present in the yaml file into the values of the config file
It is in a single file because it will be called in gui_settings.py, osm_settings.py and start_gui.py
'''


def transfer_yaml_to_config(yaml_file: str, config: any):
    with open(yaml_file) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    for key, value in data.items():
        setattr(config, key.upper(), value)
