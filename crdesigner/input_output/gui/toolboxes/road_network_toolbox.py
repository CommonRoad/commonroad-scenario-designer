from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import math

from commonroad.scenario.lanelet import LineMarking, LaneletType, RoadUser, StopLine, Lanelet
from commonroad.scenario.intersection import IntersectionIncomingElement, Intersection
from commonroad.scenario.scenario import Scenario
from commonroad.scenario.traffic_sign import *

from crdesigner.input_output.gui.toolboxes.toolbox_ui import CheckableComboBox
from crdesigner.input_output.gui.misc.map_creator import MapCreator
from crdesigner.input_output.gui.toolboxes.road_network_toolbox_ui import RoadNetworkToolboxUI

from crdesigner.input_output.gui.toolboxes.gui_sumo_simulation import SUMO_AVAILABLE
if SUMO_AVAILABLE:
    from crdesigner.map_conversion.sumo_map.cr2sumo.converter import CR2SumoMapConverter
    from crdesigner.map_conversion.sumo_map.config import SumoConfig


class RoadNetworkToolbox(QDockWidget):
    def __init__(self, current_scenario: Scenario, text_browser, callback, tmp_folder: str, selection_changed_callback):
        super().__init__("Road Network Toolbox")
        self.road_network_toolbox = RoadNetworkToolboxUI()
        self.adjust_ui()

        self.current_scenario = current_scenario
        self.text_browser = text_browser
        self.last_added_lanelet_id = None
        self.callback = callback
        self.tmp_folder = tmp_folder
        self.selection_changed_callback = selection_changed_callback
        self.initialized = False
        self.update = False

        self.initialize_lanelet_information()
        self.initialize_traffic_sign_information()
        self.initialize_traffic_light_information()
        self.initialize_intersection_information()
        self.set_default_road_network_list_information()

        self.connect_gui_elements()

    def adjust_ui(self):
        """Updates GUI properties like width, etc."""
        self.setFloating(True)
        self.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.setWidget(self.road_network_toolbox)
        self.road_network_toolbox.setMinimumWidth(375)

    def connect_gui_elements(self):
        self.initialized = False
        self.road_network_toolbox.button_add_lanelet.clicked.connect(lambda: self.add_lanelet())
        self.road_network_toolbox.button_update_lanelet.clicked.connect(lambda: self.update_lanelet())
        self.road_network_toolbox.selected_lanelet_update.currentIndexChanged.connect(
            lambda: self.lanelet_selection_changed())

        self.road_network_toolbox.button_remove_lanelet.clicked.connect(lambda: self.remove_lanelet())
        self.road_network_toolbox.button_attach_to_other_lanelet.clicked.connect(lambda: self.attach_to_other_lanelet())
        self.road_network_toolbox.button_create_adjacent.clicked.connect(lambda: self.create_adjacent())
        self.road_network_toolbox.button_connect_lanelets.clicked.connect(lambda: self.connect_lanelets())
        self.road_network_toolbox.button_rotate_lanelet.clicked.connect(lambda: self.rotate_lanelet())
        self.road_network_toolbox.button_translate_lanelet.clicked.connect(lambda: self.translate_lanelet())
        self.road_network_toolbox.button_merge_lanelets.clicked.connect(lambda: self.merge_with_successor())

        self.road_network_toolbox.button_add_traffic_sign_element.clicked.connect(
            lambda: self.add_traffic_sign_element())
        self.road_network_toolbox.button_remove_traffic_sign_element.clicked.connect(
            lambda: self.remove_traffic_sign_element())
        self.road_network_toolbox.button_add_traffic_sign.clicked.connect(
            lambda: self.add_traffic_sign())
        self.road_network_toolbox.button_remove_traffic_sign.clicked.connect(lambda: self.remove_traffic_sign())
        self.road_network_toolbox.button_update_traffic_sign.clicked.connect(lambda: self.update_traffic_sign())
        self.road_network_toolbox.selected_traffic_sign.currentTextChanged.connect(
            lambda: self.update_traffic_sign_information())

        # Traffic Lights
        self.road_network_toolbox.button_add_traffic_light.clicked.connect(lambda: self.add_traffic_light())
        self.road_network_toolbox.button_update_traffic_light.clicked.connect(lambda: self.update_traffic_light())
        self.road_network_toolbox.button_remove_traffic_light.clicked.connect(lambda: self.remove_traffic_light())
        self.road_network_toolbox.button_create_traffic_lights.clicked.connect(self.create_traffic_lights)
        self.road_network_toolbox.selected_traffic_light.currentTextChanged.connect(
            lambda: self.update_traffic_light_information())

        self.road_network_toolbox.button_four_way_intersection.clicked.connect(lambda: self.add_four_way_intersection())
        self.road_network_toolbox.button_three_way_intersection.clicked.connect(
            lambda: self.add_three_way_intersection())
        self.road_network_toolbox.selected_intersection.currentTextChanged.connect(
            lambda: self.update_intersection_information())
        self.road_network_toolbox.button_add_incoming.clicked.connect(lambda: self.add_incoming_to_table())
        self.road_network_toolbox.button_remove_incoming.clicked.connect(lambda: self.remove_incoming())
        self.road_network_toolbox.button_fit_intersection.clicked.connect(lambda: self.fit_intersection())
        self.road_network_toolbox.button_add_intersection.clicked.connect(lambda: self.add_intersection())
        self.road_network_toolbox.button_remove_intersection.clicked.connect(lambda: self.remove_intersection())
        self.road_network_toolbox.button_update_intersection.clicked.connect(lambda: self.update_intersection())

    def refresh_toolbox(self, scenario: Scenario):
        self.current_scenario = scenario
        # refresh toolboxes based on the scenario
        self.set_default_road_network_list_information()

    def lanelet_selection_changed(self):
        selected_lanelet = self.selected_lanelet()
        if selected_lanelet is not None:
            self.selection_changed_callback(sel_lanelet=selected_lanelet)
            self.update_lanelet_information(selected_lanelet)

    def initialize_toolbox(self):
        self.initialize_lanelet_information()
        self.initialize_traffic_light_information()
        self.initialize_intersection_information()
        self.initialize_traffic_sign_information()
        self.set_default_road_network_list_information()
        self.initialized = True

    def get_x_position_lanelet_start(self) -> float:
        """
        Extracts lanelet x-position of first center vertex.

        @return: x-position [m]
        """
        if self.road_network_toolbox.x_position_lanelet_start.text():
            return float(self.road_network_toolbox.x_position_lanelet_start.text())
        else:
            return 0

    def get_y_position_lanelet_start(self) -> float:
        """
        Extracts lanelet y-position of first center vertex.

        @return: y-position [m]
        """
        if self.road_network_toolbox.y_position_lanelet_start.text():
            return float(self.road_network_toolbox.y_position_lanelet_start.text())
        else:
            return 0

    def collect_lanelet_ids(self) -> List[int]:
        """
        Collects IDs of all lanelets within a CommonRoad scenario.
        @return: List of lanelet IDs.
        """
        if self.current_scenario is not None:
            return sorted([la.lanelet_id for la in self.current_scenario.lanelet_network.lanelets])
        else:
            return []

    def collect_traffic_sign_ids(self) -> List[int]:
        """
        Collects IDs of all traffic signs within a CommonRoad scenario.
        @return: List of traffic sign IDs.
        """
        if self.current_scenario is not None:
            return sorted([ts.traffic_sign_id for ts in self.current_scenario.lanelet_network.traffic_signs])
        return []

    def collect_traffic_light_ids(self) -> List[int]:
        """
        Collects IDs of all traffic lights within a CommonRoad scenario.
        @return: List of traffic light IDs.
        """
        if self.current_scenario is not None:
            return sorted([tl.traffic_light_id for tl in self.current_scenario.lanelet_network.traffic_lights])
        return []

    def collect_intersection_ids(self) -> List[int]:
        """
        Collects IDs of all intersection within a CommonRoad scenario.
        @return: List of intersection IDs.
        """
        if self.current_scenario is not None:
            return sorted([inter.intersection_id for inter in self.current_scenario.lanelet_network.intersections])
        return []

    def collect_incoming_lanelet_ids_from_intersection(self) -> List[int]:
        """
        Collects IDs of all incoming lanelets of a given intersection.
        @return: List of lanelet IDs.
        """
        lanelets = []
        if self.road_network_toolbox.selected_intersection.currentText() not in ["", "None"]:
            selected_intersection_id = int(self.road_network_toolbox.selected_intersection.currentText())
            intersection = self.current_scenario.lanelet_network.find_intersection_by_id(selected_intersection_id)
            for inc in intersection.incomings:
                lanelets += inc.incoming_lanelets
        return lanelets

    def initialize_lanelet_information(self):
        """
        Initializes lanelet GUI elements with lanelet information.
        """
        self.road_network_toolbox.x_position_lanelet_start.setText("0.0")
        self.road_network_toolbox.y_position_lanelet_start.setText("0.0")
        self.road_network_toolbox.lanelet_width.setText("3.0")
        self.road_network_toolbox.line_marking_left.setCurrentIndex(4)
        self.road_network_toolbox.line_marking_right.setCurrentIndex(4)
        self.road_network_toolbox.number_vertices.setText("20")
        self.road_network_toolbox.lanelet_length.setText("10.0")
        self.road_network_toolbox.lanelet_radius.setText("10.0")
        self.road_network_toolbox.lanelet_angle.setText("90.0")

    def initialize_traffic_sign_information(self):
        """
        Initializes traffic sign GUI elements with traffic sign information.
        """
        self.road_network_toolbox.x_position_traffic_sign.setText("0.0")
        self.road_network_toolbox.y_position_traffic_sign.setText("0.0")

    def initialize_traffic_light_information(self):
        """
        Initializes traffic light GUI elements with traffic light information.
        """
        self.road_network_toolbox.x_position_traffic_light.setText("0.0")
        self.road_network_toolbox.y_position_traffic_light.setText("0.0")
        self.road_network_toolbox.time_offset.setText("0")
        self.road_network_toolbox.time_red.setText("120")
        self.road_network_toolbox.time_red_yellow.setText("15")
        self.road_network_toolbox.time_yellow.setText("70")
        self.road_network_toolbox.time_green.setText("380")
        self.road_network_toolbox.time_inactive.setText("0")
        self.road_network_toolbox.traffic_light_active.setChecked(True)

    def initialize_intersection_information(self):
        """
        Initializes GUI elements with intersection information.
        """
        self.road_network_toolbox.intersection_diameter.setText("10")
        self.road_network_toolbox.intersection_lanelet_width.setText("3.0")
        self.road_network_toolbox.intersection_incoming_length.setText("20")

    def set_default_road_network_list_information(self):
        """
        Initializes Combobox GUI elements with lanelet information.
        """
        self.update = True
        self.road_network_toolbox.predecessors.clear()
        self.road_network_toolbox.predecessors.addItems(
            ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox.predecessors.setCurrentIndex(0)

        self.road_network_toolbox.successors.clear()
        self.road_network_toolbox.successors.addItems(
            ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox.successors.setCurrentIndex(0)

        self.road_network_toolbox.adjacent_right.clear()
        self.road_network_toolbox.adjacent_right.addItems(
            ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox.adjacent_right.setCurrentIndex(0)

        self.road_network_toolbox.adjacent_left.clear()
        self.road_network_toolbox.adjacent_left.addItems(
            ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox.adjacent_left.setCurrentIndex(0)

        self.road_network_toolbox.lanelet_referenced_traffic_sign_ids.clear()
        self.road_network_toolbox.lanelet_referenced_traffic_sign_ids.addItems(
            ["None"] + [str(item) for item in self.collect_traffic_sign_ids()])
        self.road_network_toolbox.lanelet_referenced_traffic_sign_ids.setCurrentIndex(0)

        self.road_network_toolbox.lanelet_referenced_traffic_light_ids.clear()
        self.road_network_toolbox.lanelet_referenced_traffic_light_ids.addItems(
            ["None"] + [str(item) for item in self.collect_traffic_light_ids()])
        self.road_network_toolbox.lanelet_referenced_traffic_light_ids.setCurrentIndex(0)

        self.road_network_toolbox.selected_lanelet_update.clear()
        self.road_network_toolbox.selected_lanelet_update.addItems(
            ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox.selected_lanelet_update.setCurrentIndex(0)

        self.road_network_toolbox.selected_lanelet_one.clear()
        self.road_network_toolbox.selected_lanelet_one.addItems(
            ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox.selected_lanelet_one.setCurrentIndex(0)

        self.road_network_toolbox.selected_lanelet_two.clear()
        self.road_network_toolbox.selected_lanelet_two.addItems(
            ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox.selected_lanelet_two.setCurrentIndex(0)

        self.road_network_toolbox.referenced_lanelets_traffic_sign.clear()
        self.road_network_toolbox.referenced_lanelets_traffic_sign.addItems(
            ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox.referenced_lanelets_traffic_sign.setCurrentIndex(0)

        self.road_network_toolbox.selected_traffic_sign.clear()
        self.road_network_toolbox.selected_traffic_sign.addItems(
            ["None"] + [str(item) for item in self.collect_traffic_sign_ids()])
        self.road_network_toolbox.selected_traffic_sign.setCurrentIndex(0)

        self.road_network_toolbox.referenced_lanelets_traffic_light.clear()
        self.road_network_toolbox.referenced_lanelets_traffic_light.addItems(
            ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox.referenced_lanelets_traffic_light.setCurrentIndex(0)

        self.road_network_toolbox.selected_traffic_light.clear()
        self.road_network_toolbox.selected_traffic_light.addItems(
            ["None"] + [str(item) for item in self.collect_traffic_light_ids()])
        self.road_network_toolbox.selected_traffic_light.setCurrentIndex(0)

        self.road_network_toolbox.selected_intersection.clear()
        self.road_network_toolbox.selected_intersection.addItems(
            ["None"] + [str(item) for item in self.collect_intersection_ids()])
        self.road_network_toolbox.selected_intersection.setCurrentIndex(0)

        self.road_network_toolbox.intersection_crossings.clear()
        self.road_network_toolbox.intersection_crossings.addItems(
            ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox.intersection_crossings.setCurrentIndex(0)

        self.road_network_toolbox.intersection_lanelet_to_fit.clear()
        self.road_network_toolbox.intersection_lanelet_to_fit.addItems(
            ["None"] + [str(item) for item in self.collect_incoming_lanelet_ids_from_intersection()])
        self.road_network_toolbox.intersection_lanelet_to_fit.setCurrentIndex(0)

        self.road_network_toolbox.other_lanelet_to_fit.clear()
        self.road_network_toolbox.other_lanelet_to_fit.addItems(
            ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox.other_lanelet_to_fit.setCurrentIndex(0)

        self.road_network_toolbox.intersection_incomings_table.setRowCount(0)

        self.update = False

    def add_lanelet(self, lanelet_id: int = None, update: bool = False, left_vertices: np.array = None,
                    right_vertices: np.array = None):
        """
        Adds a lanelet to the scenario based on the selected parameters by the user.

        @param lanelet_id: Id which the new lanelet should have.
        @param update: Boolean indicating whether lanelet is updated or newly created.
        @param left_vertices: Left boundary of lanelet which should be updated.
        @param right_vertices: Right boundary of lanelet which should be updated.
        """
        if self.current_scenario is None:
            self.text_browser.append("Please create first a new scenario.")
            return

        lanelet_pos_x = self.get_x_position_lanelet_start()
        lanelet_pos_y = self.get_y_position_lanelet_start()
        lanelet_width = float(self.road_network_toolbox.lanelet_width.text())
        line_marking_left = LineMarking(self.road_network_toolbox.line_marking_left.currentText())
        line_marking_right = LineMarking(self.road_network_toolbox.line_marking_right.currentText())
        num_vertices = int(self.road_network_toolbox.number_vertices.text())
        predecessors = [int(pre) for pre in self.road_network_toolbox.predecessors.get_checked_items()]
        successors = [int(suc) for suc in self.road_network_toolbox.successors.get_checked_items()]
        adjacent_left = int(self.road_network_toolbox.adjacent_left.currentText()) \
            if self.road_network_toolbox.adjacent_left.currentText() != "None" else None
        adjacent_right = int(self.road_network_toolbox.adjacent_right.currentText()) \
            if self.road_network_toolbox.adjacent_right.currentText() != "None" else None
        adjacent_left_same_direction = self.road_network_toolbox.adjacent_left_same_direction.isChecked()
        adjacent_right_same_direction = self.road_network_toolbox.adjacent_right_same_direction.isChecked()
        lanelet_type = {LaneletType(ty) for ty in self.road_network_toolbox.lanelet_type.get_checked_items()
                        if ty != "None"}
        user_one_way = {RoadUser(user) for user in self.road_network_toolbox.road_user_oneway.get_checked_items()
                        if user != "None"}
        user_bidirectional = \
            {RoadUser(user) for user in self.road_network_toolbox.road_user_bidirectional.get_checked_items()
             if user != "None"}

        traffic_signs = \
            {int(sign) for sign in self.road_network_toolbox.lanelet_referenced_traffic_sign_ids.get_checked_items()}
        traffic_lights = \
            {int(light) for light in self.road_network_toolbox.lanelet_referenced_traffic_light_ids.get_checked_items()}
        if self.road_network_toolbox.stop_line_start_x.text() != "" \
            and self.road_network_toolbox.stop_line_end_x.text() != "" \
            and self.road_network_toolbox.stop_line_start_y.text() != "" \
            and self.road_network_toolbox.stop_line_end_y.text() != "":
            stop_line_start_x = float(self.road_network_toolbox.stop_line_start_x.text())
            stop_line_end_x = float(self.road_network_toolbox.stop_line_end_x.text())
            stop_line_start_y = float(self.road_network_toolbox.stop_line_start_y.text())
            stop_line_end_y = float(self.road_network_toolbox.stop_line_end_y.text())
            stop_line_marking = LineMarking(self.road_network_toolbox.line_marking_stop_line.currentText())
            stop_line_at_end = self.road_network_toolbox.stop_line_at_end.isChecked()
            stop_line = StopLine(np.array([stop_line_start_x, stop_line_start_y]),
                                 np.array([stop_line_end_x, stop_line_end_y]), stop_line_marking, set(), set())
        elif self.road_network_toolbox.stop_line_at_end.isChecked():
            stop_line_at_end = True
            stop_line_marking = LineMarking(self.road_network_toolbox.line_marking_stop_line.currentText())
            stop_line = StopLine(np.array([0, 0]), np.array([0, 0]), stop_line_marking, set(), set())
        else:
            stop_line_at_end = False
            stop_line = None
        lanelet_length = float(self.road_network_toolbox.lanelet_length.text())
        lanelet_radius = float(self.road_network_toolbox.lanelet_radius.text())
        lanelet_angle = np.deg2rad(float(self.road_network_toolbox.lanelet_angle.text()))
        add_curved_selection = self.road_network_toolbox.curved_lanelet_selection.isChecked()
        connect_to_last_selection = self.road_network_toolbox.connect_to_previous_selection.isChecked()
        connect_to_predecessors_selection = self.road_network_toolbox.connect_to_predecessors_selection.isChecked()
        connect_to_successors_selection = self.road_network_toolbox.connect_to_successors_selection.isChecked()
        place_at_position = self.road_network_toolbox.place_at_defined_position.isChecked()

        if not update:
            if lanelet_id is None:
                lanelet_id = self.current_scenario.generate_object_id()
            if add_curved_selection:
                lanelet = MapCreator.create_curve(lanelet_width, lanelet_radius, lanelet_angle, num_vertices,
                                                  lanelet_id,
                                                  lanelet_type, predecessors, successors, adjacent_left, adjacent_right,
                                                  adjacent_left_same_direction, adjacent_right_same_direction,
                                                  user_one_way, user_bidirectional, line_marking_left,
                                                  line_marking_right, stop_line, traffic_signs, traffic_lights,
                                                  stop_line_at_end)
            else:
                lanelet = MapCreator.create_straight(lanelet_width, lanelet_length, num_vertices, lanelet_id,
                                                     lanelet_type,
                                                     predecessors, successors, adjacent_left, adjacent_right,
                                                     adjacent_left_same_direction, adjacent_right_same_direction,
                                                     user_one_way, user_bidirectional, line_marking_left,
                                                     line_marking_right, stop_line, traffic_signs, traffic_lights,
                                                     stop_line_at_end)
            if connect_to_last_selection:
                if self.last_added_lanelet_id is not None:
                    MapCreator.fit_to_predecessor(
                        self.current_scenario.lanelet_network.find_lanelet_by_id(self.last_added_lanelet_id),
                        lanelet)
                else:
                    self.text_browser.append("__Warning__: Previously add lanelet does not exist anymore. "
                                             "Change lanelet adding option.")
                    return
            elif connect_to_predecessors_selection:
                if len(predecessors) > 0:
                    MapCreator.fit_to_predecessor(
                        self.current_scenario.lanelet_network.find_lanelet_by_id(predecessors[0]), lanelet)
            elif connect_to_successors_selection:
                if len(successors) > 0:
                    MapCreator.fit_to_successor(
                        self.current_scenario.lanelet_network.find_lanelet_by_id(successors[0]), lanelet)
            elif place_at_position:
                lanelet.translate_rotate(np.array([lanelet_pos_x, lanelet_pos_y]), 0)
            self.last_added_lanelet_id = lanelet_id
        else:
            if stop_line_at_end:
                stop_line.start = left_vertices[-1]
                stop_line.end = right_vertices[-1]
            lanelet = Lanelet(left_vertices=left_vertices, right_vertices=right_vertices, predecessor=predecessors,
                              successor=successors, adjacent_left=adjacent_left, adjacent_right=adjacent_right,
                              center_vertices=0.5 * (left_vertices + right_vertices),
                              adjacent_left_same_direction=adjacent_left_same_direction,
                              adjacent_right_same_direction=adjacent_right_same_direction,
                              lanelet_id=lanelet_id, lanelet_type=lanelet_type, user_one_way=user_one_way,
                              user_bidirectional=user_bidirectional, line_marking_right_vertices=line_marking_right,
                              line_marking_left_vertices=line_marking_left, stop_line=stop_line,
                              traffic_signs=traffic_signs,
                              traffic_lights=traffic_lights)
            lanelet.translate_rotate(np.array([-lanelet.center_vertices[0][0], -lanelet.center_vertices[0][1]]), 0)
            lanelet.translate_rotate(np.array([lanelet_pos_x, lanelet_pos_y]), 0)

        self.current_scenario.add_objects(lanelet)
        self.initialize_toolbox()
        self.callback(self.current_scenario)

    def selected_lanelet(self) -> Union[Lanelet, None]:
        """
        Extracts the selected lanelet one
        @return: Selected lanelet object.
        """
        if not self.initialized:
            return
        if self.current_scenario is None:
            self.text_browser.append("create a new file")
            return None
        if self.road_network_toolbox.selected_lanelet_update.currentText() not in ["None", ""]:
            selected_lanelet = self.current_scenario.lanelet_network.find_lanelet_by_id(
                int(self.road_network_toolbox.selected_lanelet_update.currentText()))
            return selected_lanelet
        elif self.road_network_toolbox.selected_lanelet_update.currentText() in ["None", ""] and not self.update:
            self.text_browser.append("No lanelet selected.")
            return None

    def update_lanelet(self):
        """
        Updates a given lanelet based on the information configured by the user.
        """
        selected_lanelet = self.selected_lanelet()
        if selected_lanelet is None:
            return
        selected_lanelet_id = selected_lanelet.lanelet_id
        successors = [la.lanelet_id for la in self.current_scenario.lanelet_network.lanelets
                      if selected_lanelet_id in la.successor]
        predecessors = [la.lanelet_id for la in self.current_scenario.lanelet_network.lanelets
                        if selected_lanelet_id in la.predecessor]
        adjacent_left = [(la.lanelet_id, la.adj_left_same_direction)
                         for la in self.current_scenario.lanelet_network.lanelets
                         if selected_lanelet_id == la.adj_left]
        adjacent_right = [(la.lanelet_id, la.adj_right_same_direction)
                          for la in self.current_scenario.lanelet_network.lanelets
                          if selected_lanelet_id == la.adj_right]

        self.current_scenario.remove_lanelet(selected_lanelet)
        self.add_lanelet(selected_lanelet.lanelet_id, True, selected_lanelet.left_vertices,
                         selected_lanelet.right_vertices)

        for la_id in successors:
            self.current_scenario.lanelet_network.find_lanelet_by_id(la_id).add_successor(selected_lanelet_id)
        for la_id in predecessors:
            self.current_scenario.lanelet_network.find_lanelet_by_id(la_id).add_predecessor(selected_lanelet_id)
        for la_info in adjacent_left:
            self.current_scenario.lanelet_network.find_lanelet_by_id(la_info[0]).adj_left = selected_lanelet_id
            self.current_scenario.lanelet_network.find_lanelet_by_id(la_info[0]).adj_left_same_direction = la_info[1]
        for la_info in adjacent_right:
            self.current_scenario.lanelet_network.find_lanelet_by_id(la_info[0]).adj_right = selected_lanelet_id
            self.current_scenario.lanelet_network.find_lanelet_by_id(la_info[0]).adj_right_same_direction = la_info[1]

        self.set_default_road_network_list_information()
        self.callback(self.current_scenario)

    def update_lanelet_information(self, lanelet: Lanelet = None):
        """
        Updates properties of a selected lanelet.

        @param lanelet: Currently selected lanelet.
        """
        self.road_network_toolbox.x_position_lanelet_start.setText(str(lanelet.center_vertices[0][0]))
        self.road_network_toolbox.y_position_lanelet_start.setText(str(lanelet.center_vertices[0][1]))
        self.road_network_toolbox.lanelet_width.setText(
            str(np.linalg.norm(lanelet.left_vertices[0] - lanelet.right_vertices[0])))

        self.road_network_toolbox.line_marking_left.setCurrentText(lanelet.line_marking_left_vertices.value)
        self.road_network_toolbox.line_marking_right.setCurrentText(lanelet.line_marking_right_vertices.value)
        self.road_network_toolbox.number_vertices.setText(str(len(lanelet.center_vertices)))

        self.road_network_toolbox.predecessors.set_checked_items([str(pre) for pre in lanelet.predecessor])
        self.road_network_toolbox.successors.set_checked_items([str(suc) for suc in lanelet.successor])

        self.road_network_toolbox.adjacent_left.setCurrentText(str(lanelet.adj_left))
        self.road_network_toolbox.adjacent_right.setCurrentText(str(lanelet.adj_right))
        self.road_network_toolbox.adjacent_left_same_direction.setChecked(
            lanelet.adj_left_same_direction if lanelet.adj_left_same_direction is not None else False)
        self.road_network_toolbox.adjacent_right_same_direction.setChecked(
            lanelet.adj_right_same_direction if lanelet.adj_right_same_direction is not None else False)

        self.road_network_toolbox.lanelet_type.set_checked_items(
            [str(la_type.value) for la_type in lanelet.lanelet_type])

        self.road_network_toolbox.road_user_oneway.set_checked_items(
            [str(user.value) for user in lanelet.user_one_way])

        self.road_network_toolbox.road_user_bidirectional.set_checked_items(
            [str(user.value) for user in lanelet.user_bidirectional])

        self.road_network_toolbox.lanelet_referenced_traffic_sign_ids.set_checked_items(
            [str(sign) for sign in lanelet.traffic_signs])
        self.road_network_toolbox.lanelet_referenced_traffic_light_ids.set_checked_items(
            [str(light) for light in lanelet.traffic_lights])

        if lanelet.stop_line is not None:
            self.road_network_toolbox.stop_line_start_x.setText(str(lanelet.stop_line.start[0]))
            self.road_network_toolbox.stop_line_start_y.setText(str(lanelet.stop_line.start[1]))
            self.road_network_toolbox.stop_line_end_x.setText(str(lanelet.stop_line.end[0]))
            self.road_network_toolbox.stop_line_end_y.setText(str(lanelet.stop_line.end[1]))
            self.road_network_toolbox.line_marking_stop_line.setCurrentText(
                str(lanelet.stop_line.line_marking.value))
        else:
            self.road_network_toolbox.stop_line_start_x.setText("")
            self.road_network_toolbox.stop_line_start_y.setText("")
            self.road_network_toolbox.stop_line_end_x.setText("")
            self.road_network_toolbox.stop_line_end_y.setText("")
            self.road_network_toolbox.line_marking_stop_line.setCurrentText("unknown")

    def create_adjacent(self):
        """
        Create adjacent lanelet given a selected lanelet
        """
        selected_lanelet = self.selected_lanelet()
        if selected_lanelet is None:
            return
        adjacent_left = self.road_network_toolbox.create_adjacent_left_selection.isChecked()
        adjacent_same_direction = self.road_network_toolbox.create_adjacent_same_direction_selection.isChecked()

        lanelet_width = float(self.road_network_toolbox.lanelet_width.text())
        line_marking_left = LineMarking(self.road_network_toolbox.line_marking_left.currentText())
        line_marking_right = LineMarking(self.road_network_toolbox.line_marking_right.currentText())
        predecessors = [int(pre) for pre in self.road_network_toolbox.predecessors.get_checked_items()]
        successors = [int(suc) for suc in self.road_network_toolbox.successors.get_checked_items()]
        lanelet_type = {LaneletType(ty) for ty in self.road_network_toolbox.lanelet_type.get_checked_items()
                        if ty != "None"}
        user_one_way = {RoadUser(user) for user in self.road_network_toolbox.road_user_oneway.get_checked_items()
                        if user != "None"}
        user_bidirectional = \
            {RoadUser(user) for user in self.road_network_toolbox.road_user_bidirectional.get_checked_items()
             if user != "None"}
        traffic_signs = \
            {int(sign) for sign in self.road_network_toolbox.lanelet_referenced_traffic_sign_ids.get_checked_items()}
        traffic_lights = \
            {int(light) for light in self.road_network_toolbox.lanelet_referenced_traffic_light_ids.get_checked_items()}
        stop_line_at_end = False
        stop_line = None
        if self.road_network_toolbox.stop_line_start_x.text() != "" \
            and self.road_network_toolbox.stop_line_end_x.text() != "" \
            and self.road_network_toolbox.stop_line_start_y.text() != "" \
            and self.road_network_toolbox.stop_line_end_y.text() != "":
            stop_line_start_x = float(self.road_network_toolbox.stop_line_start_x.text())
            stop_line_end_x = float(self.road_network_toolbox.stop_line_end_x.text())
            stop_line_start_y = float(self.road_network_toolbox.stop_line_start_y.text())
            stop_line_end_y = float(self.road_network_toolbox.stop_line_end_y.text())
            stop_line_marking = LineMarking(self.road_network_toolbox.line_marking_stop_line.currentText())
            stop_line = StopLine(np.array([stop_line_start_x, stop_line_start_y]),
                                 np.array([stop_line_end_x, stop_line_end_y]), stop_line_marking, set(), set())
        elif self.road_network_toolbox.stop_line_at_end.isChecked():
            stop_line_at_end = True
            stop_line_marking = LineMarking(self.road_network_toolbox.line_marking_stop_line.currentText())
            stop_line = StopLine(np.array([0, 0]), np.array([0, 0]), stop_line_marking, set(), set())

        if adjacent_left:
            adjacent_lanelet = MapCreator.create_adjacent_lanelet(adjacent_left, selected_lanelet,
                                                                  self.current_scenario.generate_object_id(),
                                                                  adjacent_same_direction,
                                                                  lanelet_width, lanelet_type,
                                                                  predecessors, successors, user_one_way,
                                                                  user_bidirectional, line_marking_left,
                                                                  line_marking_right, stop_line, traffic_signs,
                                                                  traffic_lights, stop_line_at_end)
        else:
            adjacent_lanelet = MapCreator.create_adjacent_lanelet(adjacent_left, selected_lanelet,
                                                                  self.current_scenario.generate_object_id(),
                                                                  adjacent_same_direction,
                                                                  lanelet_width, lanelet_type,
                                                                  predecessors, successors, user_one_way,
                                                                  user_bidirectional, line_marking_left,
                                                                  line_marking_right, stop_line, traffic_signs,
                                                                  traffic_lights, stop_line_at_end)

        self.last_added_lanelet_id = adjacent_lanelet.lanelet_id
        self.current_scenario.add_objects(adjacent_lanelet)
        self.set_default_road_network_list_information()
        self.callback(self.current_scenario)

    def remove_lanelet(self):
        """
        Removes a selected lanelet from the scenario.
        """
        selected_lanelet = self.selected_lanelet()
        if selected_lanelet is None:
            return

        MapCreator.remove_lanelet(selected_lanelet.lanelet_id, self.current_scenario.lanelet_network)

        if selected_lanelet.lanelet_id == self.last_added_lanelet_id:
            self.last_added_lanelet_id = None

        self.set_default_road_network_list_information()
        self.callback(self.current_scenario)

    def add_four_way_intersection(self):
        """
        Adds a four-way intersection to the scenario.
        """
        if self.current_scenario is None:
            self.text_browser.append("_Warning:_ Create a new file")
            return

        width = float(self.road_network_toolbox.intersection_lanelet_width.text())
        diameter = int(self.road_network_toolbox.intersection_diameter.text())
        incoming_length = int(self.road_network_toolbox.intersection_incoming_length.text())
        add_traffic_signs = self.road_network_toolbox.intersection_with_traffic_signs.isChecked()
        add_traffic_lights = self.road_network_toolbox.intersection_with_traffic_lights.isChecked()
        country_signs = globals()["TrafficSignID" + SupportedTrafficSignCountry(
            self.current_scenario.scenario_id.country_id).name.capitalize()]

        intersection, new_traffic_signs, new_traffic_lights, new_lanelets = \
            MapCreator.create_four_way_intersection(width, diameter, incoming_length, self.current_scenario,
                                                    add_traffic_signs, add_traffic_lights, country_signs)
        self.current_scenario.add_objects(intersection)
        self.current_scenario.add_objects(new_lanelets)
        self.current_scenario.add_objects(new_traffic_signs)
        self.current_scenario.add_objects(new_traffic_lights)
        self.set_default_road_network_list_information()
        self.callback(self.current_scenario)

    def add_three_way_intersection(self):
        """
        Adds a three-way intersection to the scenario.
        """
        if self.current_scenario is None:
            self.text_browser.append("_Warning:_ Create a new file")
            return
        width = float(self.road_network_toolbox.intersection_lanelet_width.text())
        diameter = int(self.road_network_toolbox.intersection_diameter.text())
        incoming_length = int(self.road_network_toolbox.intersection_incoming_length.text())
        add_traffic_signs = self.road_network_toolbox.intersection_with_traffic_signs.isChecked()
        add_traffic_lights = self.road_network_toolbox.intersection_with_traffic_lights.isChecked()
        country_signs = globals()["TrafficSignID" + SupportedTrafficSignCountry(
            self.current_scenario.scenario_id.country_id).name.capitalize()]

        intersection, new_traffic_signs, new_traffic_lights, new_lanelets = \
            MapCreator.create_three_way_intersection(width, diameter, incoming_length, self.current_scenario,
                                                     add_traffic_signs, add_traffic_lights, country_signs)

        self.current_scenario.add_objects(intersection)
        self.current_scenario.add_objects(new_lanelets)
        self.current_scenario.add_objects(new_traffic_signs)
        self.current_scenario.add_objects(new_traffic_lights)
        self.set_default_road_network_list_information()
        self.callback(self.current_scenario)

    def update_incomings(self):
        """
        Updates incoming table information.
        """
        selected_intersection = self.current_scenario.lanelet_network.find_intersection_by_id(
            int(self.road_network_toolbox.selected_intersection.currentText()))
        for inc in selected_intersection.incomings:
            self.road_network_toolbox.intersection_incomings_table.setItem(0, 0, inc.incoming_id)

    def add_traffic_sign_element(self):
        """
        Adds traffic sign element to traffic sign.
        Only a default entry is created the user has to specify the traffic sign ID manually afterward.
        """
        if self.current_scenario is None:
            self.text_browser.append("_Warning:_ Create a new file")
            return
        num_rows = self.road_network_toolbox.traffic_sign_element_table.rowCount()
        self.road_network_toolbox.traffic_sign_element_table.insertRow(num_rows)
        combo_box = QComboBox()
        combo_box.addItems(
            [elem.name for elem in globals()["TrafficSignID"
                                             + SupportedTrafficSignCountry(
                self.current_scenario.scenario_id.country_id).name.capitalize()]])
        self.road_network_toolbox.traffic_sign_element_table.setCellWidget(num_rows, 0, combo_box)

    def remove_traffic_sign_element(self):
        """
        Removes last entry in traffic sign element table of a traffic sign.
        """
        num_rows = self.road_network_toolbox.traffic_sign_element_table.rowCount()
        self.road_network_toolbox.traffic_sign_element_table.removeRow(num_rows - 1)

    def add_traffic_sign(self, traffic_sign_id: int = None):
        """
        Adds a traffic sign to a CommonRoad scenario.

        @param traffic_sign_id: Id which the new traffic sign should have.
        """
        if self.current_scenario is None:
            self.text_browser.append("_Warning:_ Create a new file")
            return
        country_signs = globals()["TrafficSignID" + SupportedTrafficSignCountry(
            self.current_scenario.scenario_id.country_id).name.capitalize()]
        traffic_sign_elements = []
        referenced_lanelets = \
            {int(la) for la in self.road_network_toolbox.referenced_lanelets_traffic_sign.get_checked_items()}
        first_occurrence = set()  # TODO compute first occurrence
        virtual = self.road_network_toolbox.traffic_sign_virtual_selection.isChecked()
        if self.road_network_toolbox.x_position_traffic_sign.text():
            x_position = float(self.road_network_toolbox.x_position_traffic_sign.text())
        else:
            x_position = 0
        if self.road_network_toolbox.y_position_traffic_sign.text():
            y_position = float(self.road_network_toolbox.y_position_traffic_sign.text())
        else:
            y_position = 0
        for row in range(self.road_network_toolbox.traffic_sign_element_table.rowCount()):
            sign_id = self.road_network_toolbox.traffic_sign_element_table.cellWidget(row, 0).currentText()
            if self.road_network_toolbox.traffic_sign_element_table.item(row, 1) is None:
                additional_value = []
            else:
                additional_value = [self.road_network_toolbox.traffic_sign_element_table.item(row, 1).text()]
            traffic_sign_elements.append(TrafficSignElement(country_signs[sign_id], additional_value))

        if len(traffic_sign_elements) == 0:
            self.text_browser.append("_Warning:_ No traffic sign element added.")
            return
        traffic_sign_id = traffic_sign_id if traffic_sign_id is not None else \
            self.current_scenario.generate_object_id()
        new_sign = TrafficSign(traffic_sign_id, traffic_sign_elements,
                               first_occurrence, np.array([x_position, y_position]), virtual)

        self.current_scenario.add_objects(new_sign, referenced_lanelets)
        self.set_default_road_network_list_information()
        self.callback(self.current_scenario)

    def remove_traffic_sign(self):
        """
        Removes selected traffic sign from scenario.
        """
        if self.current_scenario is None:
            self.text_browser.append("_Warning:_ Create a new file")
            return
        if self.road_network_toolbox.selected_traffic_sign.currentText() not in ["", "None"]:
            selected_traffic_sign_id = int(self.road_network_toolbox.selected_traffic_sign.currentText())
        else:
            return
        traffic_sign = self.current_scenario.lanelet_network.find_traffic_sign_by_id(selected_traffic_sign_id)
        self.current_scenario.remove_traffic_sign(traffic_sign)
        self.set_default_road_network_list_information()
        self.callback(self.current_scenario)

    def update_traffic_sign(self):
        """
        Updates information of selected traffic sign.
        """
        if self.current_scenario is None:
            self.text_browser.append("_Warning:_ Create a new file")
            return
        if self.road_network_toolbox.selected_traffic_sign.currentText() not in ["", "None"]:
            selected_traffic_sign_id = int(self.road_network_toolbox.selected_traffic_sign.currentText())
        else:
            return
        traffic_sign = self.current_scenario.lanelet_network.find_traffic_sign_by_id(selected_traffic_sign_id)
        self.current_scenario.remove_traffic_sign(traffic_sign)
        self.add_traffic_sign(selected_traffic_sign_id)
        self.set_default_road_network_list_information()
        self.callback(self.current_scenario)

    def update_traffic_sign_information(self):
        """
        Updates information of traffic sign widget based on traffic sign ID selected by the user.
        """
        if self.road_network_toolbox.selected_traffic_sign.currentText() not in ["", "None"]:
            country_signs = globals()["TrafficSignID" + SupportedTrafficSignCountry(
                self.current_scenario.scenario_id.country_id).name.capitalize()]
            selected_traffic_sign_id = int(self.road_network_toolbox.selected_traffic_sign.currentText())
            traffic_sign = \
                self.current_scenario.lanelet_network.find_traffic_sign_by_id(selected_traffic_sign_id)
            referenced_lanelets = [str(la.lanelet_id) for la in
                                   self.current_scenario.lanelet_network.lanelets
                                   if selected_traffic_sign_id in la.traffic_signs]
            self.road_network_toolbox.referenced_lanelets_traffic_sign.set_checked_items(referenced_lanelets)

            self.road_network_toolbox.traffic_sign_virtual_selection.setChecked(traffic_sign.virtual)
            self.road_network_toolbox.x_position_traffic_sign.setText(str(traffic_sign.position[0]))
            self.road_network_toolbox.y_position_traffic_sign.setText(str(traffic_sign.position[1]))
            self.road_network_toolbox.traffic_sign_element_table.setRowCount(0)
            for elem in traffic_sign.traffic_sign_elements:
                self.add_traffic_sign_element()
                num_rows = self.road_network_toolbox.traffic_sign_element_table.rowCount()
                self.road_network_toolbox.traffic_sign_element_table.cellWidget(num_rows - 1, 0).setCurrentText(
                    country_signs(elem.traffic_sign_element_id).name)
                if len(elem.additional_values) > 0:
                    self.road_network_toolbox.traffic_sign_element_table.setItem(
                        num_rows - 1, 1, QTableWidgetItem(str(elem.additional_values[0])))
                else:
                    self.road_network_toolbox.traffic_sign_element_table.setItem(
                        num_rows - 1, 1, QTableWidgetItem(""))
        else:
            self.road_network_toolbox.traffic_sign_virtual_selection.setChecked(False)
            self.road_network_toolbox.x_position_traffic_sign.setText("0.0")
            self.road_network_toolbox.y_position_traffic_sign.setText("0.0")
            self.road_network_toolbox.traffic_sign_element_table.setRowCount(0)

    def add_traffic_light(self, traffic_light_id: int = None):
        """
        Adds a new traffic light to the scenario based on the user selection.

        @param traffic_light_id: Id which the new traffic sign should have.
        """
        if self.current_scenario is None:
            self.text_browser.append("_Warning:_ Create a new file")
            return
        referenced_lanelets = \
            {int(la) for la in self.road_network_toolbox.referenced_lanelets_traffic_light.get_checked_items()}
        if self.road_network_toolbox.x_position_traffic_light.text():
            x_position = float(self.road_network_toolbox.x_position_traffic_light.text())
        else:
            x_position = 0
        if self.road_network_toolbox.y_position_traffic_light.text():
            y_position = float(self.road_network_toolbox.y_position_traffic_light.text())
        else:
            y_position = 0

        traffic_light_direction = \
            TrafficLightDirection(self.road_network_toolbox.traffic_light_directions.currentText())
        time_offset = int(self.road_network_toolbox.time_offset.text())
        time_red = int(self.road_network_toolbox.time_red.text())
        time_green = int(self.road_network_toolbox.time_green.text())
        time_yellow = int(self.road_network_toolbox.time_yellow.text())
        time_red_yellow = int(self.road_network_toolbox.time_red_yellow.text())
        time_inactive = int(self.road_network_toolbox.time_inactive.text())
        traffic_light_active = self.road_network_toolbox.traffic_light_active.isChecked()
        traffic_light_cycle_order = self.road_network_toolbox.traffic_light_cycle_order.currentText().split("-")

        traffic_light_cycle = []
        for elem in traffic_light_cycle_order:
            if elem == "r" and time_red > 0:
                traffic_light_cycle.append(TrafficLightCycleElement(TrafficLightState.RED, time_red))
            elif elem == "g" and time_green > 0:
                traffic_light_cycle.append(TrafficLightCycleElement(TrafficLightState.GREEN, time_green))
            elif elem == "ry" and time_red_yellow > 0:
                traffic_light_cycle.append(TrafficLightCycleElement(TrafficLightState.RED_YELLOW, time_red_yellow))
            elif elem == "y" and time_yellow > 0:
                traffic_light_cycle.append(TrafficLightCycleElement(TrafficLightState.YELLOW, time_yellow))
            elif elem == "in" and time_inactive > 0:
                traffic_light_cycle.append(TrafficLightCycleElement(TrafficLightState.INACTIVE, time_inactive))

        if traffic_light_id is None:
            traffic_light_id = self.current_scenario.generate_object_id()

        new_traffic_light = TrafficLight(traffic_light_id, traffic_light_cycle,
                                         np.array([x_position, y_position]), time_offset, traffic_light_direction,
                                         traffic_light_active)

        self.current_scenario.add_objects(new_traffic_light, referenced_lanelets)
        self.set_default_road_network_list_information()
        self.callback(self.current_scenario)

    def remove_traffic_light(self):
        """
        Removes a traffic light from the scenario.
        """
        if self.current_scenario is None:
            self.text_browser.append("_Warning:_ Create a new file")
            return
        if self.road_network_toolbox.selected_traffic_light.currentText() not in ["", "None"]:
            selected_traffic_light_id = int(self.road_network_toolbox.selected_traffic_light.currentText())
        else:
            return
        traffic_light = \
            self.current_scenario.lanelet_network.find_traffic_light_by_id(selected_traffic_light_id)
        self.current_scenario.remove_traffic_light(traffic_light)
        self.set_default_road_network_list_information()
        self.callback(self.current_scenario)

    def update_traffic_light(self):
        """
        Updates a traffic light from the scenario based on the user selection.
        """
        if self.current_scenario is None:
            self.text_browser.append("_Warning:_ Create a new file")
            return
        if self.road_network_toolbox.selected_traffic_light.currentText() not in ["", "None"]:
            selected_traffic_light_id = int(self.road_network_toolbox.selected_traffic_light.currentText())
        else:
            return
        traffic_light = \
            self.current_scenario.lanelet_network.find_traffic_light_by_id(selected_traffic_light_id)
        self.current_scenario.remove_traffic_light(traffic_light)
        self.add_traffic_light(selected_traffic_light_id)
        self.set_default_road_network_list_information()
        self.callback(self.current_scenario)

    def update_traffic_light_information(self):
        """
        Updates information of traffic light widget based on traffic light ID selected by the user.
        """
        if self.road_network_toolbox.selected_traffic_light.currentText() not in ["", "None"]:
            selected_traffic_light_id = int(self.road_network_toolbox.selected_traffic_light.currentText())
            traffic_light = \
                self.current_scenario.lanelet_network.find_traffic_light_by_id(selected_traffic_light_id)

            self.road_network_toolbox.x_position_traffic_light.setText(str(traffic_light.position[0]))
            self.road_network_toolbox.y_position_traffic_light.setText(str(traffic_light.position[1]))
            self.road_network_toolbox.time_offset.setText(str(traffic_light.time_offset))
            self.road_network_toolbox.traffic_light_active.setChecked(True)

            cycle_order = ""
            for elem in traffic_light.cycle:
                if elem.state is TrafficLightState.RED:
                    cycle_order += "r-"
                    self.road_network_toolbox.time_red.setText(str(elem.duration))
                if elem.state is TrafficLightState.GREEN:
                    cycle_order += "g-"
                    self.road_network_toolbox.time_green.setText(str(elem.duration))
                if elem.state is TrafficLightState.YELLOW:
                    cycle_order += "y-"
                    self.road_network_toolbox.time_yellow.setText(str(elem.duration))
                if elem.state is TrafficLightState.RED_YELLOW:
                    cycle_order += "ry-"
                    self.road_network_toolbox.time_red_yellow.setText(str(elem.duration))
                if elem.state is TrafficLightState.INACTIVE:
                    cycle_order += "in-"
                    self.road_network_toolbox.time_inactive.setText(str(elem.duration))
            cycle_order = cycle_order[:-1]
            self.road_network_toolbox.traffic_light_cycle_order.setCurrentText(cycle_order)

            self.road_network_toolbox.traffic_light_directions.setCurrentText(str(traffic_light.direction.value))

            referenced_lanelets = [str(la.lanelet_id) for la in
                                   self.current_scenario.lanelet_network.lanelets
                                   if selected_traffic_light_id in la.traffic_lights]
            self.road_network_toolbox.referenced_lanelets_traffic_light.set_checked_items(referenced_lanelets)

    def create_traffic_lights(self):
        if not SUMO_AVAILABLE:
            self.text_browser.append("SUMO is not installed correctly!")
            return
        lanelet_ids = [int(lanelet_id) for lanelet_id in
                       self.road_network_toolbox.referenced_lanelets_traffic_light.get_checked_items()]
        if not lanelet_ids:
            return
        self.road_network_toolbox.referenced_lanelets_traffic_light.clear()
        converter = CR2SumoMapConverter(self.current_scenario,
                                        SumoConfig.from_scenario(self.current_scenario))
        converter.create_sumo_files(self.tmp_folder)
        oks = []
        dt = self.current_scenario.dt
        offset = int(self.road_network_toolbox.time_offset.text())
        red = int(self.road_network_toolbox.time_red.text())
        red_yellow = int(self.road_network_toolbox.time_red_yellow.text())
        green = int(self.road_network_toolbox.time_green.text())
        yellow = int(self.road_network_toolbox.time_yellow.text())
        total = red + red_yellow + green + yellow

        for lanelet_id in lanelet_ids:
            try:
                ok = converter.auto_generate_traffic_light_system(lanelet_id,
                                                                  green_time=int(green * dt),
                                                                  yellow_time=int(yellow * dt),
                                                                  all_red_time=0,
                                                                  left_green_time=math.ceil(0.06 * total * dt),
                                                                  crossing_min_time=math.ceil(0.1 * total * dt),
                                                                  crossing_clearance_time=math.ceil(0.15 * total * dt),
                                                                  time_offset=int(offset * dt))
            except Exception:
                ok = False
            oks.append(ok)
            self.text_browser.append(
                ("Created" if ok else "ERROR: Could not create") + f" traffic light system for lanelet {lanelet_id}")

        if any(oks):
            # update lanelet_network and boradcast change
            self.current_scenario.lanelet_network = converter.lanelet_network
            self.callback(self.current_scenario)

    def add_incoming_to_table(self, new_incoming: bool = True, incoming_ids: List[str] = None):
        """
        Adds a row to the intersection incoming table.
        Only a default entry is created the user has to specify the incoming afterward manually.

        @param new_incoming: Boolean indicating whether this will be an new incoming or from a new intersection
        @param incoming_ids: List of available incoming IDs.
        """
        if self.current_scenario is None:
            self.text_browser.append("_Warning:_ Create a new file")
            return

        num_rows = self.road_network_toolbox.intersection_incomings_table.rowCount()
        self.road_network_toolbox.intersection_incomings_table.insertRow(num_rows)
        lanelet_ids = [str(la_id) for la_id in self.collect_lanelet_ids()]
        if new_incoming:
            self.road_network_toolbox.intersection_incomings_table.setItem(
                num_rows, 0, QTableWidgetItem(str(self.current_scenario.generate_object_id())))
        combo_box_lanelets = CheckableComboBox()
        combo_box_lanelets.addItems(lanelet_ids)
        self.road_network_toolbox.intersection_incomings_table.setCellWidget(num_rows, 1, combo_box_lanelets)
        combo_box_successors_left = CheckableComboBox()
        combo_box_successors_left.addItems(lanelet_ids)
        self.road_network_toolbox.intersection_incomings_table.setCellWidget(num_rows, 2, combo_box_successors_left)
        combo_box_successors_straight = CheckableComboBox()
        combo_box_successors_straight.addItems(lanelet_ids)
        self.road_network_toolbox.intersection_incomings_table.setCellWidget(num_rows, 3, combo_box_successors_straight)
        combo_box_successors_right = CheckableComboBox()
        combo_box_successors_right.addItems(lanelet_ids)
        self.road_network_toolbox.intersection_incomings_table.setCellWidget(num_rows, 4, combo_box_successors_right)
        self.update_left_of_combobox(incoming_ids)

    def update_left_of_combobox(self, incoming_ids: List[str] = None):
        """
        Collects all incoming IDs in incoming table and updates left of combobox

        @param incoming_ids: List of available incoming IDs.
        """
        if incoming_ids is None:
            incoming_ids = [self.road_network_toolbox.intersection_incomings_table.item(row, 0).text()
                            for row in range(self.road_network_toolbox.intersection_incomings_table.rowCount())]
        for row in range(self.road_network_toolbox.intersection_incomings_table.rowCount()):
            combo_box_left_of = QComboBox()
            combo_box_left_of.addItems(incoming_ids)
            if row != self.road_network_toolbox.intersection_incomings_table.rowCount() - 1:
                index = self.road_network_toolbox.intersection_incomings_table.cellWidget(row, 5).findText(
                    self.road_network_toolbox.intersection_incomings_table.cellWidget(row, 5).currentText(),
                    Qt.MatchFixedString)
            else:
                index = -1
            self.road_network_toolbox.intersection_incomings_table.setCellWidget(row, 5, combo_box_left_of)
            if index >= 0:
                self.road_network_toolbox.intersection_incomings_table.cellWidget(row, 5).setCurrentIndex(index)

    def remove_intersection(self):
        """
        Removes selected intersection from lanelet network.
        """
        if self.current_scenario is None:
            self.text_browser.append("_Warning:_ Create a new file")
            return

        if self.road_network_toolbox.selected_intersection.currentText() not in ["", "None"]:
            selected_intersection_id = int(self.road_network_toolbox.selected_intersection.currentText())
            intersection = \
                self.current_scenario.lanelet_network.find_intersection_by_id(selected_intersection_id)
            self.current_scenario.remove_intersection(intersection)
            self.set_default_road_network_list_information()
            self.callback(self.current_scenario)

    def update_intersection(self):
        """
        Updates a selected intersection from the scenario.
        """
        if self.current_scenario is None:
            self.text_browser.append("_Warning:_ Create a new file")
            return

        if self.road_network_toolbox.selected_intersection.currentText() not in ["", "None"]:
            selected_intersection_id = int(self.road_network_toolbox.selected_intersection.currentText())
            intersection = \
                self.current_scenario.lanelet_network.find_intersection_by_id(selected_intersection_id)
            self.current_scenario.remove_intersection(intersection)
            self.add_intersection(selected_intersection_id)
            self.set_default_road_network_list_information()
            self.callback(self.current_scenario)

    def add_intersection(self, intersection_id: int = None):
        """
        Adds an intersection to the scenario.
        """
        if self.current_scenario is None:
            self.text_browser.append("_Warning:_ Create a new file")
            return

        if intersection_id is None:
            intersection_id = self.current_scenario.generate_object_id()
        incomings = []
        for row in range(self.road_network_toolbox.intersection_incomings_table.rowCount()):
            incoming_id = int(self.road_network_toolbox.intersection_incomings_table.item(row, 0).text())
            incoming_lanelets = \
                {int(item) for item in
                 self.road_network_toolbox.intersection_incomings_table.cellWidget(row, 1).get_checked_items()}
            if len(incoming_lanelets) < 1:
                self.text_browser.append("_Warning:_ An incoming must consist at least of one lanelet.")
                print("road_network_toolbox.py/add_intersection: An incoming must consist at least of one lanelet.")
                return
            successor_left = {int(item) for item in self.road_network_toolbox.intersection_incomings_table.cellWidget(
                row, 2).get_checked_items()}
            successor_straight = {int(item) for item in
                                  self.road_network_toolbox.intersection_incomings_table.cellWidget(
                                      row, 3).get_checked_items()}
            successor_right = {int(item) for item in self.road_network_toolbox.intersection_incomings_table.cellWidget(
                row, 4).get_checked_items()}
            if len(successor_left) + len(successor_right) + len(successor_straight) < 1:
                print("An incoming must consist at least of one successor")
                return
            left_of = int(self.road_network_toolbox.intersection_incomings_table.cellWidget(row, 5).currentText()) \
                if self.road_network_toolbox.intersection_incomings_table.cellWidget(row, 5).currentText() != "" \
                else None
            incoming = IntersectionIncomingElement(incoming_id, incoming_lanelets, successor_right,
                                                   successor_straight, successor_left, left_of)
            incomings.append(incoming)
        crossings = {int(item) for item in self.road_network_toolbox.intersection_crossings.get_checked_items()}

        if len(incomings) > 1:
            intersection = Intersection(intersection_id, incomings, crossings)
            self.current_scenario.add_objects(intersection)

            self.set_default_road_network_list_information()
            self.callback(self.current_scenario)
        else:
            self.text_browser.append("_Warning:_ An intersection must consist at least of two incomings.")
            print("road_network_toolbox.py/add_intersection: An intersection must consist at least of two incomings.")

    def remove_incoming(self):
        """
        Removes a row from the intersection incoming table.
        """
        num_rows = self.road_network_toolbox.intersection_incomings_table.rowCount()
        self.road_network_toolbox.intersection_incomings_table.removeRow(num_rows - 1)
        self.update_left_of_combobox()

    def update_intersection_information(self):
        """
        Updates information of intersection widget based on intersection ID selected by the user.
        """
        if self.road_network_toolbox.selected_intersection.currentText() not in ["", "None"]:
            selected_intersection_id = int(self.road_network_toolbox.selected_intersection.currentText())
            intersection = \
                self.current_scenario.lanelet_network.find_intersection_by_id(selected_intersection_id)
            self.road_network_toolbox.intersection_incomings_table.setRowCount(0)
            incoming_ids = [str(inc.incoming_id) for inc in intersection.incomings]
            for incoming in intersection.incomings:
                self.add_incoming_to_table(False, incoming_ids)
                num_rows = self.road_network_toolbox.intersection_incomings_table.rowCount()
                self.road_network_toolbox.intersection_incomings_table.setItem(
                    num_rows - 1, 0, QTableWidgetItem(str(incoming.incoming_id)))
                self.road_network_toolbox.intersection_incomings_table.cellWidget(
                    num_rows - 1, 1).set_checked_items([str(la_id) for la_id in incoming.incoming_lanelets])
                self.road_network_toolbox.intersection_incomings_table.cellWidget(
                    num_rows - 1, 2).set_checked_items([str(la_id) for la_id in incoming.successors_left])
                self.road_network_toolbox.intersection_incomings_table.cellWidget(
                    num_rows - 1, 3).set_checked_items([str(la_id) for la_id in incoming.successors_straight])
                self.road_network_toolbox.intersection_incomings_table.cellWidget(
                    num_rows - 1, 4).set_checked_items([str(la_id) for la_id in incoming.successors_right])
                index = self.road_network_toolbox.intersection_incomings_table.cellWidget(
                    num_rows - 1, 5).findText(str(incoming.left_of))
                self.road_network_toolbox.intersection_incomings_table.cellWidget(
                    num_rows - 1, 5).setCurrentIndex(index)
            self.road_network_toolbox.intersection_crossings.set_checked_items(
                [str(cr) for cr in intersection.crossings])

            self.road_network_toolbox.intersection_lanelet_to_fit.clear()
            self.road_network_toolbox.intersection_lanelet_to_fit.addItems(
                ["None"] + [str(item) for item in self.collect_incoming_lanelet_ids_from_intersection()])
            self.road_network_toolbox.intersection_lanelet_to_fit.setCurrentIndex(0)

    def connect_lanelets(self):
        """
        Connects two lanelets by adding a new lanelet using cubic spline interpolation.
        """
        selected_lanelet_one = self.selected_lanelet()
        if selected_lanelet_one is None:
            return
        if self.road_network_toolbox.selected_lanelet_two.currentText() != "None":
            selected_lanelet_two = self.current_scenario.lanelet_network.find_lanelet_by_id(
                int(self.road_network_toolbox.selected_lanelet_two.currentText()))
        else:
            self.text_browser.append("No lanelet selected for [2].")
            return

        connected_lanelet = MapCreator.connect_lanelets(selected_lanelet_one, selected_lanelet_two,
                                                        self.current_scenario.generate_object_id())
        self.last_added_lanelet_id = connected_lanelet.lanelet_id
        self.current_scenario.add_objects(connected_lanelet)
        self.set_default_road_network_list_information()
        self.callback(self.current_scenario)

    def attach_to_other_lanelet(self):
        """
        Attaches a lanelet to another lanelet.
        @return:
        """
        selected_lanelet_one = self.selected_lanelet()
        if selected_lanelet_one is None:
            return
        if self.road_network_toolbox.selected_lanelet_two.currentText() != "None":
            selected_lanelet_two = self.current_scenario.lanelet_network.find_lanelet_by_id(
                int(self.road_network_toolbox.selected_lanelet_two.currentText()))
        else:
            self.text_browser.append("No lanelet selected for [2].")
            return

        MapCreator.fit_to_predecessor(selected_lanelet_two, selected_lanelet_one)
        self.callback(self.current_scenario)

    def rotate_lanelet(self):
        """
        Rotates lanelet by a user-defined angle.
        """
        selected_lanelet_one = self.selected_lanelet()
        if selected_lanelet_one is None:
            return
        rotation_angle = int(self.road_network_toolbox.rotation_angle.text())
        initial_vertex = selected_lanelet_one.center_vertices[0]
        selected_lanelet_one.translate_rotate(np.array([0, 0]), np.deg2rad(rotation_angle))
        selected_lanelet_one.translate_rotate(initial_vertex - selected_lanelet_one.center_vertices[0], 0.0)
        self.callback(self.current_scenario)

    def translate_lanelet(self):
        """
        Translates lanelet by user-defined x- and y-values.
        """
        selected_lanelet_one = self.selected_lanelet()
        if selected_lanelet_one is None:
            return
        x_translation = float(self.road_network_toolbox.x_translation.text())
        y_translation = float(self.road_network_toolbox.y_translation.text())
        selected_lanelet_one.translate_rotate(np.array([x_translation, y_translation]), 0)
        self.callback(self.current_scenario)

    def merge_with_successor(self):
        """
        Merges a lanelet with its successor. If several successors exist, a new lanelet is created for each successor.
        """
        selected_lanelet_one = self.selected_lanelet()
        if selected_lanelet_one is None:
            return
        successors = []
        predecessors = selected_lanelet_one.predecessor
        for suc in selected_lanelet_one.successor:
            new_lanelet = Lanelet.merge_lanelets(selected_lanelet_one,
                                                 self.current_scenario.lanelet_network.find_lanelet_by_id(suc))
            self.current_scenario.remove_lanelet(self.current_scenario.lanelet_network.find_lanelet_by_id(suc))
            self.current_scenario.add_objects(new_lanelet)
            successors.append(new_lanelet.lanelet_id)
        self.current_scenario.remove_lanelet(selected_lanelet_one)
        for pred in predecessors:
            for suc in successors:
                self.current_scenario.lanelet_network.find_lanelet_by_id(pred).add_successor(suc)
        self.callback(self.current_scenario)

    def fit_intersection(self):
        """
        Rotates and translates a complete intersection so that it is attached to a user-defined lanelet.
        """
        if self.road_network_toolbox.selected_intersection.currentText() not in ["", "None"] \
            and self.road_network_toolbox.other_lanelet_to_fit.currentText() not in ["", "None"] \
            and self.road_network_toolbox.intersection_lanelet_to_fit.currentText() not in ["", "None"]:
            selected_intersection_id = int(self.road_network_toolbox.selected_intersection.currentText())
            intersection = self.current_scenario.lanelet_network.find_intersection_by_id(selected_intersection_id)

            predecessor_id = int(self.road_network_toolbox.other_lanelet_to_fit.currentText())
            lanelet_predecessor = self.current_scenario.lanelet_network.find_lanelet_by_id(predecessor_id)

            successor_id = int(self.road_network_toolbox.intersection_lanelet_to_fit.currentText())
            lanelet_successor = self.current_scenario.lanelet_network.find_lanelet_by_id(successor_id)

            MapCreator.fit_intersection_to_predecessor(lanelet_predecessor, lanelet_successor, intersection,
                                                       self.current_scenario.lanelet_network)
            self.callback(self.current_scenario)
