from __future__ import annotations

from typing import Union

from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.junction import (
    Junction,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.road import (
    Road,
)


class OpenDrive:
    """
    Class which describes the OpenDRIVE element by its direct children elements.

    :ivar _header: header element
    :ivar _roads: road elements in the OpenDRIVE element
    :ivar _controllers: controller elements in the OpenDRIVE element
    :ivar _junctions: junction elements in the OpenDRIVE element
    :ivar _junctionGroups: junctionGroup elements in the OpenDRIVE element
    :ivar _stations: station elements in the OpenDRIVE element
    """

    def __init__(self):
        self._header = None
        self._roads = []
        self._controllers = []
        self._junctions = []
        self._junctionGroups = []
        self._stations = []

    @property
    def header(self) -> Header:
        """
        Header element -> first element in OpenDRIVE element.

        :getter: returns the header element
        :setter: sets the header
        """
        return self._header

    @header.setter
    def header(self, value: Header):
        self._header = value

    @property
    def roads(self) -> list[Road]:
        """
        Roads in the OpenDRIVE file.

        :getter: returns the road instances in the form of a list [road1, road2, ...]s
        """
        return self._roads

    def getRoad(self, id_) -> Union[Road, None]:
        """
        Returns the road corresponding to certain road ID.

        :param: id of the road
        :return: road element
        """
        for road in self._roads:
            if road.id == id_:
                return road

        return None

    @property
    def controllers(self):
        """
        Controllers in the OpenDRIVE file.
        Not used yet, since controllers are not existent yet in the conversion.

        :getter: returns the controller instances in the form of a list [controller1, controller2, ...]
        """
        return self._controllers

    @property
    def junctions(self) -> list[Junction]:
        """
        Junctions in the OpenDrive file.

        :getter: returns the junction instances in the form of a list [junction1, junction2, ...]
        """
        return self._junctions

    def getJunction(self, junctionId) -> Union[None, Junction]:
        """
        Returns the junction corresponding to a certain ID.

        :param: id of the junction
        :return: junction element
        """
        for junction in self._junctions:
            if junction.id == junctionId:
                return junction
        return None

    @property
    def junctionGroups(self):
        """
        Junction groups in the OpenDRIVE file.
        Not used yet, since junction groups are not existent yet in the conversion.

        :getter: returns the junction group instances in the form of a list [junctionGroup1, junctionGroup2, ...]
        """
        return self._junctionGroups

    @property
    def stations(self):
        """
        Stations in the OpenDrive file -> used for rail-bound vehicle stations and/or bus stations.
        Not used yet, since stations are not existent yet in the conversion.

        :getter: returns the stations in the form of a list [station1, station2, ...]
        """
        return self._stations


class Header:
    """
    Header element of the OpenDRIVE element. Very first element in the file.

    :ivar revMajor: major revision number of ASAM OpenDRIVE format
    :ivar revMinor: minor revision number of ASAM OpenDIVE format
    :ivar name: database name
    :ivar version: version of this road network
    :ivar date: time/date of database creation according to ISO 8601
    :ivar north: max inertial y value
    :ivar south: min inertial y value
    :ivar east: max inertial x value
    :ivar west: min inertial x value
    :ivar vendor: vendor name
    :ivar geo_reference: geo-reference
    """

    def __init__(
        self,
        rev_major=None,
        rev_minor=None,
        name: str = None,
        version=None,
        date=None,
        north=None,
        south=None,
        east=None,
        west=None,
        vendor=None,
    ):
        self.revMajor = rev_major
        self.revMinor = rev_minor
        self.name = name
        self.version = version
        self.date = date
        self.north = north
        self.south = south
        self.east = east
        self.west = west
        self.vendor = vendor
        self.geo_reference = None
        self.offset = {"x": "0.0", "y": "0.0", "z": "0.0", "hdg": "0.0"}
