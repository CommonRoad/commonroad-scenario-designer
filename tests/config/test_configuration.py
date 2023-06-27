import unittest
import os
from crdesigner.config.config import ScenarioDesignerParams


class TestConfiguration(unittest.TestCase):
    """Test whether the omegaconf configuration values are correct when loading a yaml."""

    def test_config(self):
        config: ScenarioDesignerParams = \
            ScenarioDesignerParams.load(f"{os.path.dirname(os.path.realpath(__file__))}//test_config.yaml")
        self.assertEqual("test", config.general.author)
        self.assertEqual(0.5, config.opendrive.error_tolerance)


if __name__ == '__main__':
    unittest.main()
