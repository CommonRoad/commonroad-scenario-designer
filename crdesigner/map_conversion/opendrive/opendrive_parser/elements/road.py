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

__author__ = "Benjamin Orthen, Stefan Urban, Sebastian Maierhofer"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles, BMW Car@TUM"]
__version__ = "0.5"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad@lists.lrz.de"
__status__ = "Released"


class Road:
    """ """

    def __init__(self):
        self._id = None
        self._name = None
        self._junction = None
        self._length = None

        self._header = None  # TODO
        self._link = Link()
        self._types = []
        self._planView = PlanView()
        self._elevationProfile = ElevationProfile()
        self._lateralProfile = LateralProfile()
        self._lanes = Lanes()
        self._objects = []
        self._signals = []
        self._signalReferences = []

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @property
    def id(self):
        """ """
        return self._id

    @id.setter
    def id(self, value):
        """

        Args:
          value:

        Returns:

        """
        self._id = int(value)

    @property
    def name(self):
        """ """
        return self._name

    @name.setter
    def name(self, value):
        """

        Args:
          value:

        Returns:

        """
        self._name = str(value)

    @property
    def junction(self):
        """ """
        return self._junction

    @junction.setter
    def junction(self, value):
        """

        Args:
          value:

        Returns:

        """
        if not isinstance(value, Junction) and value is not None:
            raise TypeError("Property must be a Junction or NoneType")

        if value == -1:
            value = None

        self._junction = value

    @property
    def link(self):
        """ """
        return self._link

    @property
    def types(self):
        """ """
        return self._types

    @property
    def planView(self):
        """ """
        return self._planView

    @property
    def elevationProfile(self):
        """ """
        return self._elevationProfile

    @property
    def lateralProfile(self):
        """ """
        return self._lateralProfile

    @property
    def lanes(self):
        """ """
        return self._lanes

    @property
    def objects(self):
        """ """
        return self._objects

    def addObject(self, object):

        if not isinstance(object, Object):
            raise TypeError("Has to be of instance Object")

        self._objects.append(object)

    @property
    def signals(self):
        return self._signals

    def addSignal(self, signal):

        if not isinstance(signal, Signal):
            raise TypeError("Has to be of instance Signal")

        self._signals.append(signal)

    @property
    def signalReference(self):
        return self._signalReferences

    def addSignalReference(self, signal_reference):

        if not isinstance(signal_reference, SignalReference):
            raise TypeError("Has to be of instance Signal Reference")

        self._signalReferences.append(signal_reference)
