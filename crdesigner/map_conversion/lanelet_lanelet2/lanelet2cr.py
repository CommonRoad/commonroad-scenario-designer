# -*- coding: utf-8 -*-

"""Logic to convert OSM to lanelets."""

__author__ = "Benjamin Orthen, Sebastian Maierhofer"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "0.2"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad@lists.lrz.de"
__status__ = "Released"

from collections import defaultdict
from typing import List, Tuple

import numpy as np
from pyproj import Proj

from commonroad.scenario.lanelet import StopLine, LineMarking, RoadUser, Lanelet
from commonroad.scenario.traffic_sign import TrafficSignIDGermany, TrafficSignElement
from shapely.geometry import LineString

from commonroad.scenario.scenario import Scenario, ScenarioID, TrafficSign

from crdesigner.map_conversion.common.utils import generate_unique_id
from crdesigner.map_conversion.opendrive.opendrive_conversion.conversion_lanelet import ConversionLanelet
from crdesigner.map_conversion.opendrive.opendrive_conversion.conversion_lanelet_network import \
    ConversionLaneletNetwork, convert_to_new_lanelet_id
from crdesigner.map_conversion.lanelet_lanelet2.lanelet2 import OSMLanelet, WayRelation, DEFAULT_PROJ_STRING, Node, \
    RightOfWayRelation
from crdesigner.map_conversion.osm2cr.converter_modules.utility.geometry import (
    point_to_line_distance,
    distance as point_to_polyline_distance
)

NODE_DISTANCE_TOLERANCE = 0.01  # this is in meters
PRIORITY_SIGNS = [TrafficSignIDGermany.PRIORITY, TrafficSignIDGermany.RIGHT_OF_WAY]
# removed TrafficSignIDGermany.RIGHT_BEFORE_LEFT

ADJACENT_WAY_DISTANCE_TOLERANCE = 0.05


def _add_closest_traffic_sign_to_lanelet(lanelets: List[Lanelet], traffic_signs: List[TrafficSign]):
    """
    Assumes that it is given traffic signs and lanelets that should get matched (all to each)
    Each lanelet gets assigned exactly the single traffic sign closest to it
    Does nothing if the list of traffic signs is empty
    :return: the traffic signs that were assigned to any lanelet
    """
    used_signs = set()
    for l in lanelets:
        closest_traffic_sign = None
        _min_distance = None
        for t in traffic_signs:
            distance = point_to_polyline_distance(t.position, l.center_vertices)
            if _min_distance is None or distance < _min_distance:
                _min_distance = distance
                closest_traffic_sign = t
        if closest_traffic_sign is not None:
            l.add_traffic_sign_to_lanelet(closest_traffic_sign.traffic_sign_id)
            used_signs.add(closest_traffic_sign)
    return used_signs


def _add_stop_line_to_lanelet(lanelets: List[Lanelet], stop_lines: List[StopLine]):
    """
    Assigns each lanelet the first stop line that it is found to intersect with
    Several lanelets may end up getting assigned the same stop line
    :param lanelets:
    :param stop_lines:
    :return:
    """
    yield_signs = set()
    for la in lanelets:
        for s in stop_lines:
            if la.polygon.shapely_object.intersects(LineString([s.start, s.end])):
                la.stop_line = s
                # add the stop line traffic sign to the lanelet if set
                if s.traffic_sign_ref is not None:
                    la.traffic_signs.update(s.traffic_sign_ref)
                    yield_signs.update(s.traffic_sign_ref)
                break
    return yield_signs


class Lanelet2CRConverter:
    """Class to convert OSM to the Commonroad representation of Lanelets."""

    def __init__(self, proj_string: str = None):
        if proj_string:
            self.proj = Proj(proj_string)
        else:
            self.proj = Proj(DEFAULT_PROJ_STRING)
        self._left_way_ids, self._right_way_ids = None, None
        self.first_left_pts, self.last_left_pts = None, None
        self.first_right_pts, self.last_right_pts = None, None
        self.osm = None
        self.lanelet_network = None

    def __call__(
            self,
            osm: OSMLanelet,
            detect_adjacencies: bool = True,
            left_driving_system: bool = False,
    ) -> Scenario:
        """Convert OSM to Scenario.

        For each lanelet in OSM format, we have to save their first and last
        point of the left and right boundaries to determine their predecessors,
        successors and adjacent neighbors.

        Args:
          osm: OSM object which includes nodes, ways and lanelet relations.
          detect_adjacencies: Compare vertices which might be adjacent. Set
            to false if you consider it too computationally intensive.
          left_driving_system: Set to true if map describes a left_driving_system.

        Returns:
          A scenario with a lanelet network which describes the
            same map as the osm input.
        """
        # dicts to save relation of nodes to ways and lanelets
        # so the adjacencies can be determined
        self.osm = osm
        self._left_way_ids, self._right_way_ids = defaultdict(list), defaultdict(list)
        self.first_left_pts, self.last_left_pts = defaultdict(list), defaultdict(list)
        self.first_right_pts, self.last_right_pts = defaultdict(list), defaultdict(list)

        # TODO create default scenario ID or implement workaround in commonroad-io
        scenario_id = ScenarioID(country_id="ZAM", map_name="OpenDrive", map_id=123)

        scenario = Scenario(dt=0.1, scenario_id=scenario_id)
        self.lanelet_network = ConversionLaneletNetwork()

        speed_limits = {}
        speed_limit_lanelets = {}
        for speed_limit_key in osm.speed_limit_signs.keys():
            light_id = generate_unique_id()
            speed_limits[speed_limit_key] = light_id
            speed_limit_lanelets[speed_limit_key] = []
            # scenario.add_objects(speed_limit)

        for way_rel in osm.way_relations.values():
            # add traffic sign id to traffic signs for speed limit
            # create dictionary for mapping of osm id to cr id and keep id constant
            # later add speed limit as traffic sign
            lanelet = self._way_rel_to_lanelet(
                way_rel, detect_adjacencies, left_driving_system, speed_limits, speed_limit_lanelets
            )
            if lanelet is not None:
                self.lanelet_network.add_lanelet(lanelet)

        new_ids = self.lanelet_network.convert_all_lanelet_ids()

        for right_of_way_rel in osm.right_of_way_relations.values():
            # TODO convert Lanelet2 to CR and add to network
            try:
                yield_signs, priority_signs, yield_lanelets, priority_lanelets, stop_lines = (
                    self._right_of_way_to_traffic_sign(right_of_way_rel, new_ids)
                )
                # match traffic signs on the matching lanelets
                # the overwrite makes sure we only add traffic signs in the network that are assigned to any lanelet
                yield_signs_lanelets = _add_closest_traffic_sign_to_lanelet([self.lanelet_network.find_lanelet_by_id(i)
                                                                             for i in yield_lanelets], yield_signs)
                priority_signs = _add_closest_traffic_sign_to_lanelet([self.lanelet_network.find_lanelet_by_id(i)
                                                                       for i in priority_lanelets], priority_signs)
                # match stop lines on the yield lanelets
                yield_signs_stop_lines_id = _add_stop_line_to_lanelet([self.lanelet_network.find_lanelet_by_id(i)
                                                                       for i in yield_lanelets], stop_lines)
                # add any used traffic sign
                for s in (priority_signs | yield_signs_lanelets | {
                    y for y in yield_signs
                    if y.traffic_sign_id in yield_signs_stop_lines_id
                }):
                    self.lanelet_network.add_traffic_sign(s, set())
            except NotImplementedError as e:
                print(str(e))

        # TODO convert traffic signs as well
        for speed_limit_key in osm.speed_limit_signs.keys():
            speed, traffic_sign_id = osm.speed_limit_signs[speed_limit_key]
            light_id = speed_limits[speed_limit_key]
            first_occurrence = set([self.lanelet_network._old_lanelet_ids[l_id]
                                    for l_id in speed_limit_lanelets[speed_limit_key]])
            # TODO find better way to position speed limit
            position = self.lanelet_network.find_lanelet_by_id(
                self.lanelet_network._old_lanelet_ids[speed_limit_lanelets[speed_limit_key][0]]).left_vertices[0]
            speed_limit = TrafficSign(light_id, [TrafficSignElement(traffic_sign_id, [speed])], first_occurrence,
                                      position, True)
            self.lanelet_network.add_traffic_sign(speed_limit, first_occurrence)
            # scenario.add_objects(speed_limit, first_occurrence)

        scenario.add_objects(self.lanelet_network)

        return scenario

    def _right_of_way_to_traffic_sign(self, right_of_way_rel: RightOfWayRelation, new_lanelet_ids: dict):
        """
        one right_of_way regulatory element maps pretty well into commonroad scenarios
        it contains
         - a set of traffic signs active at the intersection (generally stop, yield, priority, ...)
         - a set of last lanelets before the beginning of the intersection that have
          - to yield
          - the right of way
         - a set of stop lines where vehicles crossing the yield line have to stop at

        This will be converted as follows:
         - the set of traffic signs is converted to a number of traffic signs
           - yield lanelet get assigned the yield traffic sign closest to them
                in different code -> return yield traffic signs
           - priority lanelets get assigned the priority traffic sign closest to them
                in different code -> return priority traffic signs
         - the stop lines are converted to stop lines
           - they are assigned to the closest yield traffic sign if any
           - they are assigned to the lanelets that overlap with the stop line
                in different code -> return stop lines

        The IDs of returned objects are converted according to the passed set of existing lanelet id conversions
        """
        priority_signs, yield_signs = [], []

        traffic_sign_ways = [self.osm.find_way_by_id(r) for r in right_of_way_rel.refers]
        # traffic signs will always be "ways"
        # https://github.com/fzi-forschungszentrum-informatik/Lanelet2/blob/master/lanelet2_core/doc/LinestringTagging.md
        for traffic_sign_way in traffic_sign_ways:
            traffic_sign_type = traffic_sign_way.tag_dict.get("subtype")
            virtual = traffic_sign_way.tag_dict.get("virtual", "no") == "yes"
            traffic_sign_node = self.osm.find_node_by_id(traffic_sign_way.nodes[0])

            # distinguish yield and stop sign
            # also handles right of way and priority road
            # todo internationalize
            if traffic_sign_type == "de206":
                tsid = TrafficSignIDGermany.STOP
            elif traffic_sign_type == "de205":
                tsid = TrafficSignIDGermany.YIELD
            elif traffic_sign_type == "de301" or traffic_sign_type == 'right_of_way':
                tsid = TrafficSignIDGermany.RIGHT_OF_WAY
            elif traffic_sign_type == "de306":
                tsid = TrafficSignIDGermany.PRIORITY
            elif traffic_sign_type == "de102":
                tsid = TrafficSignIDGermany.RIGHT_BEFORE_LEFT
            else:
                raise NotImplementedError(f"Lanelet type {traffic_sign_way.tag_dict['subtype']} not implemented")
            traffic_sign_element = TrafficSignElement(tsid, [])

            # extract position
            x, y = self.proj(float(traffic_sign_node.lon), float(traffic_sign_node.lat))

            ref_t_id = convert_to_new_lanelet_id(traffic_sign_way.id_, new_lanelet_ids)
            traffic_sign = TrafficSign(ref_t_id,
                                       traffic_sign_elements=[traffic_sign_element],
                                       first_occurrence=set(),
                                       position=np.array([x, y]),
                                       virtual=virtual)
            if tsid in PRIORITY_SIGNS:
                priority_signs.append(traffic_sign)
            else:
                yield_signs.append(traffic_sign)

        priority_lanelets = []
        for i in right_of_way_rel.right_of_ways:
            # never create new lanelet ids here,
            # if they don't exist yet, they are never created
            if i in new_lanelet_ids.keys():
                priority_lanelets.append(new_lanelet_ids[i])
            else:
                print(f"Warning: some priority sign references non-existing lanelet {i}")
        yield_lanelets = []
        for i in right_of_way_rel.yield_ways:
            # never create new lanelet ids here,
            # if they don't exist yet, they are never created
            if i in new_lanelet_ids.keys():
                yield_lanelets.append(new_lanelet_ids[i])
            else:
                print(f"Warning: some yield sign references non-existing lanelet {i}")

        stop_lines = []
        for stop_line in right_of_way_rel.ref_line:
            # extract geometrical features
            stop_line_way = self.osm.find_way_by_id(stop_line)
            stop_line_way_vertices = self._convert_way_to_vertices(stop_line_way)
            start = stop_line_way_vertices[0]
            end = stop_line_way_vertices[-1]

            # retrieve closest yield traffic sign if any
            ref_t_id = None
            _ref_t_min_dist = None
            for ref_t in yield_signs:
                d = point_to_line_distance(ref_t.position, start, end)
                if _ref_t_min_dist is None or d < _ref_t_min_dist:
                    ref_t_id = {ref_t.traffic_sign_id}
                    _ref_t_min_dist = d

            # initialize stop line
            stop_line = StopLine(
                start=start,
                end=end,
                traffic_sign_ref=ref_t_id,
                # TODO distinguish linemarking types
                line_marking=LineMarking.BROAD_DASHED
            )
            stop_lines.append(stop_line)
        return yield_signs, priority_signs, yield_lanelets, priority_lanelets, stop_lines

    def _way_rel_to_lanelet(
            self,
            way_rel: WayRelation,
            detect_adjacencies: bool,
            left_driving_system: bool = False,
            speed_limit_dict: dict = {},
            speed_limit_lanelts: dict = {},
    ) -> ConversionLanelet:
        """Convert a WayRelation to a Lanelet, add additional adjacency information.

        The ConversionLaneletNetwork saves the adjacency and predecessor/successor
        information.

        Args:
          way_rel: Relation of OSM to convert to Lanelet.
          osm: OSM object which contains info about nodes and ways.
          detect_adjacencies: Compare vertices which might be adjacent. Set
            to false if you consider it too computationally intensive.
          left_driving_system: Set to true if map describes a left_driving_system.
          speed_limit_dict: Dictionary with reglatory_element_id to TrafficSign mapping
          speed_limit_lanelts: mapping from speed_limit_ids to lanelets that use speed Limit

        Returns:
          A lanelet with a right and left vertice.
        """
        left_way = self.osm.find_way_by_id(way_rel.left_way)
        right_way = self.osm.find_way_by_id(way_rel.right_way)
        if len(left_way.nodes) != len(right_way.nodes):
            print(f"Trying to fix relation {way_rel.id_}...")
            self._fix_relation_unequal_ways(left_way, right_way)

        # If for some reason, relation couldn't be fixed, notify user
        if len(left_way.nodes) != len(right_way.nodes):
            print(
                f"Error: Relation {way_rel.id_} has left and right ways which are not equally long! "
                f"Please check your data! Discarding this lanelet relation."
            )
            return None

        # set only if not set before
        # one way can only have two lanelet relations which use it
        if not self._left_way_ids.get(way_rel.left_way):
            self._left_way_ids[way_rel.left_way] = way_rel.id_
        if not self._right_way_ids.get(way_rel.right_way):
            self._right_way_ids[way_rel.right_way] = way_rel.id_

        left_vertices = self._convert_way_to_vertices(left_way)
        first_left_node = left_way.nodes[0]
        last_left_node = left_way.nodes[-1]

        right_vertices = self._convert_way_to_vertices(right_way)
        first_right_node = right_way.nodes[0]
        last_right_node = right_way.nodes[-1]

        start_dist = np.linalg.norm(
            left_vertices[0] - right_vertices[0]
        ) + np.linalg.norm(left_vertices[-1] - right_vertices[-1])
        end_dist = np.linalg.norm(
            left_vertices[0] - right_vertices[-1]
        ) + np.linalg.norm(left_vertices[-1] - right_vertices[0])
        if start_dist > end_dist:
            if left_driving_system:
                # reverse right vertices if right_way is reversed
                right_vertices = right_vertices[::-1]
                first_right_node, last_right_node = (last_right_node, first_right_node)
            else:
                # reverse left vertices if left_way is reversed
                left_vertices = left_vertices[::-1]
                first_left_node, last_left_node = (last_left_node, first_left_node)
        self.first_left_pts[first_left_node].append(way_rel.id_)
        self.last_left_pts[last_left_node].append(way_rel.id_)
        self.first_right_pts[first_right_node].append(way_rel.id_)
        self.last_right_pts[last_right_node].append(way_rel.id_)

        center_vertices = np.array(
            [(l + r) / 2 for (l, r) in zip(left_vertices, right_vertices)]
        )

        # niels change
        # extract special meaning like one way, road type
        lanelet_type = None
        users_one_way = set()
        users_bidirectional = set()
        one_way_val = way_rel.tag_dict.get("one_way")
        bidirectional, one_way = one_way_val == "no", one_way_val == "yes"
        if way_rel.tag_dict.get("bicycle") == "yes":
            if one_way:
                users_one_way.add(RoadUser.BICYCLE)
            else:
                users_bidirectional.add(RoadUser.BICYCLE)
        subtype = way_rel.tag_dict.get("subtype")
        if subtype == "bicycle_lane" or subtype == "shared_walkway" or subtype == "road":
            users_one_way.add(RoadUser.BICYCLE)
            if subtype != "road":
                lanelet_type = 'biking'
        if subtype == "walkway" or subtype == "shared_walkway":
            users_bidirectional.add(RoadUser.PEDESTRIAN)
            lanelet_type = "sidewalk"
        if subtype == "crosswalk":
            users_bidirectional.add(RoadUser.PEDESTRIAN)
            lanelet_type = "crosswalk"
        if subtype == "bus_lane":
            users_one_way.add(RoadUser.BUS)
            lanelet_type = "bus"
        if subtype == "road" or subtype == "highway":
            if bidirectional:
                users_bidirectional.add(RoadUser.CAR)
                users_bidirectional.add(RoadUser.MOTORCYCLE)
            else:
                users_one_way.add(RoadUser.CAR)
                users_one_way.add(RoadUser.MOTORCYCLE)
            location_val = way_rel.tag_dict.get("location")
            if subtype == "highway":
                lanelet_type = "highway"
            elif location_val == "nonurban":
                lanelet_type = 'country'
            else:
                # todo default because of inD origin
                lanelet_type = 'urban'

        users_bidirectional.add(RoadUser.PRIORITY_VEHICLE)

        traffic_signs = []
        for key in way_rel.regulatory_elements:
            if not speed_limit_dict.get(key) is None:
                traffic_signs.append(speed_limit_dict[key])
                speed_limit_lanelts[key].append(way_rel.id_)

        if len(traffic_signs) == 0:
            traffic_signs = None
        else:
            traffic_signs = set(traffic_signs)

        lanelet = ConversionLanelet(
            left_vertices=left_vertices,
            center_vertices=center_vertices,
            right_vertices=right_vertices,
            lanelet_id=way_rel.id_,
            parametric_lane_group=None,
            user_one_way=users_one_way,
            user_bidirectional=users_bidirectional,
            lanelet_type=lanelet_type,
            traffic_signs=traffic_signs
        )

        self._check_right_and_left_neighbors(way_rel, lanelet)

        if detect_adjacencies:
            self._find_adjacencies_of_coinciding_ways(
                lanelet,
                first_left_node,
                first_right_node,
                last_left_node,
                last_right_node,
            )

        potential_successors = self._check_for_successors(
            last_left_node=last_left_node, last_right_node=last_right_node
        )
        self.lanelet_network.add_successors_to_lanelet(lanelet, potential_successors)

        potential_predecessors = self._check_for_predecessors(
            first_left_node=first_left_node, first_right_node=first_right_node
        )
        self.lanelet_network.add_predecessors_to_lanelet(
            lanelet, potential_predecessors
        )

        potential_adj_left, potential_adj_right = self._check_for_split_and_join_adjacencies(
            first_left_node, first_right_node, last_left_node, last_right_node
        )
        if potential_adj_left:
            self.lanelet_network.set_adjacent_left(lanelet, potential_adj_left[0], True)
        if potential_adj_right:
            self.lanelet_network.set_adjacent_right(
                lanelet, potential_adj_right[0], True
            )

        return lanelet

    def _fix_relation_unequal_ways(self, left_way, right_way):
        # Try to fix by adding some nodes by interpolation in the way with the least nodes...
        # TODO: Maybe we should try to add the extra nodes close to the zone
        #  where the other way has extra nodes? Or distribute evenly...
        # For now, add between two central nodes
        if (len(left_way.nodes) == len(right_way.nodes)):
            return
        if (len(left_way.nodes) < len(right_way.nodes)):
            n = len(right_way.nodes) - len(left_way.nodes)
            # Coordinates of two nodes in the middle to interpolate and add n nodes in between
            mid = int(len(left_way.nodes) / 2)
            start_node = self.osm.find_node_by_id(left_way.nodes[mid])
            end_node = self.osm.find_node_by_id(left_way.nodes[mid - 1])
            # Parse to nodes with numeric values
            start_node_f = np.array([float(start_node.lat), float(start_node.lon)])
            end_node_f = np.array([float(end_node.lat), float(end_node.lon)])
            # Add n nodes, start from last one
            for i in range(n, 0, -1):
                # TODO: What to do with the node id? For now add some big number to start node id
                k = 10
                new_id = int(start_node.id_) + k * 100 + i
                while self.osm.find_node_by_id(str(new_id)) is not None:
                    k = k + 1
                    new_id = int(start_node.id_) + k * 100 + i
                # For Getting n additional nodes, we need to split the segment into n+1 smaller segments
                new_lat = round(start_node_f[0] + (end_node_f[0] - start_node_f[0]) * i / (n + 1), 11)
                new_lon = round(start_node_f[1] + (end_node_f[1] - start_node_f[1]) * i / (n + 1), 11)
                new_node = Node(new_id, new_lat, new_lon)
                self.osm.add_node(new_node)
                left_way.nodes.insert(mid, new_node.id_)
        else:
            n = len(left_way.nodes) - len(right_way.nodes)
            # Coordinates of two nodes in the middle to interpolate and add n nodes in between
            mid = int(len(right_way.nodes) / 2)
            start_node = self.osm.find_node_by_id(right_way.nodes[mid])
            end_node = self.osm.find_node_by_id(right_way.nodes[mid - 1])
            # Parse to nodes with numeric values
            start_node_f = np.array([float(start_node.lat), float(start_node.lon)])
            end_node_f = np.array([float(end_node.lat), float(end_node.lon)])
            # Add n nodes, start from last one
            for i in range(n, 0, -1):
                # TODO: What to do with the node id? For now add some big number to start node id
                k = 10
                new_id = int(start_node.id_) + k * 100 + i
                while self.osm.find_node_by_id(str(new_id)) is not None:
                    k = k + 1
                    new_id = int(start_node.id_) + k * 100 + i
                # For Getting n additional nodes, we need to split the segment into n+1 smaller segments
                new_lat = round(start_node_f[0] + (end_node_f[0] - start_node_f[0]) * i / (n + 1), 11)
                new_lon = round(start_node_f[1] + (end_node_f[1] - start_node_f[1]) * i / (n + 1), 11)
                new_node = Node(new_id, new_lat, new_lon)
                self.osm.add_node(new_node)
                right_way.nodes.insert(mid, new_node.id_)

    def _check_for_split_and_join_adjacencies(
            self, first_left_node, first_right_node, last_left_node, last_right_node
    ) -> Tuple[List, List]:
        """Check if there are adjacencies if there is a lanelet split or join.

        joining and splitting lanelets have to be adjacent rights or lefts
        splitting lanelets share both starting points and one last point
        joining lanelets share two last points and one start point

        Args:
          first_left_node: First node of left way of the lanelet.
          first_right_node: First node of right way of the lanelet.
          last_left_node: Last node of left way of the lanelet.
          last_right_node: Last node of right way of the lanelet.

        Returns:
          A tuple of lists which contain candidates for the
          left and the right adjacency.
        """
        potential_split_start_left = self._find_lanelet_ids_of_suitable_nodes(
            self.first_left_pts, first_left_node
        )
        potential_split_start_right = self._find_lanelet_ids_of_suitable_nodes(
            self.first_right_pts, first_right_node
        )
        potential_split_end_left = self._find_lanelet_ids_of_suitable_nodes(
            self.last_right_pts, last_left_node
        )
        potential_split_end_right = self._find_lanelet_ids_of_suitable_nodes(
            self.last_left_pts, last_right_node
        )

        potential_adj_left = list(
            set(potential_split_start_left)
            & set(potential_split_start_right)
            & set(potential_split_end_left)
        )
        potential_adj_right = list(
            set(potential_split_start_left)
            & set(potential_split_start_right)
            & set(potential_split_end_right)
        )

        if not potential_adj_left or not potential_adj_right:
            potential_join_end_left = self._find_lanelet_ids_of_suitable_nodes(
                self.last_left_pts, last_left_node
            )
            potential_join_end_right = self._find_lanelet_ids_of_suitable_nodes(
                self.last_right_pts, last_right_node
            )

            if not potential_adj_left:
                potential_join_start_left = self._find_lanelet_ids_of_suitable_nodes(
                    self.first_right_pts, first_left_node
                )
                potential_adj_left = list(
                    set(potential_join_start_left)
                    & set(potential_join_end_left)
                    & set(potential_join_end_right)
                )

            if not potential_adj_right:
                potential_join_start_right = self._find_lanelet_ids_of_suitable_nodes(
                    self.first_left_pts, first_right_node
                )
                potential_adj_right = list(
                    set(potential_join_start_right)
                    & set(potential_join_end_left)
                    & set(potential_join_end_right)
                )

        return potential_adj_left, potential_adj_right

    def _check_for_predecessors(
            self, first_left_node: str, first_right_node: str
    ) -> List:

        """Check whether the first left and right node are last nodes of another lanelet.

        Args:
          first_left_node: Id of a node which is at the start of the left way.
          first_right_node: Id of a node which is at the start of the right way.

        Returns:
          List of ids of lanelets where the nodes are at their end.
        """
        potential_left_predecessors = self._find_lanelet_ids_of_suitable_nodes(
            self.last_left_pts, first_left_node
        )
        potential_right_predecessors = self._find_lanelet_ids_of_suitable_nodes(
            self.last_right_pts, first_right_node
        )
        if potential_left_predecessors and potential_right_predecessors:
            potential_predecessors = list(
                set(potential_left_predecessors) & set(potential_right_predecessors)
            )
            return potential_predecessors

        return []

    def _check_for_successors(self, last_left_node: str, last_right_node: str) -> List:
        """Check whether the last left and right node are first nodes of another lanelet.

        Args:
          last_left_node: Id of a node which is at the end of the left way.
          last_right_node: Id of a node which is at the end of the right way.

        Returns:
          List of ids of lanelets where the nodes are at their start.
        """

        potential_left_successors = self._find_lanelet_ids_of_suitable_nodes(
            self.first_left_pts, last_left_node
        )
        potential_right_successors = self._find_lanelet_ids_of_suitable_nodes(
            self.first_right_pts, last_right_node
        )
        if potential_left_successors and potential_right_successors:
            potential_successors = list(
                set(potential_left_successors) & set(potential_right_successors)
            )
            return potential_successors

        return []

    def _find_adjacencies_of_coinciding_ways(
            self,
            lanelet: ConversionLanelet,
            first_left_node: str,
            first_right_node: str,
            last_left_node: str,
            last_right_node: str,
    ):
        """Find adjacencies of a lanelet by checking if its vertices coincide with vertices of other lanelets.

        Set new adjacent left or right if it finds neighbors.

        Args:
          lanelet: Lanelet to check potential adjacencies for.
          first_left_node: Id of first left node of the lanelet relation in OSM.
          first_right_node: Id of first right node of the lanelet relation in OSM.
          last_left_node: Id of last left node of the lanelet relation in OSM.
          last_right_node: Id of last right node of the lanelet relation in OSM.

        """
        # first case: left adjacent, same direction
        if lanelet.adj_left is None:
            potential_left_front = self._find_lanelet_ids_of_suitable_nodes(
                self.first_right_pts, first_left_node
            )
            potential_left_back = self._find_lanelet_ids_of_suitable_nodes(
                self.last_right_pts, last_left_node
            )
            potential_left_same_direction = list(
                set(potential_left_front) & set(potential_left_back)
            )
            for lanelet_id in potential_left_same_direction:
                nb_lanelet = self.lanelet_network.find_lanelet_by_id(lanelet_id)
                if nb_lanelet is not None and _two_vertices_coincide(
                        lanelet.left_vertices, nb_lanelet.right_vertices
                ):
                    self.lanelet_network.set_adjacent_left(
                        lanelet, nb_lanelet.lanelet_id, True
                    )
                    break

        # second case: right adjacent, same direction
        if lanelet.adj_right is None:
            potential_right_front = self._find_lanelet_ids_of_suitable_nodes(
                self.first_left_pts, first_right_node
            )
            potential_right_back = self._find_lanelet_ids_of_suitable_nodes(
                self.last_left_pts, last_right_node
            )
            potential_right_same_direction = list(
                set(potential_right_front) & set(potential_right_back)
            )
            for lanelet_id in potential_right_same_direction:
                nb_lanelet = self.lanelet_network.find_lanelet_by_id(lanelet_id)
                if nb_lanelet is not None and _two_vertices_coincide(
                        lanelet.right_vertices, nb_lanelet.left_vertices
                ):
                    self.lanelet_network.set_adjacent_right(
                        lanelet, nb_lanelet.lanelet_id, True
                    )
                    break

        # third case: left adjacent, opposite direction
        if lanelet.adj_left is None:
            potential_left_front = self._find_lanelet_ids_of_suitable_nodes(
                self.last_left_pts, first_left_node
            )
            potential_left_back = self._find_lanelet_ids_of_suitable_nodes(
                self.first_left_pts, last_left_node
            )
            potential_left_other_direction = list(
                set(potential_left_front) & set(potential_left_back)
            )
            for lanelet_id in potential_left_other_direction:
                nb_lanelet = self.lanelet_network.find_lanelet_by_id(lanelet_id)
                # compare right vertice of nb_lanelet with left vertice of lanelet
                if nb_lanelet is not None and _two_vertices_coincide(
                        lanelet.left_vertices, nb_lanelet.left_vertices[::-1]
                ):
                    self.lanelet_network.set_adjacent_left(
                        lanelet, nb_lanelet.lanelet_id, False
                    )
                    break

        # fourth case: right adjacent, opposite direction
        if lanelet.adj_right is None:
            potential_right_front = self._find_lanelet_ids_of_suitable_nodes(
                self.last_right_pts, first_right_node
            )
            potential_right_back = self._find_lanelet_ids_of_suitable_nodes(
                self.first_right_pts, last_right_node
            )
            potential_right_other_direction = list(
                set(potential_right_front) & set(potential_right_back)
            )
            for lanelet_id in potential_right_other_direction:
                nb_lanelet = self.lanelet_network.find_lanelet_by_id(lanelet_id)
                if nb_lanelet is not None and _two_vertices_coincide(
                        lanelet.right_vertices, nb_lanelet.right_vertices[::-1]
                ):
                    self.lanelet_network.set_adjacent_right(
                        lanelet, nb_lanelet.lanelet_id, True
                    )
                    break

    def _check_right_and_left_neighbors(
            self, way_rel: WayRelation, lanelet: ConversionLanelet
    ):
        """check if lanelet has adjacent right and lefts.

        Determines it by checking if they share a common way.
        Either in opposite or in the same direction.

        Args:
          way_rel: Relation from which lanelet was created.
          lanelet: Lanelet for which to check adjacencies.
        """
        potential_right_adj = self._left_way_ids.get(way_rel.right_way)
        potential_left_adj = self._right_way_ids.get(way_rel.left_way)
        if potential_right_adj is not None:
            self.lanelet_network.set_adjacent_right(lanelet, potential_right_adj, True)

        if potential_left_adj is not None:
            self.lanelet_network.set_adjacent_left(lanelet, potential_left_adj, True)

        # check if there are adjacent right and lefts which share a same way
        # and are in the opposite direction
        if not potential_left_adj:
            potential_left_adj = self._left_way_ids.get(way_rel.left_way)
            if potential_left_adj is not None:
                self.lanelet_network.set_adjacent_left(
                    lanelet, potential_left_adj, False
                )

        if not potential_right_adj:
            potential_right_adj = self._right_way_ids.get(way_rel.right_way)
            if potential_right_adj is not None:
                self.lanelet_network.set_adjacent_right(
                    lanelet, potential_right_adj, False
                )

    def _convert_way_to_vertices(self, way) -> np.ndarray:
        """Convert a Way to a list of points.

        Args:
          way: Way to be converted.
          osm: OSM which includes the way and the nodes.
        Returns:
          The vertices of the new lanelet border.

        """
        vertices = np.empty((len(way.nodes), 2))
        for i, node_id in enumerate(way.nodes):
            nd = self.osm.find_node_by_id(node_id)
            x, y = self.proj(float(nd.lon), float(nd.lat))
            vertices[i] = [x, y]

        return vertices

    def node_distance(self, node_id1: str, node_id2: str) -> float:
        """Calculate distance of one node to other node in the projection.

        Args:
          node_id1: Id of first node.
          node_id2: id of second node.
        Returns:
          Distance in
        """
        node1 = self.osm.find_node_by_id(node_id1)
        node2 = self.osm.find_node_by_id(node_id2)
        vec1 = np.array(self.proj(float(node1.lon), float(node1.lat)))
        vec2 = np.array(self.proj(float(node2.lon), float(node2.lat)))
        return np.linalg.norm(vec1 - vec2)

    def _find_lanelet_ids_of_suitable_nodes(
            self, nodes_dict: dict, node_id: str
    ) -> List:
        """Find values of a dict where the keys are node ids.

        Return the entries if there is a value in the node_dict
        for the node_id, but also the values for nodes which are in
        the proximity of the node with the node_id.

        Args:
          nodes_dict: Dict which saves lanelet ids with node ids as keys.
          node_id: Id of node for which the other entries are searched for.
        Returns:
          List of lanelet ids which match the above-mentioned rules.
        """
        suitable_lanelet_ids = []
        suitable_lanelet_ids.extend(nodes_dict.get(node_id, []))
        for nd, lanelet_ids in nodes_dict.items():
            if self.node_distance(nd, node_id) < NODE_DISTANCE_TOLERANCE:
                suitable_lanelet_ids.extend(lanelet_ids)
        return suitable_lanelet_ids


def _two_vertices_coincide(
        vertices1: List[np.ndarray], vertices2: List[np.ndarray]
) -> bool:
    """Check if two vertices coincide and describe the same trajectory.

    For each vertice of vertices2 the minimal distance to the trajectory
    described by vertices1 is calculated. If this distance crosses a certain
    threshold, the vertices are deemed to be different.

    Args:
      vertices1: List of vertices which describe first trajectory.
      vertices2: List of vertices which describe second trajectory.

    Returns:
      True if the vertices coincide, else False.
    """
    segments = np.diff(vertices1, axis=0)

    for vert in vertices2:
        distances = np.empty([len(vertices1) + 1])
        distances[0] = np.linalg.norm(vert - vertices1[0])
        distances[-1] = np.linalg.norm(vert - vertices1[-1])
        for i, diff in enumerate(segments):
            distances[i + 1] = np.abs(
                np.cross(diff, vertices1[i] - vert)
            ) / np.linalg.norm(diff)
        if np.min(distances) > ADJACENT_WAY_DISTANCE_TOLERANCE:
            return False

    return True
