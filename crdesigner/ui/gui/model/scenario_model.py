from PyQt5.QtCore import QObject, pyqtSignal
import copy

from commonroad.scenario.intersection import Intersection
from commonroad.scenario.scenario import Scenario
from commonroad.scenario.lanelet import Lanelet, LaneletNetwork
from commonroad.common.util import Interval

from commonroad.scenario.traffic_sign import *
from commonroad.scenario.obstacle import *

from crdesigner.ui.gui.utilities.map_creator import MapCreator


class ScenarioModel(QObject):

    scenario_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.__scenarios: List[Scenario] = []
        self.__current_scenario_index = -1
        # Index if the model has already been updated
        self.__updated_scenario = False

    def scenarios(self):
        return self.__scenarios

    def set_scenario(self, scenario: Scenario):
        self.__current_scenario_index += 1
        self.__scenarios.append(copy.deepcopy(scenario))
        self.notify_all()

    def _update_scenario(self):
        if self.__updated_scenario:
            return
        else:
            new_scenario = self._current_scenario()
            # shorten the scenario list to current index in case undo was used
            self.__current_scenario_index += 1
            self.__scenarios = self.__scenarios[:self.__current_scenario_index]

            self.__scenarios.append(copy.deepcopy(new_scenario))
            self.__updated_scenario = True

    def _current_scenario(self):
        """ Private function to make the calls in this class better readable"""
        if self.__current_scenario_index == -1:
            return None
        else:
            return self.__scenarios[self.__current_scenario_index]

    def notify_all(self):
        self.__updated_scenario = False
        self.scenario_changed.emit()

    def get_current_scenario(self) -> Scenario:
        return self._current_scenario()

    def store_scenario_service_layer(self, scenario):
        self.__scenarios.append(copy.deepcopy(scenario))
        self.__current_scenario_index += 1
        self.scenario_changed.emit()

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
            return sorted([la.lanelet_id for la in self._current_scenario().lanelet_network.lanelets])
        else:
            return []

    def collect_traffic_sign_ids(self) -> List[int]:
        """
        Collects IDs of all traffic signs within a CommonRoad scenario.
        @return: List of traffic sign IDs.
        """
        if self._current_scenario() is not None:
            return sorted([ts.traffic_sign_id for ts in self._current_scenario().lanelet_network.traffic_signs])
        return []

    def collect_traffic_light_ids(self) -> List[int]:
        """
        Collects IDs of all traffic lights within a CommonRoad scenario.
        @return: List of traffic light IDs.
        """
        if self._current_scenario() is not None:
            return sorted([tl.traffic_light_id for tl in self._current_scenario().lanelet_network.traffic_lights])
        return []

    def collect_intersection_ids(self) -> List[int]:
        """
        Collects IDs of all intersection within a CommonRoad scenario.
        @return: List of intersection IDs.
        """
        if self._current_scenario() is not None:
            return sorted([inter.intersection_id for inter in self._current_scenario().lanelet_network.intersections])
        return []

    def collect_incoming_lanelet_ids_from_intersection(self, current_text) -> List[int]:
        """
        Collects IDs of all incoming lanelets of a given intersection.
        @return: List of lanelet IDs.
        """
        lanelets = []
        if current_text not in ["", "None"]:
            selected_intersection_id = int(current_text)
            intersection = self._current_scenario().lanelet_network.find_intersection_by_id(selected_intersection_id)
            for inc in intersection.incomings:
                lanelets += inc.incoming_lanelets
        return lanelets

    def scenario_created(self) -> bool:
        """
        Returns whether scenario exists.

        :return: Boolean indicating whether scenario exists.
        """
        return not self.__current_scenario_index == -1

    def add_lanelet(self, lanelet):
        self._update_scenario()
        self._current_scenario().add_objects(lanelet)
        self.notify_all()

    def add_obstacle(self, obstacle: Obstacle):
        self._update_scenario()
        self._current_scenario().add_objects(obstacle)
        self.notify_all()

    def update_lanelet(self, old_lanelet_id: int, old_lanelet: Lanelet, new_lanelet: Lanelet):
        successors = [la.lanelet_id for la in self._current_scenario().lanelet_network.lanelets if
                      old_lanelet_id in la.successor]
        predecessors = [la.lanelet_id for la in self._current_scenario().lanelet_network.lanelets if
                        old_lanelet_id in la.predecessor]
        adjacent_left = [(la.lanelet_id, la.adj_left_same_direction) for la in
                         self._current_scenario().lanelet_network.lanelets if old_lanelet_id == la.adj_left]
        adjacent_right = [(la.lanelet_id, la.adj_right_same_direction) for la in
                          self._current_scenario().lanelet_network.lanelets if old_lanelet_id == la.adj_right]

        self._update_scenario()
        self._current_scenario().remove_lanelet(old_lanelet)
        self._current_scenario().add_objects(new_lanelet)

        for la_id in successors:
            self._current_scenario().lanelet_network.find_lanelet_by_id(la_id).add_successor(old_lanelet_id)
        for la_id in predecessors:
            self._current_scenario().lanelet_network.find_lanelet_by_id(la_id).add_predecessor(old_lanelet_id)
        for la_info in adjacent_left:
            self._current_scenario().lanelet_network.find_lanelet_by_id(la_info[0]).adj_left = old_lanelet_id
            self._current_scenario().lanelet_network.find_lanelet_by_id(la_info[0]).adj_left_same_direction = la_info[1]
        for la_info in adjacent_right:
            self._current_scenario().lanelet_network.find_lanelet_by_id(la_info[0]).adj_right = old_lanelet_id
            self._current_scenario().lanelet_network.find_lanelet_by_id(
                    la_info[0]).adj_right_same_direction = la_info[1]

        self.notify_all()

    def remove_lanelet(self, lanelet_id: int):
        self._update_scenario()
        MapCreator.remove_lanelet(lanelet_id, self._current_scenario().lanelet_network)
        self.notify_all()

    def attach_to_other_lanelet(self, lanelet_one: Lanelet, lanelet_two: Lanelet):
        self._update_scenario()
        MapCreator.fit_to_predecessor(lanelet_two, lanelet_one)
        self.notify_all()

    def rotate_lanelet(self, lanelet: Lanelet, rotation_angle: int):
        self._update_scenario()
        initial_vertex = lanelet.center_vertices[0]
        lanelet.translate_rotate(np.array([0, 0]), np.deg2rad(rotation_angle))
        lanelet.translate_rotate(initial_vertex - lanelet.center_vertices[0], 0.0)
        self.notify_all()

    def translate_lanelet(self, lanelet: Lanelet):
        self._update_scenario()
        self._current_scenario().remove_lanelet(lanelet)
        self._current_scenario().add_objects(lanelet)
        self.notify_all()

    def merge_with_successor(self, lanelet: Lanelet):
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

    def merge_lanelets_dynamic_canvas(self, neighboured_lanelets):
        self._update_scenario()
        last_merged_index = None
        while neighboured_lanelets:
            lanelet = neighboured_lanelets.pop()
            for n_lanelet in neighboured_lanelets:
                if n_lanelet.lanelet_id in lanelet.predecessor or n_lanelet.lanelet_id in lanelet.successor:
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

    def add_traffic_sign(self, taffic_sign: TrafficSign, referenced_lanelets):
        self._update_scenario()
        self._current_scenario().add_objects(taffic_sign, referenced_lanelets)
        self.notify_all()

    def remove_traffic_sign(self, traffic_sign_id: int):
        self._update_scenario()
        traffic_sign = self.find_traffic_sign_by_id(traffic_sign_id)
        self._current_scenario().remove_traffic_sign(traffic_sign)
        self.notify_all()

    def remove_obstacle(self, obstacle: Obstacle):
        self._update_scenario()
        # obstacle_id = self.find_obstacle_by_id(obstacle_id)
        self._current_scenario().remove_obstacle(obstacle)
        self.notify_all()

    def update_traffic_sign(self, traffic_sign_id: int):
        self._update_scenario()
        traffic_sign = self.find_traffic_sign_by_id(traffic_sign_id)
        self._current_scenario().remove_traffic_sign(traffic_sign)

    def add_traffic_light(self, traffic_light: TrafficLight, referenced_lanelets):
        self._update_scenario()
        self._current_scenario().add_objects(traffic_light, referenced_lanelets)
        self.notify_all()

    def remove_traffic_light(self, traffic_light_id: int):
        self._update_scenario()
        traffic_light = self.find_traffic_light_by_id(traffic_light_id)
        self._current_scenario().remove_traffic_light(traffic_light)
        self.notify_all()

    def update_traffic_light(self, traffic_light_id: int):
        self._update_scenario()
        traffic_light = self.find_traffic_light_by_id(traffic_light_id)
        self._current_scenario().remove_traffic_light(traffic_light)

    def create_traffic_lights(self, lanelet_network: LaneletNetwork):
        self._update_scenario()
        self._current_scenario().replace_lanelet_network(lanelet_network)
        self.notify_all()

    def create_three_way_intersection(self, width, diameter, incoming_length, add_traffic_signs, add_traffic_lights):
        self._update_scenario()
        country_signs = globals()[
            "TrafficSignID" + SupportedTrafficSignCountry(self.get_country_id()).name.capitalize()]
        intersection, new_traffic_signs, new_traffic_lights, new_lanelets = MapCreator.create_three_way_intersection(
                width, diameter, incoming_length, self._current_scenario(), add_traffic_signs, add_traffic_lights,
                country_signs)
        self._current_scenario().add_objects(intersection)
        self._current_scenario().add_objects(new_lanelets)
        self._current_scenario().add_objects(new_traffic_signs)
        self._current_scenario().add_objects(new_traffic_lights)
        self.notify_all()

    def create_four_way_intersection(self, width, diameter, incoming_length, add_traffic_signs, add_traffic_lights):
        self._update_scenario()
        country_signs = globals()[
            "TrafficSignID" + SupportedTrafficSignCountry(self.get_country_id()).name.capitalize()]
        intersection, new_traffic_signs, new_traffic_lights, new_lanelets = MapCreator.create_four_way_intersection(
                width, diameter, incoming_length, self._current_scenario(), add_traffic_signs, add_traffic_lights,
                country_signs)
        self._current_scenario().add_objects(intersection)
        self._current_scenario().add_objects(new_lanelets)
        self._current_scenario().add_objects(new_traffic_signs)
        self._current_scenario().add_objects(new_traffic_lights)
        self.notify_all()

    def add_intersection(self, intersection: Intersection):
        self._update_scenario()
        self._current_scenario().add_objects(intersection)
        self.notify_all()

    def update_intersection(self, old_intersection_id: int):
        self._update_scenario()
        intersetion = self.find_intersection_by_id(old_intersection_id)
        self._current_scenario().remove_intersection(intersetion)

    def remove_intersection(self, intersection_id: int):
        self._update_scenario()
        intersetion = self.find_intersection_by_id(intersection_id)
        self._current_scenario().remove_intersection(intersetion)
        self.notify_all()

    def fit_intersection(self, intersection_id: int, predecessor_id: int, successor_id: int):
        self._update_scenario()
        intersection = self.find_intersection_by_id(intersection_id)
        lanelet_predecessor = self.find_lanelet_by_id(predecessor_id)
        lanelet_successor = self.find_lanelet_by_id(successor_id)

        MapCreator.fit_intersection_to_predecessor(lanelet_predecessor, lanelet_successor, intersection,
                                                   self._current_scenario().lanelet_network)
        self.notify_all()

    def generate_object_id(self):
        return self._current_scenario().generate_object_id()

    def get_scenario_dt(self):
        return self._current_scenario().dt

    def stop_spinner(self):
        self.notify_all()

    def get_scenario_id(self):
        return self._current_scenario().scenario_id

    def get_dynamic_obstacles(self):
        return self._current_scenario().dynamic_obstacles

    def generate_obj_id(self) -> int:
        return self._current_scenario().generate_object_id()

    def get_lanelets(self):
        return self._current_scenario().lanelet_network.lanelets

    def get_lanelet_network(self) -> LaneletNetwork:
        return self._current_scenario().lanelet_network

    def get_traffic_signs(self):
        return self._current_scenario().lanelet_network.traffic_signs

    def find_lanelet_by_id(self, lanelet_id: int) -> Lanelet:
        return self._current_scenario().lanelet_network.find_lanelet_by_id(lanelet_id)

    def find_lanelet_by_shape(self, shape: Shape):
        return self._current_scenario().lanelet_network.find_lanelet_by_shape(shape)

    def find_traffic_sign_by_id(self, traffic_sign_id: int) -> TrafficSign:
        return self._current_scenario().lanelet_network.find_traffic_sign_by_id(traffic_sign_id)

    def find_obstacle_by_id(self, obstacle_id: int) -> Obstacle:
        return self._current_scenario().obstacle_by_id(obstacle_id)

    def find_traffic_light_by_id(self, traffic_light_id: int) -> TrafficLight:
        return self._current_scenario().lanelet_network.find_traffic_light_by_id(traffic_light_id)

    def find_intersection_by_id(self, intersection_id: int) -> Intersection:
        return self._current_scenario().lanelet_network.find_intersection_by_id(intersection_id)

    def get_country_id(self):
        return self._current_scenario().scenario_id.country_id

    def get_obstacles(self):
        return self._current_scenario().obstacles

    def get_obstacles_by_position_intervals(self, plot_limits):
        return self._current_scenario().obstacles_by_position_intervals(
                [Interval(plot_limits[0], plot_limits[1]),
                 Interval(plot_limits[2], plot_limits[3])]) if plot_limits else self._current_scenario().obstacles

    def obstacle_by_id(self, obstacle_id: int) -> Union[Obstacle, DynamicObstacle, StaticObstacle, None]:
        return self._current_scenario().obstacle_by_id(obstacle_id)

    def replace_lanelet_network(self, lanelet_network: LaneletNetwork):
        return self._current_scenario().replace_lanelet_network(lanelet_network)

    def undo(self):
        if self.__current_scenario_index > 0:
            self.__current_scenario_index -= 1
            self.notify_all()

    def redo(self):
        if self.__current_scenario_index < len(self.__scenarios) - 1:
            self.__current_scenario_index += 1
            self.notify_all()

    def cropp_map(self, rectangle: Rectangle) -> None:
        '''
        Cropps the map and returns all lanelets which lay within the rectangle

        :param rectangle: Rectangle in which the Objects should stay in
        '''
        self._update_scenario()
        new_lanelet_network = self.get_lanelet_network().create_from_lanelet_network(
                self.get_lanelet_network(),shape_input=rectangle)
        self.replace_lanelet_network(new_lanelet_network)
        self.notify_all()

    def hidden_osm_conversion(self, scenario: Scenario):
        self._update_scenario()
        self.set_scenario(scenario)
        self.notify_all()

    def convert_osm_to_cr_with_sumo(self, osm_to_commonroad_using_sumo: Scenario):
        self._update_scenario()
        self.set_scenario(osm_to_commonroad_using_sumo)
        self.notify_all()

    def convert_open_drive_to_cr(self, scenario: Scenario):
        self._update_scenario()
        self.set_scenario(scenario)
        self.notify_all()
