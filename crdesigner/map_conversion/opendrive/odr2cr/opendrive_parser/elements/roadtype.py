from __future__ import annotations

from typing import Union


class RoadType:
    """
    Class which describes the Road type element in OpenDRIVE. It defines the main purpose of a road and the associated
    traffic rules. It can be changed as often as needed within a road element.
    The attribute country which contains the country code of the road according to ISO 3166-1 is not implemented in the
    converter as the information will not be used.

    Class is not yet supported. It is not used in the conversion to CommonRoad.
    """

    allowedTypes = [
        "unknown",
        "rural",
        "motorway",
        "town",
        "lowSpeed",
        "pedestrian",
        "bicycle",
        "townArterial",
        "townCollector",
        "townExpressway",
        "townLocal",
        "townPlayStreet",
        "townPrivate",
    ]

    def __init__(self, s_pos=None, use_type=None, speed=None):
        """
        Constructor of RoadType.

        :param s_pos: s-coordinate of start position
        :param use_type: Type of the road
        :param speed: Speed limit of the road
        """
        self.start_pos = s_pos
        self.use_type = use_type
        self.speed = speed

    @property
    def start_pos(self) -> float:
        """
        S-coordinate of the start position.

        :getter: returns s-coordinate
        :setter: sets s-coordinate
        """
        return self._sPos

    @start_pos.setter
    def start_pos(self, value):
        # pylint: disable=W0201
        self._sPos = float(value)

    @property
    def use_type(self) -> str:
        """
        Type of the road.

        :getter: returns road type
        :setter: sets road type
        """
        return self._use_type

    @use_type.setter
    def use_type(self, value):
        if value not in self.allowedTypes:
            raise AttributeError("Type not allowed.")
        # pylint: disable=W0201
        self._use_type = value

    @property
    def speed(self) -> Speed:
        """
        Speed limit of the road type.

        :getter: returns speed value
        :setter: sets speed value
        """
        return self._speed

    @speed.setter
    def speed(self, value):
        if not isinstance(value, Speed) and value is not None:
            raise TypeError("Value {} must be instance of Speed.".format(value))
        # pylint: disable=W0201
        self._speed = value


class Speed:
    """
    Class which describes the speed element of road types in OpenDRIVE. It defines the speed limit for a road type.
    """

    def __init__(self, max_speed=None, unit=None):
        """
        Constructor of class Speed.

        :param max_speed: maximum allowed speed
        :param unit: unit of attribute max_speed
        """
        self._max = max_speed
        self._unit = unit

    @property
    def max(self) -> Union[float, str, None]:
        """
        Maximum allowed speed. Can have the values 'no limit', 'undefined' or numerical values in the respective unit.

        :getter: returns max. allowed speed
        :setter: sets max. allowed speed
        """
        return self._max

    @max.setter
    def max(self, value):
        try:
            float(value)
            f = True
        except ValueError:
            f = False
        if value not in ["no limit", "undefined"] and not f:
            raise AttributeError("Invalid input!")
        self._max = str(value)

    @property
    def unit(self) -> Union[None, str]:
        """
        Unit of attribute max.

        :getter: returns unit
        :setter: sets unit
        """
        return self._unit

    @unit.setter
    def unit(self, value):
        if value not in ["km/h", "m/s", "mph"]:
            raise AttributeError("Invalid unit!")
        self._unit = str(value)
