from typing import Union

from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadPlanView import PlanView
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadLink import Link
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadLanes import Lanes
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadElevationProfile import (
    ElevationProfile,
)
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadLateralProfile import LateralProfile
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.junction import Junction
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadObject import Object
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadSignal import Signal, SignalReference


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

    # check if objects have equal instance dictionaries
    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @property
    def id(self) -> int:
        """
        ID of the road.

        :getter: returns road ID
        :setter: sets road ID
        :type: int
        """
        return self._id

    @id.setter
    def id(self, value: int):
        self._id = int(value)

    @property
    def name(self) -> str:
        """
        Name of the road.

        :getter: returns name of the road
        :setter: sets name of the road
        :type: string
        """
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = str(value)

    @property
    def junction(self) -> Union[None, Junction]:
        """
        Junction the road belongs to, if the road is a connecting road.

        :getter: returns junction
        :setter: sets junction
        :type: None or instance of class Junction()
        """
        return self._junction

    @junction.setter
    def junction(self, value):
        if not isinstance(value, Junction) and value is not None:
            raise TypeError("Property must be a Junction or NoneType")
        self._junction = value

    @property
    def link(self) -> Link:
        """
        Road linkage.

        :getter: returns linkage
        :type: instance of class Link()
        """
        return self._link

    @property
    def types(self) -> list:
        """
        Road types.

        :getter: returns road types
        :type: list of instances of class RoadType()
        """
        return self._types

    @property
    def planView(self) -> PlanView:
        """
        Geometry of road reference line.

        :getter: returns reference line geometry
        :type: instance of PlanView()
        """
        return self._planView

    @property
    def elevationProfile(self) -> ElevationProfile:
        """
        Road elevation.

        :getter: returns elevation of the road
        :type: instance of ElevationProfile()
        """
        return self._elevationProfile

    @property
    def lateralProfile(self) -> LateralProfile:
        """
        Superelevation and crossfalls of the road.

        :getter: returns superelevation and crossfalls of the road
        :type: instance of LateralProfile()
        """
        return self._lateralProfile

    @property
    def lanes(self) -> Lanes:
        """
        Lanes of the road.

        :getter: returns lanes of the road
        :type: instance of Lanes()
        """
        return self._lanes

    @property
    def objects(self) -> list:
        """
        Objects on the road.

        :getter: returns road's objects
        :type: list of instances of Object()
        """
        return self._objects

    def addObject(self, object: Object):
        """
        Adds objects to the list.
        """
        if not isinstance(object, Object):
            raise TypeError("Has to be of instance Object")

        self._objects.append(object)

    @property
    def signals(self) -> list:
        """
        Signal elements on the road.

        :getter: returns signal elements
        :type: list of instances of Signal()
        """
        return self._signals

    def addSignal(self, signal: Signal):
        """
        Adds signals to list.
        """
        if not isinstance(signal, Signal):
            raise TypeError("Has to be of instance Signal")

        self._signals.append(signal)

    @property
    def signalReference(self) -> list:
        """
        Signal elements on the road.

        :getter: returns signal elements
        :type: list of instances of SignalReference()
        """
        return self._signalReferences

    def addSignalReference(self, signal_reference: SignalReference):
        """
        Adds signal reference to list.
        """
        if not isinstance(signal_reference, SignalReference):
            raise TypeError("Has to be of instance Signal Reference")

        self._signalReferences.append(signal_reference)
