"""
This module holds the classes required for the intermediate format
"""

__author__ = "Behtarin Ferdousi"

from commonroad.scenario.intersection import Intersection, \
    IntersectionIncomingElement
from commonroad.scenario.lanelet import Lanelet, LaneletNetwork, LaneletType
from commonroad.scenario.obstacle import Obstacle
from typing import List, Set
import os

import numpy as np

from crmapconverter.osm2cr.converter_modules.intermediate_format.sumo_helper \
    import Sumo

from crmapconverter.osm2cr.converter_modules.graph_operations.road_graph \
    import Graph

from crmapconverter.osm2cr import config
from commonroad.scenario.scenario import Scenario

from commonroad.scenario.traffic_sign import TrafficSign
from commonroad.scenario.traffic_sign import TrafficLight

from crmapconverter.osm2cr.converter_modules.utility import geometry,\
    idgenerator


class Node:
    """
    Class to represent the nodes in the intermediate format
    """
    def __init__(self, node_id, point):
        """
        Initialize a node element

        :param node_id: unique id for node
        :type node_id: int
        :param point: position of the node
        :type point: geometry.position
        """

        self.id = node_id
        self.point = point


class Edge:
    """
    Class to represent the edges in the intermediate format
    """

    def __init__(self,
                 edge_id: int,
                 node1: Node,
                 node2: Node,
                 left_bound: List[np.ndarray],
                 right_bound: List[np.ndarray],
                 center_points: List[np.ndarray],
                 adjacent_right: int,
                 adjacent_right_direction_equal: bool,
                 adjacent_left: int,
                 adjacent_left_direction_equal: bool,
                 successors: List[int],
                 predecessors: List[int],
                 traffic_signs: Set[int],
                 traffic_lights: Set[int]):
        """
        Initialize an edge

        :param edge_id: unique id for edge
        :param node1: node at the start of the edge
        :param node2: node at the end of the edge
        :param left_bound: list of vertices on the left bound of edge
        :param right_bound: list of vertices on the right bound of edge
        :param center_points: list of center vertices of the edge
        :param adjacent_right: id of the adjacent right edge
        :param adjacent_right_direction_equal: true if adjacent right edge has
        the same direction, false otherwise
        :param adjacent_left: id of the adjacent left edge
        :param adjacent_left_direction_equal: true if adjacent left edge has
        the same direction, false otherwise
        :param successors: List of ids of the succcessor edges
        :param predecessors: List of ids of the predecessor edges
        :param traffic_signs: Set of id of traffic signs applied on the edge
        :param traffic_lights: Set of id of traffic lights applied on the edge
        """
        self.id = edge_id
        self.node1 = node1
        self.node2 = node2
        self.left_bound = left_bound
        self.right_bound = right_bound
        self.center_points = center_points
        self.adjacent_right = adjacent_right
        self.adjacent_left_direction_equal = adjacent_left_direction_equal
        self.adjacent_left = adjacent_left
        self.adjacent_right_direction_equal = adjacent_right_direction_equal
        self.successors = successors
        self.predecessors = predecessors
        self.traffic_signs = traffic_signs
        self.traffic_lights = traffic_lights

    def to_lanelet(self) -> Lanelet:
        """
        Converts to CommonRoad Lanelet object

        :return: CommonRoad Lanelet
        """
        return Lanelet(
            np.array(self.left_bound),
            np.array(self.center_points),
            np.array(self.right_bound),
            self.id,
            self.predecessors,
            self.successors,
            self.adjacent_left,
            self.adjacent_left_direction_equal,
            self.adjacent_right,
            self.adjacent_right_direction_equal,
            traffic_signs=self.traffic_signs,
            traffic_lights=self.traffic_lights,
            lanelet_type= {LaneletType(config.LANELETTYPE)}
        )

    @staticmethod
    def extract_from_lane(lane):
        """
        Initialize edge from the RoadGraph lane element
        :param lane: Roadgraph.lane
        :return: Edge element for the Intermediate Format
        """
        current_id = lane.id

        successors = [successor.id for successor in lane.successors]
        predecessors = [predecessor.id for predecessor in lane.predecessors]

        # left adjacent
        if lane.adjacent_left is not None:
            adjacent_left = lane.adjacent_left.id
            if lane.adjacent_left_direction_equal is not None:
                adjacent_left_direction_equal = lane.adjacent_left_direction_equal
            elif lane.edge is not None:
                adjacent_left_direction_equal = lane.forward == adjacent_left.forward
            else:
                raise ValueError("Lane has no direction info!")
        else:
            adjacent_left = None
            adjacent_left_direction_equal = None

        # right adjacent
        if lane.adjacent_right is not None:
            adjacent_right = lane.adjacent_right.id
            if lane.adjacent_right_direction_equal is not None:
                adjacent_right_direction_equal = lane.adjacent_right_direction_equal
            elif lane.edge is not None:
                adjacent_right_direction_equal = lane.forward == adjacent_right.forward
            else:
                raise ValueError("Lane has no direction info!")
        else:
            adjacent_right = None
            adjacent_right_direction_equal = None

        traffic_lights = None
        if lane.traffic_lights is not None:
            traffic_lights = [light.id for light in lane.traffic_lights]
            traffic_lights = set(traffic_lights)

        traffic_signs = None
        if lane.traffic_signs is not None:
            traffic_signs = [sign.id for sign in lane.traffic_signs]
            traffic_signs = set(traffic_signs)

        from_node = Node(lane.from_node.id, lane.from_node.get_point())
        to_node = Node(lane.to_node.id, lane.to_node.get_point())

        return Edge(current_id,
                    from_node,
                    to_node,
                    lane.left_bound,
                    lane.right_bound,
                    lane.waypoints,
                    adjacent_right,
                    adjacent_right_direction_equal,
                    adjacent_left,
                    adjacent_left_direction_equal,
                    successors,
                    predecessors,
                    traffic_signs,
                    traffic_lights
                    )


def add_is_left_of(incoming_data, incoming_data_id):
    """
    Find and add isLeftOf property for the incomings

    :param incoming_data: incomings without isLeftOf
    :param incoming_data_id: List of the id of the incomings
    :return: incomigs with the isLeftOf assigned
    """

    # Choose a reference incoming vector
    ref = incoming_data[0]['waypoints'][0] - incoming_data[0]['waypoints'][-1]
    angles = [(0, 0)]

    # calculate all incoming angle from the reference incoming vector
    for index in range(1, len(incoming_data)):
        new_v = incoming_data[index]['waypoints'][0] - incoming_data[index]['waypoints'][-1]
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
        if config.LANE_SEGMENT_ANGLE < angle <= 90 + config.LANE_SEGMENT_ANGLE:
            # is left of the previous incoming
            is_left_of = angles[prev][0]
            data_index = angles[index][0]
            incoming_data[data_index].update({'isLeftOf': incoming_data_id[is_left_of]})
        prev = index

    return incoming_data


class IntermediateFormat:
    """
    Class that represents the intermediate format

    """

    def __init__(self,
                 nodes: List[Node],
                 edges: List[Edge],
                 traffic_signs: List[TrafficSign] = None,
                 traffic_lights: List[TrafficLight] = None,
                 obstacles: List[Obstacle] = None,
                 intersections: List[Intersection] = None, ):
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
        self.traffic_signs = traffic_signs
        self.traffic_lights = traffic_lights
        self.obstacles = obstacles

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
        Find the traffic sign by the sign id

        :param sign_id: sign id of the Traffic Sign element
        :return: CommonRoad TrafficSign
        """
        for sign in self.traffic_signs:
            if sign.traffic_sign_id == sign_id:
                return sign

    @staticmethod
    def get_direction(a: List[np.ndarray], b: List[np.ndarray]):
        """
        Return direction of waypoints b from waypoints a

        :param a: List of points
        :param b: List of points
        :return: str: left or right or through
        """
        # Find angle between the line formed by a and line formed by b
        a_angle = geometry.curvature(a)
        b_angle = geometry.curvature(b)
        angle = a_angle - b_angle

        forward = True
        m = geometry.get_gradient(a)
        if m < 0:
            # Line with downward slope
            forward = False
        if angle < config.LANE_SEGMENT_ANGLE:
            return 'through'
        if forward:
            if angle < 90:
                return "right"
            return 'left'
        else:
            if angle > 90:
                return "right"
            return 'left'

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
            # node with more than 2 edge is an intersection
            if node.get_degree() > 2:
                # keep track of added lanes to consider unique intersections
                incoming = [p for p in lane.predecessors if p.id not in added_lanes]

                # Initialize incomming element with properties to be filled in
                incoming_element = {'incomingLanelet': set([incoming_lane.id for incoming_lane in incoming]),
                                    'right': [],
                                    'left': [],
                                    'through': [],
                                    'none': [],
                                    'isLeftOf': [],
                                    'waypoints': []}

                for incoming_lane in incoming:
                    directions = incoming_lane.turnlane.split(";")  # find the turnlanes

                    if not incoming_element['waypoints']:
                        # set incoming waypoints only once
                        incoming_element['waypoints'] = incoming_lane.waypoints

                    for direction in directions:
                        if direction == 'none':
                            # calculate the direction for each successor
                            for s in incoming_lane.successors:
                                angle = IntermediateFormat.get_direction(incoming_lane.waypoints,
                                                                         s.waypoints)
                                incoming_element[angle].append(s.id)
                        else:
                            incoming_element[direction].extend(
                                    [s.id for s in incoming_lane.successors])

                    if node.id in intersections:
                        # add new incoming element to existing intersection
                        intersections[node.id]['incoming'].append(incoming_element)
                    else:
                        # add new intersection
                        intersections[node.id] = \
                            {'incoming': [incoming_element]}

                    added_lanes = added_lanes.union(incoming_element['incomingLanelet'])

        # Convert to CommonRoad Intersections
        intersections_cr = []
        for intersection_node_id in intersections:
            incoming_elements = []
            incoming_data = intersections[intersection_node_id]['incoming']
            incoming_ids = [idgenerator.get_id() for incoming in incoming_data]
            incoming_data = add_is_left_of(incoming_data, incoming_ids)
            index = 0
            for incoming in incoming_data:
                incoming_lanelets = set(incoming['incomingLanelet'])
                successors_right = set(incoming["right"])
                successors_left = set(incoming["left"])
                successors_straight = set(incoming['through']).union(set(incoming['none']))
                is_left_of = incoming['isLeftOf']
                incoming_element = IntersectionIncomingElement(incoming_ids[index],
                                                               incoming_lanelets,
                                                               successors_right,
                                                               successors_straight,
                                                               successors_left,
                                                               is_left_of
                                                               )
                incoming_elements.append(incoming_element)
                index += 1

            intersections_cr.append(Intersection(idgenerator.get_id(),
                                                 incoming_elements))
        return intersections_cr

    def to_commonroad_scenario(self):
        """
        Convert Intermediate Format to CommonRoad Scenario

        :return: CommonRoad Scenario
        """
        scenario = Scenario(config.TIMESTEPSIZE, config.BENCHMARK_ID)
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

        # TODO Add Obstacles

        scenario.lanelet_network = net
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

        traffic_signs = [sign.to_traffic_sign_cr()
                         for sign in graph.traffic_signs]

        traffic_lights = [light.to_traffic_light_cr()
                          for light in graph.traffic_lights]

        intersections = IntermediateFormat.get_intersections(graph)
        return IntermediateFormat(nodes,
                                  edges,
                                  traffic_signs,
                                  traffic_lights,
                                  intersections=intersections)

    def get_obstacles(self):
        # TODO Get obstacles from SUMO route file
        pass

    def generate_sumo_config_file(self):
        """
        Method to Use Sumo to generate config file
        """
        path = config.SUMO_SAVE_FILE
        if not os.path.exists(config.SUMO_SAVE_FILE):
            os.makedirs(config.SUMO_SAVE_FILE)

        sumo = Sumo(self, path, 'test')
        sumo.write_net()
        sumo.generate_trip_file(0, 2000)
        sumo.write_config_file(0, 2000)

        print("See Sumo Config File Here: "+sumo.config_file)
        return sumo.config_file

