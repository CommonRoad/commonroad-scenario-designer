import copy
from typing import Callable, List, Optional, Set, Union

import numpy as np
from commonroad.common.util import Interval
from commonroad.geometry.shape import Rectangle, Shape
from commonroad.scenario.intersection import Intersection
from commonroad.scenario.lanelet import Lanelet, LaneletNetwork
from commonroad.scenario.obstacle import (
    DynamicObstacle,
    EnvironmentObstacle,
    Obstacle,
    PhantomObstacle,
    StaticObstacle,
)
from commonroad.scenario.scenario import (
    GeoTransformation,
    Location,
    Scenario,
    ScenarioID,
    Tag,
)
from commonroad.scenario.traffic_light import TrafficLight
from commonroad.scenario.traffic_sign import TrafficSign, TrafficSignIDCountries
from PyQt6.QtCore import QObject, pyqtSignal

from crdesigner.common.logging import logger
from crdesigner.ui.gui.utilities.map_creator import MapCreator


class ScenarioModel(QObject):
    scenario_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.__scenarios: List[Scenario] = []
        self.__current_scenario_index = -1
        # Index if the model has already been updated
        self.__updated_scenario = False
        self.__new_file_added = False

    def scenarios(self) -> List[Scenario]:
        """
        @returns: Returns a list of all scenarios
        """
        return self.__scenarios

    def set_scenario(self, scenario: Scenario):
        """
        Sets a new scenario with the given Scenario

        @param scenario: Scenario which should be added
        """
        if not self.__updated_scenario:
            self.__current_scenario_index += 1
        self.__scenarios.append(copy.deepcopy(scenario))
        self.notify_all(True)

    def _update_scenario(self):
        """
        Ensures that there is only one updated scenario and creates a new sceanario if necessary
        """
        if self.__updated_scenario:
            return
        else:
            new_scenario = self._current_scenario()
            # shorten the scenario list to current index in case undo was used
            self.__current_scenario_index += 1
            self.__scenarios = self.__scenarios[: self.__current_scenario_index]

            self.__scenarios.append(copy.deepcopy(new_scenario))
            self.__updated_scenario = True

    def _current_scenario(self) -> Optional[Scenario]:
        """Private function to make the calls in this class better readable"""
        if self.__current_scenario_index == -1:
            return None
        else:
            return self.__scenarios[self.__current_scenario_index]

    def notify_all(self, new_file_added: bool = False):
        """
        Notifies all subscribers that the scenario has been changed

        @param new_file_added: Indicates whether a new file was added
        """
        self.__new_file_added = new_file_added
        self.__updated_scenario = False
        self.scenario_changed.emit()

    def is_new_file_added(self) -> bool:
        """
        @returns: a boolean whether a new file has been added to the scenario
        """
        return self.__new_file_added

    def subscribe(self, callback: Callable[[], None]):
        """Allows subscription without exposing the signal."""
        self.scenario_changed.connect(callback)

    def get_current_scenario(self) -> Scenario:
        """Returns the current scenario."""
        return self._current_scenario()

    def collect_obstacle_ids(self) -> List[int]:
        """
        Collects IDs of all obstacles within a CommonRoad scenario.
        @return: List of all obstacles
        """
        if self._current_scenario() is not None:
            return [obs.obstacle_id for obs in self._current_scenario().obstacles]
        else:
            return []

    def collect_lanelet_ids(self) -> List[int]:
        """
        Collects IDs of all lanelets within a CommonRoad scenario.
        @return: List of lanelet IDs.
        """
        if self._current_scenario() is not None:
            return sorted(
                [la.lanelet_id for la in self._current_scenario().lanelet_network.lanelets]
            )
        else:
            return []

    def collect_traffic_sign_ids(self) -> List[int]:
        """
        Collects IDs of all traffic signs within a CommonRoad scenario.
        @return: List of traffic sign IDs.
        """
        if self._current_scenario() is not None:
            return sorted(
                [
                    ts.traffic_sign_id
                    for ts in self._current_scenario().lanelet_network.traffic_signs
                ]
            )
        return []

    def collect_traffic_light_ids(self) -> List[int]:
        """
        Collects IDs of all traffic lights within a CommonRoad scenario.
        @return: List of traffic light IDs.
        """
        if self._current_scenario() is not None:
            return sorted(
                [
                    tl.traffic_light_id
                    for tl in self._current_scenario().lanelet_network.traffic_lights
                ]
            )
        return []

    def collect_intersection_ids(self) -> List[int]:
        """
        Collects IDs of all intersection within a CommonRoad scenario.
        @return: List of intersection IDs.
        """
        if self._current_scenario() is not None:
            return sorted(
                [
                    inter.intersection_id
                    for inter in self._current_scenario().lanelet_network.intersections
                ]
            )
        return []

    def collect_incoming_lanelet_ids_from_intersection(self, current_text) -> List[int]:
        """
        Collects IDs of all incoming lanelets of a given intersection.
        @return: List of lanelet IDs.
        """
        lanelets = []
        if current_text not in ["", "None"]:
            selected_intersection_id = int(current_text)
            intersection = self._current_scenario().lanelet_network.find_intersection_by_id(
                selected_intersection_id
            )
            for inc in intersection.incomings:
                lanelets += inc.incoming_lanelets
        return lanelets

    def scenario_created(self) -> bool:
        """
        Returns whether scenario exists.

        :return: Boolean indicating whether scenario exists.
        """
        return not self.__current_scenario_index == -1

    @logger.log
    def add_lanelet(self, lanelet: Union[Lanelet, List[Lanelet]]):
        """
        Adds a lanelet to the Scenario.

        @param lanelet: lanelet or List of Lanelets which should be added to the scenario
        """
        self._update_scenario()
        self._current_scenario().add_objects(lanelet)
        self.notify_all()

    @logger.log
    def add_obstacle(self, obstacle: Obstacle):
        """
        Adds an obstacle to the Scenario.

        @param obstacle: Obstacle which should be added to the scenario
        """
        self._update_scenario()
        self._current_scenario().add_objects(obstacle)
        self.notify_all()

    @logger.log
    def update_lanelet(self, old_lanelet: Lanelet, new_lanelet: Lanelet):
        """
        Updates the Scenario by deleting the old lanelet and adding the new lanelet to the scenario.

        @param old_lanelet: old lanelet
        @param new_lanelet: new lanelet
        """
        old_lanelet_id = old_lanelet.lanelet_id
        successors = [
            la.lanelet_id
            for la in self._current_scenario().lanelet_network.lanelets
            if old_lanelet_id in la.successor
        ]
        predecessors = [
            la.lanelet_id
            for la in self._current_scenario().lanelet_network.lanelets
            if old_lanelet_id in la.predecessor
        ]
        adjacent_left = [
            (la.lanelet_id, la.adj_left_same_direction)
            for la in self._current_scenario().lanelet_network.lanelets
            if old_lanelet_id == la.adj_left
        ]
        adjacent_right = [
            (la.lanelet_id, la.adj_right_same_direction)
            for la in self._current_scenario().lanelet_network.lanelets
            if old_lanelet_id == la.adj_right
        ]

        self._update_scenario()
        self._current_scenario().remove_lanelet(old_lanelet)
        self._current_scenario().add_objects(new_lanelet)

        for la_id in successors:
            self._current_scenario().lanelet_network.find_lanelet_by_id(la_id).add_successor(
                old_lanelet_id
            )
        for la_id in predecessors:
            self._current_scenario().lanelet_network.find_lanelet_by_id(la_id).add_predecessor(
                old_lanelet_id
            )
        for la_info in adjacent_left:
            self._current_scenario().lanelet_network.find_lanelet_by_id(
                la_info[0]
            ).adj_left = old_lanelet_id
            self._current_scenario().lanelet_network.find_lanelet_by_id(
                la_info[0]
            ).adj_left_same_direction = la_info[1]
        for la_info in adjacent_right:
            self._current_scenario().lanelet_network.find_lanelet_by_id(
                la_info[0]
            ).adj_right = old_lanelet_id
            self._current_scenario().lanelet_network.find_lanelet_by_id(
                la_info[0]
            ).adj_right_same_direction = la_info[1]

        self.notify_all()

    @logger.log
    def remove_lanelet(self, lanelet_id: int):
        """
        Removes a lanelet in the Scenario.

        @param lanelet_id: Id of the lanelet which should be deleted
        """
        self._update_scenario()
        removed_lanelet = self.find_lanelet_by_id(lanelet_id)
        traffic_lights = removed_lanelet.traffic_lights
        traffic_signs = removed_lanelet.traffic_signs

        for traffic_sign_id in traffic_signs:
            if (
                len(
                    self._current_scenario().lanelet_network.get_traffic_sign_referenced_lanelets(
                        traffic_sign_id
                    )
                )
                == 1
            ):
                self._current_scenario().remove_traffic_sign(
                    self.find_traffic_sign_by_id(traffic_sign_id)
                )

        for traffic_light_id in traffic_lights:
            if (
                len(
                    self._current_scenario().lanelet_network.get_traffic_lights_referenced_lanelets(
                        traffic_light_id
                    )
                )
                == 1
            ):
                self._current_scenario().remove_traffic_light(
                    self.find_traffic_light_by_id(traffic_light_id)
                )

        MapCreator.remove_lanelet(lanelet_id, self._current_scenario().lanelet_network)
        self.notify_all()

    @logger.log
    def attach_to_other_lanelet(self, lanelet_one: Lanelet, lanelet_two: Lanelet):
        """
        Takes two lanelets and attaches lanelet_one to lanelet_two

        @param lanelet_one: lanelet which should be attached
        @param lanelet_two: lanelet to which lanelet_one should be attached to
        """
        self._update_scenario()
        MapCreator.fit_to_predecessor(lanelet_two, lanelet_one)
        self.notify_all()

    @logger.log
    def rotate_lanelet(self, lanelet_id: int, rotation_angle: int):
        """
        Rotates the lanelet with the given rotation angle

        @param lanelet_id: id of the lanelet which should be rotated
        @param rotation_angle: angle of which the lanelet should be rotated
        """
        self._update_scenario()
        lanelet = self.find_lanelet_by_id(lanelet_id)
        initial_vertex = lanelet.center_vertices[0]
        lanelet.translate_rotate(np.array([0, 0]), np.deg2rad(rotation_angle))
        lanelet.translate_rotate(initial_vertex - lanelet.center_vertices[0], 0.0)
        self._current_scenario().remove_lanelet(lanelet)
        self._current_scenario().add_objects(lanelet)
        self.notify_all()

    @logger.log
    def translate_lanelet(self, lanelet: Lanelet):
        """
        Translates the given lanelet to the newly given lanelet

        @param lanelet: edited lanelet which should be added
        """
        self._update_scenario()
        self._current_scenario().remove_lanelet(lanelet)
        self._current_scenario().add_objects(lanelet)
        self.notify_all()

    @logger.log
    def merge_with_successor(self, lanelet: Lanelet):
        """
        Merges the lanelet with it's successor

        @param lanelet: lanelet on wehich the merge should be performed
        """
        successors = []
        predecessors = lanelet.predecessor
        self._update_scenario()

        for suc in lanelet.successor:
            new_lanelet = Lanelet.merge_lanelets(lanelet, self.find_lanelet_by_id(suc))
            self._current_scenario().remove_lanelet(self.find_lanelet_by_id(suc))
            self._current_scenario().add_objects(new_lanelet)
            successors.append(new_lanelet.lanelet_id)
        self._current_scenario().remove_lanelet(lanelet)
        for pred in predecessors:
            for suc in successors:
                self.find_lanelet_by_id(pred).add_successor(suc)
        self.notify_all()

    @logger.log
    def merge_lanelets_dynamic_canvas(self, neighboured_lanelets: List[Lanelet]):
        """
        Merges the lanelets of the function merge_lanelets of the dynamic canvas

        @param neighboured_lanelets: List of lanelets which should be merged
        """
        self._update_scenario()
        last_merged_index = None
        while neighboured_lanelets:
            lanelet = neighboured_lanelets.pop()
            for n_lanelet in neighboured_lanelets:
                if (
                    n_lanelet.lanelet_id in lanelet.predecessor
                    or n_lanelet.lanelet_id in lanelet.successor
                ):
                    neighboured_lanelet = self.find_lanelet_by_id(n_lanelet.lanelet_id)
                    connected_lanelet = Lanelet.merge_lanelets(neighboured_lanelet, lanelet)
                    neighboured_lanelets.append(connected_lanelet)
                    for succ in connected_lanelet.successor:
                        self.find_lanelet_by_id(succ).add_predecessor(connected_lanelet.lanelet_id)
                    for pred in connected_lanelet.predecessor:
                        self.find_lanelet_by_id(pred).add_successor(connected_lanelet.lanelet_id)
                    self._current_scenario().add_objects(connected_lanelet)
                    neighboured_lanelets.remove(n_lanelet)
                    self._current_scenario().remove_lanelet(n_lanelet)
                    self._current_scenario().remove_lanelet(lanelet)
                    last_merged_index = connected_lanelet.lanelet_id
                    break
        return last_merged_index

    @logger.log
    def add_traffic_sign(self, traffic_sign: TrafficSign, referenced_lanelets: Set[int]):
        """
        Adds a traffic sign to the scenario

        @param traffic_sign: Traffic sign which should bne added
        @param referenced_lanelets: The IDs of the lanelets to which the traffic sign refers
        """
        self._update_scenario()
        self._current_scenario().add_objects(traffic_sign, referenced_lanelets)
        self.notify_all()

    @logger.log
    def remove_traffic_sign(self, traffic_sign_id: int):
        """
        Removes a traffic sign of the Scenario

        @param traffic_sign_id: id of the traffic sign which should be deleted
        """
        self._update_scenario()
        traffic_sign = self.find_traffic_sign_by_id(traffic_sign_id)
        self._current_scenario().remove_traffic_sign(traffic_sign)
        self.notify_all()

    @logger.log
    def remove_obstacle(self, obstacle: Obstacle):
        """
        Removes an obstacle of the scenario

        @param obstacle: obstacle which should be deleted
        """
        self._update_scenario()
        self._current_scenario().remove_obstacle(obstacle)
        self.notify_all()

    @logger.log
    def update_traffic_sign(self, traffic_sign_id: int):
        """
        Deletes the existing traffic sign of the scenario to add it as a new traffic sign

        @param traffic_sign_id: id of the updated traffic sign
        """
        self._update_scenario()
        traffic_sign = self.find_traffic_sign_by_id(traffic_sign_id)
        self._current_scenario().remove_traffic_sign(traffic_sign)

    @logger.log
    def add_traffic_light(self, traffic_light: TrafficLight, referenced_lanelets: Set[int]):
        """
        Adds traffic light to the Scenario

        @param traffic_light: Traffic light to add to the scenario
        @param referenced_lanelets: Ids of the lanelets the traffic light refers
        """
        self._update_scenario()
        self._current_scenario().add_objects(traffic_light, referenced_lanelets)
        self.notify_all()

    @logger.log
    def remove_traffic_light(self, traffic_light_id: int):
        """
        Removes a traffic light of the Scenario

        @param traffic_light_id: id of the traffic light which should be deleted
        """
        self._update_scenario()
        traffic_light = self.find_traffic_light_by_id(traffic_light_id)
        self._current_scenario().remove_traffic_light(traffic_light)
        self.notify_all()

    @logger.log
    def update_traffic_light(self, traffic_light_id: int):
        """
        Deletes the existing traffic light of the scenario to add it as a new traffic ligth

        @param traffic_light_id: id of the updated traffic light
        """
        self._update_scenario()
        traffic_light = self.find_traffic_light_by_id(traffic_light_id)
        self._current_scenario().remove_traffic_light(traffic_light)

    @logger.log
    def create_traffic_lights_for_referenced_lanelets(self, lanelet_network: LaneletNetwork):
        """
        Creates traffic lights for referenced lanlets(SUMO)

        @param lanelet_network: lanelet networks with the new traffic lights
        """
        self._update_scenario()
        self._current_scenario().replace_lanelet_network(lanelet_network)
        self.notify_all()

    @logger.log
    def create_three_way_intersection(
        self,
        width: float,
        diameter: int,
        incoming_length: int,
        add_traffic_signs: bool,
        add_traffic_lights: bool,
    ):
        """
        Creates a three-way intersection ond adds it to the scenario.

        @param width: width of the lanelets of the intersection
        @param diameter: diameter of the intersection turn radius
        @param incoming_length: length of the incoiming lanelets
        @param add_traffic_signs: boolean if traffic signs should be added
        @param add_traffic_lights: boolean if traffic lights should be added
        """
        self._update_scenario()
        country_signs = TrafficSignIDCountries[self.get_country_id()]
        intersection, new_traffic_signs, new_traffic_lights, new_lanelets = (
            MapCreator.create_three_way_intersection(
                width,
                diameter,
                incoming_length,
                self._current_scenario(),
                add_traffic_signs,
                add_traffic_lights,
                country_signs,
            )
        )
        self._current_scenario().add_objects(intersection)
        self._current_scenario().add_objects(new_lanelets)
        self._current_scenario().add_objects(new_traffic_signs)
        self._current_scenario().add_objects(new_traffic_lights)
        self.notify_all()

    @logger.log
    def create_four_way_intersection(
        self,
        width: float,
        diameter: int,
        incoming_length: int,
        add_traffic_signs: bool,
        add_traffic_lights: bool,
    ):
        """
        Creates a four-way intersection ond adds it to the scenario.

        @param width: width of the lanelets of the intersection
        @param diameter: diameter of the intersection turn radius
        @param incoming_length: length of the incoiming lanelets
        @param add_traffic_signs: boolean if traffic signs should be added
        @param add_traffic_lights: boolean if traffic lights should be added
        """
        self._update_scenario()
        country_signs = TrafficSignIDCountries[self.get_country_id()]
        intersection, new_traffic_signs, new_traffic_lights, new_lanelets = (
            MapCreator.create_four_way_intersection(
                width,
                diameter,
                incoming_length,
                self._current_scenario(),
                add_traffic_signs,
                add_traffic_lights,
                country_signs,
            )
        )
        self._current_scenario().add_objects(intersection)
        self._current_scenario().add_objects(new_lanelets)
        self._current_scenario().add_objects(new_traffic_signs)
        self._current_scenario().add_objects(new_traffic_lights)
        self.notify_all()

    @logger.log
    def add_intersection(self, intersection: Intersection):
        """
        Adds an intersection to the scenario

        @param intersection: intersection which should be added to the scenario
        """
        self._update_scenario()
        self._current_scenario().add_objects(intersection)
        self.notify_all()

    @logger.log
    def update_intersection(self, old_intersection_id: int):
        """
        Removes the current intersection in oprder to update the updated intersection in another step

        @param old_intersection_id: Id of the updated intersection
        """
        self._update_scenario()
        intersetion = self.find_intersection_by_id(old_intersection_id)
        self._current_scenario().remove_intersection(intersetion)

    @logger.log
    def remove_intersection(self, intersection_id: int):
        """
        Removes an intersection of the scenario

        @param intersection_id: Id of the intersection to be deleted
        """
        self._update_scenario()
        intersetion = self.find_intersection_by_id(intersection_id)
        self._current_scenario().remove_intersection(intersetion)
        self.notify_all()

    @logger.log
    def fit_intersection(self, intersection_id: int, predecessor_id: int, successor_id: int):
        """
        Fits an intersection to a given lanelets

        @param intersection_id: Id of the intersection which should be fitted
        @param predecessor_id: Id of the predecessor which should be fitted
        @param successor_id: Id of the successor which should be fitted
        """
        self._update_scenario()
        intersection = self.find_intersection_by_id(intersection_id)
        lanelet_predecessor = self.find_lanelet_by_id(predecessor_id)
        lanelet_successor = self.find_lanelet_by_id(successor_id)

        MapCreator.fit_intersection_to_predecessor(
            lanelet_predecessor,
            lanelet_successor,
            intersection,
            self._current_scenario().lanelet_network,
        )
        self.notify_all()

    @logger.log
    def add_successor_to_lanelet(self, lanelet_id: int, successor_id: int):
        """
        Adds a succesor id to the lanelets successor list

        @param lanelet_id: Id of the lanelt to witch the successor should be added
        @param successor_id: Id of the successor which should be addded
        """
        lanelet = self.find_lanelet_by_id(lanelet_id)
        lanelet.successor.append(successor_id)

    @logger.log
    def add_predecessor_to_lanelet(self, lanelet_id: int, predecessor_id: int):
        """
        Adds a succesor id to the lanelets predecessor list

        @param lanelet_id: Id of the lanelt to witch the predecessor should be added
        @param predecessor_id: Id of the predecessor which should be addded
        """
        lanelet = self.find_lanelet_by_id(lanelet_id)
        lanelet.predecessor.append(predecessor_id)

    @logger.log
    def generate_object_id(self) -> int:
        """
        @returns: Generates unique object ID and returns it as an integer
        """
        return self._current_scenario().generate_object_id()

    def get_scenario_dt(self) -> float:
        """
        @returns: Gives back the Global time step as a float
        """
        return self._current_scenario().dt

    def get_scenario_id(self) -> ScenarioID:
        """
        @returns: Gives back scenario ID
        """
        return self._current_scenario().scenario_id

    def get_dynamic_obstacles(self) -> List[DynamicObstacle]:
        """
        @returns: List of the Dynamic Obstacles of the scenario
        """
        return self._current_scenario().dynamic_obstacles

    def get_lanelets(self) -> List[Lanelet]:
        """
        @returns: List of the current lanelets of the scenario
        """
        return self._current_scenario().lanelet_network.lanelets

    def get_lanelet_network(self) -> LaneletNetwork:
        """
        @retruns: Gives back the lanelet network of the scenario
        """
        return self._current_scenario().lanelet_network

    def get_traffic_signs(self) -> List[TrafficSign]:
        """
        @returns: List of the traffic signs of the scenario
        """
        return self._current_scenario().lanelet_network.traffic_signs

    def find_lanelet_by_id(self, lanelet_id: int) -> Lanelet:
        """
        Takes an id and gives back the respective Lanelet

        @param lanelet_id: Id of the desired lanelet
        @returns: Lanelet assosiated with the given id
        """
        return self._current_scenario().lanelet_network.find_lanelet_by_id(lanelet_id)

    def find_lanelet_by_shape(self, shape: Shape) -> List[int]:
        """
        Takes a shape and checks whether a lanelet intersects with it and returns the lanelet ids

        @param shape: Shape for the search of the lanelets
        @returns: List of lanelets who are found by the shape
        """
        return self._current_scenario().lanelet_network.find_lanelet_by_shape(shape)

    def find_traffic_sign_by_id(self, traffic_sign_id: int) -> TrafficSign:
        """
        Searches the respective traffic sign of the id

        @param traffic_sign_id: Id of the desired traffic sign
        @returns: Gives back the searched traffic sign
        """
        return self._current_scenario().lanelet_network.find_traffic_sign_by_id(traffic_sign_id)

    def find_obstacle_by_id(
        self, obstacle_id: int
    ) -> Union[Obstacle, DynamicObstacle, StaticObstacle, None]:
        """
        Searches the obstacle by its id

        @param obstacle_id: Id of the obstacle
        @returns: Gives back the found obstacle
        """
        return self._current_scenario().obstacle_by_id(obstacle_id)

    def find_traffic_light_by_id(self, traffic_light_id: int) -> TrafficLight:
        """
        Searches the respective traffic light of the id

        @param traffic_light_id: Id of the desired traffic light
        @returns: Gives back the searched traffic light
        """
        return self._current_scenario().lanelet_network.find_traffic_light_by_id(traffic_light_id)

    def find_intersection_by_id(self, intersection_id: int) -> Intersection:
        """
        Searches the intersection by its id

        @param intersection_id: Id of the intersection
        @returns: Gives back the found intersection
        """
        return self._current_scenario().lanelet_network.find_intersection_by_id(intersection_id)

    def get_country_id(self) -> str:
        """
        @returns: Gives back the country id of the scenario
        """
        return self._current_scenario().scenario_id.country_id

    def get_obstacles(
        self,
    ) -> List[
        Union[Obstacle, StaticObstacle, DynamicObstacle, EnvironmentObstacle, PhantomObstacle]
    ]:
        """
        @returns: Gives back all obstacles of the scenario
        """
        return self._current_scenario().obstacles

    def get_obstacles_by_position_intervals(self, plot_limits) -> List[Obstacle]:
        """
        Searches Obstacle within a certain position interval

        @param plot_limits: Limits of which the obstacles should be searched
        @returns: List of obstacles found
        """
        return (
            self._current_scenario().obstacles_by_position_intervals(
                [Interval(plot_limits[0], plot_limits[1]), Interval(plot_limits[2], plot_limits[3])]
            )
            if plot_limits
            else self._current_scenario().obstacles
        )

    @logger.log
    def replace_lanelet_network(self, lanelet_network: LaneletNetwork):
        """
        Replaces the current lanelet network of the scenario with the given lanelet network

        @param lanelet_network: New lanelet Network which should replace the current one
        """
        self._current_scenario().replace_lanelet_network(lanelet_network)

    @logger.log
    def undo(self):
        """
        Sets the current scenario to the scenario before if the user triggered the undo functionality
        """
        if self.__current_scenario_index > 0:
            self.__current_scenario_index -= 1
            self.notify_all()

    @logger.log
    def redo(self):
        """
        Sets the current scenario to the scenario after if the user triggered the redo functionality
        """
        if self.__current_scenario_index < len(self.__scenarios) - 1:
            self.__current_scenario_index += 1
            self.notify_all()

    @logger.log
    def crop_map(self, rectangle: Rectangle) -> None:
        """
        Cropps the map and returns all lanelets which lay within the rectangle

        @param rectangle: Rectangle in which the Objects should stay in
        """
        self._update_scenario()
        new_lanelet_network = self.get_lanelet_network().create_from_lanelet_network(
            self.get_lanelet_network(), shape_input=rectangle
        )
        obstacles = self.get_obstacles()
        for obs in obstacles:
            if isinstance(obs, StaticObstacle) and not rectangle.contains_point(
                obs.initial_state.position
            ):
                self._current_scenario().remove_obstacle(obs)
        self.replace_lanelet_network(new_lanelet_network)
        self.notify_all()

    @logger.log
    def add_converted_scenario(self, scenario: Scenario):
        """
        Adds the given scenario which was converted to the scenario_model

        @param scenario: Converted scenario which should be added to the Model
        """
        self._update_scenario()
        self.__scenarios[self.__current_scenario_index] = scenario
        self.notify_all(True)

    def get_copy_of_scenario(self) -> Optional[Scenario]:
        """
        @returns: Returns a copy of the scenario
        """
        return copy.deepcopy(self._current_scenario())

    def update_meta_data(
        self,
        author: str,
        affiliation: str,
        source: str,
        tags: [Tag],
        configuration_id: int,
        cooperative: bool,
        country_id: str,
        map_id: int,
        map_name: str,
        obstacle_behavior: str,
        prediction_id: int,
        time_step_size: float,
        location: Location = None,
    ):
        """
        updates the scenario settings

        @param author: Author of the scenario
        @param affiliation: Affiliation of the Auther
        @param source: Where was the scenario created
        @param tags: Tags of the scenario
        @param configuration_id: configuration ID
        @param cooperative: Statement if the scenario is cooperative
        @param country_id: Id of the country in which the scenario takes place
        @param map_id: Id of the map
        @param map_name: Name of the map
        @param obstacle_behavior: Indicator of the behavior of obstacles
        @param prediction_id: Id of prediction
        @param time_step_size: Size of the time steps
        @param location: Element where the location of the scenario is stored
        """
        self._current_scenario().author = author
        self._current_scenario().affiliation = affiliation
        self._current_scenario().source = source
        self._current_scenario().tags = tags
        self._current_scenario().dt = time_step_size
        self._current_scenario().scenario_id.configuration_id = configuration_id
        self._current_scenario().scenario_id.cooperative = cooperative
        self._current_scenario().scenario_id.country_id = country_id
        self._current_scenario().scenario_id.map_id = map_id
        self._current_scenario().scenario_id.map_name = map_name
        self._current_scenario().scenario_id.obstacle_behavior = obstacle_behavior
        self._current_scenario().scenario_id.prediction_id = prediction_id
        if location is not None:
            self._current_scenario().location = location

    def update_translate_scenario(self, translation: np.ndarray, geo_reference: str):
        """
        updates the geo_reference and translates the scenario

        @param translation: Translation element of the scenario
        @param geo_reference: Geo reference
        """
        self._update_scenario()

        if (
            self._current_scenario().location is None
            or self._current_scenario().location.geo_transformation is None
        ):
            self._current_scenario().location = Location(
                geo_transformation=GeoTransformation(
                    geo_reference="", x_translation=0.0, y_translation=0.0
                )
            )

        new_translation = (
            np.array(
                [
                    self._current_scenario().location.geo_transformation.x_translation,
                    self._current_scenario().location.geo_transformation.y_translation,
                ]
            )
            - translation
        )

        self._current_scenario().location.geo_transformation.x_translation = translation[0]
        self._current_scenario().location.geo_transformation.y_translation = translation[1]
        self._current_scenario().location.geo_transformation.geo_reference = geo_reference

        self._current_scenario().translate_rotate(new_translation, 0)

        self.notify_all()
