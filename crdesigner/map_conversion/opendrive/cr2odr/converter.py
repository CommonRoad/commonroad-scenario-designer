import copy
import logging
import time
from typing import Dict, List, Union

import numpy as np
from commonroad.common.common_lanelet import LaneletType
from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.util import Path_T
from commonroad.scenario.intersection import IntersectionIncomingElement
from commonroad.scenario.lanelet import Lanelet
from commonroad.scenario.scenario import Scenario

import crdesigner.map_conversion.opendrive.cr2odr.utils.file_writer as fwr
from crdesigner.map_conversion.opendrive.cr2odr.elements.junction import Junction
from crdesigner.map_conversion.opendrive.cr2odr.elements.light import Light
from crdesigner.map_conversion.opendrive.cr2odr.elements.obstacle import (
    OpenDRIVEObstacle,
)
from crdesigner.map_conversion.opendrive.cr2odr.elements.road import LinkMap_T, Road
from crdesigner.map_conversion.opendrive.cr2odr.elements.sign import Sign
from crdesigner.map_conversion.opendrive.cr2odr.elements.stop_line import StopLine
from crdesigner.map_conversion.opendrive.cr2odr.utils import config


def get_avg(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """
    This method calculate the average for ndarrays x and y

    :param x: average of x_right and x_left
    :param y: average of y_right and y_left
    :return: average for ndarrays x and y
    """
    x_avg = -((np.min(x) + np.max(x)) / 2.0)
    y_avg = -((np.min(y) + np.max(y)) / 2.0)
    middle = np.array([x_avg, y_avg])
    return middle


def create_linkages(
    link_map: LinkMap_T,
    lane_2_lane: Dict[int, Dict[str, Dict[int, List[int]]]],
) -> None:
    """
    This function implements road-to-road linkage.
    This happens when a road has exactly one successor/predecessor.

    :param link_map: A dictionary of road ids and road links(dictionary of lanelet id
    and corresponding successors and predecessors)
    :param lane_2_lane: A dictionary of road ids and corresponding successors and predecessors
    """
    for key, value in link_map.items():
        cur_links: dict = link_map[key]["roadLinkage"]
        # lane_2_lane=link_map[key][config.LANE_INDICES_TAG]
        len_succ = len(set(cur_links["succ"]))
        len_pred = len(set(cur_links["pred"]))

        # nothing to do in this case
        if cur_links["succ"] == [] and cur_links["pred"] == []:
            print("succ and pred empty for ", key)
            continue
        # either successor or predecessor road is trivial
        if len_succ == 1 or len_pred == 1:
            Road.roads[key].add_simple_linkage(cur_links, len_succ, len_pred, lane_2_lane[key])


def process_link_map(link_map: LinkMap_T, lane_2_lane: Dict[int, Dict[str, Dict]]) -> None:
    """
    This function creates the data structure where all linkage information is stored, the link_map
    For more information on the link_map, read our documentation.

    :param link_map: dictionary of road ids and road links(dictionary of lanelet id
    and corresponding successors and predecessors)
    :param lane_2_lane: dictionary of road ids and corresponding successors and predecessors
    """
    for road_id, road_val in link_map.items():
        road_succ_pred = {"succ": [], "pred": []}
        road_succ_pred_final = {"succ": [], "pred": []}
        for lanelet, lanelet_val in road_val.items():
            if lanelet == config.LANE_INDICES_TAG:
                continue
            lane_id = Road.lanelet_to_lane[lanelet]
            lane_2_lane[road_id]["succ"][lane_id] = []
            lane_2_lane[road_id]["pred"][lane_id] = []
            for links, links_val in lanelet_val.items():
                if int(link_map[road_id][config.LANE_INDICES_TAG][lanelet]) < 0:
                    invert = False
                else:
                    invert = True
                if links == "succ" and not invert:
                    for link in links_val:
                        road_succ_pred["succ"].append(link)
                        lane_2_lane[road_id]["succ"][lane_id].append(Road.lanelet_to_lane[link])

                if links == "pred" and not invert:
                    for link in links_val:
                        road_succ_pred["pred"].append(link)
                        lane_2_lane[road_id]["pred"][lane_id].append(Road.lanelet_to_lane[link])

                if links == "succ" and invert:
                    for link in links_val:
                        road_succ_pred["pred"].append(link)
                        lane_2_lane[road_id]["pred"][lane_id].append(Road.lanelet_to_lane[link])

                if links == "pred" and invert:
                    for link in links_val:
                        road_succ_pred["succ"].append(link)
                        lane_2_lane[road_id]["succ"][lane_id].append(Road.lanelet_to_lane[link])

        link_map[road_id]["mergeLinkage"] = road_succ_pred
        for key, values in road_succ_pred.items():
            for value in values:
                road_succ_pred_final[key].append(Road.cr_id_to_od[value])
        link_map[road_id]["roadLinkage"] = road_succ_pred_final


def select_random_lanelet(lanelet_list: List[Lanelet]) -> Lanelet:
    """
    Selects a lanelet from a given list, where the lanelet must not be of type crosswalk,
    bicycle lane, bus stop, border, or unknown.

    :param lanelet_list: List of lanelets.
    :return: Lanelet.
    """
    for lanelet in lanelet_list:
        if (
            {
                LaneletType.CROSSWALK,
                LaneletType.BICYCLE_LANE,
                LaneletType.BUS_STOP,
                LaneletType.BORDER,
                LaneletType.UNKNOWN,
            }.isdisjoint(lanelet.lanelet_type)
        ) is True:
            return lanelet
    return lanelet_list[0]


class Converter:
    """
    This class converts the CommonRoad scenario object to CommonRoad file.
    The CommonRoad elements such as roads, junctions, traffic lights, traffic signal
    are converted to corresponding OpenDRIVE elements and OpenDRIVE file is created.
    """

    def __init__(self, scenario: Union[Path_T, Scenario], center: bool = False) -> None:
        """
        This function lets Class Converter to initialize object with path to CommonRoad file, scenario,
        list of successor and dictionary of converted roads and initialize the instant variables.

        :param scenario: path to CommonRoad file
        :param center: boolean value
        """
        self.center = center
        self.x_avg = 0
        self.y_avg = 0

        if isinstance(scenario, Scenario):
            self.scenario = scenario
        else:
            # if the map is not loadable by CommonRoadFileReader we just return
            # as there seems to be some major syntax faults in the input map
            try:
                self.scenario, _ = CommonRoadFileReader(scenario).open()
            except AttributeError:
                logging.error(f"{scenario} not loadable!")
                exit()

        # shorten variable name
        self.lane_net = self.scenario.lanelet_network

        # 0 centering is mostly useless because the planning problem
        # requires the same coordinate space as the input
        if self.center:
            # move lanelets into the origin
            self.scenario.translate_rotate(self.get_center(), 0.0)
            for element in self.scenario.lanelet_network.traffic_signs:
                element.translate_rotate(self.get_center(), 0.0)

        # intersection successors are needed for the conversion
        self.inter_successors = self.prepare_intersection_successors()

        # dictionary to keep track of converted roads
        self.id_dict = self.prepare_id_dict()

        self.traffic_elements = {}
        self.writer = None
        self.conv_time = 0

    def get_center(self) -> np.ndarray:
        """
        This method calculate the roads "center" to move everything into the origin

        :return: the roads "center" as (average of x_right and x_left, average of y_right and y_left)
        """
        coords_left = self.lane_net.lanelets[0].left_vertices
        coords_right = self.lane_net.lanelets[0].right_vertices
        for let in self.lane_net.lanelets:
            coords_left = np.concatenate((coords_left, let.left_vertices), axis=0)
            coords_right = np.concatenate((coords_right, let.right_vertices), axis=0)

        x_left, y_left = np.hsplit(coords_left, 2)
        x_right, y_right = np.hsplit(coords_right, 2)

        return get_avg((x_right + x_left) / 2, (y_right + y_left) / 2)

    def find_successors(self, indices: dict.keys) -> List[int]:
        """
        This method creates list of successors of all incoming lanelets

        :param indices: list of incoming lanelets (id's) to each intersection defined
        :return: list of successors of all incoming lanelets (id's)
        """
        successors = []
        for incoming_id in indices:
            # find all succesors which are part of the intersection
            lane = self.lane_net.find_lanelet_by_id(incoming_id)
            successors.extend(lane.successor)
        return successors

    def prepare_intersection_successors(self) -> List[int]:
        """
        This method creates the list of successor of all incoming lanelets(id's) of intersection defined

        :return: list of all successors that are part of the intersection
        """
        # list of all incoming lanelets (id's) to each intersection defined
        inter_incoming_lanelets = self.lane_net.map_inc_lanelets_to_intersections.keys()
        # list of their successors
        inter_successors = self.find_successors(inter_incoming_lanelets)
        return inter_successors

    def prepare_id_dict(self) -> Dict[int, bool]:
        """
        Creates a dictionary with lanelet ids as keys and boolean values.
        This helps keep track which lanelets already got converted

        :return: dictionary with lanelet ids as keys and boolean values
        """
        lane_list = self.lane_net.lanelets
        id_dict = {}
        # this is done to keep track which lanelets already got converted
        for i in range(0, len(lane_list)):
            id_dict[lane_list[i].lanelet_id] = False
        return id_dict

    def convert(self, file_path_out: str) -> None:
        """
        This function creates a OpenDRIVE file and save in specific location
        after the conversion of scenario object to OpenDRIVE file.

        :param file_path_out: Path where OpenDRIVE file to be stored
        """
        start = time.time()
        # initialize writer object
        if (
            self.scenario.location.geo_transformation is not None
            and self.scenario.location.geo_transformation.geo_reference is not None
        ):
            geo_reference = self.scenario.location.geo_transformation.geo_reference
        else:
            geo_reference = ""
        self.writer = fwr.Writer(file_path_out, geo_reference)

        lane_list = self.lane_net.lanelets

        # choose lanelet as starting point
        lanelet = copy.deepcopy(select_random_lanelet(lane_list))

        # this function constructs all roads
        # using a breadth first search approach
        self.construct_roads([lanelet.lanelet_id])
        # double check that no lanelet was missed
        self.check_all_visited()

        # These functions are responsible for road as well as junction linkage
        process_link_map(Road.link_map, Road.lane_2_lane_link)
        create_linkages(Road.link_map, Road.lane_2_lane_link)
        self.construct_junctions()
        self.add_junction_linkage(Road.link_map)

        # Obstacles, traffic signs and traffic lights conversion
        self.construct_obstacles()
        self.populate_traffic_elements(Road.cr_id_to_od)
        self.construct_traffic_elements()

        self.finalize()
        self.conv_time = time.time() - start
        self.print_time()

    def print_time(self) -> None:
        """
        This function print the time required for the file conversion in the order of second.
        """
        time_str = f"Conversion took: \t{self.conv_time:.2} seconds\n"
        logging.info(time_str)

    def finalize(self) -> None:
        """
        This function cleans up the converter object
        which makes it possible to convert multiple files queued up.
        """
        self.writer.save()
        self.reset_converter()

    def reset_converter(self):
        """
        Resets class values.
        """
        Road.cr_id_to_od.clear()
        Road.link_map.clear()
        Road.lane_2_lane_link.clear()
        Road.roads.clear()
        Road.lanelet_to_lane.clear()
        Road.counting = 20
        Junction.counting = 0
        OpenDRIVEObstacle.counting = 0

    def populate_traffic_elements(self, link_map: Dict[int, int]) -> None:
        """
        This function is responsible for populating regulatory elements.

        :param link_map: Dictionary with keys as lanelet id of CommonRoad lanelets and
        values as road id of OpenDrive roads
        """
        for lanelet in self.lane_net.lanelets:
            non_empty = False
            data = {"signs": {}, "lights": {}, "stop_lines": {}}

            if len(lanelet.traffic_signs) > 0:
                non_empty = True
                for sign in lanelet.traffic_signs:
                    data["signs"][sign] = [
                        self.lane_net.find_traffic_sign_by_id(sign),
                        lanelet.lanelet_id,
                    ]

            if len(lanelet.traffic_lights) > 0:
                non_empty = True
                for light in lanelet.traffic_lights:
                    data["lights"][light] = [
                        self.lane_net.find_traffic_light_by_id(light),
                        lanelet.lanelet_id,
                    ]

            if lanelet.stop_line is not None:
                non_empty = True
                data["stop_lines"][lanelet.lanelet_id] = [
                    lanelet.stop_line,
                    lanelet.lanelet_id,
                ]

            if non_empty:
                if len(data["stop_lines"]) > 0:
                    if self.traffic_elements.get(link_map[lanelet.lanelet_id]):
                        data["stop_lines"] = self.traffic_elements[link_map[lanelet.lanelet_id]][
                            "stop_lines"
                        ]
                if link_map.get(lanelet.lanelet_id) is not None:
                    # if condition added to prevent failure -> TODO check why sometime lane_id does not exist
                    self.traffic_elements[link_map[lanelet.lanelet_id]] = data

    def construct_traffic_elements(self) -> None:
        """
        This function converts scenario traffic elements to OpenDRIVE traffic elements.
        """
        for road_key, elements in self.traffic_elements.items():
            for specifier in elements:
                if specifier == "signs":
                    for unique_id, od_object in elements[specifier].items():
                        Sign(road_key, unique_id, od_object, self.lane_net)
                if specifier == "lights":
                    for unique_id, od_object in elements[specifier].items():
                        Light(road_key, unique_id, od_object, self.lane_net)
                if specifier == "stop_lines":
                    for unique_id, od_object in elements[specifier].items():
                        StopLine(road_key, unique_id, od_object, self.lane_net)

    def construct_roads(self, frontier: List[int]) -> None:
        """
        This method is responsible for road construction.
        We start from a given lanelet, we expand it left and right to construct its corresponding road,
        then we continue with its successors/predecessors.
        The road network is explored in a breadth-first fashion.

        :param frontier: used as a queue that contains to-be-explored nodes
        """
        if not frontier:
            return

        frontier = list(set(frontier))
        l_id = frontier.pop(0)
        lanelet = copy.deepcopy(self.lane_net.find_lanelet_by_id(l_id))

        road_lanes = [lanelet]

        road_lanes = self.extend_road(lanelet, road_lanes, left=False, append=False)
        road_lanes = self.extend_road(lanelet, road_lanes, left=True, append=True)

        # remove adjacent lanes from frontier so that they are not visited anymore
        self.add_ids(road_lanes, frontier)

        junction_id = -1

        if lanelet.lanelet_id in self.inter_successors:
            junction_id = self.lane_net.map_inc_lanelets_to_intersections[
                lanelet.predecessor[0]
            ].intersection_id

        road = Road(road_lanes, len(road_lanes), self.writer.root, junction_id)

        for i in range(road.number_of_lanes):
            if i <= road.center_number:
                for succ in road_lanes[i].successor:
                    if not self.id_dict[succ]:
                        frontier.append(succ)

                for pred in road_lanes[i].predecessor:
                    if not self.id_dict[pred]:
                        frontier.append(pred)

            else:
                for succ in road_lanes[i].predecessor:
                    if not self.id_dict[succ]:
                        frontier.append(succ)

                for pred in road_lanes[i].successor:
                    if not self.id_dict[pred]:
                        frontier.append(pred)

        self.construct_roads(frontier)

    def check_all_visited(self) -> None:
        """
        This function check that all lanelets have been added to the road network.
        This is done to guarantee correctness of the road construction algorithm
        """
        for lanelet in self.lane_net.lanelets:
            if self.id_dict.get(lanelet.lanelet_id) is None:
                raise RuntimeError(
                    f"Lanelet {lanelet.lanelet_id} not visited! Check your algorithm."
                )

    def construct_junctions(self):
        """
        This function converts scenario intersections to OpenDRIVE junctions.
        """
        for intersection in self.lane_net.intersections:
            Junction(
                intersection.incomings,
                Road.cr_id_to_od,
                Road.lanelet_to_lane,
                self.writer.root,
                self.scenario.lanelet_network,
                intersection.intersection_id,
            )

    def construct_obstacles(self) -> None:
        """
        This function converts scenario obstacles to OpenDRIVE obstacles.
        """
        obstacles = self.scenario.static_obstacles
        for obstacle in obstacles:
            center = obstacle.initial_state.position
            lanelets = self.lane_net.find_lanelet_by_position([center])[0]
            OpenDRIVEObstacle(
                obstacle.obstacle_type,
                lanelets,
                obstacle.obstacle_shape,
                obstacle.initial_state,
            )

    def add_junction_linkage(self, link_map: LinkMap_T) -> None:
        """
        This function links roads to junctions.
        This happens when a road has multiple successors/predecessors.
        If these multiple successors/predecessors are already part of a junction,
        we make the junction to a successor/predecessor.
        Otherwise, in the case of multiple successors, we define a new junction.

        :param link_map: dictionary of road ids and corresponding successors and predecessors
        """
        for road_id, road_val in link_map.items():
            if len(set(road_val["roadLinkage"]["succ"])) > 1:
                road = Road.roads[road_id]

                # check if junction already defined
                if road.lane_list[0].lanelet_id in self.lane_net.map_inc_lanelets_to_intersections:
                    junction_id = self.lane_net.map_inc_lanelets_to_intersections[
                        road.lane_list[0].lanelet_id
                    ].intersection_id
                    road.add_junction_linkage(junction_id, "successor")

                # define new junction
                else:
                    incomings = set()

                    # right,left and straight successors are treated equally
                    successors_straight = set()
                    for lanelet in road.lane_list:
                        successors_straight.update(lanelet.successor)
                        incomings.add(lanelet.lanelet_id)

                    incoming = IntersectionIncomingElement(
                        1, incomings, set(), successors_straight, set(), None
                    )

                    Junction.counting += 1
                    Junction(
                        [incoming],
                        Road.cr_id_to_od,
                        Road.lanelet_to_lane,
                        self.writer.root,
                        self.lane_net,
                        Junction.counting,
                    )

                    road.add_junction_linkage(Junction.counting, "successor")

            if len(set(road_val["roadLinkage"]["pred"])) > 1:
                road = Road.roads[road_id]

                # check if junction already defined
                if road.lane_list[0].lanelet_id in self.inter_successors:
                    junction_id = self.lane_net.map_inc_lanelets_to_intersections[
                        road.lane_list[0].predecessor[0]
                    ].intersection_id
                    road.add_junction_linkage(junction_id, "predecessor")

    def add_ids(self, road_lanes: List[Lanelet], frontier: List[int]) -> None:
        """
        This function mark ID's of lanes in the frontier as visited

        :param road_lanes: list of lanelets
        :param frontier: used as a queue that contains to-be-explored nodes
        """
        for lane in road_lanes:
            self.id_dict[lane.lanelet_id] = True
            if lane.lanelet_id in frontier:
                frontier.remove(lane.lanelet_id)

    def extend_road(
        self, current: Lanelet, road_lanes: List[Lanelet], left: bool, append: bool
    ) -> List[Lanelet]:
        """
        This function extend road left and right, returns all lanes from right to left.

        :param current: lanelet
        :param road_lanes: list of lanelet
        :param left: boolean
        :param append: boolean
        :return: list of lanelet
        """
        # extend to the right
        if not left and current.adj_right:
            lane = self.lane_net.find_lanelet_by_id(current.adj_right)

            if append:
                road_lanes.append(lane)
            else:
                road_lanes.insert(0, lane)

            if current.adj_right_same_direction:
                return self.extend_road(lane, road_lanes, left=False, append=append)

        # extend to the left
        elif left and current.adj_left:
            lane = self.lane_net.find_lanelet_by_id(current.adj_left)

            if append:
                road_lanes.append(lane)

            if current.adj_left_same_direction:
                return self.extend_road(lane, road_lanes, left=True, append=append)

            # We encountered a direction change when going left (from our point of view).
            # When switching to the next lanelet's perspective, left becomes right
            # We also need to append the new lanelets to the end of the list, since
            # they appear to the left from our perspective
            else:
                return self.extend_road(lane, road_lanes, left=False, append=append)

        return road_lanes
