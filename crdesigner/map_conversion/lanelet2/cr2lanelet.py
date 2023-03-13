from typing import List, Optional, Tuple, Union, Dict

import numpy as np
from pyproj import Proj
from commonroad.scenario.lanelet import Lanelet  # type: ignore
from commonroad.scenario.traffic_sign import TrafficLight, TrafficSign  # type: ignore
from crdesigner.map_conversion.lanelet2 import config

from crdesigner.map_conversion.lanelet2.lanelet2 import OSMLanelet, Node, Way, WayRelation, RegulatoryElement
from crdesigner.map_conversion.lanelet2.config import DEFAULT_PROJ_STRING


def _convert_subtype_names(subtype: str) -> [str, bool]:
    """
    Function that converts names of some subtypes that are slightly different
    in two formats.

    :param subtype: name of the subtype of the lanelet
    :return: name of the subtype (converted if needed) and the boolean value that states if the subtype corresponds
        to one of the possible L2 format subtypes
    """
    subtype_in = False
    if subtype in config.L2_LANELET_SUBTYPES:
        subtype_in = True
        if subtype == "urban" or subtype == "country":
            subtype = "road"
        elif subtype == "busLane":
            subtype = "bus_lane"
        elif subtype == "bicycleLane":
            subtype = "bicycle_lane"
        elif subtype == "exitRamp":
            subtype = "exit"
        elif subtype == "sidewalk":
            subtype = "walkway"
    return subtype, subtype_in


def _vertices_are_equal(vertices1: List[np.ndarray], vertices2: List[np.ndarray]) -> bool:
    """
    Checks if two list of vertices are equal up to a tolerance.

    :param vertices1: First vertices to compare.
    :param vertices2: Second vertices to compare.
    :return: True if every vertex in one list is nearly equal to the
        corresponding vertices at the same position in the other list.
    """
    if len(vertices1) != len(vertices2):
        return False
    diff = np.array(vertices1) - np.array(vertices2)
    if np.abs(np.max(diff)) < config.WAYS_ARE_EQUAL_TOLERANCE:
        return True
    return False


class CR2LaneletConverter:
    """
    Class to convert CommonRoad lanelet to the OSM representation.
    """

    def __init__(self, proj_string=None):
        """
        Initialization of CR2LaneletConverter
        
        :param proj_string: String name used for the initialization of the converter
        """
        if proj_string:
            self.proj = Proj(proj_string)
        else:
            self.proj = Proj(DEFAULT_PROJ_STRING)
        self.osm = None
        self._id_count = -1
        self.first_nodes, self.last_nodes = None, None
        self.left_ways, self.right_ways = None, None
        self.lanelet_network = None
        self.origin_utm = None

    @property
    def id_count(self) -> int:
        """
        Internal counter for giving IDs to the members of the OSM.
        Each call returns the count and increases it by one.

        :return: current id count.
        """
        tmp = self._id_count
        self._id_count -= 1
        return tmp

    def __call__(self, scenario):
        """
        Convert a scenario to an OSM xml document.

        :param scenario: Scenario that will be used for conversion
        """
        self.osm = OSMLanelet()
        self.lanelet_network = scenario.lanelet_network
        self.first_nodes = {}  # saves first left and right node | dict() but with a faster execution
        self.last_nodes = {}  # saves last left and right node
        self.left_ways = {}
        self.right_ways = {}
        if scenario.location is not None and not isinstance(scenario.location.gps_longitude, str) and\
                abs(scenario.location.gps_longitude) <= 180 and abs(scenario.location.gps_latitude) <= 90:
            self.origin_utm = self.proj(scenario.location.gps_longitude, scenario.location.gps_latitude)
        elif scenario.location is not None and isinstance(scenario.location.gps_longitude, str) and\
                abs(float(scenario.location.gps_longitude)) <= 180 and abs(float(scenario.location.gps_latitude)) <= 90:
            self.origin_utm = self.proj(float(scenario.location.gps_longitude), float(scenario.location.gps_latitude))
        else:
            self.proj = Proj(DEFAULT_PROJ_STRING)
            # set origin point (TUM MI building) in default UTM 32 zone
            self.origin_utm = self.proj(config.TUM_MI_BUILDING_X, config.TUM_MI_BUILDING_Y)

            # convert lanelets
        for lanelet in scenario.lanelet_network.lanelets:
            self._convert_lanelet(lanelet)

        # convert traffic signs
        for traffic_sign in scenario.lanelet_network.traffic_signs:
            self._convert_traffic_sign(traffic_sign)

        # convert traffic lights
        for traffic_light in scenario.lanelet_network.traffic_lights:
            self._convert_traffic_light(traffic_light)

        # map the traffic signs and the referred lanelets (yield+right_of_way) to a 'right_of_way_relation' object
        self._add_right_of_way_relation()

        # map the traffic lights and the referred lanelets to a 'right_of_way_relation' object
        self._add_regulatory_element_for_traffic_lights()

        return self.osm.serialize_to_xml()

    def _add_regulatory_element_for_traffic_lights(self):
        """
        Add traffic light relations to lanelets in lanelet2 format
        """
        # One regulatory element is created for each lanelet that has a corresponding traffic_light element
        for ll in self.lanelet_network.lanelets:
            traffic_light_reference_list = []
            for lightID in ll.traffic_lights:
                # find the coordinates of the CR traffic light
                # and check them with traffic light in L2 format that we have created

                # x,y = self.lanelet_network._traffic_lights[lightID].position
                x, y = self.lanelet_network.find_traffic_light_by_id(lightID).position

                xsign, ysign = self.proj(self.origin_utm[0] + x, self.origin_utm[1] + y, inverse=True)
                for way in self.osm.ways:
                    if self.osm.find_way_by_id(way).tag_dict.get('type') == "traffic_light":

                        nx = self.osm.find_node_by_id(self.osm.find_way_by_id(way).nodes[0]).lon
                        ny = self.osm.find_node_by_id(self.osm.find_way_by_id(way).nodes[0]).lat

                        if str(xsign) == nx and str(ysign) == ny:
                            # found the same traffic light, now to reference it
                            traffic_light_reference_list.append(way)

            if len(ll.traffic_lights) > 0:
                # map the end of the lanelet to the ref_line
                # maybe map the stop line also? Lanelets from examples didn't have stopLines so double check if needed
                x, y = self._get_shared_last_nodes_from_other_lanelets(ll)
                way_tl = Way(self.id_count, [x, y])
                self.osm.add_way(way_tl)
                way_list = [way_tl.id_]
                self.osm.add_regulatory_element(
                    RegulatoryElement(self.id_count, traffic_light_reference_list, ref_line=way_list,
                                      tag_dict={"subtype": "traffic_light", "type": "regulatory_element"}))

    def _convert_traffic_light(self, light: TrafficLight):
        """
        Add traffic light to the lanelet2 format
        """
        traffic_light_id = self.id_count
        # create a node that represent the sign position
        x1, y1 = self.proj(self.origin_utm[0] + light.position[0], self.origin_utm[1] + light.position[1], inverse=True)

        id1 = self.id_count

        # since 3 nodes are needed to represent the sign in the l2 format (only 1 in the cr format)
        # create another 2 nodes that are close to the first one

        x2, y2 = self.proj(self.origin_utm[0] + light.position[0] + 0.1, self.origin_utm[1] + light.position[1] + 0.1,
                           inverse=True)
        x3, y3 = self.proj(self.origin_utm[0] + light.position[0] - 0.1, self.origin_utm[1] + light.position[1] - 0.1,
                           inverse=True)
        id2 = self.id_count
        id3 = self.id_count

        # creating and adding those nodes to our osm
        self.osm.add_node(Node(id1, y1, x1))
        self.osm.add_node(Node(id2, y2, x2))
        self.osm.add_node(Node(id3, y3, x3))

        # get the first light color as subtype
        traffic_light_subtype = light.cycle[0].state.value

        self.osm.add_way(Way(traffic_light_id, [id1, id2, id3],
                             tag_dict={"subtype": traffic_light_subtype, "type": "traffic_light"}))

    def _add_right_of_way_relation(self):
        """
        Add traffic sign relations to the lanelet2 format
        """
        refers = []
        yield_ways = []
        right_of_ways = []
        ref_line = []
        # convert stop lines of yield lanelets to ways and add them to L2 map
        # create a dictionary to map the stop lines with newly created ways for easier mapping
        dict_stop_lines = self._create_stop_line_to_way_dictionary()

        # go through signs
        for way in self.osm.ways:
            if self.osm.find_way_by_id(way).tag_dict.get('type') == "traffic_sign":
                # find the corresponding yield and right of way ways
                # find x and y coordinates of the sign and match it to signs of the lanelets to find the lanelet

                # in lanelet2cr, only node 0 is taken for the position
                nx = self.osm.find_node_by_id(self.osm.find_way_by_id(way).nodes[0]).lon
                ny = self.osm.find_node_by_id(self.osm.find_way_by_id(way).nodes[0]).lat

                # go through the lanelets to find the lanelet that has the matching traffic_sign in its attribute
                for ll in self.lanelet_network.lanelets:
                    for traffic_sign_id in ll.traffic_signs:
                        x, y = self.lanelet_network.find_traffic_sign_by_id(traffic_sign_id).position
                        x_sign, y_sign = self.proj(self.origin_utm[0] + x, self.origin_utm[1] + y, inverse=True)
                        # have to map the signs based on the position,
                        # as the same 2 signs do not have the same ID in L2 and CR format
                        if nx == str(x_sign) and ny == str(y_sign):
                            # position matches, found the corresponding lanelet with selected sign
                            # extract the way that corresponds to our lanelet
                            # sign -> lanelet -> way (right+left) -> wayrelation
                            right_way_id = self.right_ways[ll.lanelet_id]
                            left_way_id = self.left_ways[ll.lanelet_id]
                            for way_rel in self.osm.way_relations:
                                if (self.osm.find_way_rel_by_id(
                                        way_rel).right_way == right_way_id and self.osm.find_way_rel_by_id(
                                        way_rel).left_way == left_way_id):
                                    # found the corresponding way_rel, append to the lanelet
                                    refers, yield_ways, right_of_ways, ref_line = \
                                        self._append_from_sign(ll, way, way_rel, dict_stop_lines)
        # do not add right_of_way_rel if there are no signs
        if len(refers) > 0:
            self.osm.add_regulatory_element(
                RegulatoryElement(self.id_count, refers, yield_ways, right_of_ways, ref_line=ref_line,
                                  tag_dict={"subtype": "right_of_way", "type": "regulatory_element"}))

    def _create_stop_line_to_way_dictionary(self) -> Dict[int, str]:
        """
        Creates a dictionary that maps lanelet (CR) id's with their corresponding way (stop line) (L2) id's.

        :return: Above stated dictionary
        """
        dict_stop_lines = {}
        for ll in self.lanelet_network.lanelets:
            if ll.stop_line:
                # found a lanelet with a stop line
                stop_line = ll.stop_line
                # stop line has 2 points (each point has x and y coordinates)
                stop_line_start = stop_line.start
                stop_line_end = stop_line.end
                # transform the x and y coordinates to the L2 coordinate system
                x_start, y_start = self.proj(self.origin_utm[0] + stop_line_start[0],
                                             self.origin_utm[1] + stop_line_start[1], inverse=True)
                x_end, y_end = self.proj(self.origin_utm[0] + stop_line_end[0], self.origin_utm[1] + stop_line_end[1],
                                         inverse=True)
                # create nodes from the points and add them to the osm
                node_start = Node(self.id_count, y_start, x_start)
                node_end = Node(self.id_count, y_end, x_end)
                self.osm.add_node(node_start)
                self.osm.add_node(node_end)
                # create a way from newly created nodes and add it to the osm
                stop_line_way = Way(self.id_count, [node_start.id_, node_end.id_], tag_dict={"type": "stop_line"})
                self.osm.add_way(stop_line_way)
                # map the way with the lanelet
                dict_stop_lines[ll.lanelet_id] = stop_line_way.id_
        return dict_stop_lines

    def _append_from_sign(self, ll: Lanelet, way: Way, way_rel: WayRelation, dict_stop_lines: Dict[int, str]) -> \
            Tuple[List[Way], List[WayRelation], List[WayRelation], List[str]]:
        """
        Extracts relevant information from the way that represents a traffic sign, such sa subtype and name,
        and appends the information to one (or none) of the possible arrays

        :param ll: lanelet from which we use its id to match it with the corresponding stop line in the dict_stop_lines
        :param way: way that corresponds to the traffic sign being converted
        :param way_rel: way relation that corresponds to the right and left way of the lanelet.
        :param dict_stop_lines: dictionary that maps the id of the lanelet(CR) with its corresponding stop_line way(L2).
        :return: tuple of lists that correspond to the attributes of the regulatory element constructor
        """
        refers = []
        yield_ways = []
        right_of_ways = []
        ref_line = []
        # subtype from the L2 format, i.e. "de205" -> CR format, i.e. "205"
        subtype = self.osm.find_way_by_id(way).tag_dict.get('subtype')[2:]
        # iterate through sign IDs to find the corresponding sign with that subtype
        sign_name = ""
        sign_found = False
        for country in config.CR2LANELET_SUPPORTED_COUNTRIES_LIST:
            if sign_found is True:
                break
            for countrySign in country:
                if subtype == str(countrySign.value):
                    sign_name = countrySign.name
                    sign_found = True
        # no need to add the speed limit sign to the way of rel
        if sign_name != "MAX_SPEED":
            refers.append(way)
        # for now only check the german types,
        # as it follows the conversion in add_sign function
        if sign_name in ("YIELD", "STOP"):
            yield_ways.append(way_rel)
            # what if it does not have a stop line? Or it must have it?
            stop_line_way = dict_stop_lines[ll.lanelet_id]
            if stop_line_way:
                ref_line.append(stop_line_way)
        elif sign_name in ("RIGHT_OF_WAY", "PRIORITY"):
            right_of_ways.append(way_rel)

        return refers, yield_ways, right_of_ways, ref_line

    def _convert_traffic_sign(self, sign: TrafficSign):
        """
        Convert a traffic sign to way which will be mapped by RightOfWay Regulatory element
        Add the resulting right of way relation to the OSM.

        :param sign: Traffic Sign to be converted.
        """
        # create a node that represent the sign position
        x1, y1 = self.proj(self.origin_utm[0] + sign.position[0], self.origin_utm[1] + sign.position[1], inverse=True)
        id1 = self.id_count

        # since 2 nodes are needed to represent the sign in the l2 format (only 1 in the cr format)
        # create another node that is close to the first one
        x2, y2 = self.proj(self.origin_utm[0] + sign.position[0] + 0.25, self.origin_utm[1] + sign.position[1] + 0.25,
                           inverse=True)
        id2 = self.id_count

        # creating and adding those nodes to our osm
        self.osm.add_node(Node(id1, y1, x1))
        self.osm.add_node(Node(id2, y2, x2))

        # matching the type of the traffic sign
        sign_id = sign.traffic_sign_elements[0].traffic_sign_element_id
        val = ""
        for country in config.CR2LANELET_SUPPORTED_COUNTRIES_LIST:
            for k in country:
                if k == sign_id:
                    val = k.value

        traffic_sign_wayid = self.id_count
        virtual = sign.virtual

        # extract the country name of the sign, so we can map it to a dictionary
        sign_country_name = str(type(sign.traffic_sign_elements[0].traffic_sign_element_id).__name__)

        # map the supported countries to their 2 letter prefixs
        country_prefix_dictionary = config.CR2LANELET_SUPPORTED_COUNTRIES_PREFIX_DICTIONARY

        subtype = country_prefix_dictionary[sign_country_name]

        # if it is a speed sign, don't add way but add regulatory element "speed_limit"
        self.osm.add_way(Way(traffic_sign_wayid, [id1, id2],
                             tag_dict={"subtype": subtype + str(val), "type": "traffic_sign", "virtual": str(virtual)}))

    def _convert_lanelet(self, lanelet: Lanelet):
        """
        Convert a lanelet to a way relation.
        Add the resulting relation and its ways and nodes to the OSM.

        :param lanelet: Lanelet to be converted.
        """
        # check if there are shared ways
        right_way_id = self._get_potential_right_way(lanelet)
        left_way_id = self._get_potential_left_way(lanelet)

        left_nodes, right_nodes = self._create_nodes(lanelet, left_way_id, right_way_id)

        self.first_nodes[lanelet.lanelet_id] = (left_nodes[0], right_nodes[0])
        self.last_nodes[lanelet.lanelet_id] = (left_nodes[-1], right_nodes[-1])

        if not left_way_id:
            left_way = Way(self.id_count, left_nodes)
            self.osm.add_way(left_way)
            left_way_id = left_way.id_
        if not right_way_id:
            right_way = Way(self.id_count, right_nodes)
            self.osm.add_way(right_way)
            right_way_id = right_way.id_

        # get the lanelet type of the lanelet we are converting
        subtype = ""
        if len(lanelet.lanelet_type) > 0:
            subtype = list(lanelet.lanelet_type)[0].value
        # have to convert the names as they are slightly different in both formats
        subtype, subtype_in = _convert_subtype_names(subtype)

        # append left and right way
        self.left_ways[lanelet.lanelet_id] = left_way_id
        self.right_ways[lanelet.lanelet_id] = right_way_id

        # create the way relation
        way_rel = WayRelation(self.id_count, left_way_id, right_way_id, tag_dict={"type": "lanelet"})

        # convert the speed signs
        self._convert_speed_sign(lanelet, way_rel)

        # update the way relation with the subtype, if it exists
        if subtype_in is True:
            way_rel.tag_dict.update({"subtype": subtype})

        # add the way relation to the osm
        self.osm.add_way_relation(way_rel)

    def _create_nodes(self, lanelet: Lanelet, left_way_id: int, right_way_id: int) -> Tuple[List[str], List[str]]:
        """
        Create new nodes for the ways of the lanelet.
        Add them to OSM and return a list of the node ids.
        In case a left or right way already exists, the returned list
        only contains the first and last node of the way.

        :param lanelet: Lanelet of which the right and left vertices should be converted to ways.
        :param left_way_id: Id of a potential shared left way which was already converted.
            if this is not None, the left vertices of the lanelet do not have to be converted again.
        :param right_way_id: Id of a potential right way, similar to left_way_id.
        :return: A tuple of lists of node ids for the left and the right way.
        """
        left_nodes, right_nodes = [], []
        start_index = 0
        end_index = len(lanelet.left_vertices)
        pot_first_left_node, pot_first_right_node = self._get_shared_first_nodes_from_other_lanelets(lanelet)
        pot_last_left_node, pot_last_right_node = self._get_shared_last_nodes_from_other_lanelets(lanelet)

        if pot_first_left_node:
            start_index = 1
        if pot_last_left_node:
            end_index = -1
        if left_way_id:
            first_left_node: Optional[str]
            last_left_node: Optional[str]
            first_left_node, last_left_node = self._get_first_and_last_nodes_from_way(left_way_id,
                                                                                      lanelet.adj_left_same_direction)
        else:
            first_left_node = pot_first_left_node
            last_left_node = pot_last_left_node
            left_nodes = self._create_nodes_from_vertices(lanelet.left_vertices[start_index:end_index])
        if right_way_id:
            first_right_node: Optional[str]
            last_right_node: Optional[str]
            first_right_node, last_right_node = self._get_first_and_last_nodes_from_way\
            (right_way_id, lanelet.adj_right_same_direction)
        else:
            first_right_node = pot_first_right_node
            last_right_node = pot_last_right_node
            right_nodes = self._create_nodes_from_vertices(lanelet.right_vertices[start_index:end_index])

        if first_left_node:
            left_nodes.insert(0, first_left_node)
        if first_right_node:
            right_nodes.insert(0, first_right_node)

        if last_left_node:
            left_nodes.append(last_left_node)
        if last_right_node:
            right_nodes.append(last_right_node)

        return left_nodes, right_nodes

    def _get_first_and_last_nodes_from_way(self, way_id: int, same_dir: bool) -> Tuple[str, str]:
        """
        Get the first and the last node of a way.
        Reverse order of nodes if way is reversed.
         
        :param way_id: Id of way.
        :param same_dir: True if way is in normal direction, False if it is reversed.
        :return: Tuple with first and last node.
        """
        way = self.osm.find_way_by_id(way_id)
        first_idx, last_idx = (0, -1) if same_dir else (-1, 0)
        return way.nodes[first_idx], way.nodes[last_idx]

    def _create_nodes_from_vertices(self, vertices: List[np.ndarray]) -> List[str]:
        """
        Create nodes and add them to the OSM.

        :param vertices: List of vertices from a lanelet boundary.
        :return: Ids of nodes which were created.
        """
        nodes = []
        for vertex in vertices:
            lon, lat = self.proj(self.origin_utm[0] + vertex[0], self.origin_utm[1] + vertex[1], inverse=True)
            node = Node(self.id_count, lat, lon)
            nodes.append(node.id_)
            self.osm.add_node(node)
        return nodes

    def _get_potential_right_way(self, lanelet) -> Union[None, int]:
        """
        Check if a shared right boundary with another lanelet can be transformed
        to the same way.

        :param lanelet: Lanelet of which right boundary should be converted to a way.
        :return: Id of a way which can be shared, else None if it is not possible.
        """
        if lanelet.adj_right:
            if lanelet.adj_right_same_direction:
                potential_right_way = self.left_ways.get(lanelet.adj_right)
            else:
                potential_right_way = self.right_ways.get(lanelet.adj_right)
            if potential_right_way:
                adj_right = self.lanelet_network.find_lanelet_by_id(lanelet.adj_right)
                vertices = (
                    adj_right.left_vertices if lanelet.adj_right_same_direction else adj_right.right_vertices[::-1])
                if _vertices_are_equal(lanelet.right_vertices, vertices):
                    return potential_right_way

        return None

    def _get_potential_left_way(self, lanelet) -> Union[None, int]:
        """
        Check if a shared left boundary with another lanelet can be transformed
        to the same way.

        :param lanelet: Lanelet of which left boundary should be converted to a way.
        :return: Id of a way which can be shared, else None if it is not possible.
        """
        if lanelet.adj_left:
            if lanelet.adj_left_same_direction:
                potential_left_way = self.right_ways.get(lanelet.adj_left)
            else:
                potential_left_way = self.left_ways.get(lanelet.adj_left)
            if potential_left_way:
                adj_left = self.lanelet_network.find_lanelet_by_id(lanelet.adj_left)
                vertices = (
                    adj_left.right_vertices if lanelet.adj_left_same_direction else adj_left.left_vertices[::-1])
                if _vertices_are_equal(lanelet.left_vertices, vertices):
                    return potential_left_way

        return None

    def _get_shared_first_nodes_from_other_lanelets(self, lanelet: Lanelet) \
            -> Tuple[Union[str, None], Union[str, None]]:
        """
        Get already created nodes from other lanelets which could also
        be used by this lanelet as first nodes.

        :param lanelet: Lanelet for which shared nodes should be found.
        :return: Id of first left and first right node if they exist.
        """
        if lanelet.predecessor:
            for lanelet_id in lanelet.predecessor:
                first_left_node, first_right_node = self.last_nodes.get(lanelet_id, (None, None))
                if first_left_node:
                    return first_left_node, first_right_node
            for pred_id in lanelet.predecessor:
                pred = self.lanelet_network.find_lanelet_by_id(pred_id)
                for succ_id in pred.successor:
                    first_left_node, first_right_node = self.first_nodes.get(succ_id, (None, None))
                    if first_left_node:
                        return first_left_node, first_right_node
        return None, None

    def _get_shared_last_nodes_from_other_lanelets(self, lanelet: Lanelet) -> Tuple[Union[str, None], Union[str, None]]:
        """
        Get already created nodes from other lanelets which could also
        be used by this lanelet as last nodes.

        :param lanelet: Lanelet for which shared nodes should be found.
        :return: Id of last left and last right node if they exist.
        """
        if lanelet.successor:
            for lanelet_id in lanelet.successor:
                last_left_node, last_right_node = self.first_nodes.get(lanelet_id, (None, None))
                if last_left_node:
                    return last_left_node, last_right_node
            for succ_id in lanelet.successor:
                succ = self.lanelet_network.find_lanelet_by_id(succ_id)
                for pred_id in succ.predecessor:
                    last_left_node, last_right_node = self.last_nodes.get(pred_id, (None, None))
                    if last_left_node:
                        return last_left_node, last_right_node

        return None, None

    def _convert_speed_sign(self, lanelet: Lanelet, way_rel: WayRelation):
        """
        Convert speed signs(CR) into regulatory elements(L2)

        :param lanelet: Lanelet(CR) that contains the traffic sign
        :param way_rel: Way relation, in which regulatory elements will append newly converted speed sign.
        """
        speed_sign_ids = []
        # check if the lanelet has a traffic sign (speed limit) assigned to it.
        # if so, create a regulatory element for speed limit and reference it
        for traffic_sign in lanelet.traffic_signs:
            for sign in self.lanelet_network.traffic_signs:
                if sign.traffic_sign_id == traffic_sign:
                    if list(sign.traffic_sign_elements)[0].traffic_sign_element_id.name == "MAX_SPEED":
                        # found a max speed sign, create a reg. element
                        speed_sign_id = self.id_count
                        speed_sign_ids.append(speed_sign_id)
                        max_speed = sign.traffic_sign_elements[0].additional_values[0]
                        self.osm.add_regulatory_element(RegulatoryElement(speed_sign_id,
                                                                          tag_dict={"sign_type": max_speed,
                                                                                    "subtype": "speed_limit",
                                                                                    "type": "regulatory_element"}))
        for speed_sign_id in speed_sign_ids:
            way_rel.regulatory_elements.append(str(speed_sign_id))
