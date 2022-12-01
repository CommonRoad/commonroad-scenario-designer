from omegaconf import ListConfig, DictConfig
from typing import Union


class Configuration:
    """Base class for all configurations of the GUI and the converter tools."""
    def __init__(self, config: Union[ListConfig, DictConfig]):
        """Initialize the base configuration.

        :param config: The configuration parameters imported from the .yaml file.
        :type config: Union[ListConfig, DictConfig]
        """
        self._opendrive = OpenDrive2CRConfiguration(config)
        self._file_header = FileHeaderConfig(config)

    @property
    def opendrive(self) -> 'OpenDrive2CRConfiguration':
        """Get the configuration related to converting OpenDrive to CommonRoad.

        :return: The configuration object for OpenDrive2CR.
        :rtype: OpenDrive2CRConfiguration
        """
        return self._opendrive

    @property
    def file_header(self) -> 'FileHeaderConfig':
        """Gets the file header configuration.

        :return: The file header configuration
        :rtype: FileHeaderConfig
        """
        return self._file_header


class FileHeaderConfig:
    """Class holding all relevant configuration parameters for a file header."""
    def __init__(self, config: Union[ListConfig, DictConfig]):
        """Initializes a file header configuration object.

        :param config: The configuration parameters imported from a .yaml file.
        :type config: Union[ListConfig, DictConfig]
        """
        self.source = config.file_header.source
        self.author = config.file_header.author
        self.affiliation = config.file_header.affiliation
        self.time_step_size = config.file_header.time_step_size


class OpenDrive2CRConfiguration:
    """Class holding all relevant configuration parameters for the OpenDRIVE conversion."""
    def __init__(self, config: Union[ListConfig, DictConfig]):
        """Initializes a plane conversion configuration object"""
        self.error_tolerance = config.opendrive.error_tolerance
        self.min_delta_s = config.opendrive.min_delta_s
        self.precision = config.opendrive.precision
        self.driving_default_lanelet_type = config.opendrive.driving_default_lanelet_type
        self.general_lanelet_type_activ = config.opendrive.general_lanelet_type_activ
        self.general_lanelet_type = config.opendrive.general_lanelet_type
        self.lanelet_types_backwards_compatible = config.opendrive.lanelet_types_backwards_compatible
        self.default_country_id = config.opendrive.default_signal_country