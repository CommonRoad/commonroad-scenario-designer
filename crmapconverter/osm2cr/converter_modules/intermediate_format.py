"""
This module holds the classes required for the intermediate format
"""

__author__ = "Behtarin Ferdousi, Fabian Höltke"

import copy
import numpy as np
from typing import List, Set, Dict
import warnings

from commonroad.scenario.lanelet import Lanelet, LaneletNetwork, LaneletType
from commonroad.scenario.obstacle import Obstacle
from commonroad.scenario.scenario import Scenario
from commonroad.scenario.traffic_sign import TrafficSign, TrafficLight
from commonroad.scenario.intersection import Intersection, IntersectionIncomingElement
from commonroad.planning.planning_problem import PlanningProblem, PlanningProblemSet
from commonroad.scenario.trajectory import State
from commonroad.planning.goal import GoalRegion
from commonroad.common.util import Interval
from commonroad.geometry.shape import Rectangle, Circle

from crmapconverter.osm2cr.converter_modules.graph_operations.road_graph import Graph
from crmapconverter.osm2cr import config
from crmapconverter.osm2cr.converter_modules.utility import geometry, idgenerator
from crmapconverter.osm2cr.converter_modules.utility.traffic_light_generator import TrafficLightGenerator

# mapping from crossed lanelet ids to the crossing ones
Crossings = Dict[int, Set[int]]


class Node:
    """
    Class to represent the nodes in the intermediate format
    """

    def __init__(self, node_id:int , point: geometry.Point):
        """
        Initialize a node element

        :param node_id: unique id for node
        :type node_id: int
        :param point: position of the node
        :type point: geometry.position
        """

        self.id = node_id
        self.point = point


def is_valid(lanelet):
    polygon = lanelet.convert_to_polygon().shapely_object
    if not polygon.is_valid:
        warnings.warn("Lanelet " + str(lanelet.lanelet_id) + " invalid")
        return False
    return True


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
                 traffic_lights: Set[int],
                 edge_type: str = config.LANELETTYPE):
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
        self.edge_type = edge_type

    def to_lanelet(self) -> Lanelet:
        """
        Converts to CommonRoad Lanelet object

        :return: CommonRoad Lanelet
        """
        lanelet = Lanelet(np.array(self.left_bound),
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
                          lanelet_type={LaneletType(self.edge_type)})
        is_valid(lanelet)
        return lanelet

    @staticmethod
    def extract_from_lane(lane) -> "Edge":
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

        traffic_lights = set()
        if lane.traffic_lights is not None:
            traffic_lights = {light.id for light in lane.traffic_lights}

        traffic_signs = set()
        if lane.traffic_signs is not None:
            traffic_signs = {sign.id for sign in lane.traffic_signs}

        from_node = Node(lane.from_node.id, lane.from_node.get_point())
        to_node = Node(lane.to_node.id, lane.to_node.get_point())

        return Edge(current_id, from_node, to_node, lane.left_bound, lane.right_bound, lane.waypoints, adjacent_right,
                    adjacent_right_direction_equal, adjacent_left, adjacent_left_direction_equal, successors,
                    predecessors, traffic_signs, traffic_lights)


def add_is_left_of(incoming_data, incoming_data_id):
    """
    Find and add isLeftOf property for the incomings

    :param incoming_data: incomings without isLeftOf
    :param incoming_data_id: List of the id of the incomings
    :return: incomings with the isLeftOf assigned
    """

    # choose a reference incoming vector
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
        
        # add is_left_of relation if angle is less than intersection straight treshold
        if angle <= 180 - config.INTERSECTION_STRAIGHT_THRESHOLD:
            # is left of the previous incoming
            is_left_of = angles[prev][0]
            data_index = angles[index][0]
            incoming_data[data_index].update({'isLeftOf': incoming_data_id[is_left_of]})
        
        prev = index

    return incoming_data


def get_lanelet_intersections(crossing_interm: "IntermediateFormat",
                              crossed_interm: "IntermediateFormat") -> Crossings:
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
            crossed_lanelet.convert_to_polygon())
        crossings[crossed_lanelet.lanelet_id] = set(crossing_lanelet_ids)
    return crossings


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
                 intersections: List[Intersection] = None):
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

        self.intersection_enhancement()

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
        Find traffic light by the sign id

        :param sign_id: sign id of the Traffic Light element
        :return: CommonRoad TrafficLight
        """
        for light in self.traffic_lights:
            if light.traffic_light_id == light_id:
                return light

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
            directions = {sorted_keys[0]: 'left', sorted_keys[1]: 'through', sorted_keys[2]: 'right'}

        # if 2 successors we assume that they both cannot have the same direction
        if len(sorted_angels) == 2:

            directions = dict.fromkeys(sorted_angels)

            if (abs(sorted_values[0]) > straight_threshold_angel) \
                    and (abs(sorted_values[1]) > straight_threshold_angel):
                directions[sorted_keys[0]] = 'left'
                directions[sorted_keys[1]] = 'right'
            elif abs(sorted_values[0]) < abs(sorted_values[1]):
                directions[sorted_keys[0]] = 'through'
                directions[sorted_keys[1]] = 'right'
            elif abs(sorted_values[0]) > abs(sorted_values[1]):
                directions[sorted_keys[0]] = 'left'
                directions[sorted_keys[1]] = 'through'
            else:
                directions[sorted_keys[0]] = 'through'
                directions[sorted_keys[1]] = 'through'

        # if we have 1 or more than 3 successors it's hard to make predictions,
        # therefore only straight_threshold_angel is used
        if len(sorted_angels) == 1 or len(sorted_angels) > 3:
            directions = dict.fromkeys(sorted_angels, 'through')
            for key in sorted_angels:
                if sorted_angels[key] < -straight_threshold_angel:
                    directions[key] = 'left'
                if sorted_angels[key] > straight_threshold_angel:
                    directions[key] = 'right'

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
            if (node.get_degree() > 2 or (node.is_crossing and node.get_degree() == 2)):
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
                        if incoming_lane.adjacent_left_direction_equal and left.id not in added_lanes:
                            lanes_to_add.append(left)
                            added_lanes.add(left.id)
                            left = left.adjacent_left
                        else:
                            left = None
                    while right:
                        if incoming_lane.adjacent_right_direction_equal and right.id not in added_lanes:
                            lanes_to_add.append(right)
                            added_lanes.add(right.id)
                            right = right.adjacent_right
                        else:
                            right = None

                incoming.extend(lanes_to_add)
                
                # Initialize incoming element with properties to be filled in
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
                            directions = IntermediateFormat.get_directions(incoming_lane)
                            for key in directions:
                                incoming_element[directions[key]].append(key)
                        else:
                            # TODO implement unknown direction keys
                            try:
                                incoming_element[direction].extend(
                                        [s.id for s in incoming_lane.successors])
                            except KeyError:
                                print('unknown intersection direction key: '+ direction)
                                # calculate the direction for each successor
                                directions = IntermediateFormat.get_directions(incoming_lane)
                                for key in directions:
                                    incoming_element[directions[key]].append(key)

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
            intersections_cr.append(Intersection(idgenerator.get_id(), incoming_elements))
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

        traffic_signs = [sign.to_traffic_sign_cr() for sign in graph.traffic_signs]

        traffic_lights = [light.to_traffic_light_cr() for light in graph.traffic_lights]

        intersections = IntermediateFormat.get_intersections(graph)



        return IntermediateFormat(nodes,
                                  edges,
                                  traffic_signs,
                                  traffic_lights,
                                  intersections=intersections)

    def get_dummy_planning_problem_set(self):
        """
        Creates a dummy planning problem set for the export to XML

        :return: Dummy planning problem set
        """
        pp_id = idgenerator.get_id()
        rectangle = Rectangle(4.3, 8.9, center=np.array([0.1, 0.5]), orientation=1.7)
        circ = Circle(2.0, np.array([0.0, 0.0]))
        goal_region = GoalRegion([State(time_step=Interval(0, 1), velocity=Interval(0.0, 1), position=rectangle),
                                  State(time_step=Interval(1, 2), velocity=Interval(0.0, 1), position=circ)])
        planning_problem = PlanningProblem(pp_id, State(velocity=0.1, position=np.array([[0], [0]]), orientation=0,
                                                       yaw_rate=0, slip_angle=0, time_step=0), goal_region)

        return PlanningProblemSet(list([planning_problem]))

    def remove_invalid_references(self):
        """
        remove references of traffic lights and signs that point to
        non existing elements.
        """
        traffic_light_ids = {tlight.traffic_light_id for tlight in
                        self.traffic_lights}
        traffic_sign_ids = {tsign.traffic_sign_id for tsign in
                        self.traffic_signs}
        for edge in self.edges:
            for t_light_ref in set(edge.traffic_lights):
                if not t_light_ref in traffic_light_ids:
                    edge.traffic_lights.remove(t_light_ref)
                    # print("removed traffic light ref", t_light_ref, "from edge",
                    #     edge.id)
            for t_sign_ref in set(edge.traffic_signs):
                if not t_sign_ref in traffic_sign_ids:
                    edge.traffic_signs.remove(t_sign_ref)
                    # print("removed traffic sign ref", t_sign_ref, "from lanelet",
                    #     edge.lanelet_id)

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

    def intersection_enhancement(self):
        """
        Enhance intersections with traffic lights. 
        Method will remove intersections found in osm and add its own instead.
        """

        def remove_non_intersection_lights(all_incoming_lanes_in_scenario):
            traffic_lights_on_intersections = []
            for incoming_lane in all_incoming_lanes_in_scenario:
                if incoming_lane.traffic_lights:
                    traffic_lights_on_intersections.extend(incoming_lane.traffic_lights)
            self.traffic_lights = list(filter(lambda x: x.traffic_light_id in traffic_lights_on_intersections, self.traffic_lights))

        def remove_existing_traffic_lights(incoming_lanes):
            for lane in incoming_lanes:
                if lane.traffic_lights:
                    for light_id in lane.traffic_lights:
                        light = self.find_traffic_light_by_id(light_id)
                        if light is not None:
                            self.traffic_lights.remove(light)
                lane.traffic_lights = set()

        def remove_innner_lights(intersection, incoming_lanes):
            remove = False
            for lane in incoming_lanes:
                if len(lane.predecessors) > 1 and geometry.distance(lane.center_points[0], [lane.center_points[-1]]) < 2: # shorter than 2 meters
                    remove = True
                    indicating_lane = lane.id
            if remove:
                for incoming in intersection.incomings:
                    for incoming_lane in incoming.incoming_lanelets:
                        if incoming_lane == indicating_lane:
                            for incoming_t in incoming.incoming_lanelets:
                                self.find_edge_by_id(incoming_t).traffic_lights = set()
  
        def create_new_traffic_lights(intersection):
            # create traffic light generator for intersection based on number of incomings
            traffic_light_generator = TrafficLightGenerator(len(intersection.incomings))

            # begin with incoming that is not left of any other
            left_of_map =  {}
            for incoming in intersection.incomings:
                left_of_map[incoming] = incoming.left_of

            incoming = None
            # try to find incoming that is not right of any other incoming (3 incomings)
            for key in left_of_map:
                if key.incoming_id not in left_of_map.values() and key.left_of is not None:
                    incoming = key
                    break
            # if unable to find any than begin with any other incoming (4 incomings)
            if incoming is None:
                incoming = intersection.incomings[0]
            processed_incomings = set()

            # loop over incomings
            while incoming is not None:

                if incoming in processed_incomings:
                    break

                # postition of traffic light
                for lane_id in incoming.incoming_lanelets:
                    edge = self.find_edge_by_id(lane_id)
                    if not edge.adjacent_right:
                        position_point = edge.right_bound[-1]
                        break

                # create new traffic light
                new_traffic_light = traffic_light_generator.generate_traffic_light(position=position_point, new_id=idgenerator.get_id())
                self.traffic_lights.append(new_traffic_light)

                # add reference to each incoming lane
                for lane_id in incoming.incoming_lanelets:
                    lane = self.find_edge_by_id(lane_id)
                    lane.traffic_lights.add(new_traffic_light.traffic_light_id)

                # process next left of current incoming
                processed_incomings.add(incoming)
                # new incoming is incoming with left_of id of current incoming, else None
                incoming = next((i for i in intersection.incomings if i.incoming_id == incoming.left_of), None)
                # edge case if only 2 incomings were found:
                if len(intersection.incomings) == 2:
                    incoming = intersection.incomings[-1]


        # keep track of all incoming lanes in scenario
        all_incoming_lanes_in_scenario = []

        # iterate over all intersections in scenario
        for intersection in self.intersections:
            has_traffic_lights = False
            incoming_lanes = []

            #find all incoming lanes in intersection and determine if they have traffic lights
            for incoming in intersection.incomings:
                for incoming_lane in incoming.incoming_lanelets:
                    lane = self.find_edge_by_id(incoming_lane)
                    if lane.traffic_lights:
                        has_traffic_lights = True
                    # also check up to 2 predecessors ahead of lane
                    pre1 = self.find_edge_by_id(lane.predecessors[0]) if len(lane.predecessors) == 1 else None
                    pre2 = self.find_edge_by_id(pre1.predecessors[0]) if pre1 and len(pre1.predecessors) == 1 else None
                    if pre1 and pre1.traffic_lights:
                        has_traffic_lights = True
                    if pre2 and pre2.traffic_lights:
                        has_traffic_lights = True
                        
                    incoming_lanes.append(lane)
            # extend all incoming lanes in scenario
            all_incoming_lanes_in_scenario.extend(incoming_lanes)

            # modify intersection if traffic lights where found, else skip to next intersection
            if has_traffic_lights:
                # remove existing traffic lights
                remove_existing_traffic_lights(incoming_lanes)
                # create new traffic lights
                create_new_traffic_lights(intersection)
                # remove inner traffic lights in the middle of bigger crossings
                remove_innner_lights(intersection, incoming_lanes)

        # remove traffic lights that are not part of any intersection
        remove_non_intersection_lights(all_incoming_lanes_in_scenario)
        # clean up and remove invalid references
        self.remove_invalid_references()
