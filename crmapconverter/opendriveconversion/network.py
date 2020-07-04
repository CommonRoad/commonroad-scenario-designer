# -*- coding: utf-8 -*-


"""Module to contain Network which can load an opendrive object and then export
to lanelets. Iternally, the road network is represented by ParametricLanes."""
import numpy as np

from commonroad.scenario.scenario import (
    Scenario, GeoTransformation, Location
)

from crmapconverter.opendriveparser.elements.opendrive import OpenDrive

from crmapconverter.opendriveconversion.utils import encode_road_section_lane_width_id
from crmapconverter.opendriveconversion.lanelet_network import ConversionLaneletNetwork
from crmapconverter.opendriveconversion.converter import OpenDriveConverter

from commonroad.scenario.traffic_sign import (
    TrafficSign, TrafficLight, TrafficSignElement,
    SupportedTrafficSignCountry, TrafficSignIDZamunda, TrafficSignIDGermany, TrafficSignIDUsa, TrafficSignIDChina,
    TrafficSignIDSpain, TrafficSignIDRussia, TrafficLightDirection

)

from crmapconverter.opendriveconversion.plane_elements.geo_reference import get_geo_reference

__author__ = "Benjamin Orthen, Stefan Urban"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "1.2.0"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad-i06@in.tum.de"
__status__ = "Released"


class Network:
    """Represents a network of parametric lanes, with a LinkIndex
    which stores the neighbor relations between the parametric lanes.

    Args:

    """

    def __init__(self):
        self._planes = []
        self._link_index = None
        self._traffic_lights = []
        self._traffic_signs = []
        self._geo_ref = None

    # def __eq__(self, other):
    # return self.__dict__ == other.__dict__

    def load_opendrive(self, opendrive: OpenDrive):
        """Load all elements of an OpenDRIVE network to a parametric lane representation

        Args:
          opendrive:

        """

        self._link_index = LinkIndex()
        self._link_index.create_from_opendrive(opendrive)

        try:
            self._geo_ref = opendrive.header.geo_reference
        except TypeError:
            self._geo_ref = None

        # Convert all parts of a road to parametric lanes (planes)
        for road in opendrive.roads:
            road.planView.precalculate()

            # The reference border is the base line for the whole road
            reference_border = OpenDriveConverter.create_reference_border(
                road.planView, road.lanes.laneOffsets
            )

            # A lane section is the smallest part that can be converted at once
            for lane_section in road.lanes.lane_sections:

                parametric_lane_groups = OpenDriveConverter.lane_section_to_parametric_lanes(
                    lane_section, reference_border
                )
                # parametric_lane_groups is a list of ParametricLaneGroup()
                # ParametricLaneGroup() contains a list of ParametricLane() s

                self._planes.extend(parametric_lane_groups)

                for signal in road.signals:

                    position, tangent = road.planView.calc(signal.s)
                    """position = np.array([position[0] + signal.t * np.cos(tangent + 3.1416/2),
                                         position[1] + signal.t * np.sin(tangent + 3.1416/2)])"""
                    position = np.array([1, 1])

                    if signal.dynamic == 'no':

                        if signal.subtype == '-1' or 'none':
                            additional_values = []
                        else:
                            additional_values = list([signal.subtype])

                        if signal.country == 'DEU':
                            try:
                                element_id = TrafficSignIDGermany(signal.type)
                            except ValueError:
                                element_id = TrafficSignIDGermany.UNKNOWN

                        elif signal.country == 'USA':
                            try:
                                element_id = TrafficSignIDUsa(signal.type)
                            except ValueError:
                                element_id = TrafficSignIDUsa.UNKNOWN

                        elif signal.country == 'CHN':
                            try:
                                element_id = TrafficSignIDChina(signal.type)
                            except ValueError:
                                element_id = TrafficSignIDChina.UNKNOWN

                        elif signal.country == 'ESP':
                            try:
                                element_id = TrafficSignIDSpain(signal.type)
                            except ValueError:
                                element_id = TrafficSignIDSpain.UNKNOWN

                        elif signal.country == 'RUS':
                            try:
                                element_id = TrafficSignIDRussia(signal.type)
                            except ValueError:
                                element_id = TrafficSignIDRussia.UNKNOWN

                        else:
                            try:
                                element_id = TrafficSignIDZamunda(signal.type)
                            except ValueError:
                                element_id = TrafficSignIDZamunda.UNKNOWN
                                additional_values = []

                        traffic_sign_element = TrafficSignElement(
                            traffic_sign_element_id=element_id,
                            additional_values=additional_values
                        )

                        traffic_sign = TrafficSign(
                            traffic_sign_id=signal.id + 1000,
                            traffic_sign_elements=list([traffic_sign_element]),
                            first_occurrence=None,
                            position=position,
                            virtual=False
                        )

                        self._traffic_signs.append(traffic_sign)

                    elif signal.dynamic == 'yes':
                        traffic_light = TrafficLight(
                            traffic_light_id=signal.id + 1000,
                            cycle=[],
                            position=position,
                            time_offset=0,
                            direction=TrafficLightDirection.STRAIGHT,
                            active=False
                        )

                        self._traffic_lights.append(traffic_light)

    def export_lanelet_network(
            self, filter_types: list = None
    ) -> "ConversionLaneletNetwork":
        """Export network as lanelet network.

        Args:
          filter_types: types of ParametricLane objects to be filtered. (Default value = None)

        Returns:
          The converted LaneletNetwork object.
        """

        # Convert groups to lanelets
        lanelet_network = ConversionLaneletNetwork()

        for parametric_lane in self._planes:
            if filter_types is not None and parametric_lane.type not in filter_types:
                continue

            lanelet = parametric_lane.to_lanelet()

            lanelet.predecessor = self._link_index.get_predecessors(parametric_lane.id_)
            lanelet.successor = self._link_index.get_successors(parametric_lane.id_)

            lanelet_network.add_lanelet(lanelet)

        # prune because some
        # successorIds get encoded with a non existing successorID
        # of the lane link
        lanelet_network.prune_network()
        # concatenate possible lanelets with their successors
        lanelet_network.concatenate_possible_lanelets()

        # Perform lane splits and joins
        lanelet_network.join_and_split_possible_lanes()

        lanelet_network.convert_all_lanelet_ids()

        return lanelet_network

    def export_commonroad_scenario(
            self, dt: float = 0.1, benchmark_id=None, filter_types=None
    ):
        """Export a full CommonRoad scenario

        Args:
          dt:  (Default value = 0.1)
          benchmark_id:  (Default value = None)
          filter_types:  (Default value = None)

        Returns:

        """
        if self._geo_ref is not None:
            longitude, latitude = get_geo_reference(self._geo_ref)
            geo_transformation = GeoTransformation(geo_reference=self._geo_ref)

            if longitude is not None and latitude is not None:
                location = Location(
                    geo_transformation=geo_transformation,
                    gps_latitude=latitude, gps_longitude=longitude
                )

            else:
                location = Location(geo_transformation=geo_transformation)
        else:
            location = None

        scenario = Scenario(
            dt=dt, benchmark_id=benchmark_id if benchmark_id is not None else "none",
            location=location
        )

        scenario.add_objects(
            self.export_lanelet_network(
                filter_types=filter_types
                if isinstance(filter_types, list)
                else ["driving", "onRamp", "offRamp", "exit", "entry"]
            )
        )

        lanelet_network = scenario.lanelet_network

        for traffic_light in self._traffic_lights:

            distance = []
            for lanelet in lanelet_network.lanelets:
                pos_1 = traffic_light.position
                n = len(lanelet.center_vertices[0])
                pos_2 = np.array(lanelet.center_vertices[0][int(n/2)], lanelet.center_vertices[1][int(n/2)])
                dist = np.linalg.norm(pos_1 - pos_2)
                distance.append(dist)

            id_for_adding = lanelet_network.lanelets[distance.index(min(distance))].lanelet_id
            lanelet_network.add_traffic_light(traffic_light, {id_for_adding})

        for traffic_sign in self._traffic_signs:

            distance = []
            for lanelet in lanelet_network.lanelets:
                pos_1 = traffic_sign.position
                n = len(lanelet.center_vertices[0])
                pos_2 = np.array(lanelet.center_vertices[0][int(n/2)], lanelet.center_vertices[1][int(n/2)])
                dist = np.linalg.norm(pos_1 - pos_2)
                distance.append(dist)

            id_for_adding = lanelet_network.lanelets[distance.index(min(distance))].lanelet_id
            lanelet_network.add_traffic_sign(traffic_sign, {id_for_adding})

        return scenario


class LinkIndex:
    """Overall index of all links in the file, save everything as successors, predecessors can be found via a reverse search"""

    def __init__(self):
        self._successors = {}

    def create_from_opendrive(self, opendrive):
        """Create a LinkIndex from an OpenDrive object.

        Args:
          opendrive: OpenDrive style object.

        Returns:

        """
        self._add_junctions(opendrive)
        # Extract link information from road lanes
        for road in opendrive.roads:
            for lane_section in road.lanes.lane_sections:
                for lane in lane_section.allLanes:
                    parametric_lane_id = encode_road_section_lane_width_id(
                        road.id, lane_section.idx, lane.id, -1
                    )

                    # Not the last lane section? > Next lane section in same road
                    if lane_section.idx < road.lanes.getLastLaneSectionIdx():
                        successorId = encode_road_section_lane_width_id(
                            road.id, lane_section.idx + 1, lane.link.successorId, -1
                        )

                        self.add_link(parametric_lane_id, successorId, lane.id >= 0)

                    # Last lane section! > Next road in first lane section
                    # Try to get next road
                    elif (
                            road.link.successor is not None
                            and road.link.successor.elementType != "junction"
                    ):

                        next_road = opendrive.getRoad(road.link.successor.element_id)

                        if next_road is not None:

                            if road.link.successor.contactPoint == "start":
                                successorId = encode_road_section_lane_width_id(
                                    next_road.id, 0, lane.link.successorId, -1
                                )

                            else:  # contact point = end
                                successorId = encode_road_section_lane_width_id(
                                    next_road.id,
                                    next_road.lanes.getLastLaneSectionIdx(),
                                    lane.link.successorId,
                                    -1,
                                )
                            self.add_link(parametric_lane_id, successorId, lane.id >= 0)

                    # Not first lane section? > Previous lane section in same road
                    if lane_section.idx > 0:
                        predecessorId = encode_road_section_lane_width_id(
                            road.id, lane_section.idx - 1, lane.link.predecessorId, -1
                        )

                        self.add_link(predecessorId, parametric_lane_id, lane.id >= 0)

                    # First lane section! > Previous road
                    # Try to get previous road
                    elif (
                            road.link.predecessor is not None
                            and road.link.predecessor.elementType != "junction"
                    ):

                        prevRoad = opendrive.getRoad(road.link.predecessor.element_id)

                        if prevRoad is not None:

                            if road.link.predecessor.contactPoint == "start":
                                predecessorId = encode_road_section_lane_width_id(
                                    prevRoad.id, 0, lane.link.predecessorId, -1
                                )

                            else:  # contact point = end
                                predecessorId = encode_road_section_lane_width_id(
                                    prevRoad.id,
                                    prevRoad.lanes.getLastLaneSectionIdx(),
                                    lane.link.predecessorId,
                                    -1,
                                )
                            self.add_link(
                                predecessorId, parametric_lane_id, lane.id >= 0
                            )

    def add_link(self, parametric_lane_id, successor, reverse: bool = False):
        """

        Args:
          parametric_lane_id:
          successor:
          reverse:  (Default value = False)

        Returns:

        """

        # if reverse, call function recursively with switched parameters
        if reverse:
            self.add_link(successor, parametric_lane_id)
            return

        if parametric_lane_id not in self._successors:
            self._successors[parametric_lane_id] = []

        if successor not in self._successors[parametric_lane_id]:
            self._successors[parametric_lane_id].append(successor)

    def _add_junctions(self, opendrive):
        """

        Args:
          opendrive:

        Returns:

        """
        # add junctions to link_index
        # if contact_point is start, and laneId from connecting_road is negative
        # the connecting_road is the successor
        # if contact_point is start, and laneId from connecting_road is positive
        # the connecting_road is the predecessor
        # for contact_point == end it's exactly the other way
        for junction in opendrive.junctions:
            for connection in junction.connections:
                incoming_road = opendrive.getRoad(connection.incomingRoad)
                connecting_road = opendrive.getRoad(connection.connectingRoad)
                contact_point = connection.contactPoint

                for lane_link in connection.laneLinks:
                    if contact_point == "start":

                        # decide which lane section to use (first or last)
                        if lane_link.fromId < 0:
                            lane_section_idx = (
                                incoming_road.lanes.getLastLaneSectionIdx()
                            )
                        else:
                            lane_section_idx = 0
                        incoming_road_id = encode_road_section_lane_width_id(
                            incoming_road.id, lane_section_idx, lane_link.fromId, -1
                        )
                        connecting_road_id = encode_road_section_lane_width_id(
                            connecting_road.id, 0, lane_link.toId, -1
                        )
                        self.add_link(
                            incoming_road_id, connecting_road_id, lane_link.toId > 0
                        )
                    else:
                        # decide which lane section to use (first or last)
                        if lane_link.fromId < 0:
                            lane_section_idx = 0

                        else:
                            lane_section_idx = (
                                incoming_road.lanes.getLastLaneSectionIdx()
                            )
                        incoming_road_id = encode_road_section_lane_width_id(
                            incoming_road.id, 0, lane_link.fromId, -1
                        )
                        connecting_road_id = encode_road_section_lane_width_id(
                            connecting_road.id,
                            connecting_road.lanes.getLastLaneSectionIdx(),
                            lane_link.toId,
                            -1,
                        )
                        self.add_link(
                            incoming_road_id, connecting_road_id, lane_link.toId < 0
                        )

    def remove(self, parametric_lane_id):
        """

        Args:
          parametric_lane_id:

        """
        # Delete key
        if parametric_lane_id in self._successors:
            del self._successors[parametric_lane_id]

        # Delete all occurances in successor lists
        for successorsId, successors in self._successors.items():
            if parametric_lane_id in successors:
                self._successors[successorsId].remove(parametric_lane_id)

    def get_successors(self, parametric_lane_id: str) -> list:
        """

        Args:
          parametric_lane_id: Id of ParametricLane for which to search
            successors.

        Returns:
          List of successors belonging the the ParametricLane.
        Par
        """
        if parametric_lane_id not in self._successors:
            return []

        return self._successors[parametric_lane_id]

    def get_predecessors(self, parametric_lane_id: str) -> list:
        """

        Args:
          parametric_lane_id: Id of ParametricLane for which to search predecessors.

        Returns:
          List of predecessors of a ParametricLane.
        """
        predecessors = []
        for successor_plane_id, successors in self._successors.items():
            if parametric_lane_id not in successors:
                continue

            if successor_plane_id in predecessors:
                continue

            predecessors.append(successor_plane_id)

        return predecessors
