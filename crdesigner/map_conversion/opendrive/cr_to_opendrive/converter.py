import copy
import time

from posixpath import lexists
from typing import Dict, List

from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.obstacle import Obstacle
from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.sign import Sign
from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.light import Light
from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.stop_line import StopLine
import crdesigner.map_conversion.opendrive.cr_to_opendrive.utils.file_writer as fwr
from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.road import Road
from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.junction import Junction

from commonroad.scenario.intersection import IntersectionIncomingElement
from commonroad.scenario.scenario import Scenario
from commonroad.scenario.lanelet import Lanelet


class Converter:
    """
    This class converts the CommonRoad scenario object to CommonRoad file.
    The CommonRoad elements such as roads, junctions, traffic lights, traffic signal
    are converted to corresponding OpenDRIVE elements and OpenDRIVE file is created.
    """
    def __init__(self, file_path: str, sc: Scenario, successors: List[int], ids: Dict[int, bool]):
        self.path = file_path
        self.scenario = sc
        self.inter_successors = successors
        self.id_dict = ids
        self.lane_net = self.scenario.lanelet_network
        self.traffic_elements = {}
        self.writer = None
        self.conv_time = 0

    def convert(self, file_path_out: str):
        """
        This function creates a OpenDRIVE file and save in specific location
        after the conversion of scenario object to OpenDRIVE file.

        :param file_path_out: Path where OpenDRIVE file to be stored
        """
        start = time.time()
        # initialize writer object
        self.writer = fwr.Writer(file_path_out)

        lane_list = self.lane_net.lanelets
       
        # choose lanelet as starting point
        lanelet = copy.deepcopy(lane_list[0])

        # this function constructs all roads
        # using a breadth first search approach
        self.construct_roads([lanelet.lanelet_id])
        # double check that no lanelet was missed
        self.check_all_visited()

        # These functions are responsible for road as well as junction linkage
        self.process_link_map(Road.link_map, Road.lane_2_lane_link)
        self.create_linkages(Road.link_map, Road.lane_2_lane_link)
        self.construct_junctions()
        self.add_junction_linkage(Road.link_map)

        # Obstacles, traffic signs and traffic lights conversion
        self.construct_obstacles()
        self.populate_traffic_elements(Road.cr_id_to_od)
        self.construct_traffic_elements()

        self.finalize()
        self.conv_time = time.time() - start
        self.print_time()

    def print_time(self):
        """
        This function print the time required for the file conversion in the order of second.
        """
        conv = "Converter\n"
        time = f"Conversion took: \t{self.conv_time:.2} seconds\n"
        print(conv + time)

    def finalize(self):
        """
        This function cleans up the converter object
        which makes it possible to convert multiple files queued up.
        """
        self.writer.save()
        Road.cr_id_to_od.clear()
        Road.link_map.clear()
        Road.lane_2_lane_link.clear()
        Road.roads.clear()
        Road.lane_to_lane.clear()
        Road.counting = 20
        Junction.counting = 0
        Obstacle.counting = 0

    def populate_traffic_elements(self, link_map: Dict[int, int]):
        """
        This function is responsible for populating traffic elements.

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
                    data["lights"][sign] = [
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
                self.traffic_elements[link_map[lanelet.lanelet_id]] = data

    def construct_traffic_elements(self):
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

    def construct_roads(self, frontier: List[int]):
        """
        This method is responsible for road construction.
        We start from a given lanelet, we expand it left and right to construct its corresponding road,
        then we continue with its succesors/predecessors.
        The road network is explored in a breadth-first fashion.

        :param frontier: used as a queue that contains to-be-explored nodes
        """
        if not frontier:
            return

        frontier = list(set(frontier))
        id = frontier.pop(0)
        lanelet = copy.deepcopy(self.lane_net.find_lanelet_by_id(id))

        road_lanes = [lanelet]

        road_lanes = self.extend_road(lanelet, road_lanes, left=False, append=False)
        road_lanes = self.extend_road(lanelet, road_lanes, left=True, append=True)

        self.add_ids(road_lanes, frontier)

        junction_id = -1

        if lanelet.lanelet_id in self.inter_successors:
            junction_id = self.lane_net.map_inc_lanelets_to_intersections[
                lanelet.predecessor[0]
            ].intersection_id

        road = Road(road_lanes, len(road_lanes), self.writer.root, lanelet, junction_id)

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
        return

    def check_all_visited(self):
        """
        This function check that all lanelets have been added to the road network.
        This is done to guarantee correctness of the road construction algorithm
        """
        for lanelet in self.lane_net.lanelets:
            if not self.id_dict[lanelet.lanelet_id]:
                raise KeyError(
                    "Lanelet {} not visited! Check your algorithm.".format(
                        lanelet.lanelet_id
                    )
                )

    def construct_junctions(self):
        """
        This function converts scenario junctions to OpenDRIVE junctions.
        """
        for intersection in self.lane_net.intersections:
            Junction(
                intersection.incomings,
                Road.cr_id_to_od,
                Road.lane_to_lane,
                self.writer.root,
                self.scenario.lanelet_network,
                intersection.intersection_id,
            )

    def construct_obstacles(self):
        """
        This function converts scenario obstacles to OpenDRIVE obstacles.
        """
        obstacles = self.scenario.static_obstacles
        lanelets = self.lane_net.map_obstacles_to_lanelets(obstacles)

        for obstacle in obstacles:

            center = obstacle.initial_state.position
            lanelets = self.lane_net.find_lanelet_by_position([center])[0]
            Obstacle(
                obstacle.obstacle_type,
                lanelets,
                obstacle.obstacle_shape,
                obstacle.initial_state,
            )

    def process_link_map(self, link_map: Dict[int, Dict[int, Dict[str, List[int]]]],
                         lane_2_lane: Dict[int, Dict[str, Dict]]):
        """
        This function creates the data structure where all linkage information is stored, the link_map
        For more information on the link_map, read our documentation.

        :param link_map: dictionary of road ids and road links(dictionary of lanelet id
        and corresponding successors and predessors)
        :param lane_2_lane: dictionary of road ids and corresponding successors and predessors
        """
        for road_id, road_val in link_map.items():
            road_succ_pred = {"succ": [], "pred": []}
            road_succ_pred_final = {"succ": [], "pred": []}
            for lanelet, lanelet_val in road_val.items():
                if lanelet == "laneIndices":
                    continue
                lane_id = Road.lane_to_lane[lanelet]
                lane_2_lane[road_id]["succ"][lane_id] = []
                lane_2_lane[road_id]["pred"][lane_id] = []
                for links, links_val in lanelet_val.items():
                    if int(link_map[road_id]["laneIndices"][lanelet]) < 0:
                        invert = False
                    else:
                        invert = True
                    if links == "succ" and not invert:
                        for link in links_val:
                            road_succ_pred["succ"].append(link)
                            lane_2_lane[road_id]["succ"][lane_id].append(
                                Road.lane_to_lane[link]
                            )

                    if links == "pred" and not invert:
                        for link in links_val:
                            road_succ_pred["pred"].append(link)
                            lane_2_lane[road_id]["pred"][lane_id].append(
                                Road.lane_to_lane[link]
                            )

                    if links == "succ" and invert:
                        for link in links_val:
                            road_succ_pred["pred"].append(link)
                            lane_2_lane[road_id]["pred"][lane_id].append(
                                Road.lane_to_lane[link]
                            )

                    if links == "pred" and invert:
                        for link in links_val:
                            road_succ_pred["succ"].append(link)
                            lane_2_lane[road_id]["succ"][lane_id].append(
                                Road.lane_to_lane[link]
                            )

            link_map[road_id]["mergeLinkage"] = road_succ_pred
            for key, values in road_succ_pred.items():
                for value in values:
                    road_succ_pred_final[key].append(Road.cr_id_to_od[value])
            link_map[road_id]["roadLinkage"] = road_succ_pred_final

    def create_linkages(self, link_map: Dict[int, Dict[int, Dict[str, List[int]]]],
                        lane_2_lane: Dict[int, Dict[str, Dict[int, List[int]]]]):
        """
        This function implements road-to-road linkage.
        This happens when a road has exactly one successor/predecessor.

        :param link_map: A dictionary of road ids and road links(dictionary of lanelet id
        and corresponding successors and predessors)
        :param lane_2_lane: A dictionary of road ids and corresponding successors and predessors
        """
        for key, value in link_map.items():
            cur_links: dict = link_map[key]["roadLinkage"]
            cur_links_lanelets: dict = link_map[key]
            # lane_2_lane=link_map[key]["laneIndices"]
            cur_key = key
            len_succ = len(set(cur_links["succ"]))
            len_pred = len(set(cur_links["pred"]))

            # nothing to do in this case
            if cur_links["succ"] == [] and cur_links["pred"] == []:
                print("succ and pred empty for ", key)
                continue
            # either successor or predecessor road is trivial
            if len_succ == 1 or len_pred == 1:
                # print("add_simple_linkage for road_id: ", key)
                Road.roads[key].add_simple_linkage(
                    cur_key, cur_links, len_succ, len_pred, cur_links_lanelets, lane_2_lane[key]
                )

    def add_junction_linkage(self, link_map: Dict[int, Dict[int, Dict[str, List[int]]]]):
        """
        This function links roads to junctions.
        This happens when a road has multiple successors/predecessors.
        If these multiple successors/predecessors are already part of a junction,
        we make the junction to a successor/predecessor.
        Otherwise, in the case of mupltiple successors, we define a new junction.

        :param lane_2_lane: dictionary of road ids and corresponding successors and predessors
        """
        for road_id, road_val in link_map.items():
            if len(set(road_val["roadLinkage"]["succ"])) > 1:
                road = Road.roads[road_id]

                # check if junction already defined
                if (
                    road.lane_list[0].lanelet_id
                    in self.lane_net.map_inc_lanelets_to_intersections
                ):
                    junction_id = self.lane_net.map_inc_lanelets_to_intersections[
                        road.lane_list[0].lanelet_id
                    ].intersection_id
                    road.add_junction_linkage(junction_id, "successor")

                # define new junction
                else:
                    incomings = []

                    # right,left and straight successors are treated equally
                    successors_straight = set()
                    for lanelet in road.lane_list:
                        successors_straight.update(lanelet.successor)
                        incomings.append(lanelet.lanelet_id)

                    incoming = IntersectionIncomingElement(
                        1, incomings, set(), successors_straight, set(), None
                    )

                    Junction.counting += 1
                    Junction(
                        [incoming],
                        Road.cr_id_to_od,
                        Road.lane_to_lane,
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

    def add_ids(self, road_lanes: List[Lanelet], frontier: List[int]):
        """
        This function mark ID's of lanes in the frontier as visited

        :param road_lanes: list of lanelets
        :param frontier: used as a queue that contains to-be-explored nodes
        """
        for lane in road_lanes:
            self.id_dict[lane.lanelet_id] = True
            if lane.lanelet_id in frontier:
                frontier.remove(lane.lanelet_id)

    def extend_road(self, current: Lanelet, road_lanes: List[Lanelet], left: bool, append: bool) -> List[Lanelet]:
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
