from omegaconf import ListConfig, DictConfig
from typing import Union


class Configuration:
    """Base class for all configurations of the GUI and the converter tools."""
    def __init__(self, config: Union[ListConfig, DictConfig]):
        """Initialize the base configuration.

        :param config: The configuration parameters imported from the .yaml file.
        :type config: Union[ListConfig, DictConfig]
        """
        self._opendrive_config = OpenDrive2CRConfiguration(config)
        self._file_header = FileHeaderConfig(config)

    @property
    def opendrive_config(self) -> 'OpenDrive2CRConfiguration':
        """Get the configuration related to converting OpenDrive to CommonRoad.

        :return: The configuration object for OpenDrive2CR.
        :rtype: OpenDrive2CRConfiguration
        """
        return self._opendrive_config

    @property
    def file_header(self) -> 'FileHeaderConfig':
        """Gets the file header configuration.

        :return: The file header configuration
        :rtype: FileHeaderConfig
        """
        return self._file_header


class OpenDrive2CRConfiguration:
    """Base class holding all relevant information for the conversion from OpenDrive to CommonRoad."""

    def __init__(self, config: Union[ListConfig, DictConfig]):
        """Initializes a OpenDrive2CRConfiguration object.

        :param config: The configuration parameters imported from a .yaml file.
        :type config: Union[ListConfig, DictConfig]
        """
        self._plane_conversion = PlaneConversionConfig(config)

    @property
    def plane_conversion(self) -> 'PlaneConversionConfig':
        """Gets the plane conversion configuration.

        :return: The plane conversion configuration.
        :rtype: PlaneConversionConfig
        """
        return self._plane_conversion


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


class PlaneConversionConfig:
    """Class holding all relevant configuration parameters for the plane conversion of OpenDrive2CR."""
    def __init__(self, config: Union[ListConfig, DictConfig]):
        """Initializes a plane conversion configuration object"""
        self.error_tolerance = config.plane_conversion.error_tolerance
        self.min_delta_s = config.plane_conversion.min_delta_s
        self.precision = config.plane_conversion.precision
