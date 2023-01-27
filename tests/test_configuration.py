import unittest
import os
from crdesigner.configurations.configuration_builder import ConfigurationBuilder


class TestConfiguration(unittest.TestCase):
    """Test whether the omegaconf configuration values are correct."""
    def setUp(self) -> None:
        super().setUp()
        path_config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../crdesigner/configurations")
        ConfigurationBuilder.set_path_to_config(path_config)
        self.config = ConfigurationBuilder.build_configuration()

    def test_config(self):
        self.assertEqual(self.config.file_header.author, "Sebastian Maierhofer")
        self.assertEqual(self.config.file_header.affiliation, "Technical University of Munich")
        self.assertEqual(self.config.file_header.source, "CommonRoad Scenario Designer")
        self.assertEqual(self.config.file_header.time_step_size, 0.1)

        self.assertEqual(self.config.opendrive.error_tolerance, 0.15)
        self.assertEqual(self.config.opendrive.min_delta_s, 0.5)
        self.assertEqual(self.config.opendrive.precision, 0.5)
        self.assertEqual(self.config.opendrive.driving_default_lanelet_type, "urban")


if __name__ == '__main__':
    unittest.main()
