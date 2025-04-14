import copy
from collections import deque
from typing import Dict, List, Optional, Set, Tuple

import iso3166
import numpy as np
from commonroad.scenario.lanelet import (
    Lanelet,
    LaneletNetwork,
    LaneletType,
    LineMarking,
    StopLine,
)
from commonroad.scenario.scenario import (
    GeoTransformation,
    Location,
    Scenario,
    ScenarioID,
)
from commonroad.scenario.traffic_sign import (
    TrafficSign,
    TrafficSignElement,
    TrafficSignIDChina,
    TrafficSignIDGermany,
    TrafficSignIDRussia,
    TrafficSignIDSpain,
    TrafficSignIDUsa,
    TrafficSignIDZamunda,
)
from pyproj import CRS, Transformer

from crdesigner.common.common_file_reader_writer import project_lanelet
from crdesigner.common.config.general_config import GeneralConfig, general_config
from crdesigner.common.config.opendrive_config import OpenDriveConfig, open_drive_config
from crdesigner.map_conversion.common.conversion_lanelet import ConversionLanelet
from crdesigner.map_conversion.common.conversion_lanelet_network import (
    ConversionLaneletNetwork,
)
from crdesigner.map_conversion.common.utils import generate_unique_id
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_conversion import utils
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_conversion.converter import (
    OpenDriveConverter,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_conversion.plane_elements.crosswalks import (
    get_crosswalks,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_conversion.plane_elements.geo_reference import (
    get_geo_reference,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_conversion.plane_elements.plane_group import (
    ParametricLaneGroup,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_conversion.plane_elements.traffic_signals import (
    assign_traffic_signals_to_road,
    get_traffic_signal_references,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_conversion.utils import (
    encode_road_section_lane_width_id,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.opendrive import (
    OpenDrive,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.road import (
    Road,
)


def get_all_adjacent_lanelets(lanelet_network, incoming_lanelet_id):
    """
    Get all adjacent lanelets of the incoming lanelet, considering transitive adjacency.

    :param lanelet_network: Lanelet network object to find lanelets by ID.
    :param incoming_lanelet_id: ID of the incoming lanelet.
    :return: Set of all adjacent lanelets, including transitive adjacency.
    """
    # Initialize a set to store all lanelets, including transitive adjacent ones
    all_adjacent_lanelets = {incoming_lanelet_id}

    # Use a queue to process lanelets iteratively
    queue = [incoming_lanelet_id]

    # Track visited lanelets to avoid processing the same lanelet twice
    visited = {incoming_lanelet_id}

    while queue:
        current_lanelet = queue.pop(0)
        # Get adjacent lanelets (left and right neighbors)
        adjacent_lanelets = set()
        lanelet = lanelet_network.find_lanelet_by_id(current_lanelet)
        if lanelet.adj_left is not None:
            adjacent_lanelets.add(lanelet.adj_left)
        if lanelet.adj_right is not None:
            adjacent_lanelets.add(lanelet.adj_right)

        # Add new adjacent lanelets to the set and queue
        for adj_lanelet in adjacent_lanelets:
            if adj_lanelet not in visited:
                visited.add(adj_lanelet)
                all_adjacent_lanelets.add(adj_lanelet)
                queue.append(adj_lanelet)

    return all_adjacent_lanelets


def update_line_markings(lanelet_network: ConversionLaneletNetwork) -> ConversionLaneletNetwork:
    """
    Updates line markings of lanelets vertices in the conversion lanelet network,
    as Opendrive format only supports line markings for the outer vertices of the lanelet.
    If the two lanelets are adjacent, corresponding line marking of the shared vertices should be the same.

    :param lanelet_network: ConversionLaneletNetwork that should be updated.
    :return: Updated ConversionLaneletNetwork.
    """
    for la in lanelet_network.lanelets:
        # left vertices line marking
        if la.line_marking_left_vertices is LineMarking.UNKNOWN:
            # check if there exists an adjacent left lanelet
            if la.adj_left is not None:
                # if the adjacent left lanelet is of the same direction, copy the line marking of the right vertices
                if la.adj_left_same_direction is True:
                    la.line_marking_left_vertices = lanelet_network.find_lanelet_by_id(
                        la.adj_left
                    ).line_marking_right_vertices
                else:
                    la.line_marking_left_vertices = lanelet_network.find_lanelet_by_id(
                        la.adj_left
                    ).line_marking_left_vertices
        # right vertices line marking
        if la.line_marking_right_vertices is LineMarking.UNKNOWN:
            # check if there exists an adjacent right lanelet
            if la.adj_right is not None:
                # if the adjacent right lanelet is of the same direction, copy the line marking of the left
                if la.adj_right_same_direction is True:
                    la.line_marking_right_vertices = lanelet_network.find_lanelet_by_id(
                        la.adj_right
                    ).line_marking_left_vertices
                else:
                    la.line_marking_right_vertices = lanelet_network.find_lanelet_by_id(
                        la.adj_right
                    ).line_marking_right_vertices

    return lanelet_network


def convert_to_base_lanelet_network(lanelet_network: ConversionLaneletNetwork) -> LaneletNetwork:
    """Converts a ConversionLaneletNetwork to a LaneletNetwork.

    :param lanelet_network: ConversionLaneletNetwork that should be converted to a LaneletNetwork.
    :return: The converted LaneletNetwork.
    """
    network = LaneletNetwork()
    for inter in lanelet_network.intersections:
        network.add_intersection(inter)
    for sign in lanelet_network.traffic_signs:
        network.add_traffic_sign(sign, set())
    for light in lanelet_network.traffic_lights:
        network.add_traffic_light(light, set())
    for la in lanelet_network.lanelets:
        network.add_lanelet(
            Lanelet(
                la.left_vertices,
                la.center_vertices,
                la.right_vertices,
                la.lanelet_id,
                la.predecessor,
                la.successor,
                la.adj_left,
                la.adj_left_same_direction,
                la.adj_right,
                la.adj_right_same_direction,
                la.line_marking_left_vertices,
                la.line_marking_right_vertices,
                la.stop_line,
                la.lanelet_type,
                la.user_one_way,
                la.user_bidirectional,
                la.traffic_signs,
                la.traffic_lights,
            )
        )
    return network


class Network:
    """Represents a network of parametric lanes, with a LinkIndex
    which stores the neighbor relations between the parametric lanes.
    """

    def __init__(self, config: OpenDriveConfig = open_drive_config):
        """Initializes a network object."""
        self._config = config
        self._planes: List[ParametricLaneGroup] = []
        self._link_index = None
        self._geo_ref = None
        self._offset = None
        self._traffic_lights = []
        self._traffic_signs = []
        self._stop_lines = []
        self._crosswalks = []
        self._country_ID = None

    def assign_country_id(self, value: str):
        """Assign country ID according to the ISO 3166-1 3 letter standard

        :param value: Nae of location as a string.
        """
        value = value.upper()
        if value in iso3166.countries_by_name:
            self._country_ID = iso3166.countries_by_name[value].alpha3
        elif value in iso3166.countries_by_alpha2:
            self._country_ID = iso3166.countries_by_alpha2[value].alpha3
        elif value in iso3166.countries_by_alpha3:
            self._country_ID = value
        else:
            self._country_ID = "ZAM"

    def load_opendrive(self, opendrive: OpenDrive):
        """Load all elements of an OpenDRIVE network to a parametric lane representation

        :param opendrive: OpenDRIVE network whose elements should be loaded.
        """
        # TODO: Extract location information from Geotranformation in opendrive
        # proj_string_transformed = Transformer.from_pipeline(opendrive.header.geo_reference)

        self._link_index = LinkIndex()
        self._link_index.create_from_opendrive(opendrive)

        self._geo_ref = opendrive.header.geo_reference
        self._offset = opendrive.header.offset

        # Get country ID form signal data in openDrive and set it as attribute of the network object
        self.assign_country_id(Network.get_country_id_from_opendrive(opendrive.roads))

        # extract signal references beforehand to be able to assign them correctly
        traffic_light_dirs: Dict[str, Set[str]] = {}
        traffic_light_lanes: Dict[str, Tuple[int, int]] = {}
        for road in opendrive.roads:
            get_traffic_signal_references(road, traffic_light_dirs, traffic_light_lanes)

        # Convert all parts of a road to parametric lanes (planes)
        for road in opendrive.roads:
            road.plan_view.precalculate()
            self._extract_road_speed_limit(road)

            # The reference border is the baseline for the whole road
            reference_border = OpenDriveConverter.create_reference_border(
                road.plan_view, road.lanes.lane_offsets
            )

            # Extracting signals, signs and stop lines from each road
            traffic_lights, traffic_signs, stop_lines = assign_traffic_signals_to_road(
                road, traffic_light_dirs, traffic_light_lanes
            )
            self._traffic_lights.extend(traffic_lights)
            self._traffic_signs.extend(traffic_signs)
            self._stop_lines.extend(stop_lines)

            # Get crosswalks
            self._crosswalks.extend(get_crosswalks(road))

            # stop lines from road objects
            self._stop_lines_from_road(road)

            # A lane section is the smallest part that can be converted at once
            for lane_section in road.lanes.lane_sections:
                parametric_lane_groups = OpenDriveConverter.lane_section_to_parametric_lanes(
                    lane_section,
                    reference_border,
                    road.cr_traffic_lights,
                    road.cr_traffic_signs,
                    road.cr_stop_lines,
                    road.driving_direction,
                )

                self._planes.extend(parametric_lane_groups)

                # check if parametric lane group is not part of intersection

                for intersection in self._link_index.intersection_maps():
                    incomings_to_remove = []
                    for incoming_lane_id, successors in intersection.items():
                        for lane_group in parametric_lane_groups:
                            if (
                                lane_group.id_ == incoming_lane_id or lane_group.id_ in successors
                            ) and lane_group.type != "driving":
                                incomings_to_remove.append(incoming_lane_id)
                    for incoming in incomings_to_remove:
                        del intersection[incoming]

    def _extract_road_speed_limit(self, road: Road):
        """
        Extract road speed limit and assign it lanes.

        :param road: Road to evaluate.
        """
        if road.types:
            for road_type in road.types:
                if road_type.speed:
                    max_speed = road_type.speed.max  # possible values: "no limit", "undefined", int
                    unit_speed = road_type.speed.unit  # possible values: "km/h", "m/s", "mph"

                    if max_speed == "no limit" or max_speed == "undefined":
                        break

                    else:
                        max_speed = float(max_speed)

                        # convert km/h or mph to m/s
                        if unit_speed == "km/h":
                            max_speed = max_speed * 0.277
                        elif unit_speed == "mph":
                            max_speed = max_speed * 0.447

                        # assign the road speed limit to all road sections that don't have a speed limit
                        for section in road.lanes.lane_sections:
                            # check the position of the road section and the starting position of a road type
                            if section.sPos >= road_type.start_pos:
                                for rightLane in section.right_lanes:
                                    if rightLane.speed is None:
                                        rightLane.speed = max_speed
                                for leftLane in section.left_lanes:
                                    if leftLane.speed is None:
                                        leftLane.speed = max_speed
                                for centerLane in section.center_lanes:
                                    if centerLane.speed is None:
                                        centerLane.speed = max_speed

    def _stop_lines_from_road(self, road: Road):
        """
        Extracts stop lines from road.

        :param road: Road to extract stop lines from.
        """
        for road_object in road.objects:
            if road_object.name == "StopLine":
                position, tangent, _, _ = road.plan_view.calc(
                    road_object.s, compute_curvature=False
                )
                position = np.array(
                    [
                        position[0] + road_object.t * np.cos(tangent + np.pi / 2),
                        position[1] + road_object.t * np.sin(tangent + np.pi / 2),
                    ]
                )

                angle = road_object.hdg + tangent
                # check if stop line is orthogonal to reference line
                if np.round(tangent) == 0:
                    angle = np.pi / 2
                # check orientation of stop line
                if road_object.orientation == "+":
                    position_1 = np.array(
                        [
                            position[0] - 0.5 * road_object.validLength * np.cos(angle),
                            position[1] - 0.5 * road_object.validLength * np.sin(angle),
                        ]
                    )
                    position_2 = np.array(
                        [
                            position[0] + 0.5 * road_object.validLength * np.cos(angle),
                            position[1] + 0.5 * road_object.validLength * np.sin(angle),
                        ]
                    )
                else:
                    position_1 = np.array(
                        [
                            position[0] + 0.5 * road_object.validLength * np.cos(angle),
                            position[1] + 0.5 * road_object.validLength * np.sin(angle),
                        ]
                    )
                    position_2 = np.array(
                        [
                            position[0] - 0.5 * road_object.validLength * np.cos(angle),
                            position[1] - 0.5 * road_object.validLength * np.sin(angle),
                        ]
                    )

                stop_line = StopLine(position_1, position_2, LineMarking.SOLID)
                self._stop_lines.append(stop_line)

    def export_lanelet_network(
        self, transformer: Optional[Transformer], filter_types: Optional[List[str]] = None
    ) -> LaneletNetwork:
        """Export network as lanelet network.

        :param transformer: Coordinate projection transformer.
        :param filter_types: Types of ParametricLane objects to be filtered. Default value is None.
        :return: The converted LaneletNetwork object.
        """

        # Convert groups to lanelets
        lanelet_network = ConversionLaneletNetwork(self._config, transformer)

        for parametric_lane in self._planes:
            if filter_types is not None and parametric_lane.type not in filter_types:
                # Remove lanelets from intersections dictionary that do not fit the filtered type criterion
                self._link_index.clean_intersections(parametric_lane.id_)
                continue  # skip also for general lanelet generation
            lanelet = parametric_lane.to_lanelet(
                self._config.error_tolerance,
                self._config.min_delta_s,
                transformer,
                parametric_lane.driving_direction,
            )
            lanelet.predecessor = self._link_index.get_predecessors(parametric_lane.id_)
            lanelet.successor = self._link_index.get_successors(parametric_lane.id_)
            lanelet_network.add_lanelet(lanelet)

            # Create a map of lanelet_description to traffic signs/lights so that they can be assigned as
            # reference to the correct lanelets later

        # prune because some
        # successorIds get encoded with a non-existing successorID
        # of the lane link
        lanelet_network.prune_network()

        # concatenate possible lanelets with their successors
        replacement_id_map = lanelet_network.concatenate_possible_lanelets()
        self._link_index.concatenate_lanes_in_intersection_map(replacement_id_map)

        # Perform lane splits and joins
        lanelet_network.join_and_split_possible_lanes()

        lanelet_network.convert_all_lanelet_ids()
        self._link_index.update_intersection_lane_id(lanelet_network.old_lanelet_ids())
        # self.traffic_signal_elements.update_traffic_signs_map_lane_id(lanelet_network.old_lanelet_ids())

        for crosswalk in self._crosswalks:
            if transformer is not None:
                project_lanelet(crosswalk, transformer)
            lanelet_network.add_lanelet(crosswalk)

        # generating intersections
        incoming_lanelet_ids = set().union(
            *[
                get_all_adjacent_lanelets(lanelet_network, key)
                for intersection_map in self._link_index.intersection_maps()
                for key in intersection_map.keys()
            ]
        )
        for intersection_map in self._link_index.intersection_maps():
            # Remove lanelets that are not part of the network (as they are of a different type)
            intersection_id_counter = generate_unique_id()
            lanelet_network._old_lanelet_ids[intersection_id_counter] = intersection_id_counter
            lanelet_network.create_intersection(intersection_map, incoming_lanelet_ids)

        self.relate_crosswalks_to_intersection(lanelet_network)

        if transformer is not None:
            # Apply the transformer to traffic controls
            for xs in [
                self._traffic_lights,
                self._traffic_signs,
            ]:
                for x in xs:
                    x.position = np.array(transformer.transform(*x.position))
            for x in self._stop_lines:
                x.start = np.array(transformer.transform(*x.start))
                x.end = np.array(transformer.transform(*x.end))

        # Assign traffic signals, lights and stop lines to lanelet network
        lanelet_network.add_traffic_lights_to_network(self._traffic_lights)
        lanelet_network.add_traffic_signs_to_network(self._traffic_signs)
        lanelet_network.add_stop_lines_to_network(self._stop_lines)

        # create virtual traffic signs for individual lane speed limits
        drivable_lanelets = [
            lanelet.lanelet_id
            for lanelet in lanelet_network.lanelets
            if lanelet.lanelet_type
            not in [{LaneletType.BICYCLE_LANE}, {LaneletType.SIDEWALK}, {LaneletType.BORDER}]
        ]

        # for all lanelets with no predecessor and no traffic sign, add a virtual sign to the lanelet
        lanelet_with_no_pred = [
            lanelet
            for lanelet in drivable_lanelets
            if lanelet_network.find_lanelet_by_id(lanelet).predecessor == []
            and lanelet_network.find_lanelet_by_id(lanelet).speed is not None
        ]
        for lanelet in lanelet_with_no_pred:
            already_has_sign = False
            ids = lanelet_network.find_lanelet_by_id(lanelet).traffic_signs
            for sign_id in ids:
                sign = lanelet_network.find_traffic_sign_by_id(sign_id)
                elems = [
                    sign.traffic_sign_elements
                    for elem in sign.traffic_sign_elements
                    if elem.traffic_sign_element_id.name == "MAX_SPEED"
                ]

                if any(elems):
                    already_has_sign = True
                    break
            if not already_has_sign:
                self.add_virtual_traffic_sign(
                    lanelet_network.find_lanelet_by_id(lanelet), lanelet_network
                )

        self.find_lane_speed_changes(drivable_lanelets, lanelet_network)
        self.reference_traffic_signs_with_equal_speed(drivable_lanelets, lanelet_network)
        lanelet_network = update_line_markings(lanelet_network)
        return convert_to_base_lanelet_network(lanelet_network)

    def relate_crosswalks_to_intersection(self, lanelet_network: ConversionLaneletNetwork):
        """
        Find for each crossing the intersection it belongs to
        :param lanelet_network: ConversionLaneletNetwork
        """

        def is_relevant_intersection() -> bool:
            """
            checks whether a lanelet intersect an intersection
            :return: Boolean indicating satisfaction
            """
            for incoming in intersection.incomings:
                rel_lanelets = (
                    incoming.incoming_lanelets.union(incoming.successors_left)
                    .union(incoming.successors_right)
                    .union(incoming.successors_left)
                )
                for la_id in rel_lanelets:
                    la = lanelet_network.find_lanelet_by_id(la_id)
                    if la.polygon.shapely_object.intersects(crosswalk.polygon.shapely_object):
                        return True
            return False

        for crosswalk in self._crosswalks:
            for intersection in lanelet_network.intersections:
                if is_relevant_intersection():
                    intersection.crossings.add(crosswalk.lanelet_id)
                    break

    def reference_traffic_signs_with_equal_speed(
        self, lanelets: List[int], lanelet_network: ConversionLaneletNetwork
    ):
        """If there are multiple lanelets that all have an equal lane speed, finds the first traffic sign of any
        predecessor with the same speed and references it for all lanelets.

        :param lanelets: The lanelets to be considered.
        :param lanelet_network: The lanelet network that the lanelets belong to.
        """
        visited = []
        for lane in lanelets:
            visited.append(lane)
            lane = lanelet_network.find_lanelet_by_id(lane)
            speeds = [
                lanelet_network.find_lanelet_by_id(pred).speed
                for pred in lane.predecessor
                if lane.speed is not None
            ]
            if not speeds == [] and speeds.count(speeds[0]) == len(speeds):
                # lane speeds are all the same, find first sign with equal speed
                predecessors = deque(lane.predecessor)
                # if we find a sign, update all the visited lanes with a reference to it
                update_with_reference = []
                traffic_sign_found = False
                while not traffic_sign_found:
                    while predecessors:
                        pred = predecessors.popleft()
                        visited.append(pred)
                        update_with_reference.append(pred)
                        # if we visited a predecessor, we can remove it from the lanelets, so we don't visit it twice
                        if pred in lanelets:
                            lanelets.remove(pred)
                        # If we haven't already visited the predecessor, then extend the list of predecessors but only
                        # by new unique predecessors.
                        if pred not in visited:
                            predecessors.extend(
                                [
                                    p
                                    for p in lanelet_network.find_lanelet_by_id(pred).predecessor
                                    if p not in predecessors
                                ]
                            )

                        # check if the predecessor has a traffic sign with equal speed as the lane
                        sign = self.get_traffic_sign_with_equal_speed(
                            lanelet_network.find_lanelet_by_id(pred), lanelet_network, speeds[0]
                        )
                        if sign is not None:
                            traffic_sign_found = True
                            # update all traversed predecessors with a reference to this signal, do not add reference
                            # if lane already has a sign
                            for update_lane_id in update_with_reference:
                                update_lane = lanelet_network.find_lanelet_by_id(update_lane_id)
                                if (
                                    sign.traffic_sign_id not in update_lane.traffic_signs
                                    and self.get_traffic_sign_with_equal_speed(
                                        update_lane, lanelet_network, speeds[0] is None
                                    )
                                ):
                                    update_lane_id.add_traffic_sign_to_lanelet(sign.traffic_sign_id)
                            break
                    break

    def find_lane_speed_changes(
        self, lanelets: List[int], lanelet_network: ConversionLaneletNetwork
    ):
        """Iteratively finds changes in lane speed between a lanelet and its predecessors. If there is a change, a
        virtual speed sign is added to the lanelet.

        :param lanelets: The list of lanelets that is checked for changes in lane speeds.
        :param lanelet_network: The lanelet network that the lanelets belong to.
        """
        visited = []
        for lane in lanelets:
            lane = lanelet_network.find_lanelet_by_id(lane)
            visited.append(lane.lanelet_id)
            if lane.speed is None:
                break
            for pred in lane.predecessor:
                if lanelet_network.find_lanelet_by_id(pred).speed != lane.speed:
                    self.add_virtual_traffic_sign(lane, lanelet_network)
                    break
                # Only extend lanelets by unique predecessors, if we have not already visisted them
                if pred not in visited:
                    lanelets.extend(
                        [
                            p
                            for p in lanelet_network.find_lanelet_by_id(pred).predecessor
                            if p not in lanelets
                        ]
                    )

    def get_traffic_sign_with_equal_speed(
        self, lanelet: ConversionLanelet, lanelet_network: ConversionLaneletNetwork, speed: float
    ) -> Optional[TrafficSign]:
        """Checks if the supplied lanelet has a traffic sign with a speed limit equal to the value given by the
        argument speed. If a sign was found, it is returned.

        :param lanelet: The lanelet to check for a sign with equal speed.
        :param lanelet_network: The lanelet network the lanelet belongs to.
        :param speed: The speed to compare the sign's speed to.
        :return: The traffic sign with equal speed, if one is found. Returns None else.
        """
        for id in lanelet.traffic_signs:
            sign = lanelet_network.find_traffic_sign_by_id(id)
            for elem in sign.traffic_sign_elements:
                if (
                    elem.traffic_sign_element_id
                    in [
                        TrafficSignIDZamunda.MAX_SPEED,
                        TrafficSignIDGermany.MAX_SPEED,
                        TrafficSignIDUsa.MAX_SPEED,
                        TrafficSignIDChina.MAX_SPEED,
                        TrafficSignIDSpain.MAX_SPEED,
                        TrafficSignIDRussia.MAX_SPEED,
                    ]
                    and float(elem.additional_values[0]) == speed
                ):
                    return sign
        return None

    def add_virtual_traffic_sign(
        self, lanelet: ConversionLanelet, network: ConversionLaneletNetwork
    ):
        """Adds a virtual traffic sign to a lanelet.

        :param lanelet: Lanelet to add virtual traffic signal to.
        :param network: The lanelet network to which the lanelet belongs to.
        """
        traffic_sign_enum = utils.get_traffic_sign_enum_from_country(
            utils.get_signal_country(self._country_ID)
        )
        element_id = traffic_sign_enum.MAX_SPEED
        additional_values = [str(float(lanelet.speed))]
        traffic_sign_element = TrafficSignElement(
            traffic_sign_element_id=element_id, additional_values=additional_values
        )
        traffic_sign = TrafficSign(
            traffic_sign_id=generate_unique_id(),
            traffic_sign_elements=list([traffic_sign_element]),
            first_occurrence={lanelet.lanelet_id},
            position=lanelet.center_vertices[0],
            virtual=True,
        )
        network.add_traffic_signs_to_network([traffic_sign])
        lanelet.add_traffic_sign_to_lanelet(traffic_sign.traffic_sign_id)

    def export_commonroad_scenario(
        self,
        g_config: GeneralConfig = general_config,
        od_config: OpenDriveConfig = open_drive_config,
    ):
        """Export a full CommonRoad scenario

        :param g_config: General config parameters.
        :param od_config: OpenDRIVE specific config parameters.
        """
        transformer = None
        location_kwargs = {}
        if self._geo_ref is not None and self._config.proj_string_odr is not None:
            longitude, latitude = get_geo_reference(self._geo_ref)
            if longitude is not None and latitude is not None:
                location_kwargs = dict(gps_latitude=latitude, gps_longitude=longitude)

            crs_from = CRS(self._geo_ref)
            crs_to = CRS(self._config.proj_string_odr)
            transformer = Transformer.from_proj(crs_from, crs_to)

        location = Location(
            geo_transformation=(
                GeoTransformation(geo_reference=self._config.proj_string_odr)
                if self._config.proj_string_odr is not None
                else None
            ),
            **location_kwargs,
        )

        scenario_id = ScenarioID(
            country_id=g_config.country_id if self._country_ID == "ZAM" else self._country_ID,
            map_name=g_config.map_name,
            map_id=g_config.map_id,
        )

        scenario = Scenario(dt=g_config.time_step_size, scenario_id=scenario_id, location=location)

        scenario.add_objects(
            self.export_lanelet_network(
                transformer=transformer, filter_types=od_config.filter_types
            )
        )

        return scenario

    @staticmethod
    def get_country_id_from_opendrive(roads: List[Road]) -> str:
        """
        Get country id of a specific lanelet network

        :param roads: Roads from which country id should be returned.
        :return: The country id.
        """
        for road in roads:
            for signal in road.signals:
                return signal.country
        return "ZAM"


class LinkIndex:
    """Overall index of all links in the file, save everything as successors, predecessors can be
    found via a reverse search"""

    def __init__(self):
        self._successors = {}
        self._intersections = []
        self._intersection_dict = {}

    def intersection_maps(self) -> List[Dict[str, List[str]]]:
        return self._intersections

    def create_from_opendrive(self, opendrive: OpenDrive):
        """Create a LinkIndex from an OpenDrive object.

        :param opendrive: OpenDrive style object.
        """
        self._add_junctions(opendrive)

        # Extract link information from road lanes
        for road in opendrive.roads:
            for lane_section in road.lanes.lane_sections:
                for lane in lane_section.all_lanes:
                    parametric_lane_id = encode_road_section_lane_width_id(
                        road.id, lane_section.idx, lane.id, -1
                    )

                    # Not the last lane section? > Next lane section in same road
                    if lane_section.idx < road.lanes.get_last_lane_section_idx():
                        successor_id = encode_road_section_lane_width_id(
                            road.id, lane_section.idx + 1, lane.link.successorId, -1
                        )

                        self.add_link(
                            parametric_lane_id, successor_id, lane.id >= 0, road.driving_direction
                        )

                    # Last lane section! > Next road in first lane section
                    # Try to get next road
                    elif (
                        road.link.successor is not None
                        and road.link.successor.elementType != "junction"
                    ):
                        next_road = opendrive.getRoad(road.link.successor.element_id)

                        if next_road is not None:
                            if road.link.successor.contactPoint == "start":
                                successor_id = encode_road_section_lane_width_id(
                                    next_road.id, 0, lane.link.successorId, -1
                                )

                            else:  # contact point = end
                                successor_id = encode_road_section_lane_width_id(
                                    next_road.id,
                                    next_road.lanes.get_last_lane_section_idx(),
                                    lane.link.successorId,
                                    -1,
                                )
                            self.add_link(
                                parametric_lane_id,
                                successor_id,
                                lane.id >= 0,
                                road.driving_direction,
                            )

                    # Not first lane section? > Previous lane section in same road
                    if lane_section.idx > 0:
                        predecessor_id = encode_road_section_lane_width_id(
                            road.id, lane_section.idx - 1, lane.link.predecessorId, -1
                        )

                        self.add_link(
                            predecessor_id, parametric_lane_id, lane.id >= 0, road.driving_direction
                        )

                    # First lane section! > Previous road
                    # Try to get previous road
                    elif (
                        road.link.predecessor is not None
                        and road.link.predecessor.elementType != "junction"
                    ):
                        prev_road = opendrive.getRoad(road.link.predecessor.element_id)

                        if prev_road is not None:
                            if road.link.predecessor.contactPoint == "start":
                                predecessor_id = encode_road_section_lane_width_id(
                                    prev_road.id, 0, lane.link.predecessorId, -1
                                )

                            else:  # contact point = end
                                predecessor_id = encode_road_section_lane_width_id(
                                    prev_road.id,
                                    prev_road.lanes.get_last_lane_section_idx(),
                                    lane.link.predecessorId,
                                    -1,
                                )
                            self.add_link(
                                predecessor_id,
                                parametric_lane_id,
                                lane.id >= 0,
                                road.driving_direction,
                            )

    def add_intersection_link(
        self,
        parametric_lane_id: str,
        successor: str,
        reverse: bool = False,
        driving_direction: bool = True,
    ):
        """
        Similar to add_link, adds successors only in an intersection_dict.
        This is a temporary dictionary to accumulate junction information for each open drive junction as a dictionary
        and then store it as a list in the intersection attribute of this class

        :param parametric_lane_id: Lane_id as per concatenated format based on opendrive IDs.
        :param successor: Successor of the opendrive lane.
        :param reverse: Whether the direction is opposite. Default is False.
        :param driving_direction: Whether the driving is right-hand. Default is True.
        """
        # check left-hand driving
        if driving_direction is False:
            reverse = not reverse

        if reverse:
            self.add_intersection_link(successor, parametric_lane_id)
            return

        if parametric_lane_id not in self._intersection_dict:
            self._intersection_dict[parametric_lane_id] = []

        if successor not in self._intersection_dict[parametric_lane_id]:
            self._intersection_dict[parametric_lane_id].append(successor)

    def add_link(
        self,
        parametric_lane_id: str,
        successor: str,
        reverse: bool = False,
        driving_direction: bool = True,
    ):
        """Adds links to a parametric lane.

        :param parametric_lane_id: The ID of the lane to which to add link.
        :param successor: Successor of the lane.
        :param reverse: Whether direction is reversed.
        :param driving_direction: Whether the driving is right-hand. Default is True.
        """
        # check left-hand driving
        if driving_direction is False:
            reverse = not reverse

        # if reverse, call function recursively with switched parameters
        if reverse:
            self.add_link(successor, parametric_lane_id)
            return

        if parametric_lane_id not in self._successors:
            self._successors[parametric_lane_id] = []

        if successor not in self._successors[parametric_lane_id]:
            self._successors[parametric_lane_id].append(successor)

    def _add_junctions(self, opendrive: OpenDrive):
        """Adds junctions.

        :param opendrive: The opendrive object to which junctions should be added.
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
                            lane_section_idx = incoming_road.lanes.get_last_lane_section_idx()
                        else:
                            lane_section_idx = 0
                        incoming_road_id = encode_road_section_lane_width_id(
                            incoming_road.id, lane_section_idx, lane_link.fromId, -1
                        )
                        connecting_road_id = encode_road_section_lane_width_id(
                            connecting_road.id, 0, lane_link.toId, -1
                        )
                        self.add_link(
                            incoming_road_id,
                            connecting_road_id,
                            lane_link.toId > 0,
                            incoming_road.driving_direction,
                        )
                        self.add_intersection_link(
                            incoming_road_id,
                            connecting_road_id,
                            lane_link.toId > 0,
                            incoming_road.driving_direction,
                        )

                    else:
                        incoming_road_id = encode_road_section_lane_width_id(
                            incoming_road.id, 0, lane_link.fromId, -1
                        )
                        connecting_road_id = encode_road_section_lane_width_id(
                            connecting_road.id,
                            connecting_road.lanes.get_last_lane_section_idx(),
                            lane_link.toId,
                            -1,
                        )
                        self.add_link(
                            incoming_road_id,
                            connecting_road_id,
                            lane_link.toId < 0,
                            incoming_road.driving_direction,
                        )
                        self.add_intersection_link(
                            incoming_road_id,
                            connecting_road_id,
                            lane_link.toId < 0,
                            incoming_road.driving_direction,
                        )
            # Extracting OpenDRIVE junction links to formulate CommonRoad intersections
            self._intersections.append(self._intersection_dict)
            # dictionary reinitialized to get junction information for next junction without appending values
            # of previous junction
            self._intersection_dict = dict()

    def remove(self, parametric_lane_id: str):
        """Removes a parametric lane from the opendrive network.

        :param parametric_lane_id: ID of lane that should be removed.
        """
        # Delete key
        if parametric_lane_id in self._successors:
            del self._successors[parametric_lane_id]

        # Delete all occurances in successor lists
        for successorsId, successors in self._successors.items():
            if parametric_lane_id in successors:
                self._successors[successorsId].remove(parametric_lane_id)

    def get_successors(self, parametric_lane_id: str) -> List:
        """Get successors of the specified parametric lane.

        :param parametric_lane_id: ID of ParametricLane for which to search successors.
        :return: List of successors belonging to the ParametricLane
        """
        if parametric_lane_id not in self._successors:
            return []

        return self._successors[parametric_lane_id]

    def get_predecessors(self, parametric_lane_id: str) -> List:
        """Get predecessors of the specified parametric lane.

        :param parametric_lane_id: ID of ParametricLane for which to search predecessors.
        :return: List of predecessors belonging to the ParametricLane
        """
        predecessors = []
        for successor_plane_id, successors in self._successors.items():
            if parametric_lane_id not in successors:
                continue

            if successor_plane_id in predecessors:
                continue

            predecessors.append(successor_plane_id)

        return predecessors

    def clean_intersections(self, parametric_lane_id: str):
        """
        Remove lanes that are not part of the lanelet network based on the filters.

        :param parametric_lane_id: ID of the lane that needs to be removed.
        """
        for intersection in self._intersections:
            if parametric_lane_id in intersection.keys():
                del intersection[parametric_lane_id]

    def concatenate_lanes_in_intersection_map(self, replacement_id_map: Dict):
        """
        Lanelets are concatenated if possible, hence some lanelets ids that exist in intersections
        are no longer valid and also need to be replaced with the lanelet id they are concatenated with.

        :param replacement_id_map: Dict that maps lanelets to their new IDs as per the concatenation results from
            lanelet_network.concatenate_possible_lanelets
        """
        updated_intersection_maps = []
        for intersection_map in self.intersection_maps():
            intersection_map_concatenated_lanelets = copy.copy(intersection_map)
            # Check if old lanelet is in keys
            for old_id, new_id in replacement_id_map.items():
                for incoming, successors in intersection_map.items():
                    updated_successors = [new_id if x == old_id else x for x in successors]
                    intersection_map[incoming] = updated_successors
                if old_id in intersection_map.keys():
                    intersection_map_concatenated_lanelets[new_id] = intersection_map[old_id]
                    del intersection_map_concatenated_lanelets[old_id]

                # Check if old lanelet is in values
            updated_intersection_maps.append(intersection_map_concatenated_lanelets)
        self._intersections = updated_intersection_maps

    def update_intersection_lane_id(self, old_id_to_new_id_map):
        """
        Updates the lanelet ids in the intersection map from the concatenated opendrive based format to
        the CommonRoad format

        :param old_id_to_new_id_map: Dict that maps the old lanelet IDs to new lanelet IDs using the attribute
            lanelet_network.old_lanelet_ids()
        """

        updated_intersection_maps = []
        for intersection_map in self.intersection_maps():
            intersection_map_new_id = dict()
            for incoming, connecting in intersection_map.items():
                # Replacing keys/incoming ids with new ids
                if incoming in old_id_to_new_id_map.keys():
                    new_incoming_id = old_id_to_new_id_map[incoming]
                    connecting = [old_id_to_new_id_map.get(item) for item in connecting]
                    intersection_map_new_id[new_incoming_id] = connecting

            updated_intersection_maps.append(intersection_map_new_id)
        self._intersections = updated_intersection_maps
