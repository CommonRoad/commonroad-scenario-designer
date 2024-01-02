import os

from crdesigner.common.config import CONFIG_DIR
from crdesigner.common.config.config_base import Attribute, BaseConfig
from crdesigner.common.config.general_config import general_config
from crdesigner.common.config.gui_config import gui_config
from crdesigner.common.config.lanelet2_config import lanelet2_config
from crdesigner.common.config.opendrive_config import open_drive_config
from crdesigner.common.config.osm_config import osm_config

CONFIGS_TO_RENDER = [general_config, gui_config, osm_config, open_drive_config, lanelet2_config]


def _load_custom_settings(new_path):
    custom_config_dir = os.path.join(new_path, "custom_settings.yaml")
    for config in CONFIGS_TO_RENDER:
        config.CUSTOM_SETTINGS_PATH = Attribute(custom_config_dir)
        config.restore_from_yaml_file()


class SettingsConfig(BaseConfig):
    """
    This class saves general settings of the other settings and handles the loading and saving of custom settings.
    """

    CUSTOM_SETTINGS_DIR: Attribute = Attribute(CONFIG_DIR)
    CUSTOM_SETTINGS_PATH: Attribute = Attribute(os.path.join(CONFIG_DIR, "custom_settings.yaml"))


settings = SettingsConfig()
settings.restore_from_yaml_file()
vars(type(settings))["CUSTOM_SETTINGS_DIR"].subscribe(_load_custom_settings)
_load_custom_settings(settings.CUSTOM_SETTINGS_DIR)
