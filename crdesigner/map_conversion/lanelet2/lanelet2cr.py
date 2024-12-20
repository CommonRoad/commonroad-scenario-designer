import logging
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from commonroad.scenario.area import Area, AreaBorder
from commonroad.scenario.lanelet import (
    Lanelet,
    LaneletNetwork,
    LineMarking,
    RoadUser,
    StopLine,
)
from commonroad.scenario.scenario import (
    GeoTransformation,  # type: ignore
    Location,
    Scenario,
    ScenarioID,
    TrafficLight,
    TrafficSign,
)
from commonroad.scenario.traffic_light import (
    TrafficLightCycle,
    TrafficLightCycleElement,
    TrafficLightDirection,
    TrafficLightState,
)
from commonroad.scenario.traffic_sign import (
    TrafficSignElement,
    TrafficSignIDGermany,
    TrafficSignIDUsa,
    TrafficSignIDZamunda,
)
from pyproj import CRS, Transformer
from shapely.geometry import LineString  # type: ignore

from crdesigner.common.config.general_config import GeneralConfig, general_config
from crdesigner.common.config.gui_config import lanelet2_default
from crdesigner.common.config.lanelet2_config import Lanelet2Config, lanelet2_config
from crdesigner.map_conversion.common.conversion_lanelet import ConversionLanelet
from crdesigner.map_conversion.common.conversion_lanelet_network import (
    ConversionLaneletNetwork,
)
from crdesigner.map_conversion.common.geometry import (
    distance as point_to_polyline_distance,
)
from crdesigner.map_conversion.common.geometry import point_to_line_distance
from crdesigner.map_conversion.common.utils import generate_unique_id
from crdesigner.map_conversion.lanelet2.lanelet2 import (
    Node,
    OSMLanelet,
    RegulatoryElement,
    Way,
    WayRelation,
)
from crdesigner.verification_repairing.verification.hol.functions.predicates.lanelet_predicates import (
    _wrong_left_right_boundary_side,
)

date_strftime_format = "%d-%b-%y %H:%M:%S"
message_format = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=message_format, datefmt=date_strftime_format)


def convert_type_subtype_to_line_marking_lanelet(
    tag_dict: Dict[str, str], multipolygon: bool = False
) -> Tuple[LineMarking, Optional[LineMarking]]:
    """
    Function that takes a type and a subtype of a L2 way's tag dictionary and converts it to a CR lanelet linemarking

    :param tag_dict: tag dictionary of a L2 way with a type and a subtype that that need to be converted.
    :param multipolygon: boolean that indicates whether we are converting a line marking of a way that is a part of a
    multipolygon, as there is no need to separate the linemarkings of a multipolygon.
    :return: Tuple with the converted & the optional line marking that will be copied to the relevant adjacent lanelet.
    The optional linemarking is due to different styles of road marking notation between CR and L2.
    """
    l2_type = tag_dict.get("type")
    l2_subtype = tag_dict.get("subtype")
    linemarking = LineMarking.UNKNOWN  # default
    second_linemarking = None  # used to 'transfer' the second line marking to the adjacent lanelet

    if l2_type == "line_thin":
        if l2_subtype == "solid":
            linemarking = LineMarking.SOLID
        elif l2_subtype == "dashed":
            linemarking = LineMarking.DASHED
        elif l2_subtype == "solid_solid":
            linemarking = LineMarking.SOLID
            second_linemarking = LineMarking.SOLID
            if multipolygon:
                return LineMarking.SOLID_SOLID, None
        elif l2_subtype == "solid_dashed":
            linemarking = LineMarking.SOLID
            second_linemarking = LineMarking.DASHED
            if multipolygon:
                return LineMarking.SOLID_DASHED, None
        elif l2_subtype == "dashed_solid":
            linemarking = LineMarking.DASHED
            second_linemarking = LineMarking.SOLID
            if multipolygon:
                return LineMarking.DASHED_SOLID, None
        elif l2_subtype == "dashed_dashed":
            linemarking = LineMarking.DASHED
            second_linemarking = LineMarking.DASHED
            if multipolygon:
                return LineMarking.DASHED_DASHED, None

    elif l2_type == "line_thick":
        if l2_subtype == "solid":
            linemarking = LineMarking.BROAD_SOLID
        elif l2_subtype == "dashed":
            linemarking = LineMarking.BROAD_DASHED
        elif l2_subtype == "solid_solid":
            linemarking = LineMarking.BROAD_SOLID
            second_linemarking = LineMarking.BROAD_SOLID
            if multipolygon:
                return LineMarking.SOLID_SOLID, None
        elif l2_subtype == "solid_dashed":
            linemarking = LineMarking.BROAD_SOLID
            second_linemarking = LineMarking.BROAD_DASHED
            if multipolygon:
                return LineMarking.SOLID_DASHED, None
        elif l2_subtype == "dashed_solid":
            linemarking = LineMarking.BROAD_DASHED
            second_linemarking = LineMarking.BROAD_SOLID
            if multipolygon:
                return LineMarking.DASHED_SOLID, None
        elif l2_subtype == "dashed_dashed":
            linemarking = LineMarking.BROAD_DASHED
            second_linemarking = LineMarking.BROAD_DASHED
            if multipolygon:
                return LineMarking.DASHED_DASHED, None

    elif l2_type == "curbstone":
        if l2_subtype == "low":
            linemarking = LineMarking.LOWERED_CURB
        else:
            linemarking = LineMarking.CURB

    return linemarking, second_linemarking


def _add_closest_traffic_sign_to_lanelet(
    lanelets: List[Lanelet], traffic_signs: List[TrafficSign]
) -> set:
    """
    Assumes that it is given traffic signs and lanelets that should get matched (all to each)
    Each lanelet gets assigned exactly the single traffic sign closest to it
    Does nothing if the list of traffic signs is empty

    :return: the traffic signs that were assigned to any lanelet
    """
    used_signs = set()
    for la in lanelets:
        closest_traffic_sign = None
        _min_distance = None
        for t in traffic_signs:
            distance = point_to_polyline_distance(t.position, la.center_vertices)
            if _min_distance is None or distance < _min_distance:
                _min_distance = distance
                closest_traffic_sign = t
        if closest_traffic_sign is not None:
            la.add_traffic_sign_to_lanelet(closest_traffic_sign.traffic_sign_id)
            used_signs.add(closest_traffic_sign)
    return used_signs


def _add_stop_line_to_lanelet(lanelets: List[Lanelet], stop_lines: List[StopLine]) -> set:
    """
    Assigns each lanelet the first stop line that it is found to intersect with
    Several lanelets may end up getting assigned the same stop line

    :param lanelets: list of the lanelets
    :param stop_lines: list of the stop lines
    :return: set of yield signs
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


def _extract_special_meaning_to_lanelet(way_rel: WayRelation) -> Tuple[str, set, set]:
    """
    Extracts special meaning from the way relation (L2) to the converted lanelet (CR),
    such as one_way/bidirectional users and the type of the lanelet

    :param way_rel: way relation that is being converted
    :return: Tuple that contains the lanelet type, and the bidirectional and one way users of the lanelet
    """
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
    if subtype in {"bicycle_lane", "shared_walkway", "road"}:
        users_one_way.add(RoadUser.BICYCLE)
        if subtype != "road":
            lanelet_type = "biking"
    if subtype in {"walkway", "shared_walkway"}:
        users_bidirectional.add(RoadUser.PEDESTRIAN)
        lanelet_type = "sidewalk"
    if subtype == "crosswalk":
        users_bidirectional.add(RoadUser.PEDESTRIAN)
        lanelet_type = "crosswalk"
    if subtype == "bus_lane":
        users_one_way.add(RoadUser.BUS)
        lanelet_type = "bus"
    if subtype in {"road", "highway"}:
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
            lanelet_type = "country"
        else:
            lanelet_type = "urban"

    users_bidirectional.add(RoadUser.PRIORITY_VEHICLE)
    return lanelet_type, users_one_way, users_bidirectional


def _append_traffic_light_cycles(traffic_light_way: Way) -> List[TrafficLightCycleElement]:
    """
    Creates traffic light elements (CR) that correspond to the state of their L2 copy,
    and adds them to the traffic light cycle list that is being used to create a
    Traffic Light element in CR format

    :param traffic_light_way: way that represents a traffic light in L2 format
    :return: a list of traffic light cycle elements
    """
    # adding the cycles of the traffic light. As L2 format does not have timestamps
    # the default value of a traffic light duration is 5 seconds.
    cycle_list = []
    state = traffic_light_way.tag_dict.get("subtype")
    if state == "red_yellow_green":
        cycle_list.append(TrafficLightCycleElement(TrafficLightState.RED, 5))
        cycle_list.append(TrafficLightCycleElement(TrafficLightState.YELLOW, 5))
        cycle_list.append(TrafficLightCycleElement(TrafficLightState.GREEN, 5))
    if state == "red_green":
        cycle_list.append(TrafficLightCycleElement(TrafficLightState.RED, 5))
        cycle_list.append(TrafficLightCycleElement(TrafficLightState.GREEN, 5))
    if state == "red_yellow":
        cycle_list.append(TrafficLightCycleElement(TrafficLightState.RED, 5))
        cycle_list.append(TrafficLightCycleElement(TrafficLightState.YELLOW, 5))
    if state == "red":
        cycle_list.append(TrafficLightCycleElement(TrafficLightState.RED, 5))
    if state == "yellow":
        cycle_list.append(TrafficLightCycleElement(TrafficLightState.YELLOW, 5))
    else:
        cycle_list.append(TrafficLightCycleElement(TrafficLightState.INACTIVE, 5))
    return cycle_list


def _two_vertices_coincide(
    vertices1: np.ndarray, vertices2: np.ndarray, adjacent_way_distance_tolerance: float
) -> bool:
    """
    Check if two vertices coincide and describe the same linestring.
    For each vertex of vertices2 the minimal distance to the linestring
    described by vertices1 is calculated. If this distance crosses a certain
    threshold, the vertices are deemed to be different.

    :param vertices1: List of vertices which describe first trajectory.
    :param vertices2: List of vertices which describe second trajectory.
    :param adjacent_way_distance_tolerance: Threshold indicating adjacent ways.
    :return: True if the vertices coincide, else False.
    """
    segments = np.diff(vertices1, axis=0)

    for vert in vertices2:
        distances = np.empty([len(vertices1) + 1])
        distances[0] = np.linalg.norm(vert[0:2] - vertices1[0][0:2])
        distances[-1] = np.linalg.norm(vert[0:2] - vertices1[-1][0:2])
        for i, diff in enumerate(segments):
            distances[i + 1] = np.abs(
                np.cross(diff[0:2], vertices1[i][0:2] - vert[0:2])
            ) / np.linalg.norm(diff[0:2])
        if np.min(distances) > adjacent_way_distance_tolerance:
            return False

    return True


class Lanelet2CRConverter:
    """
    Class to convert OSM to the Commonroad representation of Lanelets.
    """

    def __init__(
        self, config: Lanelet2Config = lanelet2_config, cr_config: GeneralConfig = general_config
    ):
        """
        Initialization of the Lanelet2CRConverter
        """
        self._config = config
        self._cr_config = cr_config
        crs_from = CRS(lanelet2_default)
        crs_to = CRS(general_config.proj_string_cr)
        self.transformer = Transformer.from_proj(crs_from, crs_to)
        self._left_way_ids: Optional[Dict[str, str]] = None
        self._right_way_ids: Optional[Dict[str, str]] = None
        self.first_left_pts: Optional[Dict[str, List[str]]] = None
        self.last_left_pts: Optional[Dict[str, List[str]]] = None
        self.first_right_pts: Optional[Dict[str, List[str]]] = None
        self.last_right_pts: Optional[Dict[str, List[str]]] = None
        self.osm: Optional[OSMLanelet] = None
        self.lanelet_network: Optional[LaneletNetwork] = None

        # Origin of the transformed coordinates
        # if config.translate = False: defaults to (0, 0)
        # if config.translate = True: origin is set to the geo location, and transformed coordinates are translated
        self.origin_utm: Optional[Tuple[float, float]] = None

    def __call__(self, osm: OSMLanelet) -> Union[Scenario, None]:
        """
        Convert OSM to Scenario.
        For each lanelet in OSM format, we have to save their first and last
        point of the left and right boundaries to determine their predecessors,
        successors and adjacent neighbors.

        :param osm: OSM object which includes nodes, ways and lanelet relations.
        :return: A scenario with a lanelet network which describes the
            same map as the osm input.
        """
        # dicts to save relation of nodes to ways and lanelets
        # so the adjacencies can be determined

        self.osm = osm
        self._left_way_ids, self._right_way_ids = defaultdict(list), defaultdict(list)
        self.first_left_pts, self.last_left_pts = defaultdict(list), defaultdict(list)
        self.first_right_pts, self.last_right_pts = defaultdict(list), defaultdict(list)
        if len(self.osm.nodes.values()) == 0:
            logging.warning("Lanelet2CRConverter: Selected Scenario is empty.")
            return None

        origin_lat = min([node.lat for node in self.osm.nodes.values()])
        origin_lon = min(
            [node.lon for node in self.osm.nodes.values()]
        )  # use left-most lower corner as origin
        logging.info(
            "Lanelet2CRConverter OSM bounds - lower-left: {}/{} - " "upper right {}/{}".format(
                origin_lat,
                origin_lon,
                max([node.lat for node in self.osm.nodes.values()]),
                max([node.lon for node in self.osm.nodes.values()]),
            )
        )
        if self._config.translate:
            self.origin_utm = self.transformer.transform(origin_lat, origin_lon)
        else:
            self.origin_utm = (0, 0)

        # create CR scenario object
        scenario_id = ScenarioID(
            country_id=self._cr_config.country_id,
            map_name=self._cr_config.map_name,
            map_id=self._cr_config.map_id,
        )
        scenario = Scenario(
            dt=self._cr_config.time_step_size,
            scenario_id=scenario_id,
            location=Location(gps_latitude=origin_lat, gps_longitude=origin_lon),
        )

        # add GeoTransformation
        geo_transformation = GeoTransformation()
        geo_transformation.geo_reference = self._cr_config.proj_string_cr
        # consider x ans y translation (relevant if self._config.translate is set)
        geo_transformation.x_translation = self.origin_utm[0]
        geo_transformation.y_translation = self.origin_utm[1]

        scenario.location.geo_transformation = geo_transformation

        self.lanelet_network = ConversionLaneletNetwork()

        # Retain traffic light IDs for Autoware
        if self._config.autoware:
            _highest_traffic_light_id = str(0)
            for way in osm.ways:
                if osm.ways[way].tag_dict.get("type") == "traffic_light":
                    if way > _highest_traffic_light_id:
                        _highest_traffic_light_id = way
            generate_unique_id(int(_highest_traffic_light_id))

        speed_limits = {}
        speed_limit_lanelets = {}  # type: ignore
        for speed_limit_key in osm.speed_limit_signs.keys():
            sign_id = generate_unique_id()
            speed_limits[speed_limit_key] = sign_id
            speed_limit_lanelets[speed_limit_key] = []

        for way_rel in osm.way_relations.values():
            # add traffic sign id to traffic signs for speed limit
            # create dictionary for mapping of osm id to cr id and keep id constant
            # later add speed limit as traffic sign
            lanelet = self._way_rel_to_lanelet(
                way_rel,
                self._config.adjacencies,
                self._config.left_driving,
                speed_limits,
                speed_limit_lanelets,
            )
            if lanelet is not None:
                self.lanelet_network.add_lanelet(lanelet)

        # dictionary
        new_ids = self.lanelet_network.convert_all_lanelet_ids()

        # right of way conversion
        for right_of_way_rel in osm.right_of_way_relations.values():
            try:
                (
                    yield_signs,
                    priority_signs,
                    yield_lanelets,
                    priority_lanelets,
                    stop_lines,
                ) = self._right_of_way_to_traffic_sign(right_of_way_rel, new_ids)
                # match traffic signs on the matching lanelets
                # the overwrite makes sure we only add traffic signs in the network that are assigned to any lanelet
                yield_signs_lanelets = _add_closest_traffic_sign_to_lanelet(
                    [self.lanelet_network.find_lanelet_by_id(i) for i in yield_lanelets],
                    yield_signs,
                )
                priority_signs = _add_closest_traffic_sign_to_lanelet(
                    [self.lanelet_network.find_lanelet_by_id(i) for i in priority_lanelets],
                    priority_signs,
                )
                # match stop lines on the yield lanelets
                yield_signs_stop_lines_id = _add_stop_line_to_lanelet(
                    [self.lanelet_network.find_lanelet_by_id(i) for i in yield_lanelets], stop_lines
                )
                # add any used traffic sign
                for s in (
                    priority_signs
                    | yield_signs_lanelets
                    | {y for y in yield_signs if y.traffic_sign_id in yield_signs_stop_lines_id}
                ):
                    self.lanelet_network.add_traffic_sign(s, set())
            except NotImplementedError as e:
                logging.error("Lanelet2CRConverter: " + str(e))

        # multipolygon to area conversion
        for multipolygon in osm.multipolygons.values():
            area_id = generate_unique_id()
            area_border_list = list()
            for outer in multipolygon.outer_list:
                way = osm.find_way_by_id(outer)
                area_border = AreaBorder(
                    area_border_id=generate_unique_id(),
                    border_vertices=self._convert_way_to_vertices(way),
                    adjacent=[],
                    line_marking=None,
                )
                area_border_list.append(area_border)

                # line_marking
                area_border.line_marking = convert_type_subtype_to_line_marking_lanelet(
                    way.tag_dict, multipolygon=True
                )[0]

                # an area border is adjacent to a lanelet if they share at least one point
                for lanelet in self.lanelet_network.lanelets:
                    left = [
                        np.isin(x, area_border.border_vertices).all() for x in lanelet.left_vertices
                    ]
                    right = [
                        np.isin(x, area_border.border_vertices).all()
                        for x in lanelet.right_vertices
                    ]
                    if (True in left) or (True in right):
                        area_border.adjacent.append(lanelet.lanelet_id)

            area_types = set()
            area_types.add(
                multipolygon.tag_dict.get("subtype")
            )  # can subtype have multiple values?
            self.lanelet_network.add_area(
                Area(area_id=area_id, border=area_border_list, area_types=area_types), set()
            )

        # speed limit sign conversion
        for speed_limit_key in osm.speed_limit_signs.keys():
            # only convert speed limit signs which are assigned to a lanelet
            if speed_limit_lanelets[speed_limit_key]:
                speed, traffic_sign_id = osm.speed_limit_signs[speed_limit_key]
                light_id = speed_limits[speed_limit_key]
                first_occurrence = {
                    self.lanelet_network._old_lanelet_ids[l_id]
                    for l_id in speed_limit_lanelets[speed_limit_key]
                }
                position = self.lanelet_network.find_lanelet_by_id(
                    self.lanelet_network._old_lanelet_ids[speed_limit_lanelets[speed_limit_key][0]]
                ).left_vertices[0]
                speed_limit = TrafficSign(
                    light_id,
                    [TrafficSignElement(traffic_sign_id, [speed])],
                    first_occurrence,
                    position,
                    True,
                )
                self.lanelet_network.add_traffic_sign(speed_limit, first_occurrence)

        # traffic light conversion
        for way in osm.ways:
            if osm.ways[way].tag_dict.get("type") == "traffic_light":
                self.traffic_light_conversion(osm.ways[way], new_ids)

        for la in self.lanelet_network.lanelets:
            la.__class__ = Lanelet
        self.lanelet_network.__class__ = LaneletNetwork

        # if lanelet2 map is a sub-map of another map, relations could be wrong
        self.lanelet_network.cleanup_lanelet_references()
        self.lanelet_network.cleanup_traffic_sign_references()
        self.lanelet_network.cleanup_traffic_light_references()

        scenario.add_objects(self.lanelet_network)

        return scenario

    def traffic_light_conversion(self, traffic_light_way: Way, new_lanelet_ids: Dict[str, int]):
        """
        Converting a traffic light, which is formatted as Way in Lanelet2 format, to
        CommonRoad format

        :param traffic_light_way: Way that is being used for conversion
        :param new_lanelet_ids: Dictionary that appends new ids to newly created CR objects
        """
        # create a TrafficLight element (CR format) from the traffic light way (L2 format\<)
        # id,cycle,position,offset,direction,active
        # for autoware, the traffic light id is retained
        if self._config.autoware:
            new_id = int(traffic_light_way.id_)
            active = False
            cycle_list = [TrafficLightCycleElement(TrafficLightState.INACTIVE, 5)]

        else:
            new_id = generate_unique_id()
            active = True
            cycle_list = _append_traffic_light_cycles(traffic_light_way)

        # TL in L2 format is represented with 3 nodes, we will take the one in the middle
        node = self.osm.nodes[traffic_light_way.nodes[1]]

        # convert to CR space
        x, y = self.transformer.transform(node.lon, node.lat)
        x -= self.origin_utm[0]
        y -= self.origin_utm[1]

        position = np.array([x, y, float(node.ele)]) if node.ele != "0.0" else np.array([x, y])

        # need to assign lanelet to that trafficLight
        # find the traffic_light_relations corresponding to our traffic_light_way and add them to the list
        traffic_light_relations = []
        for tl_relation in self.osm.traffic_light_relations:
            for ref in self.osm.traffic_light_relations[tl_relation].refers:
                if ref == traffic_light_way.id_:
                    traffic_light_relations.append(tl_relation)

        # now go through the lanelets and find the relation, which would match the traffic light and the lanelet
        wr_lanelets = set()
        for wr in self.osm.way_relations:
            for re in self.osm.way_relations[wr].regulatory_elements:
                if re in traffic_light_relations:
                    # found the wr, now need to match it with corresponding lanelet
                    # for that the "new_lanelet_ids" dict is used that is sent to this function
                    wr_lanelets.add(new_lanelet_ids[wr])

        # create the traffic light
        traffic_light = TrafficLight(
            new_id,
            position,
            TrafficLightCycle(cycle_list, 1),
            active=active,
            direction=TrafficLightDirection.STRAIGHT,
        )

        # add the traffic light to our lanelet network
        self.lanelet_network.add_traffic_light(traffic_light, wr_lanelets)

    def _right_of_way_to_traffic_sign(
        self, right_of_way_rel: RegulatoryElement, new_lanelet_ids: Dict[str, int]
    ) -> Tuple[List[TrafficSign], List[TrafficSign], List[int], List[int], List[StopLine]]:
        """
        One right_of_way regulatory element maps pretty well into commonroad scenarios
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

        :param right_of_way_rel: corresponding RegulatoryElement object
        :param new_lanelet_ids: dictionary of the lanelet IDs
        :return: Tuple with the relevant attributes extracted from the regulatory element
        """

        traffic_sign_ways = [self.osm.find_way_by_id(r) for r in right_of_way_rel.refers]
        # traffic signs will always be "ways"
        # https://github.com/fzi-forschungszentrum-informatik/Lanelet2/blob/master/lanelet2_core/doc
        # /LinestringTagging.md

        priority_signs, yield_signs = self._traffic_sign_ways_to_traffic_signs(traffic_sign_ways)

        priority_lanelets = []
        for i in right_of_way_rel.right_of_ways:
            # never create new lanelet ids here,
            # if they don't exist yet, they are never created
            if i in new_lanelet_ids.keys():
                priority_lanelets.append(new_lanelet_ids[i])
            else:
                logging.warning(
                    "Lanelet2CRConverter::_right_of_way_to_traffic_sign: some priority sign "
                    "references non-existing lanelet {}".format(i)
                )

        yield_lanelets = []
        for i in right_of_way_rel.yield_ways:
            # never create new lanelet ids here,
            # if they don't exist yet, they are never created
            if i in new_lanelet_ids.keys():
                yield_lanelets.append(new_lanelet_ids[i])
            else:
                logging.warning(
                    "Lanelet2CRConverter::_right_of_way_to_traffic_sign: some yield sign "
                    "references non-existing lanelet {}".format(i)
                )

        stop_lines = []
        for stop_line in right_of_way_rel.ref_line:
            # extract geometrical features
            stop_line_way = self.osm.find_way_by_id(stop_line)
            stop_line_way_vertices = self._convert_way_to_vertices(stop_line_way)
            start = stop_line_way_vertices[0]
            end = stop_line_way_vertices[-1]

            # retrieve the closest yield traffic sign if any
            # ref_t_id = None
            ref_t_set_id = set()
            _ref_t_min_dist = None
            for ref_t in yield_signs:
                d = point_to_line_distance(ref_t.position, start, end)
                if _ref_t_min_dist is None or d < _ref_t_min_dist:
                    ref_t_set_id = {ref_t.traffic_sign_id}
                    _ref_t_min_dist = d

            # initialize stop line
            stop_line = StopLine(
                start=start,
                end=end,
                traffic_sign_ref=ref_t_set_id,
                line_marking=LineMarking.BROAD_DASHED,
            )
            stop_lines.append(stop_line)
        return yield_signs, priority_signs, yield_lanelets, priority_lanelets, stop_lines

    def _traffic_sign_ways_to_traffic_signs(
        self, traffic_sign_ways: List
    ) -> Tuple[List[TrafficSign], List[TrafficSign]]:
        """
        Converts traffic sign ways (L2) into traffic signs (CR)

        :param traffic_sign_ways: ways that will be converted into traffic signs
        :return: tuple of lists that match according to the priority of the traffic sign.
        """

        priority_signs, yield_signs = [], []
        for traffic_sign_way in traffic_sign_ways:
            # distinguish yield and stop sign
            # also handles right of way and priority road

            # extract the id of the sign, i.e. "de205"
            traffic_sign_type = traffic_sign_way.tag_dict.get("subtype")

            # extract the visual attribute
            virtual = traffic_sign_way.tag_dict.get("virtual", "no") == "yes"

            # extract the position of the traffic sign
            traffic_sign_node = self.osm.find_node_by_id(traffic_sign_way.nodes[0])

            # Lanelet2 has the format of the sign as "a-za-z[a-zA-Z0-9]+"
            # CR format of signs is same excluding the first 2 country letters, i.e. CR-"205" = L2-"de205"
            # Remove the country prefix, and focus on the numbered value.
            # Iterate through the Enums of signs in each country to find the corresponding sing value

            filtered_traffic_sign_type_name = traffic_sign_type[
                2:
            ]  # removing 2 country-prefix letters

            # iterate through the list of enum classes to find the corresponding country based on the code
            supported_country_list = [TrafficSignIDGermany, TrafficSignIDUsa, TrafficSignIDZamunda]

            # find the traffic sign
            traffic_sign_found = False
            tsid = TrafficSignIDZamunda.STOP  # default sign
            for country in supported_country_list:
                for country_sign in country:
                    if country_sign.value == filtered_traffic_sign_type_name:
                        # traffic sign ID 252 is replaced by 260
                        if (
                            country is TrafficSignIDGermany or country is TrafficSignIDZamunda
                        ) and country_sign.value == "252":
                            tsid = country("260")
                        else:
                            tsid = country(country_sign.value)
                        traffic_sign_found = True
                if traffic_sign_found:
                    break
            if traffic_sign_found == 0:
                raise NotImplementedError(
                    f"Lanelet type {traffic_sign_way.tag_dict['subtype']} not implemented"
                )

            # create the element of the traffic sign
            traffic_sign_element = TrafficSignElement(tsid, [])

            # extract position
            x, y = self.transformer.transform(
                float(traffic_sign_node.lat), float(traffic_sign_node.lon)
            )
            x -= self.origin_utm[0]
            y -= self.origin_utm[1]
            ref_t_id = generate_unique_id()
            position = (
                np.array([x, y, float(traffic_sign_node.ele)])
                if traffic_sign_node.ele != "0.0"
                else np.array([x, y])
            )

            # create the traffic sign
            traffic_sign = TrafficSign(
                ref_t_id,
                traffic_sign_elements=[traffic_sign_element],
                first_occurrence=set(),
                position=position,
                virtual=virtual,
            )
            # traffic sign names need to be universal(i.e."YIELD" should be the name of both German and USA Yield signs)

            # append the sign to either priority or yield signs
            if tsid.name in self._config.priority_signs:
                priority_signs.append(traffic_sign)
            else:
                yield_signs.append(traffic_sign)

        return priority_signs, yield_signs

    def _way_rel_to_lanelet(
        self,
        way_rel: WayRelation,
        detect_adjacencies,
        left_driving_system=False,
        speed_limit_dict: Optional[Dict[int, int]] = None,
        speed_limit_lanelets: Optional[Dict[int, list]] = None,
    ) -> Optional[ConversionLanelet]:
        """
        Convert a WayRelation to a Lanelet, add additional adjacency information.
        The ConversionLaneletNetwork saves the adjacency and predecessor/successor
        information.

        :param way_rel: Relation of OSM to convert to Lanelet.
        :param detect_adjacencies: Compare vertices which might be adjacent. Set
            to false if you consider it too computationally intensive.
        :param left_driving_system: Set to true if map describes a left_driving_system.
        :param speed_limit_dict: Dictionary with regulatory_element_id to TrafficSign mapping
        :param speed_limit_lanelets: mapping from speed_limit_ids to lanelets that use speed Limit
        :return: A lanelet with a right and left vertex
        """
        if speed_limit_dict is None:
            speed_limit_dict = {}
        if speed_limit_lanelets is None:
            speed_limit_lanelets = {}

        left_way = self.osm.find_way_by_id(way_rel.left_way)
        right_way = self.osm.find_way_by_id(way_rel.right_way)

        # a conversion bug happens if the outer ways of adjacent lanelets don't have the same number of nodes
        # it is solved in 'repair_normal_adjacency' function of the LaneletRepairing class.
        if len(left_way.nodes) != len(right_way.nodes):
            logging.info(
                "Lanelet2CRConverter::_way_rel_to_lanelet: Trying to fix relation {}...".format(
                    way_rel.id_
                )
            )

            self._fix_relation_unequal_ways(left_way, right_way)

        # If for some reason, relation couldn't be fixed, notify user
        if len(left_way.nodes) != len(right_way.nodes):
            logging.error(
                "Lanelet2CRConverter::_way_rel_to_lanelet: Error: Relation {} has left and right "
                "ways which are not equally long! Please check your data! Discarding this "
                "lanelet relation.".format(way_rel.id_)
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

        start_dist = np.linalg.norm(left_vertices[0] - right_vertices[0]) + np.linalg.norm(
            left_vertices[-1] - right_vertices[-1]
        )

        end_dist = np.linalg.norm(left_vertices[0] - right_vertices[-1]) + np.linalg.norm(
            left_vertices[-1] - right_vertices[0]
        )

        if start_dist > end_dist:
            if left_driving_system:
                # reverse right vertices if right_way is reversed
                right_vertices = right_vertices[::-1]
                first_right_node, last_right_node = (last_right_node, first_right_node)
            else:
                # reverse left vertices if left_way is reversed
                left_vertices = left_vertices[::-1]
                first_left_node, last_left_node = (last_left_node, first_left_node)

        # set center vertices
        center_vertices = np.array(
            [(left + right) / 2 for (left, right) in zip(left_vertices, right_vertices)]
        )

        wrong_left_right_boundary_side = _wrong_left_right_boundary_side(
            center_vertices, left_vertices, right_vertices, lanelet2_config
        )

        if wrong_left_right_boundary_side:
            left_vertices, right_vertices = (
                np.flip(left_vertices, axis=0),
                np.flip(right_vertices, axis=0),
            )
            center_vertices = (left_vertices + right_vertices) / 2
            first_left_node, last_left_node = (last_left_node, first_left_node)
            first_right_node, last_right_node = (last_right_node, first_right_node)

        # set first and last points
        self.first_left_pts[first_left_node].append(way_rel.id_)
        self.last_left_pts[last_left_node].append(way_rel.id_)
        self.first_right_pts[first_right_node].append(way_rel.id_)
        self.last_right_pts[last_right_node].append(way_rel.id_)

        # extract special meaning like way, direction and road type
        lanelet_type, users_one_way, users_bidirectional = _extract_special_meaning_to_lanelet(
            way_rel
        )

        traffic_signs = []
        for key in way_rel.regulatory_elements:
            if speed_limit_dict.get(key) is not None:
                traffic_signs.append(speed_limit_dict[key])
                speed_limit_lanelets[key].append(way_rel.id_)

        if len(traffic_signs) == 0:
            traffic_signs = set()
        else:
            traffic_signs = set(traffic_signs)

        left_linemarking, second_left_linemarking = convert_type_subtype_to_line_marking_lanelet(
            left_way.tag_dict
        )
        right_linemarking, second_right_linemarking = convert_type_subtype_to_line_marking_lanelet(
            right_way.tag_dict
        )

        lanelet = ConversionLanelet(
            left_vertices=left_vertices,
            center_vertices=center_vertices,
            right_vertices=right_vertices,
            lanelet_id=way_rel.id_,
            parametric_lane_group=None,
            user_one_way=users_one_way,
            user_bidirectional=users_bidirectional,
            lanelet_type=lanelet_type,
            traffic_signs=traffic_signs,
            line_marking_left_vertices=left_linemarking,
            line_marking_right_vertices=right_linemarking,
        )

        self._check_right_and_left_neighbors(way_rel, lanelet)

        potential_successors = self._check_for_successors(
            last_left_node=last_left_node, last_right_node=last_right_node
        )
        self.lanelet_network.add_successors_to_lanelet(lanelet, potential_successors)

        potential_predecessors = self._check_for_predecessors(
            first_left_node=first_left_node, first_right_node=first_right_node
        )
        self.lanelet_network.add_predecessors_to_lanelet(lanelet, potential_predecessors)

        potential_adj_left, potential_adj_right = self._check_for_split_and_join_adjacencies(
            first_left_node, first_right_node, last_left_node, last_right_node
        )
        if potential_adj_left:
            self.lanelet_network.set_adjacent_left(lanelet, potential_adj_left[0], True)
        if potential_adj_right:
            self.lanelet_network.set_adjacent_right(lanelet, potential_adj_right[0], True)

        if detect_adjacencies:
            self._find_adjacencies_of_coinciding_ways(
                lanelet,
                first_left_node,
                first_right_node,
                last_left_node,
                last_right_node,
            )

        # adjusting the l2 line marking style to the cr line marking style
        if second_left_linemarking:
            if self.lanelet_network.find_lanelet_by_id(lanelet.adj_left):
                adjacent_left = self.lanelet_network.find_lanelet_by_id(lanelet.adj_left)
                if lanelet.adj_left_same_direction:
                    adjacent_left.line_marking_right_vertices = second_left_linemarking
                else:
                    adjacent_left.line_marking_left_vertices = second_left_linemarking

        if second_right_linemarking:
            if self.lanelet_network.find_lanelet_by_id(lanelet.adj_right):
                adjacent_right = self.lanelet_network.find_lanelet_by_id(lanelet.adj_right)
                if lanelet.adj_right_same_direction:
                    adjacent_right.left_marking_left_vertices = second_right_linemarking
                else:
                    adjacent_right.right_marking_right_vertices = second_right_linemarking

        return lanelet

    def _fix_relation_unequal_ways(self, left_way: Way, right_way: Way):
        """
        Fix the way relation if the nodes of the ways are not the same

        :param left_way:
        :param right_way:
        """
        if len(left_way.nodes) == len(right_way.nodes):
            return
        if len(left_way.nodes) < len(right_way.nodes):
            self.create_additional_nodes(left_way, right_way)
        else:
            self.create_additional_nodes(right_way, left_way)

    def _check_for_split_and_join_adjacencies(
        self, first_left_node, first_right_node, last_left_node, last_right_node
    ) -> Tuple[List, List]:
        """
        Check if there are adjacencies if there is a lanelet split or join.
        joining and splitting lanelets have to be adjacent rights or lefts
        splitting lanelets share both starting points and one last point
        joining lanelets share two last points and one start point

        :param first_left_node: First node of left way of the lanelet.
        :param first_right_node: First node of right way of the lanelet.
        :param last_left_node: Last node of left way of the lanelet.
        :param last_right_node: Last node of right way of the lanelet.
        :return: A tuple of lists which contain candidates for the
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

    def _check_for_predecessors(self, first_left_node: str, first_right_node: str) -> List:
        """
        Check whether the first left and right node are last nodes of another lanelet.

        :param first_left_node: Id of a node which is at the start of the left way.
        :param first_right_node: Id of a node which is at the start of the right way.
        :return: List of ids of lanelets where the nodes are at their end.
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
        """
        Check whether the last left and right node are first nodes of another lanelet.

        :param last_left_node: Id of a node which is at the end of the left way.
        :param last_right_node: Id of a node which is at the end of the right way.
        :return: List of ids of lanelets where the nodes are at their start.
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
        """
        Find adjacencies of a lanelet by checking if its vertices coincide with vertices of other lanelets.
        Set new adjacent left or right if it finds neighbors.

        :param lanelet: Lanelet to check potential adjacencies for.
        :param first_left_node: Id of first left node of the lanelet relation in OSM.
        :param first_right_node: Id of first right node of the lanelet relation in OSM.
        :param last_left_node: Id of last left node of the lanelet relation in OSM.
        :param last_right_node: Id of last right node of the lanelet relation in OSM.
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
                    lanelet.left_vertices,
                    nb_lanelet.right_vertices,
                    self._config.adjacent_way_distance_tolerance,
                ):
                    self.lanelet_network.set_adjacent_left(lanelet, nb_lanelet.lanelet_id, True)
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
                    lanelet.right_vertices,
                    nb_lanelet.left_vertices,
                    self._config.adjacent_way_distance_tolerance,
                ):
                    self.lanelet_network.set_adjacent_right(lanelet, nb_lanelet.lanelet_id, True)
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
                # compare right vertex of nb_lanelet with left vertex of lanelet
                if nb_lanelet is not None and _two_vertices_coincide(
                    lanelet.left_vertices,
                    nb_lanelet.left_vertices[::-1],
                    self._config.adjacent_way_distance_tolerance,
                ):
                    self.lanelet_network.set_adjacent_left(lanelet, nb_lanelet.lanelet_id, False)
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
                    lanelet.right_vertices,
                    nb_lanelet.right_vertices[::-1],
                    self._config.adjacent_way_distance_tolerance,
                ):
                    self.lanelet_network.set_adjacent_right(lanelet, nb_lanelet.lanelet_id, True)
                    break

    def _check_right_and_left_neighbors(self, way_rel: WayRelation, lanelet: ConversionLanelet):
        """
        Check if lanelet has adjacent right and lefts.
        Determines it by checking if they share a common way.
        Either in opposite or in the same direction.

        :param way_rel: Relation from which lanelet was created.
        :param lanelet: Lanelet for which to check adjacencies.
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
                self.lanelet_network.set_adjacent_left(lanelet, potential_left_adj, False)

        if not potential_right_adj:
            potential_right_adj = self._right_way_ids.get(way_rel.right_way)
            if potential_right_adj is not None:
                self.lanelet_network.set_adjacent_right(lanelet, potential_right_adj, False)

    def _convert_way_to_vertices(self, way: Way) -> np.ndarray:
        """
        Convert a Way to a list of points.

        :param way: Way to be converted.
        :return: The vertices of the new lanelet border.
        """
        if any([self.osm.find_node_by_id(node_id).ele != "0.0" for node_id in way.nodes]):
            vertices = np.empty((len(way.nodes), 3))
        else:
            vertices = np.empty((len(way.nodes), 2))
        for i, node_id in enumerate(way.nodes):
            nd = self.osm.find_node_by_id(node_id)
            x, y = self.transformer.transform(float(nd.lat), float(nd.lon))
            x -= self.origin_utm[0]
            y -= self.origin_utm[1]
            vertices[i] = [x, y, float(nd.ele)] if nd.ele != "0.0" else [x, y]

        return vertices

    def node_distance(self, node_id1: str, node_id2: str) -> float:
        """
        Calculate distance of one node to other node in the projection.

        :param node_id1: Id of first node.
        :param node_id2: id of second node.
        :return: Distance of the nodes
        """
        node1 = self.osm.find_node_by_id(node_id1)
        node2 = self.osm.find_node_by_id(node_id2)
        vec1 = np.array(self.transformer.transform(float(node1.lat), float(node1.lon)))
        vec2 = np.array(self.transformer.transform(float(node2.lat), float(node2.lon)))
        return np.linalg.norm(vec1 - vec2)

    def _find_lanelet_ids_of_suitable_nodes(
        self, nodes_dict: Dict[str, List[str]], node_id: str
    ) -> List:
        """
        Find values of a dict where the keys are node ids.
        Return the entries if there is a value in the node_dict
        for the node_id, but also the values for nodes which are in
        the proximity of the node with the node_id.

        :param nodes_dict: Dict which saves lanelet ids with node ids as keys.
        :param node_id: Id of node for which the other entries are searched for.
        :return: List of lanelet ids which match the above-mentioned rules.
        """
        suitable_lanelet_ids = []
        suitable_lanelet_ids.extend(nodes_dict.get(node_id, []))
        for nd, lanelet_ids in nodes_dict.items():
            if self.node_distance(nd, node_id) < self._config.node_distance_tolerance:
                suitable_lanelet_ids.extend(lanelet_ids)
        return suitable_lanelet_ids

    def create_additional_nodes(self, shorter_way: Way, longer_way: Way):
        """
        Function that creates additional nodes and adds them to the shorter way in order
        to fix the relation of unequal ways

        :param shorter_way: Way that has a shorter length than the other one
        :param longer_way: Way that has a longer length than the other one
        """
        n = len(longer_way.nodes) - len(shorter_way.nodes)
        # Coordinates of two nodes in the middle to interpolate and add n nodes in between
        mid = int(len(shorter_way.nodes) / 2)
        start_node = self.osm.find_node_by_id(shorter_way.nodes[mid])
        end_node = self.osm.find_node_by_id(shorter_way.nodes[mid - 1])
        # Parse to nodes with numeric values
        start_node_f = np.array(
            [float(start_node.lat), float(start_node.lon), float(start_node.ele)]
        )
        end_node_f = np.array([float(end_node.lat), float(end_node.lon), float(end_node.ele)])
        # Add n nodes, start from last one
        for i in range(n, 0, -1):
            k = self._config.start_node_id_value
            new_id = int(start_node.id_) + k * 100 + i
            while self.osm.find_node_by_id(str(new_id)) is not None:
                k = k + 1
                new_id = int(start_node.id_) + k * 100 + i
            # For Getting n additional nodes, we need to split the segment into n+1 smaller segments
            new_lat = round(start_node_f[0] + (end_node_f[0] - start_node_f[0]) * i / (n + 1), 11)
            new_lon = round(start_node_f[1] + (end_node_f[1] - start_node_f[1]) * i / (n + 1), 11)
            new_ele = round(start_node_f[2] + (end_node_f[2] - start_node_f[2]) * i / (n + 1), 11)
            new_node = Node(new_id, new_lat, new_lon, new_ele)
            self.osm.add_node(new_node)
            shorter_way.nodes.insert(mid, new_node.id_)
