import os
import unittest

from crdesigner.common.config.general_config import general_config
from crdesigner.common.config.osm_config import osm_config
from crdesigner.common.config.settings_config import settings


class TestConfiguration(unittest.TestCase):
    """Test whether the omegaconf configuration values are correct when loading a yaml."""

    def test_config(self):
        """Test whether the config values are correct when custom path loading a yaml."""
        custom_path = os.path.dirname(os.path.realpath(__file__))
        settings.CUSTOM_SETTINGS_DIR = custom_path
        settings.notify_all()

        self.assertEqual("Max Mustermann", general_config.author)
        self.assertEqual(7.0, osm_config.MERGE_DISTANCE)
        self.assertTrue(osm_config.LOAD_TUNNELS)


if __name__ == "__main__":
    unittest.main()
