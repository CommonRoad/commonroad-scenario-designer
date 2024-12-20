from typing import List, Tuple, Union

from commonroad.common.common_lanelet import StopLine
from commonroad.scenario.traffic_light import TrafficLight
from commonroad.scenario.traffic_sign import TrafficSign

from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.junction import (
    Junction,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadElevationProfile import (
    ElevationProfile,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadLanes import (
    Lanes,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadLateralProfile import (
    LateralProfile,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadLink import (
    Link,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadObject import (
    Object,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadPlanView import (
    PlanView,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadSignal import (
    Signal,
    SignalReference,
)


class Road:
    """
    Class which describes the road elements in OpenDRIVE. In OpenDRIVE the road network is represented by road elements.

    :ivar _id: ID of the road
    :ivar _name: name of the road
    :ivar _junction: junction the road belongs to as a connecting road
    :ivar _length: length of the road reference line
    :ivar _link: road linkage
    :ivar _types: road types
    :ivar _planView: geometry of the reference line
    :ivar _elevationProfile: road elevation
    :ivar _lateralProfile: superelevation and crossfalls of the road
    :ivar _lanes: lanes of the road
    :ivar _objects: objects on the road
    :ivar _signals: signal elements on the road
    :ivar _signalReferences: signal elements on the road (reused signal definitions)
    :ivar _driving_direction driving side, true if RHT, false if LHT
    """

    def __init__(self):
        self._id = None
        self._name = None
        self._junction = None

        self._link = Link()
        self._types = []
        self._planView = PlanView()
        self._elevationProfile = ElevationProfile()
        self._lateralProfile = LateralProfile()
        self._lanes = Lanes()
        self._objects = []
        self._signals = []
        self._signalReferences = []
        self._cr_traffic_lights: List[Tuple[TrafficLight, Tuple[int, int], float]] = []
        self._cr_traffic_signs: List[Tuple[TrafficSign, Tuple[int, int], float]] = []
        self._cr_stop_lines: List[Tuple[StopLine, Tuple[int, int], float]] = []
        self._driving_direction = True

    # check if objects have equal instance dictionaries
    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @property
    def id(self) -> int:
        """ID of the road."""
        return self._id

    @id.setter
    def id(self, value: int):
        self._id = int(value)

    @property
    def name(self) -> str:
        """Name of the road."""
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = str(value)

    @property
    def junction(self) -> Union[None, Junction]:
        """Junction the road belongs to, if the road is a connecting road."""
        return self._junction

    @junction.setter
    def junction(self, value):
        if not isinstance(value, Junction) and value is not None:
            raise TypeError("Property must be a Junction or NoneType")
        self._junction = value

    @property
    def link(self) -> Link:
        """Road linkage."""
        return self._link

    @property
    def types(self) -> list:
        """Road types."""
        return self._types

    @property
    def plan_view(self) -> PlanView:
        """Geometry of road reference line."""
        return self._planView

    @property
    def elevation_profile(self) -> ElevationProfile:
        """Road elevation."""
        return self._elevationProfile

    @property
    def lateral_profile(self) -> LateralProfile:
        """Superelevation and crossfalls of the road."""
        return self._lateralProfile

    @property
    def lanes(self) -> Lanes:
        """Lanes of the road."""
        return self._lanes

    @property
    def driving_direction(self) -> bool:
        """Driving direction"""
        return self._driving_direction

    @driving_direction.setter
    def driving_direction(self, value):
        if not isinstance(value, bool):
            raise TypeError("Property must be a boolean")
        self._driving_direction = value

    @property
    def objects(self) -> list:
        """Objects on the road."""
        return self._objects

    def add_object(self, object: Object):
        """Adds objects to the list."""
        if not isinstance(object, Object):
            raise TypeError("Has to be of instance Object")

        self._objects.append(object)

    @property
    def signals(self) -> List[Signal]:
        """Signal elements on the road."""
        return self._signals

    def add_signal(self, signal: Signal):
        """Adds signals to list."""
        if not isinstance(signal, Signal):
            raise TypeError("Has to be of instance Signal")

        self._signals.append(signal)

    @property
    def signal_reference(self) -> List[SignalReference]:
        """Signal elements on the road."""
        return self._signalReferences

    def add_signal_reference(self, signal_reference: SignalReference):
        """Adds signal reference to list."""
        if not isinstance(signal_reference, SignalReference):
            raise TypeError("Has to be of instance Signal Reference")

        self._signalReferences.append(signal_reference)

    @property
    def cr_traffic_lights(self) -> List[Tuple[TrafficLight, Tuple[int, int], float]]:
        return self._cr_traffic_lights

    @property
    def cr_traffic_signs(self) -> List[Tuple[TrafficSign, Tuple[int, int], float]]:
        return self._cr_traffic_signs

    @property
    def cr_stop_lines(self) -> List[Tuple[StopLine, Tuple[int, int], float]]:
        return self._cr_stop_lines

    def add_traffic_light(self, traffic_light: Tuple[TrafficLight, Tuple[int, int], float]):
        """Adds CommonRoad traffic light to road for further processing."""
        self._cr_traffic_lights.append(traffic_light)

    def add_traffic_sign(self, traffic_sign: Tuple[TrafficSign, Tuple[int, int], float]):
        """Adds CommonRoad traffic sign to road for further processing."""
        self._cr_traffic_signs.append(traffic_sign)

    def add_stop_line(self, stop_line: Tuple[StopLine, Tuple[int, int], float]):
        """Adds CommonRoad stop line to road for further processing."""
        self._cr_stop_lines.append(stop_line)
