# import functions to read xml file and visualize commonroad objects
from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.scenario import scenario


# time, size for benchmarking
import time
import os
import numpy as np

class DataLoader:
    """
    This class is used to read a CommonRoad XML file and create a scenario object.
    Here we also prepare some additional data strutures, which we then pass to the converter
    along with the scenario object
    """
    def __init__(self, path: str, center: bool = False):
        start = time.time()
        self.path = path
        self.center = center
        self.x_avg = 0
        self.y_avg = 0
        # if the map is not loadable by CommonRoadFileReader we just return
        # as there seems to be some major syntax faults in the input map
        try:
            self.scenario, _ = CommonRoadFileReader(path).open()
        except AttributeError:
            print(f"{self.path} not loadable!")
            exit()

        # shorten variable name
        self.lane_net = self.scenario.lanelet_network

        # 0 centering is mostly useless because the planning problem
        # requires the same coordinate space as the input
        if self.center:
            # move lanelets into the origin
            self.scenario.translate_rotate(self.getCenter(), 0.0)
            for element in self.scenario.lanelet_network.traffic_signs:
                element.translate_rotate(self.getCenter(), 0.0)


        # intersection successors are needed for the conversion
        self.inter_successors = self.prepareIntersectionSuccessors()

        # dictionary to keep track of converted roads
        self.id_dict = self.prepareIdDict()

        self.initTime = time.time() - start

    def initialize(self) -> (scenario, list, dict):
        """
        Get the needed data for conversion

        :return: scenario object, intersection successors, dictionary of converted roads
        """
        return self.scenario, self.inter_successors, self.id_dict

    def getAvg(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """
        This method calculate the average for ndarrays x and y

        :param x: average of x_right and x_left 
        :param y: average of y_right and y_left 
        :return: average for ndarrays x and y
        """
        self.x_avg = -((np.min(x) + np.max(x)) / 2.0)
        self.y_avg = -((np.min(y) + np.max(y)) / 2.0)
        self.middle = np.array([self.x_avg, self.y_avg])
        return self.middle

    def getCenter(self) -> np.ndarray:
        """
        This method calculate the roads "center" to move everything into the origin

        :return: the roads "center" as (average of x_right and x_left, average of y_right and y_left)  
        """
        coords_left = self.lane_net.lanelets[0].left_vertices
        coords_right = self.lane_net.lanelets[0].right_vertices
        for lane in self.lane_net.lanelets:
            coords_left = np.concatenate((coords_left, lane.left_vertices), axis=0)
            coords_right = np.concatenate((coords_right, lane.right_vertices), axis=0)

        x_left, y_left = np.hsplit(coords_left, 2)
        x_right, y_right = np.hsplit(coords_right, 2)

        return self.getAvg((x_right + x_left)/2, (y_right+y_left)/2)

    def find_successors(self, indices: dict.keys) -> list:
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

    def prepareIntersectionSuccessors(self) -> list:
        """
        This method creates the list of successor of all incoming lanelets(id's) of intersection defined

        :return: list of all successors that are part of the intersection
        """
        # list of all incoming lanelets (id's) to each intersection defined
        inter_incoming_lanelets = self.lane_net.map_inc_lanelets_to_intersections.keys()
        # list of their successors
        inter_successors = self.find_successors(inter_incoming_lanelets)
        return inter_successors


    def prepareIdDict(self) -> dict:
        """
        Creates a dictionary with lanelet ids as keys and boolean values.
        This helps keep track which lanelets already got converted

        :return: dictionary with lanelet ids as keys and boolena values
        """
        laneList = self.lane_net.lanelets
        id_dict = {}
        # this is done to keep track which lanelets already got converted
        for i in range(0, len(laneList)):
            id_dict[laneList[i].lanelet_id] = False
        return id_dict

    def __str__(self) -> str:
        """
        Provide overview of Dataloader class 

        :return: Information related to path, size of loaded file, the center coordinate of roads, time required for object initialization
        """
        header = "Dataloader\n"
        loadedFile = f"Loaded file:\t\t {self.path}\n"
        loadedFileSize = f"loaded file size:\t {os.path.getsize(self.path)} bytes\n"
        centered = f"Center coordinates:\t {self.x_avg, self.y_avg}\n"
        time = f"Initialization took:\t {self.initTime:.2} seconds\n"
        if self.center: 
            return header + loadedFile + loadedFileSize + centered + time
        else:
            return header + loadedFile + loadedFileSize + time
