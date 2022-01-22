from posixpath import lexists
from typing import Dict, List
from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.obstacle import Obstacle
from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.sign import Sign
from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.light import Light
import crdesigner.map_conversion.opendrive.cr_to_opendrive.utils.file_writer as fwr
from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.road import Road
from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.junction import Junction
from commonroad.scenario.intersection import IntersectionIncomingElement
from commonroad.scenario import scenario
import copy
import time


class Converter:
    """
    This class converts the CommonRoad scenario object to CommonRoad file.
    The commonraod elements such as roads, junctions, traffic lights, traffic signal
    are converted to corresponding OpenDRIVE elements and OpenDRIVE file is created.

    """
    def __init__(self, file_path: str, scenario: scenario, successors: List[int], ids: Dict[int, bool]):
        self.path = file_path
        self.scenario = scenario
        self.inter_successors = successors
        self.id_dict = ids
        self.lane_net = self.scenario.lanelet_network
        self.trafficElements = {}

    def convert(self, file_path_out: str):
        """
        This function creates a OpenDRIVE file and save in specific location
        after the conversion of scenario object to OpenDRIVE file.

        :param file_path_out: Path where OpenDRIVE file to be stored
        """
        start = time.time()
        # initialize writer object
        self.writer = fwr.Writer(file_path_out)

        laneList = self.lane_net.lanelets
        # choose lanelet as starting point
        lanelet = copy.deepcopy(laneList[0])

        # this function constructs all roads 
        # using a breadth first search approach
        self.constructRoads([lanelet.lanelet_id])

        # double check that no lanelet was missed
        self.checkAllVisited()

        # These functions are responsible for road as well as junction linkage
        self.processLinkMap(Road.linkMap, Road.lane2lanelink)
        self.createLinkages(Road.linkMap, Road.lane2lanelink)
        self.constructJunctions()
        self.addJunctionLinkage(Road.linkMap)

        # Obstacles, traffic signs and traffic lights conversion
        self.constructObstacles()
        self.populateTrafficElements(Road.crIdToOD)
        self.constructTrafficElements()

        self.finalize()
        self.convTime = time.time() - start
        self.printTime()

    def printTime(self):
        """
        This function print the time required for the file conversion in the order of second.
        """
        conv = "Converter\n"
        time = f"Conversion took: \t{self.convTime:.2} seconds\n"
        print(conv + time)

    def finalize(self):
        """
        This function cleans up the converter object
        which makes it possible to convert multiple files queued up.
        """
        self.writer.save()
        Road.crIdToOD.clear()
        Road.linkMap.clear()
        Road.lane2lanelink.clear()
        Road.roads.clear()
        Road.laneToLane.clear()
        Road.counting = 20
        Junction.counting = 0
        Obstacle.counting = 0

    def populateTrafficElements(self, linkMap: dict):
        """
        This function is responsible for populating traffic elements.
        """
        for lanelet in self.lane_net.lanelets:
            nonEmpty = False
            data = {"signs": {}, "lights": {}}

            if len(lanelet.traffic_signs) > 0:
                nonEmpty = True
                for sign in lanelet.traffic_signs:
                    data["signs"][sign] = [
                        self.lane_net.find_traffic_sign_by_id(sign),
                        lanelet.lanelet_id,
                    ]

            if len(lanelet.traffic_lights) > 0:
                nonEmpty = True
                for light in lanelet.traffic_lights:
                    data["lights"][sign] = [
                        self.lane_net.find_traffic_light_by_id(light),
                        lanelet.lanelet_id,
                    ]

            if nonEmpty:
                self.trafficElements[linkMap[lanelet.lanelet_id]] = data

    def constructTrafficElements(self):
        """
        This function converts scenario traffic elements to OpenDRIVE traffic elements.
        """
        for roadKey, elements in self.trafficElements.items():
            for specifier in elements:
                if specifier == "signs":
                    for uniqueId, ODobject in elements[specifier].items():
                        Sign(roadKey, uniqueId, ODobject, self.lane_net)
                if specifier == "lights":
                    for uniqueId, ODobject in elements[specifier].items():
                        Light(roadKey, uniqueId, ODobject, self.lane_net)

    def constructRoads(self, frontier: list):
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

        roadLanes = [lanelet]

        roadLanes = self.extendRoad(lanelet, roadLanes, left=False, append=False)
        roadLanes = self.extendRoad(lanelet, roadLanes, left=True, append=True)

        self.addIds(roadLanes, frontier)

        junctionId = -1

        if lanelet.lanelet_id in self.inter_successors:
            junctionId = self.lane_net.map_inc_lanelets_to_intersections[
                lanelet.predecessor[0]
            ].intersection_id

        road = Road(roadLanes, len(roadLanes), self.writer.root, lanelet, junctionId)

        for i in range(road.numberOfLanes):
            if i <= road.centerNumber:
                for succ in roadLanes[i].successor:
                    if not self.id_dict[succ]:
                        frontier.append(succ)

                for pred in roadLanes[i].predecessor:
                    if not self.id_dict[pred]:
                        frontier.append(pred)

            else:
                for succ in roadLanes[i].predecessor:
                    if not self.id_dict[succ]:
                        frontier.append(succ)

                for pred in roadLanes[i].successor:
                    if not self.id_dict[pred]:
                        frontier.append(pred)

        self.constructRoads(frontier)
        return

    def checkAllVisited(self):
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

    def constructJunctions(self):
        """
        This function converts scenario junctions to OpenDRIVE junctions.
        """
        for intersection in self.lane_net.intersections:
            Junction(
                intersection.incomings,
                Road.crIdToOD,
                Road.laneToLane,
                self.writer.root,
                self.scenario.lanelet_network,
                intersection.intersection_id,
            )

    def constructObstacles(self):
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

    def processLinkMap(self, linkMap: dict, lane2lane: dict):
        """
        This function creates the data structure where all linkage information is stored, the linkMap
        For more information on the linkMap, read our documentation.

        :param linkMap: dictionary of road ids and road links(dictionary of lanelet id
        and corresponding successors and predessors)
        :param lane2lane: dictionary of road ids and corresponding successors and predessors
        """
        for road_id, road_val in linkMap.items():
            roadSuccPred = {"succ": [], "pred": []}
            roadSuccPredFinal = {"succ": [], "pred": []}
            for lanelet, lanelet_val in road_val.items():
                if lanelet == "laneIndices":
                    continue
                laneId = Road.laneToLane[lanelet]
                lane2lane[road_id]["succ"][laneId] = []
                lane2lane[road_id]["pred"][laneId] = []
                for links, links_val in lanelet_val.items():
                    if int(linkMap[road_id]["laneIndices"][lanelet]) < 0:
                        invert = False
                    else:
                        invert = True
                    if links == "succ" and not invert:
                        for link in links_val:
                            roadSuccPred["succ"].append(link)
                            lane2lane[road_id]["succ"][laneId].append(
                                Road.laneToLane[link]
                            )

                    if links == "pred" and not invert:
                        for link in links_val:
                            roadSuccPred["pred"].append(link)
                            lane2lane[road_id]["pred"][laneId].append(
                                Road.laneToLane[link]
                            )

                    if links == "succ" and invert:
                        for link in links_val:
                            roadSuccPred["pred"].append(link)
                            lane2lane[road_id]["pred"][laneId].append(
                                Road.laneToLane[link]
                            )

                    if links == "pred" and invert:
                        for link in links_val:
                            roadSuccPred["succ"].append(link)
                            lane2lane[road_id]["succ"][laneId].append(
                                Road.laneToLane[link]
                            )

            linkMap[road_id]["mergeLinkage"] = roadSuccPred
            for key, values in roadSuccPred.items():
                for value in values:
                    roadSuccPredFinal[key].append(Road.crIdToOD[value])
            linkMap[road_id]["roadLinkage"] = roadSuccPredFinal

    def createLinkages(self, linkMap: dict, lane2lane):
        """
        This function implements road-to-road linkage.
        This happens when a road has exactly one successor/predecessor.

        :param linkMap: A dictionary of road ids and road links(dictionary of lanelet id
        and corresponding successors and predessors)
        :param lane2lane: A dictionary of road ids and corresponding successors and predessors
        """
        for key, value in linkMap.items():
            curLinks: dict = linkMap[key]["roadLinkage"]
            curLinksLanelets: dict = linkMap[key]
            # lane2lane=linkMap[key]["laneIndices"]
            curKey = key
            lenSucc = len(set(curLinks["succ"]))
            lenPred = len(set(curLinks["pred"]))

            # nothing to do in this case
            if curLinks["succ"] == [] and curLinks["pred"] == []:
                print("succ and pred empty for ", key)
                continue
            # either successor or predecessor road is trivial
            if lenSucc == 1 or lenPred == 1:
                # print("addSimpleLinkage for road_id: ", key)
                Road.roads[key].addSimpleLinkage(
                    curKey, curLinks, lenSucc, lenPred, curLinksLanelets, lane2lane[key]
                )

    def addJunctionLinkage(self, linkMap: dict):
        """
        This function links roads to junctions.
        This happens when a road has multiple successors/predecessors.
        If these multiple successors/predecessors are already part of a junction,
        we make the junction to a successor/predecessor.
        Otherwise, in the case of mupltiple successors, we define a new junction.

        :param lane2lane: dictionary of road ids and corresponding successors and predessors
        """
        for road_id, road_val in linkMap.items():
            if len(set(road_val["roadLinkage"]["succ"])) > 1:
                road = Road.roads[road_id]

                # check if junction already defined
                if (
                    road.laneList[0].lanelet_id
                    in self.lane_net.map_inc_lanelets_to_intersections
                ):
                    junctionId = self.lane_net.map_inc_lanelets_to_intersections[
                        road.laneList[0].lanelet_id
                    ].intersection_id
                    road.addJunctionLinkage(junctionId, "successor")

                # define new junction
                else:
                    incomings = []

                    # right,left and straight successors are treated equally
                    successors_straight = set()
                    for lanelet in road.laneList:
                        successors_straight.update(lanelet.successor)
                        incomings.append(lanelet.lanelet_id)

                    incoming = IntersectionIncomingElement(
                        1, incomings, set(), successors_straight, set(), None
                    )

                    Junction.counting += 1

                    Junction(
                        [incoming],
                        Road.crIdToOD,
                        Road.laneToLane,
                        self.writer.root,
                        self.lane_net,
                        Junction.counting,
                    )

                    road.addJunctionLinkage(Junction.counting, "successor")

            if len(set(road_val["roadLinkage"]["pred"])) > 1:
                road = Road.roads[road_id]

                # check if junction already defined
                if road.laneList[0].lanelet_id in self.inter_successors:
                    junctionId = self.lane_net.map_inc_lanelets_to_intersections[
                        road.laneList[0].predecessor[0]
                    ].intersection_id
                    road.addJunctionLinkage(junctionId, "predecessor")

    def addIds(self, roadLanes: list, frontier: list):
        """
        This function mark ID's of lanes in the frontier as visited

        :param roadLanes: list of lanelets
        :param frontier: used as a queue that contains to-be-explored nodes
        """
        for lane in roadLanes:
            self.id_dict[lane.lanelet_id] = True
            if lane.lanelet_id in frontier:
                frontier.remove(lane.lanelet_id)

    def extendRoad(self, current, roadLanes, left, append):
        """
        This function extend road left and right, returns all lanes from right to left.

        :param current: lanelet
        :param roadLanes: list of lanelet
        :param left: boolean
        :param append: boolean
        :return: list of lanelet
        """
        # extend to the right
        if not left and current.adj_right:
            lane = self.lane_net.find_lanelet_by_id(current.adj_right)

            if append:
                roadLanes.append(lane)
            else:
                roadLanes.insert(0, lane)

            if current.adj_right_same_direction:
                return self.extendRoad(lane, roadLanes, left=False, append=append)

        # extend to the left
        elif left and current.adj_left:
            lane = self.lane_net.find_lanelet_by_id(current.adj_left)

            if append:
                roadLanes.append(lane)

            if current.adj_left_same_direction:
                return self.extendRoad(lane, roadLanes, left=True, append=append)

            # We encountered a direction change when going left (from our point of view).
            # When switching to the next lanelet's perspective, left becomes right
            # We also need to append the new lanelets to the end of the list, since they appear to the left from our perspective
            else:
                return self.extendRoad(lane, roadLanes, left=False, append=append)

        return roadLanes
