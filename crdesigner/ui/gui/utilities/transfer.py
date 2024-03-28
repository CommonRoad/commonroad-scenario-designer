import yaml


# TODO: Moved to utilites
def transfer_yaml_to_config(yaml_file: str, config: any):
    """
    this function will be called to update the values in the config file by the values of the yaml file.
    """
    with open(yaml_file) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    for key, value in data.items():
        setattr(config, key.upper(), value)
