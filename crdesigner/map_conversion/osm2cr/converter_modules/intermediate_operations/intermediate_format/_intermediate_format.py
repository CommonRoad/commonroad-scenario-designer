import copy
from typing import Dict, List, Set, Tuple

from commonroad.scenario.intersection import Intersection, IntersectionIncomingElement
from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.scenario.obstacle import Obstacle
from commonroad.scenario.scenario import (
    GeoTransformation,
    Location,
    Scenario,
    ScenarioID,
)
from commonroad.scenario.traffic_light import TrafficLight
from commonroad.scenario.traffic_sign import TrafficSign

from crdesigner.common.config.general_config import general_config
from crdesigner.common.config.osm_config import osm_config as config
from crdesigner.map_conversion.common import geometry
from crdesigner.map_conversion.osm2cr.converter_modules.intermediate_operations.intersection_enhancement import (
    intersection_enhancement,
)
from crdesigner.map_conversion.osm2cr.converter_modules.utility import idgenerator

from ...graph_operations.road_graph._graph import Graph
from ._intermediate_edge import Edge
from ._intermediate_node import Node

# mapping from crossed lanelet ids to the crossing ones
Crossings = Dict[int, Set[int]]


class IntermediateFormat:
    """
    Class that represents the intermediate format
    """

    def __init__(
        self,
        nodes: List[Node],
        edges: List[Edge],
        center_point: Tuple[float, float],
        traffic_signs: List[TrafficSign] = None,
        traffic_lights: List[TrafficLight] = None,
        obstacles: List[Obstacle] = None,
        intersections: List[Intersection] = None,
    ):
        """
        Initialize the Intermediate Format

        :param nodes: List of nodes in the format
        :param edges: List of edges representing the roads
        :param traffic_signs: List of CommonRoad traffic signs on the map
        :param traffic_lights: List of CommonRoad traffic lights on the map
        :param obstacles: List of CommonRoad obstacles
        :param intersections: List of CommonRoad intersections
        """

        self.nodes = nodes
        self.edges = edges
        self.intersections = intersections
        self.center_point = center_point
        if self.intersections is None:
            self.intersections = []
        self.traffic_signs = traffic_signs
        if self.traffic_signs is None:
            self.traffic_signs = []
        self.traffic_lights = traffic_lights
        if self.traffic_lights is None:
            self.traffic_lights = []
        self.obstacles = obstacles
        if self.obstacles is None:
            self.obstacles = []

        if config.INTERSECTION_ENHANCEMENT:
            intersection_enhancement(self)

    def find_edge_by_id(self, edge_id):
        """
        Find the edge in the format by id

        :param edge_id: unique id of the edge
        :return: Edge
        """
        for edge in self.edges:
            if edge.id == edge_id:
                return edge

    def find_traffic_sign_by_id(self, sign_id):
        """
        Find traffic sign by the sign id

        :param sign_id: sign id of the Traffic Sign element
        :return: CommonRoad TrafficSign
        """
        for sign in self.traffic_signs:
            if sign.traffic_sign_id == sign_id:
                return sign

    def find_traffic_light_by_id(self, light_id):
        """
        Find traffic light by the light id

        :param light_id: light id of the Traffic Light element
        :return: CommonRoad TrafficLight
        """
        for light in self.traffic_lights:
            if light.traffic_light_id == light_id:
                return light

    @staticmethod
    def add_is_left_of(incoming_data, incoming_data_id):
        """
        Find and add isLeftOf property for the incomings

        :param incoming_data: incomings without isLeftOf
        :param incoming_data_id: List of the id of the incomings
        :return: incomings with the isLeftOf assigned
        """

        # choose a reference incoming vector
        ref = incoming_data[0]["waypoints"][0] - incoming_data[0]["waypoints"][-1]
        angles = [(0, 0)]

        # calculate all incoming angle from the reference incoming vector
        for index in range(1, len(incoming_data)):
            new_v = incoming_data[index]["waypoints"][0] - incoming_data[index]["waypoints"][-1]
            angle = geometry.get_angle(ref, new_v)
            if angle < 0:
                angle += 360
            angles.append((index, angle))

        # sort the angles from the reference to go clockwise
        angles.sort(key=lambda tup: tup[1])
        prev = -1

        # take the incomings which have less than 90 degrees in between
        for index in range(0, len(incoming_data)):
            angle = angles[index][1] - angles[prev][1]
            if angle < 0:
                angle += 360

            # add is_left_of relation if angle is less than intersection straight treshold
            if angle <= 180 - config.INTERSECTION_STRAIGHT_THRESHOLD:
                # is left of the previous incoming
                is_left_of = angles[prev][0]
                data_index = angles[index][0]
                incoming_data[data_index].update({"isLeftOf": incoming_data_id[is_left_of]})

            prev = index

        return incoming_data

    @staticmethod
    def get_directions(incoming_lane):
        """
        Find all directions of a incoming lane's successors

        :param incoming_lane: incoming lane from intersection
        :return: str: left or right or through
        """
        straight_threshold_angel = config.INTERSECTION_STRAIGHT_THRESHOLD
        assert 0 < straight_threshold_angel < 90

        successors = incoming_lane.successors
        angels = {}
        directions = {}
        for s in successors:
            # only use the last three waypoints of the incoming for angle calculation
            a_angle = geometry.curvature(incoming_lane.waypoints[-3:])
            b_angle = geometry.curvature(s.waypoints)
            angle = a_angle - b_angle
            angels[s.id] = angle

            # determine direction of waypoints

            # right-turn
            if geometry.is_clockwise(s.waypoints) > 0:
                angels[s.id] = abs(angels[s.id])
            # left-turn
            if geometry.is_clockwise(s.waypoints) < 0:
                angels[s.id] = -abs(angels[s.id])

        # sort after size
        sorted_angels = {k: v for k, v in sorted(angels.items(), key=lambda item: item[1])}
        sorted_keys = list(sorted_angels.keys())
        sorted_values = list(sorted_angels.values())

        # if 3 successors we assume the directions
        if len(sorted_angels) == 3:
            directions = {
                sorted_keys[0]: "left",
                sorted_keys[1]: "through",
                sorted_keys[2]: "right",
            }

        # if 2 successors we assume that they both cannot have the same direction
        if len(sorted_angels) == 2:
            directions = dict.fromkeys(sorted_angels)

            if (abs(sorted_values[0]) > straight_threshold_angel) and (
                abs(sorted_values[1]) > straight_threshold_angel
            ):
                directions[sorted_keys[0]] = "left"
                directions[sorted_keys[1]] = "right"
            elif abs(sorted_values[0]) < abs(sorted_values[1]):
                directions[sorted_keys[0]] = "through"
                directions[sorted_keys[1]] = "right"
            elif abs(sorted_values[0]) > abs(sorted_values[1]):
                directions[sorted_keys[0]] = "left"
                directions[sorted_keys[1]] = "through"
            else:
                directions[sorted_keys[0]] = "through"
                directions[sorted_keys[1]] = "through"

        # if we have 1 or more than 3 successors it's hard to make predictions,
        # therefore only straight_threshold_angel is used
        if len(sorted_angels) == 1 or len(sorted_angels) > 3:
            directions = dict.fromkeys(sorted_angels, "through")
            for key in sorted_angels:
                if sorted_angels[key] < -straight_threshold_angel:
                    directions[key] = "left"
                if sorted_angels[key] > straight_threshold_angel:
                    directions[key] = "right"

        return directions

    @staticmethod
    def get_intersections(graph) -> List[Intersection]:
        """
        Generate the intersections from RoadGraph

        :param graph: RoadGraph
        :return: List of CommonRoad Intersections
        """
        intersections = {}
        added_lanes = set()
        for lane in graph.lanelinks:
            node = lane.to_node
            # node with more than 2 edges or marked as crossing is an intersection
            if node.get_degree() > 2 or (node.is_crossing and node.get_degree() == 2):
                # keep track of added lanes to consider unique intersections
                incoming = [p for p in lane.predecessors if p.id not in added_lanes]

                # skip if no incoming was found
                if not incoming:
                    continue

                # add adjacent lanes
                lanes_to_add = []
                for incoming_lane in incoming:
                    left = incoming_lane.adjacent_left
                    right = incoming_lane.adjacent_right
                    while left:
                        if left.adjacent_right_direction_equal and left.id not in added_lanes:
                            lanes_to_add.append(left)
                            added_lanes.add(left.id)
                            left = left.adjacent_left
                        else:
                            left = None
                    while right:
                        if right.adjacent_left_direction_equal and right.id not in added_lanes:
                            lanes_to_add.append(right)
                            added_lanes.add(right.id)
                            right = right.adjacent_right
                        else:
                            right = None

                incoming.extend(lanes_to_add)

                # Initialize incoming element with properties to be filled in
                incoming_element = {
                    "incomingLanelet": set([incoming_lane.id for incoming_lane in incoming]),
                    "right": [],
                    "left": [],
                    "through": [],
                    "none": [],
                    "isLeftOf": None,
                    "waypoints": [],
                }

                for incoming_lane in incoming:
                    directions = incoming_lane.turnlane.split(";")  # find the turnlanes

                    if not incoming_element["waypoints"]:
                        # set incoming waypoints only once
                        incoming_element["waypoints"] = incoming_lane.waypoints

                    for direction in directions:
                        if direction == "none":
                            # calculate the direction for each successor
                            directions = IntermediateFormat.get_directions(incoming_lane)
                            for key in directions:
                                incoming_element[directions[key]].append(key)
                        else:
                            # TODO implement unknown direction keys
                            try:
                                incoming_element[direction].extend(
                                    [s.id for s in incoming_lane.successors]
                                )
                            except KeyError:
                                print("unknown intersection direction key: " + direction)
                                # calculate the direction for each successor
                                directions = IntermediateFormat.get_directions(incoming_lane)
                                for key in directions:
                                    incoming_element[directions[key]].append(key)

                if node.id in intersections:
                    # add new incoming element to existing intersection
                    intersections[node.id]["incoming"].append(incoming_element)
                else:
                    # add new intersection
                    intersections[node.id] = {"incoming": [incoming_element]}

                added_lanes = added_lanes.union(incoming_element["incomingLanelet"])

        # Convert to CommonRoad Intersections
        intersections_cr = []
        for intersection_node_id in intersections:
            incoming_elements = []
            incoming_data = intersections[intersection_node_id]["incoming"]
            incoming_ids = [idgenerator.get_id() for incoming in incoming_data]
            incoming_data = IntermediateFormat.add_is_left_of(incoming_data, incoming_ids)
            index = 0
            for incoming in incoming_data:
                incoming_lanelets = set(incoming["incomingLanelet"])
                successors_right = set(incoming["right"])
                successors_left = set(incoming["left"])
                successors_straight = set(incoming["through"]).union(set(incoming["none"]))
                is_left_of = incoming["isLeftOf"]
                incoming_element = IntersectionIncomingElement(
                    incoming_ids[index],
                    incoming_lanelets,
                    successors_right,
                    successors_straight,
                    successors_left,
                    is_left_of,
                )
                incoming_elements.append(incoming_element)
                index += 1
            intersections_cr.append(Intersection(idgenerator.get_id(), incoming_elements))
        return intersections_cr

    def to_commonroad_scenario(self):
        """
        Convert Intermediate Format to CommonRoad Scenario

        :return: CommonRoad Scenario
        """
        location_kwargs = dict(
            gps_latitude=self.center_point[0], gps_longitude=self.center_point[1]
        )
        location = Location(
            geo_transformation=GeoTransformation(geo_reference=general_config.proj_string_cr),
            **location_kwargs,
        )

        scenario = Scenario(
            general_config.time_step_size,
            ScenarioID(
                country_id=general_config.country_id,
                map_name=general_config.map_name,
                map_id=general_config.map_id,
            ),
            location=location,
        )
        net = LaneletNetwork()

        # Add edges
        for edge in self.edges:
            lanelet = edge.to_lanelet()
            net.add_lanelet(lanelet)

        # Add Traffic Signs
        for sign in self.traffic_signs:
            net.add_traffic_sign(sign, set())

        # Add Traffic Lights
        for light in self.traffic_lights:
            net.add_traffic_light(light, set())

        # Add Intersections
        for intersection in self.intersections:
            net.add_intersection(intersection)

        scenario.replace_lanelet_network(net)
        return scenario

    @staticmethod
    def extract_from_road_graph(graph: Graph):
        """
        Extract map information from RoadGraph in OSM Converter

        :param graph: RoadGraph
        :return: Intermediate Format
        """
        road_graph = graph
        nodes = [Node(node.id, node.get_point()) for node in road_graph.nodes]
        edges = []
        lanes = graph.get_all_lanes()
        for lane in lanes:
            edge = Edge.extract_from_lane(lane)
            edges.append(edge)

        traffic_signs = [sign.to_traffic_sign_cr() for sign in graph.traffic_signs]

        traffic_lights = [light.to_traffic_light_cr() for light in graph.traffic_lights]

        intersections = IntermediateFormat.get_intersections(graph)

        return IntermediateFormat(
            nodes,
            edges,
            graph.center_point,
            traffic_signs,
            traffic_lights,
            intersections=intersections,
        )

    @staticmethod
    def get_lanelet_intersections(
        crossing_interm: "IntermediateFormat", crossed_interm: "IntermediateFormat"
    ) -> Crossings:
        """
        Calculate all polygon intersections of the lanelets of the two networks.
        For each lanelet of b return the crossing lanelets of a as list.

        :param crossing_interm: crossing network
        :param crossed_interm: network crossed by crossing_interm
        :return: Dict of crossing lanelet ids for each lanelet
        """
        crossing_lane_network = crossing_interm.to_commonroad_scenario().lanelet_network
        crossed_lane_network = crossed_interm.to_commonroad_scenario().lanelet_network
        crossings = dict()
        for crossed_lanelet in crossed_lane_network.lanelets:
            crossing_lanelet_ids = crossing_lane_network.find_lanelet_by_shape(
                crossed_lanelet.polygon
            )
            crossings[crossed_lanelet.lanelet_id] = set(crossing_lanelet_ids)
        return crossings

    def remove_invalid_references(self):
        """
        remove references of traffic lights and signs that point to
        non existing elements.
        """
        traffic_light_ids = {tlight.traffic_light_id for tlight in self.traffic_lights}
        traffic_sign_ids = {tsign.traffic_sign_id for tsign in self.traffic_signs}
        for edge in self.edges:
            for t_light_ref in set(edge.traffic_lights):
                if t_light_ref not in traffic_light_ids:
                    edge.traffic_lights.remove(t_light_ref)

            for t_sign_ref in set(edge.traffic_signs):
                if t_sign_ref not in traffic_sign_ids:
                    edge.traffic_signs.remove(t_sign_ref)

    def merge(self, other_interm: "IntermediateFormat"):
        """
        Merge other instance of intermediate format into this.
        The other instance is not changed.

        :param other_interm: the indtance of intermediate format to merge
        """
        self.nodes.extend(copy.deepcopy(other_interm.nodes))
        edges_to_merge = copy.deepcopy(other_interm.edges)
        for edge in edges_to_merge:
            edge.edge_type = config.SUBLAYER_LANELETTYPE
        self.edges.extend(edges_to_merge)
        self.obstacles.extend(copy.deepcopy(other_interm.obstacles))
        self.traffic_signs.extend(copy.deepcopy(other_interm.traffic_signs))
        self.traffic_lights.extend(copy.deepcopy(other_interm.traffic_lights))
        self.intersections.extend(copy.deepcopy(other_interm.intersections))

    def add_crossing_information(self, crossings: Crossings):
        """
        Add information about crossings to the intersections.
        The parameter maps each lanelet id to the crossing lanelet ids.

        :param crossings: dict of crossed and crossing lanelets
        """

        all_crossed_ids = set([crossed for crossed in crossings if crossings[crossed]])
        all_crossing_ids = set()
        for i in self.intersections:
            # find all lanelets of the intersection that are crossed
            intersection_lanelet_ids = set()
            for incoming in i.incomings:
                intersection_lanelet_ids |= set(incoming.successors_left)
                intersection_lanelet_ids |= set(incoming.successors_straight)
                intersection_lanelet_ids |= set(incoming.successors_right)
            intersected_lanelets_of_i = intersection_lanelet_ids & all_crossed_ids
            # add information about crossings to intersection
            for intersected in intersected_lanelets_of_i:
                all_crossing_ids |= crossings[intersected]
                for crossing_id in crossings[intersected]:
                    i.crossings.add(crossing_id)

        # adjust edge type of crossing edges
        for edge in self.edges:
            if edge.id in all_crossing_ids:
                edge.edge_type = config.CROSSING_LANELETTYPE
