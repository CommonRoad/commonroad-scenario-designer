"""
This module holds the classes required for the intermediate format
"""
from commonroad.scenario.intersection import Intersection, IntersectionIncomingElement
from commonroad.scenario.lanelet import LaneletType, Lanelet, LaneletNetwork
from commonroad.scenario.obstacle import Obstacle
from typing import List, Set

import numpy as np

from crmapconverter.osm2cr.converter_modules.intermediate_format.sumo_helper import Sumo

from crmapconverter.osm2cr.converter_modules.graph_operations.road_graph import Graph

from crmapconverter.osm2cr import config
from commonroad.scenario.scenario import Scenario

from commonroad.scenario.traffic_sign import TrafficSign
from commonroad.scenario.traffic_sign import TrafficLight

from crmapconverter.osm2cr.converter_modules.utility import geometry, idgenerator


class Node:
    def __init__(self, id, point):
        self.id = id
        self.point = point

class Edge:
    """
    Class to represent the edges in the intermediate format
    """

    def __init__(self,
                 id: int,
                 node1: geometry.Point,
                 node2: geometry.Point,
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
        self.id = id
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
            traffic_lights=self.traffic_lights
        )

    @staticmethod
    def extract_from_lane(lane):
        current_id = lane.id
        left_bound = lane.left_bound
        right_bound = lane.right_bound
        center_points = lane.waypoints
        successors = []
        for successor in lane.successors:
            successors.append(successor.id)
        predecessors = []
        for predecessor in lane.predecessors:
            predecessors.append(predecessor.id)
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

        successors = [successor.id for successor in lane.successors]
        predecessors = [predecessor.id for predecessor in lane.predecessors]
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
    ref = incoming_data[0]['waypoints'][0] - incoming_data[0]['waypoints'][-1]
    angles = [(0, 0)]
    # calculate all incoming angle from the reference incoming
    for index in range(1, len(incoming_data)):
        new_v = incoming_data[index]['waypoints'][0] -  incoming_data[index]['waypoints'][-1]
        angles.append((index, geometry.angle_to(ref, new_v)))

    #sort the angles from the reference to go clockwise
    angles.sort(key = lambda tup: tup[1])
    prev = -1

    # take the incomings which have less than 90 degree in between
    for index in range(0,len(incoming_data)):
        angle = angles[index][1] - angles[prev][1]
        if angle<0:
            angle = 360+angle
        if angle <= 90+ config.LANE_SEGMENT_ANGLE:
            # is left of
            is_left_of = angles[index][0]
            data_index = angles[prev][0]
            incoming_data[data_index].update({'isLeftOf': [incoming_data_id[is_left_of]]})
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
                 intersections: List[Intersection] = None,):
        """

        :param nodes: List of nodes in the format
        :param edges: List of edges representing the roads
        :param traffic_signs: List of traffic signs on the map
        :param obstacles: List of obstacles
        """

        self.nodes = nodes
        self.edges = edges
        self.intersections = intersections
        self.traffic_signs = traffic_signs
        self.traffic_lights = traffic_lights
        self.obstacles = obstacles


    def find_edge_by_id(self, id):
        for edge in self.edges:
            if edge.id == id:
                return edge

    def find_traffic_sign_by_id(self, id):
        for sign in self.traffic_signs:
            if sign.traffic_sign_id == id:
                return sign

    @staticmethod
    def get_direction(a, b):
        a_angle = geometry.curvature(a)
        b_angle = geometry.curvature(b)
        angle = a_angle - b_angle
        forward = True
        m = geometry.get_gradient(a)
        if m<0:
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
        intersections = {}
        added_lanes = set()
        for lane in graph.lanelinks:
            node = lane.to_node
            if node.get_degree() > 2:
                incoming = [p for p in lane.predecessors if p.id not in added_lanes]
                incoming_element = {'incomingLanelet': set([incoming_lane.id for incoming_lane in incoming]),
                                    'right': [],
                                    'left': [],
                                    'through': [],
                                    'none': [],
                                    'isLeftOf':[],
                                    'waypoints': []}
                for incoming_lane in incoming:
                    directions = incoming_lane.turnlane.split(";")
                    if incoming_element['waypoints'] == []:
                        incoming_element['waypoints'] = incoming_lane.waypoints
                    for direction in directions:
                        if direction == 'none':
                            for s in incoming_lane.successors:
                                angle = IntermediateFormat.get_direction(incoming_lane.waypoints,
                                                                         s.waypoints)
                                incoming_element[angle].append(s.id)
                        else:
                            incoming_element[direction].extend([s.id for s in incoming_lane.successors])
                    if node.id in intersections:
                        # update
                        intersections[node.id]['incoming'].append(incoming_element)
                    else:
                        intersections[node.id] = \
                            {'incoming': [incoming_element]}
                    added_lanes = added_lanes.union(incoming_element['incomingLanelet'])


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
                is_left_of = set(incoming['isLeftOf'])
                incoming_element = IntersectionIncomingElement(incoming_ids[index],
                                                               incoming_lanelets,
                                                               successors_right,
                                                               successors_straight,
                                                               successors_left,
                                                               is_left_of
                                                               )
                incoming_elements.append(incoming_element)
                index+=1

            intersections_cr.append(Intersection(idgenerator.get_id(), incoming_elements))
        return intersections_cr

    def to_commonroad_scenario(self):
        scenario = Scenario(config.TIMESTEPSIZE, config.BENCHMARK_ID)
        net = LaneletNetwork()
        for edge in self.edges:
            lanelet = edge.to_lanelet()
            net.add_lanelet(lanelet)

        for sign in self.traffic_signs:
            net.add_traffic_sign(sign, set())

        for light in self.traffic_lights:
            net.add_traffic_light(light, set())

        for intersection in self.intersections:
            net.add_intersection(intersection)

        scenario.lanelet_network = net
        return scenario

    @staticmethod
    def extract_road_graph(graph: Graph):
        road_graph = graph
        nodes = [Node(node.id, node.get_point()) for node in road_graph.nodes]
        edges = []
        lanes = graph.get_all_lanes()
        for lane in lanes:
            edge = Edge.extract_from_lane(lane)
            edges.append(edge)
        IntermediateFormat.get_intersections(graph)
        traffic_signs = [sign.to_traffic_sign_cr() for sign in graph.traffic_signs]
        traffic_lights = [light.to_traffic_light_cr() for light in graph.traffic_lights]
        intersections = IntermediateFormat.get_intersections(graph)
        return IntermediateFormat(nodes,
                                  edges,
                                  traffic_signs,
                                  traffic_lights,
                                  intersections=intersections)


    def get_obstacles(self):
        pass


    def get_sumo(self):
        s =Sumo(self)
        s.write_net('files/sumo/')