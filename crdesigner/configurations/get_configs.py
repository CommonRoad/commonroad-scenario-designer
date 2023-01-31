import os
from crdesigner.configurations.configuration_builder import ConfigurationBuilder
from crdesigner.configurations.configuration import Configuration


def get_configs() -> Configuration:
    """Helper function to directly create a configuration from all provided .yaml files.

    :return: Configuration constructed from the .yaml files
    :rtype: :class:`Configuration`
    """
    path_config = os.path.dirname(os.path.realpath(__file__))
    ConfigurationBuilder.set_path_to_config(path_config)
    config = ConfigurationBuilder.build_configuration()
    return config
