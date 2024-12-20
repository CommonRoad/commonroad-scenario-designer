import logging
import warnings
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from commonroad.common.common_lanelet import LaneletType, LineMarking
from commonroad.scenario.area import Area
from commonroad.scenario.lanelet import Lanelet
from commonroad.scenario.scenario import Location, Scenario
from commonroad.scenario.traffic_light import TrafficLight
from commonroad.scenario.traffic_sign import TrafficSign
from pyproj import CRS, Transformer

from crdesigner.common.config.general_config import GeneralConfig, general_config
from crdesigner.common.config.gui_config import lanelet2_default
from crdesigner.common.config.lanelet2_config import Lanelet2Config, lanelet2_config
from crdesigner.map_conversion.common.utils import generate_unique_id
from crdesigner.map_conversion.lanelet2.lanelet2 import (
    Multipolygon,
    Node,
    OSMLanelet,
    RegulatoryElement,
    Way,
    WayRelation,
)


def _set_overriding_tags_for_bidirectional_users(lanelet: Lanelet, way_rel: WayRelation):
    """
    Function that extracts bidirectional users from CR lanelet and creates according overriding tags for L2 lanelet

    :param lanelet: Lanelet in CR format from which bidirectional users are extracted
    :param way_rel: WayRelation for which the tag_dict is updated with overriding tags according to extracted
    bidirectional users
    """
    for user_bidirectional in lanelet.user_bidirectional:
        user_bidirectional_value = user_bidirectional.value

        # change due to differences in cr and l2 formats
        if user_bidirectional_value == "priorityVehicle":
            user_bidirectional_value = "emergency"

        if user_bidirectional_value in lanelet2_config.supported_lanelet2_vehicles:
            way_rel.tag_dict["one_way:" + "vehicle:" + user_bidirectional_value] = "no"

        elif user_bidirectional_value == "vehicle":
            way_rel.tag_dict["one_way:vehicle"] = "no"

        elif user_bidirectional_value == "bicycle" or user_bidirectional_value == "pedestrian":
            way_rel.tag_dict["one_way:" + user_bidirectional_value] = "no"


def _line_marking_to_type_subtype_vertices(line_marking: LineMarking) -> [str, str]:
    """
    Function that converts CR line marking of left or right vertices to an L2 format

    :param line_marking: line marking
    :return: tuple of strings that represent type and subtype of way based on CR line markings in L2 format
    """
    lanelet2_type = "unknown"  # default type, empty dict for 'unknown' and 'no_marking'
    # as they don't exist in L2 format
    subtype = "unknown"  # default subtype, empty dict for 'unknown' and 'no_marking' as they don't exist in L2 format
    if line_marking is LineMarking.DASHED:
        lanelet2_type = "line_thin"
        subtype = "dashed"
    if line_marking is LineMarking.BROAD_DASHED:
        lanelet2_type = "line_thick"
        subtype = "dashed"
    if line_marking is LineMarking.SOLID:
        lanelet2_type = "line_thin"
        subtype = "solid"
    if line_marking is LineMarking.BROAD_SOLID:
        lanelet2_type = "line_thick"
        subtype = "solid"
    if line_marking is LineMarking.CURB:
        lanelet2_type = "curbstone"
        subtype = "high"
    if line_marking is LineMarking.LOWERED_CURB:
        lanelet2_type = "curbstone"
        subtype = "low"
    if line_marking is LineMarking.DASHED_SOLID:
        lanelet2_type = "line_thick"
        subtype = "dashed_solid"
    if line_marking is LineMarking.SOLID_DASHED:
        lanelet2_type = "line_thick"
        subtype = "solid_dashed"
    if line_marking is LineMarking.SOLID_SOLID:
        lanelet2_type = "line_thick"
        subtype = "solid_solid"
    if line_marking is LineMarking.DASHED_DASHED:
        lanelet2_type = "line_thick"
        subtype = "dashed_dashed"

    return lanelet2_type, subtype


def _extract_and_convert_subtype_name(
    cr_subtypes: List[str], l2_subtypes: List[str]
) -> [str, bool]:
    """
    Function that extracts the most specific lanelet type and, if needed, converts its name as it could slightly differ
    between formats.

    :param cr_subtypes: list of the subtype names of the lanelet
    :param l2_subtypes: lanelet2 subtypes that are available in commonroad
    :return: name of the most specific subtype (converted if needed)
    and the boolean value that states if the subtype corresponds to one of the possible L2 format subtypes
    """
    # extracting lanelet types that exist in L2 format
    common_subtypes = list(set(cr_subtypes).intersection(l2_subtypes))
    # if there is not a single common lanelet type, return False
    if len(common_subtypes) == 0:
        return "", False

    # return the most specific lanelet type
    if "sidewalk" in common_subtypes:
        return "walkway", True
    if "crosswalk" in common_subtypes:
        return "crosswalk", True
    if "bicycleLane" in common_subtypes:
        return "bicycle_lane", True
    if "exitRamp" in common_subtypes:
        return "exit", True
    if "busLane" in common_subtypes:
        return "bus_lane", True
    if "highway" in common_subtypes or "interstate" in common_subtypes:
        return "highway", True
    if "urban" in common_subtypes or "country" in common_subtypes:
        return "road", True


def _vertices_are_equal(
    vertices1: List[np.ndarray], vertices2: List[np.ndarray], ways_are_equal_tolerance: float
) -> bool:
    """
    Checks if two list of vertices are equal up to a tolerance.

    :param vertices1: First vertices to compare.
    :param vertices2: Second vertices to compare.
    :param ways_are_equal_tolerance: value of the tolerance for which we mark ways as equal
    :return: True if every vertex in one list is nearly equal to the
        corresponding vertices at the same position in the other list.
    """
    if len(vertices1) != len(vertices2):
        return False
    diff = np.array(vertices1) - np.array(vertices2)
    if np.abs(np.max(diff)) < ways_are_equal_tolerance:
        return True
    return False


class CR2LaneletConverter:
    """
    Class to convert CommonRoad lanelet to the OSM representation.
    """

    def __init__(
        self, config: Lanelet2Config = lanelet2_config, cr_config: GeneralConfig = general_config
    ):
        """
        Initialization of CR2LaneletConverter

        :param config: Lanelet2 config parameters.
        """
        generate_unique_id(0)  # reset ID counter for next test case
        self._config = config
        self._cr_config = cr_config
        self.transformer = None
        self.osm = None
        self._id_count = 1
        self.first_nodes, self.last_nodes = None, None
        self.left_ways, self.right_ways = None, None
        self.lanelet_network = None
        self.origin_utm = (0, 0)

        self.scenario_translation = (0, 0)

    def _create_transformer(self, scenario: Scenario):
        """
        Creates a Transformer object for conversion from CR o Lanelet2.
        The input projection is determined from the geo transformation of the CR scenario if provided, otherwise the
        projection string from self._config is used,
        The output projection is set to "ETRF89".
        Additionally, the x and y translation from the scenario object are considered (if provided).
        """
        loc: Location = scenario.location
        proj_string_from = None
        if loc is not None and loc.geo_transformation is not None:
            geo_trans = loc.geo_transformation
            # get projection string from geo reference
            proj_string_from = geo_trans.geo_reference
            # get translation w.r.t. lat/lon location from scenario object
            self.scenario_translation = (geo_trans.x_translation, geo_trans.y_translation)
            # TODO: z rotation and scaling are currently ignored
            if geo_trans.z_rotation != 0.0 or geo_trans.scaling != 1:
                warnings.warn(
                    "<CR2LaneletConverter>: z_rotation and scaling are not considered during transformation"
                )
        if proj_string_from is None:
            proj_string_from = self._cr_config.proj_string_cr
        crs_from = CRS(proj_string_from)
        crs_to = CRS(lanelet2_default)
        self.transformer = Transformer.from_proj(crs_from, crs_to)

    @property
    def id_count(self) -> int:
        """
        Internal counter for giving IDs to the members of the OSM.
        Each call returns the count and increases it by one.

        :return: current id count.
        """
        tmp = self._id_count
        self._id_count += 1
        return tmp

    def __call__(self, scenario):
        """
        Convert a scenario to an OSM xml document.

        :param scenario: Scenario that will be used for conversion
        """
        self._create_transformer(scenario)
        self.osm = OSMLanelet()
        self.lanelet_network = scenario.lanelet_network
        self.first_nodes = {}  # saves first left and right node | dict() but with a faster execution
        self.last_nodes = {}  # saves last left and right node
        self.left_ways = {}
        self.right_ways = {}

        # set origin shift according to translation in scenario
        if self.scenario_translation[0] != 0 and self.scenario_translation[1] != 0:
            self.origin_utm = self.scenario_translation

        # convert lanelets
        for lanelet in scenario.lanelet_network.lanelets:
            self._convert_lanelet(lanelet)

        # convert traffic signs
        for traffic_sign in scenario.lanelet_network.traffic_signs:
            self._convert_traffic_sign(traffic_sign)

        # convert traffic lights
        for traffic_light in scenario.lanelet_network.traffic_lights:
            self._convert_traffic_light(traffic_light)

        # convert areas
        for area in scenario.lanelet_network.areas:
            self._convert_area(area)

        # map the traffic signs and the referred lanelets (yield+right_of_way) to a 'right_of_way_relation' object
        self._add_right_of_way_relation()

        # map the traffic lights and the referred lanelets to a 'right_of_way_relation' object
        self._add_regulatory_element_for_traffic_lights()

        # append the lane_change flag to osm ways if the autoware flag is set to True
        if self._config.autoware is True:
            self._append_lane_change_tags()

        return self.osm.serialize_to_xml()

    def _add_regulatory_element_for_traffic_lights(self):
        """
        Add traffic light relations to lanelets in lanelet2 format
        """
        # One regulatory element is created for each lanelet that has a corresponding traffic_light element
        for idx, ll in enumerate(self.lanelet_network.lanelets):
            traffic_light_reference_list = []
            for light_id in ll.traffic_lights:
                # find the coordinates of the CR traffic light
                # and check them with traffic light in L2 format that we have created

                # if 'position' returns 2 values, *z will be empty. Else, it will be an array with remaining values
                x, y, *z = self.lanelet_network.find_traffic_light_by_id(light_id).position
                if len(z) == 0:
                    z = 0
                else:
                    z = z[0]

                lat_sign, lon_sign = self.transformer.transform(
                    self.origin_utm[0] + x, self.origin_utm[1] + y
                )
                for way in self.osm.ways:
                    if self.osm.find_way_by_id(way).tag_dict.get("type") == "traffic_light":
                        n_lon = self.osm.find_node_by_id(self.osm.find_way_by_id(way).nodes[0]).lon
                        n_lat = self.osm.find_node_by_id(self.osm.find_way_by_id(way).nodes[0]).lat

                        if str(lon_sign) == n_lon and str(lat_sign) == n_lat:
                            # found the same traffic light, now to reference it
                            traffic_light_reference_list.append(way)

            if len(ll.traffic_lights) > 0:
                # map the end of the lanelet to the ref_line
                # maybe map the stop line also? Lanelets from examples didn't have stopLines so double check if needed
                x, y = self._get_shared_last_nodes_from_other_lanelets(ll)
                if x is None or y is None:
                    x, y = self.last_nodes.get(ll.lanelet_id, (None, None))
                way_tl = Way(self.id_count, [x, y])
                self.osm.add_way(way_tl)
                way_list = [way_tl.id_]
                regulatory_element_id = self.id_count
                self.osm.add_regulatory_element(
                    RegulatoryElement(
                        regulatory_element_id,
                        traffic_light_reference_list,
                        ref_line=way_list,
                        tag_dict={"subtype": "traffic_light", "type": "regulatory_element"},
                    )
                )
                get_way_relation_key = list(self.osm.way_relations.keys())[idx]
                way_rel = self.osm.find_way_rel_by_id(get_way_relation_key)
                reg_elements_arr = way_rel.regulatory_elements
                reg_elements_arr.append(regulatory_element_id)
                new_way_rel = WayRelation(
                    get_way_relation_key,
                    way_rel.left_way,
                    way_rel.right_way,
                    tag_dict=way_rel.tag_dict,
                    regulatory_elements=reg_elements_arr,
                )
                self.osm.add_way_relation(new_way_rel)

    def _convert_area(self, area: Area):
        """
        Converts a CommonRoad area to the Lanelet2 multipolygon.

        :param area: area to be converted.
        """
        outer_list = list()
        for border in area.border:
            nodes = self._create_nodes_from_vertices(border.border_vertices)
            type, subtype = _line_marking_to_type_subtype_vertices(border.line_marking)
            way = Way(self.id_count, nodes, {"subtype": subtype, "type": type})
            self.osm.add_way(way)
            outer_list.append(way.id_)
        tag_dict = {}
        if area.area_types:
            for area_type in area.area_types:
                tag_dict["subtype"] = str(area_type.value)
        multipolygon = Multipolygon(self.id_count, outer_list, tag_dict)
        self.osm.add_multipolygon(multipolygon)

    def _convert_traffic_light(self, light: TrafficLight):
        """
        Add traffic light to the lanelet2 format
        """
        traffic_light_id = self.id_count
        autoware = self._config.autoware

        # consider z-coordinate
        z = 5  # Set a base of 5m and replace it with new value
        if len(light.position) == 3:
            z = light.position[2]

        id1 = self.id_count

        # since 3 nodes are needed to represent the sign in the l2 format (only 1 in the cr format)
        # create another 2 nodes that are close to the first one
        # create a node that represent the sign position

        lat1, lon1 = self.transformer.transform(
            self.origin_utm[0] + light.position[0], self.origin_utm[1] + light.position[1]
        )
        lat2, lon2 = self.transformer.transform(
            self.origin_utm[0] + light.position[0] + 0.1,
            self.origin_utm[1] + light.position[1] + 0.1,
        )
        if not autoware:
            lat3, lon3 = self.transformer.transform(
                self.origin_utm[0] + light.position[0] - 0.1,
                self.origin_utm[1] + light.position[1] - 0.1,
            )
            id3 = self.id_count

        id2 = self.id_count

        # creating and adding those nodes to our osm
        localx1, localy1, localx2, localy2, localx3, localy3 = None, None, None, None, None, None

        if self._config.use_local_coordinates:
            localx1, localy1 = light.position[0], light.position[1]
            localx2, localy2 = light.position[0] - 0.1, light.position[1] + 0.1
            localx3, localy3 = light.position[0] - 0.1, light.position[1] - 0.1
        self.osm.add_node(
            Node(id1, lat1, lon1, z, autoware=autoware, local_x=localx1, local_y=localy1)
        )
        self.osm.add_node(
            Node(id2, lat2, lon2, z, autoware=autoware, local_x=localx2, local_y=localy2)
        )
        if not autoware:
            self.osm.add_node(
                Node(id3, lat3, lon3, z, autoware=autoware, local_x=localx3, local_y=localy3)
            )

        # get the first light color as subtype
        traffic_light_subtype = ""
        for col in light.color:
            traffic_light_subtype += f"{col.value}_"
        traffic_light_subtype = traffic_light_subtype[:-1]
        # traffic_light_subtype = light.traffic_light_cycle.cycle_elements[0].state.value
        # Autoware supports that traffic lights only consist of 2 nodes instead of 3
        if autoware:
            self.osm.add_way(
                Way(
                    traffic_light_id,
                    [id1, id2],
                    tag_dict={
                        "subtype": traffic_light_subtype,
                        "type": "traffic_light",
                        "height": "1.2",
                    },
                )
            )
        else:
            self.osm.add_way(
                Way(
                    traffic_light_id,
                    [id1, id2, id3],
                    tag_dict={"subtype": traffic_light_subtype, "type": "traffic_light"},
                )
            )

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
            if self.osm.find_way_by_id(way).tag_dict.get("type") == "traffic_sign":
                # find the corresponding yield and right of way ways
                # find x and y coordinates of the sign and match it to signs of the lanelets to find the lanelet
                # consider z-coordinate as well

                # in lanelet2cr, only node 0 is taken for the position
                n_lon = self.osm.find_node_by_id(self.osm.find_way_by_id(way).nodes[0]).lon
                n_lat = self.osm.find_node_by_id(self.osm.find_way_by_id(way).nodes[0]).lat
                n_ele = self.osm.find_node_by_id(self.osm.find_way_by_id(way).nodes[0]).ele

                # go through the lanelets to find the lanelet that has the matching traffic_sign in its attribute
                for ll in self.lanelet_network.lanelets:
                    for traffic_sign_id in ll.traffic_signs:
                        # if 'position' returns 2 values, *z will be empty. Else, it will be an array with remaining
                        # values
                        x, y, *z = self.lanelet_network.find_traffic_sign_by_id(
                            traffic_sign_id
                        ).position
                        if len(z) == 0:
                            z = 0
                        else:
                            z = z[0]
                        lat_sign, lon_sign = self.transformer.transform(
                            self.origin_utm[0] + x, self.origin_utm[1] + y
                        )
                        # have to map the signs based on the position,
                        # as the same 2 signs do not have the same ID in L2 and CR format
                        if n_lon == str(lon_sign) and n_lat == str(lat_sign) and n_ele == str(z):
                            # position matches, found the corresponding lanelet with selected sign
                            # extract the way that corresponds to our lanelet
                            # sign -> lanelet -> way (right+left) -> way relation
                            right_way_id = self.right_ways[ll.lanelet_id]
                            left_way_id = self.left_ways[ll.lanelet_id]
                            for way_rel in self.osm.way_relations:
                                if (
                                    self.osm.find_way_rel_by_id(way_rel).right_way == right_way_id
                                    and self.osm.find_way_rel_by_id(way_rel).left_way == left_way_id
                                ):
                                    # found the corresponding way_rel, append to the lanelet
                                    refers, yield_ways, right_of_ways, ref_line = (
                                        self._append_from_sign(ll, way, way_rel, dict_stop_lines)
                                    )
        # do not add right_of_way_rel if there are no signs
        if len(refers) > 0:
            self.osm.add_regulatory_element(
                RegulatoryElement(
                    self.id_count,
                    refers,
                    yield_ways,
                    right_of_ways,
                    ref_line=ref_line,
                    tag_dict={"subtype": "right_of_way", "type": "regulatory_element"},
                )
            )

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
                lat_start, lon_start = self.transformer.transform(
                    self.origin_utm[0] + stop_line_start[0], self.origin_utm[1] + stop_line_start[1]
                )
                lat_end, lon_end = self.transformer.transform(
                    self.origin_utm[0] + stop_line_end[0], self.origin_utm[1] + stop_line_end[1]
                )

                # consider the z-coordinate
                z_start = 0
                if len(stop_line_start) == 3:
                    z_start = stop_line_start[2]
                z_end = 0
                if len(stop_line_end) == 3:
                    z_end = stop_line_end[2]

                # create nodes from the points and add them to the osm
                node_start = Node(
                    self.id_count, lat_start, lon_start, z_start, autoware=self._config.autoware
                )
                node_end = Node(
                    self.id_count, lat_end, lon_end, z_end, autoware=self._config.autoware
                )
                self.osm.add_node(node_start)
                self.osm.add_node(node_end)
                # create a way from newly created nodes and add it to the osm
                stop_line_way = Way(
                    self.id_count, [node_start.id_, node_end.id_], tag_dict={"type": "stop_line"}
                )
                self.osm.add_way(stop_line_way)
                # map the way with the lanelet
                dict_stop_lines[ll.lanelet_id] = stop_line_way.id_
        return dict_stop_lines

    def _append_from_sign(
        self, ll: Lanelet, way: Way, way_rel: WayRelation, dict_stop_lines: Dict[int, str]
    ) -> Tuple[List[Way], List[WayRelation], List[WayRelation], List[str]]:
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
        subtype = self.osm.find_way_by_id(way).tag_dict.get("subtype")[2:]
        # iterate through sign IDs to find the corresponding sign with that subtype
        sign_name = ""
        sign_found = False
        for country in self._config.supported_countries:
            if sign_found is True:
                break
            for country_sign in country:
                if subtype == str(country_sign.value):
                    sign_name = country_sign.name
                    sign_found = True
        # no need to add the speed limit sign to the way of rel
        if sign_name != "MAX_SPEED":
            refers.append(way)
        # for now only check the german types,
        # as it follows the conversion in add_sign function
        if sign_name in ("YIELD", "STOP"):
            yield_ways.append(way_rel)
            # what if it does not have a stop line? Or it must have it?
            logging.info("cr2lanelet::_append_from_sign: lanelet with yield sign has no")
            if stop_line_way := dict_stop_lines.get(ll.lanelet_id) is not None:
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
        lat_1, lon_1 = self.transformer.transform(
            self.origin_utm[0] + sign.position[0], self.origin_utm[1] + sign.position[1]
        )
        id1 = self.id_count

        # since 2 nodes are needed to represent the sign in the l2 format (only 1 in the cr format)
        # create another node that is close to the first one
        lat_2, lon_2 = self.transformer.transform(
            self.origin_utm[0] + sign.position[0] + 0.25,
            self.origin_utm[1] + sign.position[1] + 0.25,
        )
        id2 = self.id_count

        # check if the sign has z-coordinate (elevation)
        z = 0
        if len(sign.position) == 3:  # the sign has a z-coordinate
            z = sign.position[2]

        # creating and adding those nodes to our osm
        self.osm.add_node(Node(id1, lat_1, lon_1, z, autoware=self._config.autoware))
        self.osm.add_node(Node(id2, lat_2, lon_2, z, autoware=self._config.autoware))

        # matching the type of the traffic sign
        sign_id = sign.traffic_sign_elements[0].traffic_sign_element_id
        val = ""
        for country in self._config.supported_countries:
            for k in country:
                if k == sign_id:
                    val = k.value

        traffic_sign_wayid = self.id_count
        virtual = sign.virtual

        # extract the country name of the sign, so we can map it to a dictionary
        sign_country_name = str(
            type(sign.traffic_sign_elements[0].traffic_sign_element_id).__name__
        )

        # map the supported countries to their 2 letter prefixs
        country_prefix_dictionary = self._config.supported_countries_prefixes

        subtype = country_prefix_dictionary[sign_country_name]

        # if it is a speed sign, don't add way but add regulatory element "speed_limit"
        self.osm.add_way(
            Way(
                traffic_sign_wayid,
                [id1, id2],
                tag_dict={
                    "subtype": subtype + str(val),
                    "type": "traffic_sign",
                    "virtual": str(virtual),
                },
            )
        )

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
            lanelet2_type, subtype = _line_marking_to_type_subtype_vertices(
                lanelet.line_marking_left_vertices
            )
            if lanelet2_type != "unknown":
                left_way.tag_dict = {"type": lanelet2_type, "subtype": subtype}
            self.osm.add_way(left_way)
            left_way_id = left_way.id_
        if not right_way_id:
            right_way = Way(self.id_count, right_nodes)
            lanelet2_type, subtype = _line_marking_to_type_subtype_vertices(
                lanelet.line_marking_right_vertices
            )
            if lanelet2_type != "unknown":
                right_way.tag_dict = {"type": lanelet2_type, "subtype": subtype}
            self.osm.add_way(right_way)
            right_way_id = right_way.id_

        # create a list of lanelet type values, so we can extract the most specific one to convert it to L2 format
        lanelet_types = []
        for type_enum in list(lanelet.lanelet_type):
            lanelet_types.append(type_enum.value)

        # extracting and converting the most specific lanelet type
        subtype, subtype_in = _extract_and_convert_subtype_name(
            lanelet_types, self._config.supported_lanelet2_subtypes
        )

        # append left and right way
        self.left_ways[lanelet.lanelet_id] = left_way_id
        self.right_ways[lanelet.lanelet_id] = right_way_id

        # create the way relation
        way_rel = WayRelation(
            self.id_count, left_way_id, right_way_id, tag_dict={"type": "lanelet"}
        )

        # convert the speed signs
        self._convert_speed_sign(lanelet, way_rel)

        # update the way relation with the subtype, if it exists
        if subtype_in is True:
            way_rel.tag_dict.update({"subtype": subtype})

            # set the location tag
            if LaneletType.URBAN in lanelet.lanelet_type:
                way_rel.tag_dict["location"] = "urban"
            else:
                way_rel.tag_dict["location"] = "nonurban"

        # set the overriding tags for bidirectional users
        _set_overriding_tags_for_bidirectional_users(lanelet, way_rel)

        # add the way relation to the osm
        self.osm.add_way_relation(way_rel)

    def _create_nodes(
        self, lanelet: Lanelet, left_way_id: int, right_way_id: int
    ) -> Tuple[List[str], List[str]]:
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
        pot_first_left_node, pot_first_right_node = (
            self._get_shared_first_nodes_from_other_lanelets(lanelet)
        )
        pot_last_left_node, pot_last_right_node = self._get_shared_last_nodes_from_other_lanelets(
            lanelet
        )

        if pot_first_left_node:
            start_index = 1
        if pot_last_left_node:
            end_index = -1
        if left_way_id:
            first_left_node: Optional[str]
            last_left_node: Optional[str]
            first_left_node, last_left_node = self._get_first_and_last_nodes_from_way(
                left_way_id, lanelet.adj_left_same_direction
            )
        else:
            first_left_node = pot_first_left_node
            last_left_node = pot_last_left_node
            left_nodes = self._create_nodes_from_vertices(
                lanelet.left_vertices[start_index:end_index]
            )
        if right_way_id:
            first_right_node: Optional[str]
            last_right_node: Optional[str]
            first_right_node, last_right_node = self._get_first_and_last_nodes_from_way(
                right_way_id, lanelet.adj_right_same_direction
            )
        else:
            first_right_node = pot_first_right_node
            last_right_node = pot_last_right_node
            right_nodes = self._create_nodes_from_vertices(
                lanelet.right_vertices[start_index:end_index]
            )

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
            lat, lon = self.transformer.transform(
                self.origin_utm[0] + vertex[0], self.origin_utm[1] + vertex[1]
            )
            ele = 0  # z-coordinate value
            if (
                len(vertex) > 2
            ):  # if vertex returns z-coordinate (along with x and y), take it into account
                ele = vertex[2]
            if self._config.use_local_coordinates:
                node = Node(
                    self.id_count,
                    lat,
                    lon,
                    ele,
                    autoware=self._config.autoware,
                    local_x=vertex[0],
                    local_y=vertex[1],
                )
            else:
                node = Node(self.id_count, lat, lon, ele, autoware=self._config.autoware)
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
                    adj_right.left_vertices
                    if lanelet.adj_right_same_direction
                    else adj_right.right_vertices[::-1]
                )
                if _vertices_are_equal(
                    lanelet.right_vertices, vertices, self._config.ways_are_equal_tolerance
                ):
                    # if the shared way is found, we update its tag_dict with lanelet line markings

                    # extract the relevant line marking, so we can convert it to L2 format
                    adj_right_line_marking = (
                        adj_right.line_marking_left_vertices
                        if lanelet.adj_right_same_direction
                        else adj_right.line_marking_right_vertices
                    )

                    # converting line markings to L2 format
                    type_lanelet, subtype_lanelet = _line_marking_to_type_subtype_vertices(
                        lanelet.line_marking_right_vertices
                    )
                    type_adj_right, subtype_adj_right = _line_marking_to_type_subtype_vertices(
                        adj_right_line_marking
                    )

                    # update the tag dict accordingly
                    if type_lanelet != "unknown":
                        if type_adj_right != "unknown":
                            # if there are two linemarking types, add the subtypes together to match the L2 notation
                            # as the type should be the same, the type of the first lanelet line marking is used
                            subtype = subtype_lanelet + "_" + subtype_adj_right
                            # dashed_dashed does not exist in L2 format
                            if subtype == "dashed_dashed":
                                subtype = "dashed"
                        else:
                            subtype = subtype_lanelet
                        self.osm.ways[potential_right_way].tag_dict = {
                            "type": type_lanelet,
                            "subtype": subtype,
                        }
                    else:
                        if type_adj_right != "unknown":
                            subtype = subtype_adj_right
                            self.osm.ways[potential_right_way].tag_dict = {
                                "type": type_adj_right,
                                "subtype": subtype,
                            }

                    # if both lanelet types are unknown (cr default), a tag_dict is not created
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
                    adj_left.right_vertices
                    if lanelet.adj_left_same_direction
                    else adj_left.left_vertices[::-1]
                )
                if _vertices_are_equal(
                    lanelet.left_vertices, vertices, self._config.ways_are_equal_tolerance
                ):
                    # if the shared way is found, we update its tag_dict with lanelet line markings

                    # extract the relevant CR line marking, so we can convert it to L2 format
                    adj_left_line_marking = (
                        adj_left.line_marking_right_vertices
                        if lanelet.adj_left_same_direction
                        else adj_left.line_marking_left_vertices
                    )

                    # converting CR line markings to L2 format
                    type_lanelet, subtype_lanelet = _line_marking_to_type_subtype_vertices(
                        lanelet.line_marking_left_vertices
                    )
                    type_adj_left, subtype_adj_left = _line_marking_to_type_subtype_vertices(
                        adj_left_line_marking
                    )

                    # update the tag dict accordingly
                    if type_lanelet != "unknown":
                        if type_adj_left != "unknown":
                            # if there are two linemarking types, add the subtypes together to match the L2 notation
                            # as the type should be the same, the type of the first lanelet line marking is used
                            subtype = subtype_adj_left + "_" + subtype_lanelet
                            # dashed_dashed does not exist in L2 format
                            if subtype == "dashed_dashed":
                                subtype = "dashed"
                        else:
                            subtype = subtype_lanelet
                        self.osm.ways[potential_left_way].tag_dict = {
                            "type": type_lanelet,
                            "subtype": subtype,
                        }
                    else:
                        if type_adj_left != "unknown":
                            subtype = subtype_adj_left
                            self.osm.ways[potential_left_way].tag_dict = {
                                "type": type_adj_left,
                                "subtype": subtype,
                            }

                    # if both lanelet types are unknown (cr default), a tag_dict is not created
                    return potential_left_way

        return None

    def _get_shared_first_nodes_from_other_lanelets(
        self, lanelet: Lanelet
    ) -> Tuple[Union[str, None], Union[str, None]]:
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

    def _get_shared_last_nodes_from_other_lanelets(
        self, lanelet: Lanelet
    ) -> Tuple[Union[str, None], Union[str, None]]:
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
                    if (
                        list(sign.traffic_sign_elements)[0].traffic_sign_element_id.name
                        == "MAX_SPEED"
                    ):
                        # found a max speed sign, create a reg. element
                        speed_sign_id = self.id_count
                        speed_sign_ids.append(speed_sign_id)
                        max_speed = sign.traffic_sign_elements[0].additional_values[0]
                        self.osm.add_regulatory_element(
                            RegulatoryElement(
                                speed_sign_id,
                                tag_dict={
                                    "sign_type": max_speed,
                                    "subtype": "speed_limit",
                                    "type": "regulatory_element",
                                },
                            )
                        )
        for speed_sign_id in speed_sign_ids:
            way_rel.regulatory_elements.append(str(speed_sign_id))

    def _append_lane_change_tags(self):
        """
        Function that appends the lane change tags to osm ways based on the linemarking of the way.
        Possibility of a lane change has been copied from the Lanelet2 documentation.
        The lane change tags are being used by Autoware.
        """
        ways = list(self.osm.ways.values())
        for way in ways:
            if way.tag_dict:
                if "subtype" in way.tag_dict:
                    subtype = way.tag_dict["subtype"]
                    if subtype == "dashed" or subtype == "dashed_dashed":
                        way.tag_dict["lane_change"] = "yes"
                    elif subtype == "dashed_solid":
                        way.tag_dict["lane_change"] = "left->right: yes"
                    elif subtype == "solid_dashed":
                        way.tag_dict["lane_change"] = "right->left: yes"
                    elif (
                        way.tag_dict["type"] != "traffic_light"
                        and way.tag_dict["type"] != "traffic_sign"
                    ):
                        way.tag_dict["lane_change"] = "no"
                    else:
                        # if the line marking does not exist, lane change is not possible
                        way.tag_dict["lane_change"] = "no"
            else:
                # if the line marking does not exist, lane change is not possible
                way.tag_dict["lane_change"] = "no"
