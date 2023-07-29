from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import math

from commonroad.scenario.lanelet import LineMarking, LaneletType, RoadUser, StopLine, Lanelet
from commonroad.scenario.intersection import IntersectionIncomingElement, Intersection
from commonroad.scenario.scenario import Scenario
from commonroad.scenario.traffic_sign import *
from commonroad.scenario.traffic_light import TrafficLightDirection, TrafficLightCycle, TrafficLight, TrafficLightCycleElement, TrafficLightState

from crdesigner.ui.gui.mwindow.service_layer.services.waitingspinnerwidget import QtWaitingSpinner
from crdesigner.ui.gui.mwindow.toolboxes.toolbox_ui import CheckableComboBox
from crdesigner.ui.gui.mwindow.service_layer.map_creator import MapCreator
from crdesigner.ui.gui.mwindow.toolboxes.road_network_toolbox.road_network_toolbox_ui import RoadNetworkToolboxUI
# from crdesigner.ui.gui.mwindow import AnimatedViewerWrapper
from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.gui_sumo_simulation import SUMO_AVAILABLE
from crdesigner.map_conversion.osm2cr import config
from crdesigner.ui.gui.mwindow.service_layer import config as config_settings

if SUMO_AVAILABLE:
    from crdesigner.map_conversion.sumo_map.cr2sumo.converter import CR2SumoMapConverter
    from crdesigner.map_conversion.map_conversion_interface import SumoConfig


class RequestRunnable(QRunnable):
    def __init__(self, fun, roadNetworkToolbox):
        QRunnable.__init__(self)
        self.fun = fun
        self.roadNetworkToolbox = roadNetworkToolbox

    def run(self):
        self.fun()
        QMetaObject.invokeMethod(self.roadNetworkToolbox, "stopSpinner", Qt.QueuedConnection,
                                 Q_ARG(str, "Conversion Ended"))


class RoadNetworkToolbox(QDockWidget, ):
    def __init__(self, current_scenario: Scenario, text_browser, callback, tmp_folder: str, selection_changed_callback,
                 mwindow):
        super().__init__("Road Network Toolbox")
        self.road_network_toolbox_ui = RoadNetworkToolboxUI(mwindow)
        self.adjust_ui()
        self.mwindow = mwindow
        self.current_scenario = current_scenario
        self.text_browser = text_browser
        self.last_added_lanelet_id = None
        self.callback = callback
        self.tmp_folder = tmp_folder
        self.selection_changed_callback = selection_changed_callback
        self.initialized = False
        self.update = False
        self.updated_lanelet = False
        self.aerial_map_threshold = config.AERIAL_IMAGE_THRESHOLD

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
        self.setWidget(self.road_network_toolbox_ui)
        self.road_network_toolbox_ui.setMinimumWidth(375)

    def connect_gui_elements(self):

        self.initialized = False
        self.road_network_toolbox_ui.button_add_lanelet.clicked.connect(lambda: self.add_lanelet())

        self.road_network_toolbox_ui.button_update_lanelet.clicked.connect(lambda: self.update_lanelet())
        self.road_network_toolbox_ui.selected_lanelet_update.currentIndexChanged.connect(
                lambda: self.lanelet_selection_changed())

        # Lanelet buttons
        self.road_network_toolbox_ui.button_remove_lanelet.clicked.connect(lambda: self.remove_lanelet())
        self.road_network_toolbox_ui.button_attach_to_other_lanelet.clicked.connect(
                lambda: self.attach_to_other_lanelet())

        # connect radiobuttons for adding to the adjust_add_sections function which shows and hides choices
        self.road_network_toolbox_ui.place_at_position.clicked.connect(
                lambda: self.road_network_toolbox_ui.adjust_add_sections())
        self.road_network_toolbox_ui.connect_to_previous_selection.clicked.connect(
                lambda: self.road_network_toolbox_ui.adjust_add_sections())
        self.road_network_toolbox_ui.connect_to_predecessors_selection.clicked.connect(
                lambda: self.road_network_toolbox_ui.adjust_add_sections())
        self.road_network_toolbox_ui.connect_to_successors_selection.clicked.connect(
                lambda: self.road_network_toolbox_ui.adjust_add_sections())
        self.road_network_toolbox_ui.connecting_radio_button_group.buttonClicked.connect(
                lambda: self.initialize_basic_lanelet_information())

        self.road_network_toolbox_ui.button_create_adjacent.clicked.connect(lambda: self.create_adjacent())
        self.road_network_toolbox_ui.button_connect_lanelets.clicked.connect(lambda: self.connect_lanelets())
        self.road_network_toolbox_ui.button_rotate_lanelet.clicked.connect(lambda: self.rotate_lanelet())
        self.road_network_toolbox_ui.button_translate_lanelet.clicked.connect(lambda: self.translate_lanelet())
        self.road_network_toolbox_ui.button_merge_lanelets.clicked.connect(lambda: self.merge_with_successor())

        # Traffic Signs
        self.road_network_toolbox_ui.button_add_traffic_sign_element.clicked.connect(
                lambda: self.add_traffic_sign_element())
        self.road_network_toolbox_ui.button_remove_traffic_sign_element.clicked.connect(
                lambda: self.remove_traffic_sign_element())
        self.road_network_toolbox_ui.button_add_traffic_sign.clicked.connect(lambda: self.add_traffic_sign())
        self.road_network_toolbox_ui.button_remove_traffic_sign.clicked.connect(lambda: self.remove_traffic_sign())
        self.road_network_toolbox_ui.button_update_traffic_sign.clicked.connect(lambda: self.update_traffic_sign())
        self.road_network_toolbox_ui.selected_traffic_sign.currentTextChanged.connect(
                lambda: self.update_traffic_sign_information())

        # Traffic Lights
        self.road_network_toolbox_ui.button_add_traffic_light.clicked.connect(lambda: self.add_traffic_light())
        self.road_network_toolbox_ui.button_update_traffic_light.clicked.connect(lambda: self.update_traffic_light())
        self.road_network_toolbox_ui.button_remove_traffic_light.clicked.connect(lambda: self.remove_traffic_light())
        self.road_network_toolbox_ui.button_create_traffic_lights.clicked.connect(lambda: self.create_traffic_lights())
        self.road_network_toolbox_ui.selected_traffic_light.currentTextChanged.connect(
                lambda: self.update_traffic_light_information())

        # Intersections
        self.road_network_toolbox_ui.button_four_way_intersection.clicked.connect(
                lambda: self.add_four_way_intersection())
        self.road_network_toolbox_ui.button_three_way_intersection.clicked.connect(
                lambda: self.add_three_way_intersection())
        self.road_network_toolbox_ui.selected_intersection.currentTextChanged.connect(
                lambda: self.update_intersection_information())
        self.road_network_toolbox_ui.button_add_incoming.clicked.connect(lambda: self.add_incoming_to_table())
        self.road_network_toolbox_ui.button_remove_incoming.clicked.connect(lambda: self.remove_incoming())
        self.road_network_toolbox_ui.button_fit_intersection.clicked.connect(lambda: self.fit_intersection())
        self.road_network_toolbox_ui.button_add_intersection.clicked.connect(lambda: self.add_intersection())
        self.road_network_toolbox_ui.button_remove_intersection.clicked.connect(lambda: self.remove_intersection())
        self.road_network_toolbox_ui.button_update_intersection.clicked.connect(lambda: self.update_intersection())
        # Aerial Image buttons
        self.road_network_toolbox_ui.button_add_aerial_image.clicked.connect(lambda: self.show_aerial_image())
        self.road_network_toolbox_ui.button_remove_aerial_image.clicked.connect(lambda: self.remove_aerial_image())

    def refresh_toolbox(self, scenario: Scenario):
        self.current_scenario = scenario
        # refresh toolboxes based on the scenario
        self.set_default_road_network_list_information()

    def lanelet_selection_changed(self):
        selected_lanelet = self.selected_lanelet()
        if selected_lanelet is not None:
            self.selection_changed_callback(sel_lanelets=selected_lanelet)
            self.update_lanelet_information(selected_lanelet)

    def initialize_toolbox(self):
        self.initialize_traffic_light_information()
        self.initialize_intersection_information()
        self.initialize_traffic_sign_information()
        self.set_default_road_network_list_information()
        self.initialized = True

    def get_x_position_lanelet_start(self, update=False) -> float:
        """
        Extracts lanelet x-position of first center vertex.

        @return: x-position [m]
        """
        if not update:
            if self.road_network_toolbox_ui.place_at_position.isChecked() and \
                    self.road_network_toolbox_ui.lanelet_start_position_x.text() and \
self.road_network_toolbox_ui.lanelet_start_position_x.text() != "-":
                return float(self.road_network_toolbox_ui.lanelet_start_position_x.text().replace(",", "."))
            else:
                return 0
        else:
            if self.road_network_toolbox_ui.selected_lanelet_start_position_x.text() and \
                    self.road_network_toolbox_ui.selected_lanelet_start_position_x.text() != "-":
                return float(self.road_network_toolbox_ui.selected_lanelet_start_position_x.text().replace(",", "."))
            else:
                return 0

    def get_y_position_lanelet_start(self, update=False) -> float:
        """
        Extracts lanelet y-position of first center vertex.

        @return: y-position [m]
        """
        if not update:
            if self.road_network_toolbox_ui.place_at_position.isChecked() and \
self.road_network_toolbox_ui.lanelet_start_position_y.text() and \
self.road_network_toolbox_ui.lanelet_start_position_y.text() != "-":
                return float(self.road_network_toolbox_ui.lanelet_start_position_y.text().replace(",", "."))
            else:
                return 0
        else:
            if self.road_network_toolbox_ui.selected_lanelet_start_position_y.text() and \
self.road_network_toolbox_ui.selected_lanelet_start_position_y.text() != "-":
                return float(self.road_network_toolbox_ui.selected_lanelet_start_position_y.text().replace(",", "."))
            else:
                return 0

    def get_x_position_lanelet_end(self, update=False) -> float:
        """
        Extracts lanelet x-position of last center vertex.

        @return: x-position [m]
        """
        if not update:
            if self.road_network_toolbox_ui.lanelet_end_position_x.text() and \
                    self.road_network_toolbox_ui.lanelet_end_position_x.text() != "-":
                return float(self.road_network_toolbox_ui.lanelet_end_position_x.text().replace(",", "."))
            else:
                return 0
        else:
            if self.road_network_toolbox_ui.selected_lanelet_end_position_x.text() and \
                    self.road_network_toolbox_ui.selected_lanelet_end_position_x.text() != "-":
                return float(self.road_network_toolbox_ui.selected_lanelet_end_position_x.text().replace(",", "."))
            else:
                return 0

    def get_y_position_lanelet_end(self, update=False) -> float:
        """
        Extracts lanelet y-position of last center vertex.

        @return: y-position [m]
        """
        if not update:
            if self.road_network_toolbox_ui.lanelet_end_position_y.text() and \
                    self.road_network_toolbox_ui.lanelet_end_position_y.text() != "-":
                return float(self.road_network_toolbox_ui.lanelet_end_position_y.text().replace(",", "."))
            else:
                return 0
        else:
            if self.road_network_toolbox_ui.selected_lanelet_end_position_y.text() and \
                    self.road_network_toolbox_ui.selected_lanelet_end_position_y.text() != "-":
                return float(self.road_network_toolbox_ui.selected_lanelet_end_position_y.text().replace(",", "."))
            else:
                return 0

    def get_float(self, str) -> float:
        """
        Validates number and replace , with . to be able to insert german floats

        @return: string argument as valid float if not empty or not - else standard value 5
        """
        if str.text() == "-":
            self.text_browser.append("Inserted value of invalid. Standard value 5 will be used instead.")
        if str.text() and str.text() != "-":
            return float(str.text().replace(",", "."))
        else:
            return 5

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
        if self.road_network_toolbox_ui.selected_intersection.currentText() not in ["", "None"]:
            selected_intersection_id = int(self.road_network_toolbox_ui.selected_intersection.currentText())
            intersection = self.current_scenario.lanelet_network.find_intersection_by_id(selected_intersection_id)
            for inc in intersection.incomings:
                lanelets += inc.incoming_lanelets
        return lanelets

    def initialize_basic_lanelet_information(self):
        """
        Initializes lanelet GUI elements with lanelet information.
        """

        if not self.road_network_toolbox_ui.place_at_position.isChecked() and not \
self.road_network_toolbox_ui.connect_to_previous_selection.isChecked() and not \
        self.road_network_toolbox_ui.connect_to_predecessors_selection.isChecked() and not \
        self.road_network_toolbox_ui.connect_to_successors_selection.isChecked():
            self.road_network_toolbox_ui.adding_method = ""
            return

        if self.road_network_toolbox_ui.connect_to_predecessors_selection.isChecked():
            self.road_network_toolbox_ui.predecessors.view().pressed.connect(
                    self.initialize_predecessor_and_successor_fields)
        elif self.road_network_toolbox_ui.connect_to_successors_selection.isChecked():
            self.road_network_toolbox_ui.successors.view().pressed.connect(
                    self.initialize_predecessor_and_successor_fields)

        # Line marking fields
        line_markings = [e.value for e in LineMarking]
        self.road_network_toolbox_ui.line_marking_right.addItems(line_markings)
        self.road_network_toolbox_ui.line_marking_left.addItems(line_markings)

        # Advanced
        road_user_list = [r.value for r in RoadUser]
        lanelet_type_list = [e.value for e in LaneletType]

        # When connect to previous is selected and the last added lanelet is not none, then initialize all fields
        # with the value of the last lanelet
        if self.road_network_toolbox_ui.connect_to_previous_selection.isChecked():
            if self.last_added_lanelet_id is not None:
                last_lanelet = self.current_scenario.lanelet_network.find_lanelet_by_id(self.last_added_lanelet_id)
                self.road_network_toolbox_ui.previous_lanelet.addItem(str(last_lanelet.lanelet_id))

                self.road_network_toolbox_ui.lanelet_length.setText(self.get_length(last_lanelet))
                self.road_network_toolbox_ui.lanelet_width.setText(self.get_width(last_lanelet))

                # line_markings are the values of last lanelet

                for i in range(0, len(line_markings)):
                    if line_markings[i] == last_lanelet.line_marking_right_vertices.value:
                        break
                self.road_network_toolbox_ui.line_marking_right.setCurrentIndex(i)

                for i in range(0, len(line_markings)):
                    if line_markings[i] == last_lanelet.line_marking_left_vertices.value:
                        break
                self.road_network_toolbox_ui.line_marking_left.setCurrentIndex(i)

                # Advanced fields
                list_bidirectional = [e.value for e in last_lanelet.user_bidirectional]
                for i in range(0, len(road_user_list) - 1):
                    self.road_network_toolbox_ui.road_user_bidirectional.addItem(road_user_list[i])
                    item = self.road_network_toolbox_ui.road_user_bidirectional.model().item(i, 0)
                    if road_user_list[i] in list_bidirectional:
                        item.setCheckState(Qt.Checked)
                    else:
                        item.setCheckState(Qt.Unchecked)

                list_oneway = [e.value for e in last_lanelet.user_one_way]
                for i in range(0, len(road_user_list) - 1):
                    self.road_network_toolbox_ui.road_user_oneway.addItem(road_user_list[i])
                    item = self.road_network_toolbox_ui.road_user_oneway.model().item(i, 0)
                    if road_user_list[i] in list_oneway:
                        item.setCheckState(Qt.Checked)
                    else:
                        item.setCheckState(Qt.Unchecked)

                list_types = [e.value for e in last_lanelet.lanelet_type]
                for i in range(0, len(lanelet_type_list) - 1):
                    self.road_network_toolbox_ui.lanelet_type.addItem(lanelet_type_list[i])
                    item = self.road_network_toolbox_ui.lanelet_type.model().item(i, 0)
                    if lanelet_type_list[i] in list_types:
                        item.setCheckState(Qt.Checked)
                    else:
                        item.setCheckState(Qt.Unchecked)

            else:
                self.road_network_toolbox_ui.previous_lanelet.addItem("None")
        else:

            # Length and width
            self.road_network_toolbox_ui.lanelet_length.setText("10.0")
            self.road_network_toolbox_ui.lanelet_width.setText("3.0")
            self.road_network_toolbox_ui.line_marking_right.setCurrentIndex(4)
            self.road_network_toolbox_ui.line_marking_left.setCurrentIndex(4)

            # Advanced fields
            for i in range(0, len(road_user_list) - 1):
                self.road_network_toolbox_ui.road_user_bidirectional.addItem(road_user_list[i])
                item = self.road_network_toolbox_ui.road_user_bidirectional.model().item(i, 0)
                item.setCheckState(Qt.Unchecked)

            for i in range(0, len(road_user_list) - 1):
                self.road_network_toolbox_ui.road_user_oneway.addItem(road_user_list[i])
                item = self.road_network_toolbox_ui.road_user_oneway.model().item(i, 0)
                item.setCheckState(Qt.Unchecked)

            for i in range(0, len(lanelet_type_list) - 1):
                self.road_network_toolbox_ui.lanelet_type.addItem(lanelet_type_list[i])
                item = self.road_network_toolbox_ui.lanelet_type.model().item(i, 0)
                item.setCheckState(Qt.Unchecked)

        line_markings_stop_line = [e.value for e in LineMarking if
                                   e.value not in [LineMarking.UNKNOWN.value, LineMarking.NO_MARKING.value]]
        self.road_network_toolbox_ui.line_marking_stop_line.addItems(line_markings_stop_line)

        # Neighboring fields
        self.road_network_toolbox_ui.predecessors.clear()
        self.road_network_toolbox_ui.predecessors.addItems(
                ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox_ui.predecessors.setCurrentIndex(0)

        self.road_network_toolbox_ui.successors.clear()
        self.road_network_toolbox_ui.successors.addItems(["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox_ui.successors.setCurrentIndex(0)

        self.road_network_toolbox_ui.adjacent_right.clear()
        self.road_network_toolbox_ui.adjacent_right.addItems(
                ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox_ui.adjacent_right.setCurrentIndex(0)

        self.road_network_toolbox_ui.adjacent_left.clear()
        self.road_network_toolbox_ui.adjacent_left.addItems(
                ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox_ui.adjacent_left.setCurrentIndex(0)

        # Advanced
        self.road_network_toolbox_ui.lanelet_referenced_traffic_sign_ids.clear()
        self.road_network_toolbox_ui.lanelet_referenced_traffic_sign_ids.addItems(
                ["None"] + [str(item) for item in self.collect_traffic_sign_ids()])
        self.road_network_toolbox_ui.lanelet_referenced_traffic_sign_ids.setCurrentIndex(0)

        self.road_network_toolbox_ui.lanelet_referenced_traffic_light_ids.clear()
        self.road_network_toolbox_ui.lanelet_referenced_traffic_light_ids.addItems(
                ["None"] + [str(item) for item in self.collect_traffic_light_ids()])
        self.road_network_toolbox_ui.lanelet_referenced_traffic_light_ids.setCurrentIndex(0)

    def initialize_predecessor_and_successor_fields(self):
        """
        Initializes lanelet information fields according to the selected predecessor / successor when connect to
        predecessor / successor is selected
        selects always the first in the list of predecessors / successors
        """
        if len(self.road_network_toolbox_ui.predecessors.get_checked_items()) == 0 and len(
                self.road_network_toolbox_ui.successors.get_checked_items()) == 0:
            return
        if self.road_network_toolbox_ui.connect_to_predecessors_selection.isChecked():
            pred = self.road_network_toolbox_ui.predecessors.get_checked_items()[0]
            if not pred.isdigit():
                return
            lanelet = self.current_scenario.lanelet_network.find_lanelet_by_id(int(pred))
        elif self.road_network_toolbox_ui.connect_to_successors_selection.isChecked():
            suc = self.road_network_toolbox_ui.successors.get_checked_items()[0]
            if not suc.isdigit():
                return
            lanelet = self.current_scenario.lanelet_network.find_lanelet_by_id(int(suc))
        if lanelet is None:
            return

        self.road_network_toolbox_ui.lanelet_width.setText(self.get_width(lanelet))
        self.road_network_toolbox_ui.lanelet_length.setText(self.get_length(lanelet))

        self.road_network_toolbox_ui.number_vertices.setText(str(len(lanelet.center_vertices)))

        self.road_network_toolbox_ui.line_marking_left.setCurrentText(lanelet.line_marking_left_vertices.value)
        self.road_network_toolbox_ui.line_marking_right.setCurrentText(lanelet.line_marking_right_vertices.value)

        self.road_network_toolbox_ui.lanelet_type.set_checked_items(
                [str(la_type.value) for la_type in lanelet.lanelet_type])

        self.road_network_toolbox_ui.road_user_oneway.set_checked_items(
                [str(user.value) for user in lanelet.user_one_way])

        self.road_network_toolbox_ui.road_user_bidirectional.set_checked_items(
                [str(user.value) for user in lanelet.user_bidirectional])

    def initialize_traffic_sign_information(self):
        """
        Initializes traffic sign GUI elements with traffic sign information.
        """
        self.road_network_toolbox_ui.x_position_traffic_sign.setText("0.0")
        self.road_network_toolbox_ui.y_position_traffic_sign.setText("0.0")

    def initialize_traffic_light_information(self):
        """
        Initializes traffic light GUI elements with traffic light information.
        """
        self.road_network_toolbox_ui.x_position_traffic_light.setText("0.0")
        self.road_network_toolbox_ui.y_position_traffic_light.setText("0.0")
        self.road_network_toolbox_ui.time_offset.setText("0")
        self.road_network_toolbox_ui.time_red.setText("120")
        self.road_network_toolbox_ui.time_red_yellow.setText("15")
        self.road_network_toolbox_ui.time_yellow.setText("70")
        self.road_network_toolbox_ui.time_green.setText("380")
        self.road_network_toolbox_ui.time_inactive.setText("0")
        self.road_network_toolbox_ui.traffic_light_active.setChecked(True)

    def initialize_intersection_information(self):
        """
        Initializes GUI elements with intersection information.
        """
        self.road_network_toolbox_ui.intersection_diameter.setText("10")
        self.road_network_toolbox_ui.intersection_lanelet_width.setText("3.0")
        self.road_network_toolbox_ui.intersection_incoming_length.setText("20")

    def set_default_road_network_list_information(self):
        """
        Initializes Combobox GUI elements with lanelet information.
        """

        self.update = True

        self.road_network_toolbox_ui.selected_lanelet_start_position_x.clear()
        self.road_network_toolbox_ui.selected_lanelet_start_position_y.clear()
        self.road_network_toolbox_ui.selected_lanelet_end_position_x.clear()
        self.road_network_toolbox_ui.selected_lanelet_end_position_y.clear()
        self.road_network_toolbox_ui.selected_lanelet_width.clear()
        self.road_network_toolbox_ui.selected_lanelet_length.clear()

        self.road_network_toolbox_ui.selected_curved_checkbox.setChecked(False)
        self.road_network_toolbox_ui.selected_curved_checkbox.button.setEnabled(True)

        line_markings = [e.value for e in LineMarking]
        self.road_network_toolbox_ui.selected_line_marking_left.clear()
        self.road_network_toolbox_ui.selected_line_marking_left.addItems(line_markings)
        self.road_network_toolbox_ui.selected_line_marking_left.setCurrentIndex(4)
        self.road_network_toolbox_ui.selected_line_marking_right.clear()
        self.road_network_toolbox_ui.selected_line_marking_right.addItems(line_markings)
        self.road_network_toolbox_ui.selected_line_marking_right.setCurrentIndex(4)

        self.road_network_toolbox_ui.selected_stop_line_box.setChecked(False)

        self.road_network_toolbox_ui.selected_predecessors.clear()
        self.road_network_toolbox_ui.selected_predecessors.addItems(
                ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox_ui.selected_predecessors.setCurrentIndex(0)

        self.road_network_toolbox_ui.selected_successors.clear()
        self.road_network_toolbox_ui.selected_successors.addItems(
                ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox_ui.selected_successors.setCurrentIndex(0)

        self.road_network_toolbox_ui.selected_adjacent_right.clear()
        self.road_network_toolbox_ui.selected_adjacent_right.addItems(
                ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox_ui.selected_adjacent_right.setCurrentIndex(0)

        self.road_network_toolbox_ui.selected_adjacent_left.clear()
        self.road_network_toolbox_ui.selected_adjacent_left.addItems(
                ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox_ui.selected_adjacent_left.setCurrentIndex(0)

        self.road_network_toolbox_ui.selected_lanelet_referenced_traffic_sign_ids.clear()
        self.road_network_toolbox_ui.selected_lanelet_referenced_traffic_sign_ids.addItems(
                ["None"] + [str(item) for item in self.collect_traffic_sign_ids()])
        self.road_network_toolbox_ui.selected_lanelet_referenced_traffic_sign_ids.setCurrentIndex(0)

        self.road_network_toolbox_ui.selected_lanelet_referenced_traffic_light_ids.clear()
        self.road_network_toolbox_ui.selected_lanelet_referenced_traffic_light_ids.addItems(
                ["None"] + [str(item) for item in self.collect_traffic_light_ids()])
        self.road_network_toolbox_ui.selected_lanelet_referenced_traffic_light_ids.setCurrentIndex(0)

        self.road_network_toolbox_ui.selected_lanelet_update.clear()
        self.road_network_toolbox_ui.selected_lanelet_update.addItems(
                ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox_ui.selected_lanelet_update.setCurrentIndex(0)

        self.road_network_toolbox_ui.selected_lanelet_one.clear()
        self.road_network_toolbox_ui.selected_lanelet_one.addItems(
                ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox_ui.selected_lanelet_one.setCurrentIndex(0)

        self.road_network_toolbox_ui.selected_lanelet_two.clear()
        self.road_network_toolbox_ui.selected_lanelet_two.addItems(
                ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox_ui.selected_lanelet_two.setCurrentIndex(0)

        self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.clear()
        self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.addItems(
                ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.setCurrentIndex(0)

        self.road_network_toolbox_ui.selected_traffic_sign.clear()
        self.road_network_toolbox_ui.selected_traffic_sign.addItems(
                ["None"] + [str(item) for item in self.collect_traffic_sign_ids()])
        self.road_network_toolbox_ui.selected_traffic_sign.setCurrentIndex(0)

        self.road_network_toolbox_ui.referenced_lanelets_traffic_light.clear()
        self.road_network_toolbox_ui.referenced_lanelets_traffic_light.addItems(
                ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox_ui.referenced_lanelets_traffic_light.setCurrentIndex(0)

        self.road_network_toolbox_ui.selected_traffic_light.clear()
        self.road_network_toolbox_ui.selected_traffic_light.addItems(
                ["None"] + [str(item) for item in self.collect_traffic_light_ids()])
        self.road_network_toolbox_ui.selected_traffic_light.setCurrentIndex(0)

        self.road_network_toolbox_ui.selected_intersection.clear()
        self.road_network_toolbox_ui.selected_intersection.addItems(
                ["None"] + [str(item) for item in self.collect_intersection_ids()])
        self.road_network_toolbox_ui.selected_intersection.setCurrentIndex(0)

        self.road_network_toolbox_ui.intersection_crossings.clear()
        self.road_network_toolbox_ui.intersection_crossings.addItems(
                ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox_ui.intersection_crossings.setCurrentIndex(0)

        self.road_network_toolbox_ui.intersection_lanelet_to_fit.clear()
        self.road_network_toolbox_ui.intersection_lanelet_to_fit.addItems(
                ["None"] + [str(item) for item in self.collect_incoming_lanelet_ids_from_intersection()])
        self.road_network_toolbox_ui.intersection_lanelet_to_fit.setCurrentIndex(0)

        self.road_network_toolbox_ui.other_lanelet_to_fit.clear()
        self.road_network_toolbox_ui.other_lanelet_to_fit.addItems(
                ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox_ui.other_lanelet_to_fit.setCurrentIndex(0)

        self.road_network_toolbox_ui.intersection_incomings_table.setRowCount(0)

        self.update = False

    def add_lanelet(self, lanelet_id: int = None, left_vertices: np.array = None, right_vertices: np.array = None):
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

        if not self.road_network_toolbox_ui.place_at_position.isChecked() and not \
        self.road_network_toolbox_ui.connect_to_previous_selection.isChecked() and not \
                self.road_network_toolbox_ui.connect_to_successors_selection.isChecked() and not \
                self.road_network_toolbox_ui.connect_to_predecessors_selection.isChecked():
            self.text_browser.append("Please select an adding option.")
            return

        predecessors = [int(pre) for pre in self.road_network_toolbox_ui.predecessors.get_checked_items()]
        successors = [int(suc) for suc in self.road_network_toolbox_ui.successors.get_checked_items()]

        place_at_position = self.road_network_toolbox_ui.place_at_position.isChecked()
        connect_to_last_selection = self.road_network_toolbox_ui.connect_to_previous_selection.isChecked()
        connect_to_predecessors_selection = self.road_network_toolbox_ui.connect_to_predecessors_selection.isChecked()
        connect_to_successors_selection = self.road_network_toolbox_ui.connect_to_successors_selection.isChecked()

        if connect_to_last_selection and self.last_added_lanelet_id is None:
            self.text_browser.append("__Warning__: Previously add lanelet does not exist anymore. "
                                     "Change lanelet adding option.")
            return
        if connect_to_predecessors_selection and len(predecessors) == 0:
            self.text_browser.append("__Warning__: No predecessors are selected.")
            return
        if connect_to_successors_selection and len(successors) == 0:
            self.text_browser.append("__Warning__: No successors are selected.")
            return

        lanelet_start_pos_x = self.get_x_position_lanelet_start(False)
        lanelet_start_pos_y = self.get_y_position_lanelet_start(False)

        lanelet_width = self.get_float(self.road_network_toolbox_ui.lanelet_width)
        line_marking_left = LineMarking(self.road_network_toolbox_ui.line_marking_left.currentText())
        line_marking_right = LineMarking(self.road_network_toolbox_ui.line_marking_right.currentText())
        num_vertices = int(self.road_network_toolbox_ui.number_vertices.text())
        adjacent_left = int(
                self.road_network_toolbox_ui.adjacent_left.currentText()) if \
                self.road_network_toolbox_ui.adjacent_left.currentText() != "None" else None
        adjacent_right = int(
                self.road_network_toolbox_ui.adjacent_right.currentText()) if \
                self.road_network_toolbox_ui.adjacent_right.currentText() != "None" else None
        adjacent_left_same_direction = self.road_network_toolbox_ui.adjacent_left_same_direction.isChecked()
        adjacent_right_same_direction = self.road_network_toolbox_ui.adjacent_right_same_direction.isChecked()
        lanelet_type = {LaneletType(ty) for ty in self.road_network_toolbox_ui.lanelet_type.get_checked_items() if
                        ty != "None"}
        user_one_way = {RoadUser(user) for user in self.road_network_toolbox_ui.road_user_oneway.get_checked_items() if
                        user != "None"}
        user_bidirectional = {RoadUser(user) for user in
                              self.road_network_toolbox_ui.road_user_bidirectional.get_checked_items() if
                              user != "None"}

        traffic_signs = {int(sign) for sign in
                         self.road_network_toolbox_ui.lanelet_referenced_traffic_sign_ids.get_checked_items()}
        traffic_lights = {int(light) for light in
                          self.road_network_toolbox_ui.lanelet_referenced_traffic_light_ids.get_checked_items()}
        if self.road_network_toolbox_ui.stop_line_check_box.isChecked():
            if self.road_network_toolbox_ui.stop_line_beginning.isChecked():
                stop_line_at_end = False
                stop_line_at_beginning = True
                stop_line_marking = LineMarking(self.road_network_toolbox_ui.line_marking_stop_line.currentText())
                stop_line = StopLine(np.array([0, 0]), np.array([0, 0]), stop_line_marking, set(), set())
            elif self.road_network_toolbox_ui.stop_line_end.isChecked():
                stop_line_at_end = True
                stop_line_at_beginning = False
                stop_line_marking = LineMarking(self.road_network_toolbox_ui.line_marking_stop_line.currentText())
                stop_line = StopLine(np.array([0, 0]), np.array([0, 0]), stop_line_marking, set(), set())
        else:
            stop_line_at_end = False
            stop_line_at_beginning = False
            stop_line = None

        lanelet_length = self.get_float(self.road_network_toolbox_ui.lanelet_length)
        lanelet_radius = self.get_float(self.road_network_toolbox_ui.lanelet_radius)
        lanelet_angle = np.deg2rad(self.get_float(self.road_network_toolbox_ui.lanelet_angle))
        add_curved_selection = self.road_network_toolbox_ui.curved_check_button.button.isChecked()

        if lanelet_id is None:
            lanelet_id = self.current_scenario.generate_object_id()
        if add_curved_selection:
            lanelet = MapCreator.create_curve(lanelet_width, lanelet_radius, lanelet_angle, num_vertices, lanelet_id,
                                              lanelet_type, predecessors, successors, adjacent_left, adjacent_right,
                                              adjacent_left_same_direction, adjacent_right_same_direction, user_one_way,
                                              user_bidirectional, line_marking_left, line_marking_right, stop_line,
                                              traffic_signs, traffic_lights, stop_line_at_end, stop_line_at_beginning)
        else:
            lanelet = MapCreator.create_straight(lanelet_width, lanelet_length, num_vertices, lanelet_id, lanelet_type,
                                                 predecessors, successors, adjacent_left, adjacent_right,
                                                 adjacent_left_same_direction, adjacent_right_same_direction,
                                                 user_one_way, user_bidirectional, line_marking_left,
                                                 line_marking_right, stop_line, traffic_signs, traffic_lights,
                                                 stop_line_at_end, stop_line_at_beginning)

        if connect_to_last_selection:
            last_lanelet = self.current_scenario.lanelet_network.find_lanelet_by_id(self.last_added_lanelet_id)
            lanelet.translate_rotate(
                    np.array([last_lanelet.center_vertices[-1][0], last_lanelet.center_vertices[-1][1]]), 0)
            MapCreator.fit_to_predecessor(last_lanelet, lanelet)
        elif connect_to_predecessors_selection:
            if len(predecessors) > 0:
                predecessor = self.current_scenario.lanelet_network.find_lanelet_by_id(predecessors[0])
                lanelet.translate_rotate(
                        np.array([predecessor.center_vertices[-1][0], predecessor.center_vertices[-1][1]]), 0)
                MapCreator.fit_to_predecessor(predecessor, lanelet)
        elif connect_to_successors_selection:
            if len(successors) > 0:
                successor = self.current_scenario.lanelet_network.find_lanelet_by_id(successors[0])

                x_start = successor.center_vertices[0][0] - lanelet_length
                y_start = successor.center_vertices[0][1]

                lanelet.translate_rotate(np.array([x_start, y_start]), 0)
                MapCreator.fit_to_successor(successor, lanelet)
        elif place_at_position:
            lanelet.translate_rotate(np.array([lanelet_start_pos_x, lanelet_start_pos_y]), 0)
            if not self.road_network_toolbox_ui.horizontal.isChecked():
                if self.road_network_toolbox_ui.select_end_position.isChecked():
                    rotation_angle = math.degrees(
                            math.asin((self.get_y_position_lanelet_end() - lanelet_start_pos_y) / lanelet_length))
                    # convert rotation_angle to positive angle since translate_rotate function only expects positive
                    # angle
                    if self.get_x_position_lanelet_end() < lanelet_start_pos_x:
                        rotation_angle = 180 - rotation_angle
                    if rotation_angle < 0:
                        rotation_angle = 360 + rotation_angle
                elif self.road_network_toolbox_ui.rotate.isChecked():
                    rotation_angle = int(self.road_network_toolbox_ui.rotation_angle_end.text())

                initial_vertex_x = lanelet.center_vertices[0]
                if rotation_angle > 360:
                    rotation_angle %= 360
                lanelet.translate_rotate(np.array([0, 0]), np.deg2rad(rotation_angle))
                lanelet.translate_rotate(initial_vertex_x - lanelet.center_vertices[0], 0.0)

        self.last_added_lanelet_id = lanelet_id

        self.current_scenario.add_objects(lanelet)

        # uncheck all buttons and hide all selected boxes
        self.road_network_toolbox_ui.connecting_radio_button_group.setExclusive(False)
        if self.road_network_toolbox_ui.place_at_position.isChecked():
            self.road_network_toolbox_ui.place_at_position.click()
        elif self.road_network_toolbox_ui.connect_to_previous_selection.isChecked():
            self.road_network_toolbox_ui.connect_to_previous_selection.click()
        elif self.road_network_toolbox_ui.connect_to_predecessors_selection.isChecked():
            self.road_network_toolbox_ui.connect_to_predecessors_selection.click()
        elif self.road_network_toolbox_ui.connect_to_successors_selection.isChecked():
            self.road_network_toolbox_ui.connect_to_successors_selection.click()
        self.road_network_toolbox_ui.connecting_radio_button_group.setExclusive(True)

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
        if self.road_network_toolbox_ui.selected_lanelet_update.currentText() not in ["None", ""]:
            selected_lanelet = self.current_scenario.lanelet_network.find_lanelet_by_id(
                    int(self.road_network_toolbox_ui.selected_lanelet_update.currentText()))
            return selected_lanelet
        elif self.road_network_toolbox_ui.selected_lanelet_update.currentText() in ["None", ""] and not self.update:
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
        successors = [la.lanelet_id for la in self.current_scenario.lanelet_network.lanelets if
                      selected_lanelet_id in la.successor]
        predecessors = [la.lanelet_id for la in self.current_scenario.lanelet_network.lanelets if
                        selected_lanelet_id in la.predecessor]
        adjacent_left = [(la.lanelet_id, la.adj_left_same_direction) for la in
                         self.current_scenario.lanelet_network.lanelets if selected_lanelet_id == la.adj_left]
        adjacent_right = [(la.lanelet_id, la.adj_right_same_direction) for la in
                          self.current_scenario.lanelet_network.lanelets if selected_lanelet_id == la.adj_right]

        self.current_scenario.remove_lanelet(selected_lanelet)
        self.add_updated_lanelet(selected_lanelet.lanelet_id, selected_lanelet.left_vertices,
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

        self.updated_lanelet = True
        self.set_default_road_network_list_information()
        self.callback(self.current_scenario)

    def add_updated_lanelet(self, lanelet_id: int, left_vertices: np.array = None, right_vertices: np.array = None):
        """
        Adds an updated lanelet to the scenario based on the selected parameters by the user.
        The original lanelet has to be removed beforeward.

        @param lanelet_id: Id which the new lanelet should have.
        @param update: Boolean indicating whether lanelet is updated or newly created.
        @param left_vertices: Left boundary of lanelet which should be updated.
        @param right_vertices: Right boundary of lanelet which should be updated.
        """

        predecessors = [int(pre) for pre in self.road_network_toolbox_ui.selected_predecessors.get_checked_items()]
        successors = [int(suc) for suc in self.road_network_toolbox_ui.selected_successors.get_checked_items()]

        lanelet_start_pos_x = self.get_x_position_lanelet_start(True)
        lanelet_start_pos_y = self.get_y_position_lanelet_start(True)
        lanelet_end_pos_x = self.get_x_position_lanelet_end(True)
        lanelet_end_pos_y = self.get_y_position_lanelet_end(True)

        lanelet_width = self.get_float(self.road_network_toolbox_ui.selected_lanelet_width)
        line_marking_left = LineMarking(self.road_network_toolbox_ui.selected_line_marking_left.currentText())
        line_marking_right = LineMarking(self.road_network_toolbox_ui.selected_line_marking_right.currentText())
        num_vertices = int(self.road_network_toolbox_ui.selected_number_vertices.text())
        adjacent_left = int(
                self.road_network_toolbox_ui.selected_adjacent_left.currentText()) if \
                self.road_network_toolbox_ui.selected_adjacent_left.currentText() != "None" else None
        adjacent_right = int(
                self.road_network_toolbox_ui.selected_adjacent_right.currentText()) if \
                self.road_network_toolbox_ui.selected_adjacent_right.currentText() != "None" else None
        adjacent_left_same_direction = self.road_network_toolbox_ui.selected_adjacent_left_same_direction.isChecked()
        adjacent_right_same_direction = self.road_network_toolbox_ui.selected_adjacent_right_same_direction.isChecked()
        lanelet_type = {LaneletType(ty) for ty in self.road_network_toolbox_ui.selected_lanelet_type.get_checked_items()
                        if ty != "None"}
        user_one_way = {RoadUser(user) for user in
                        self.road_network_toolbox_ui.selected_road_user_oneway.get_checked_items() if user != "None"}
        user_bidirectional = {RoadUser(user) for user in
                              self.road_network_toolbox_ui.selected_road_user_bidirectional.get_checked_items() if
                              user != "None"}

        traffic_signs = {int(sign) for sign in
                         self.road_network_toolbox_ui.selected_lanelet_referenced_traffic_sign_ids.get_checked_items()}
        traffic_lights = {int(light) for light in
                          self.road_network_toolbox_ui.selected_lanelet_referenced_traffic_light_ids
                          .get_checked_items()}
        if self.road_network_toolbox_ui.selected_stop_line_box.isChecked():
            if self.road_network_toolbox_ui.selected_stop_line_beginning.isChecked():
                stop_line_at_end = False
                stop_line_at_beginning = True
                stop_line_marking = LineMarking(
                        self.road_network_toolbox_ui.selected_line_marking_stop_line.currentText())
                stop_line = StopLine(np.array([0, 0]), np.array([0, 0]), stop_line_marking, set(), set())
            elif self.road_network_toolbox_ui.selected_stop_line_end.isChecked():
                stop_line_at_end = True
                stop_line_at_beginning = False
                stop_line_marking = LineMarking(
                        self.road_network_toolbox_ui.selected_line_marking_stop_line.currentText())
                stop_line = StopLine(np.array([0, 0]), np.array([0, 0]), stop_line_marking, set(), set())
            else:
                stop_line_start_x = self.get_float(self.road_network_toolbox_ui.selected_stop_line_start_x)
                stop_line_end_x = self.get_float(self.road_network_toolbox_ui.selected_stop_line_end_x)
                stop_line_start_y = self.get_float(self.road_network_toolbox_ui.selected_stop_line_start_y)
                stop_line_end_y = self.get_float(self.road_network_toolbox_ui.selected_stop_line_end_y)
                stop_line_marking = LineMarking(
                        self.road_network_toolbox_ui.selected_line_marking_stop_line.currentText())
                stop_line_at_end = False
                stop_line_at_beginning = False
                stop_line = StopLine(np.array([stop_line_start_x, stop_line_start_y]),
                                     np.array([stop_line_end_x, stop_line_end_y]), stop_line_marking, set(), set())
        else:
            stop_line_at_end = False
            stop_line_at_beginning = False
            stop_line = None

        lanelet_length = self.get_float(self.road_network_toolbox_ui.selected_lanelet_length)
        lanelet_radius = self.get_float(self.road_network_toolbox_ui.selected_lanelet_radius)
        lanelet_angle = np.deg2rad(self.get_float(self.road_network_toolbox_ui.selected_lanelet_angle))
        add_curved_selection = self.road_network_toolbox_ui.selected_curved_checkbox.button.isChecked()

        if stop_line is not None:
            stop_line_start = stop_line.start
            stop_line_end = stop_line.end

        if add_curved_selection:
            lanelet = MapCreator.create_curve(lanelet_width, lanelet_radius, lanelet_angle, num_vertices, lanelet_id,
                                              lanelet_type, predecessors, successors, adjacent_left, adjacent_right,
                                              adjacent_left_same_direction, adjacent_right_same_direction, user_one_way,
                                              user_bidirectional, line_marking_left, line_marking_right, stop_line,
                                              traffic_signs, traffic_lights, stop_line_at_end, stop_line_at_beginning)
            rotation_angle = 0
        else:
            lanelet = MapCreator.create_straight(lanelet_width, lanelet_length, num_vertices, lanelet_id, lanelet_type,
                                                 predecessors, successors, adjacent_left, adjacent_right,
                                                 adjacent_left_same_direction, adjacent_right_same_direction,
                                                 user_one_way, user_bidirectional, line_marking_left,
                                                 line_marking_right, stop_line, traffic_signs, traffic_lights,
                                                 stop_line_at_end, stop_line_at_beginning)
            rotation_angle = math.degrees(math.asin((lanelet_end_pos_y - lanelet_start_pos_y) / lanelet_length))

        lanelet.translate_rotate(np.array([lanelet_start_pos_x, lanelet_start_pos_y]), 0)

        # convert rotation_angle to positive angle since translate_rotate function only expects positive
        # angle
        if lanelet_end_pos_x < lanelet_start_pos_x:
            rotation_angle = 180 - rotation_angle
        if rotation_angle < 0:
            rotation_angle = 360 + rotation_angle

        initial_vertex = lanelet.center_vertices[0]
        lanelet.translate_rotate(np.array([0, 0]), np.deg2rad(rotation_angle))
        lanelet.translate_rotate(initial_vertex - lanelet.center_vertices[0], 0.0)

        # rotation destroys position of stop line therefore save stop line position and afterwards set stop line
        # position again to right value
        if stop_line is not None and not stop_line_at_end and not stop_line_at_beginning:
            lanelet.stop_line.start = stop_line_start
            lanelet.stop_line.end = stop_line_end

        self.last_added_lanelet_id = lanelet_id

        self.current_scenario.add_objects(lanelet)

        self.callback(self.current_scenario)

    def get_length(self, lanelet: Lanelet = None):
        """
        Calculates length of the lanelet.

        @param lanelet: Lanelet of which the length should be calculated.
        @return: length of lanelet
        """
        return str(
                np.linalg.norm(lanelet.center_vertices[0] - lanelet.center_vertices[len(lanelet.center_vertices) - 1]))

    def get_width(self, lanelet: Lanelet = None):
        """
        Calculates width of the lanelet.

        @param lanelet: Lanelet of which the width should be calculated.
        @return: width of lanelet
        """
        return str(np.linalg.norm(lanelet.left_vertices[0] - lanelet.right_vertices[0]))

    def lanelet_is_straight(self, lanelet: Lanelet = None):
        """
        Checks wether lanelet is straight

        @param lanelet: Lanelet of which it should be checked whether it is straight.
        @return: bool value of result
        """
        x_start = round(lanelet.left_vertices[0][0] - lanelet.right_vertices[0][0], 3)
        y_start = round(lanelet.left_vertices[0][1] - lanelet.right_vertices[0][1], 3)
        x_end = round(lanelet.left_vertices[len(lanelet.left_vertices) - 1][0] -
                      lanelet.right_vertices[len(lanelet.right_vertices) - 1][0], 3)
        y_end = round(lanelet.left_vertices[len(lanelet.left_vertices) - 1][1] -
                      lanelet.right_vertices[len(lanelet.right_vertices) - 1][1], 3)
        return x_start == x_end and y_start == y_end

    def update_lanelet_information(self, lanelet: Lanelet = None):
        """
        Updates properties of a selected lanelet.

        @param lanelet: Currently selected lanelet.
        """
        if self.road_network_toolbox_ui.connect_to_predecessors_selection.isChecked():
            self.road_network_toolbox_ui.predecessors.setCurrentIndex(lanelet.lanelet_id)
            self.road_network_toolbox_ui.predecessors.set_checked_items([str(lanelet.lanelet_id)])
            self.initialize_predecessor_and_successor_fields()
        elif self.road_network_toolbox_ui.connect_to_successors_selection.isChecked():
            self.road_network_toolbox_ui.successors.setCurrentIndex(lanelet.lanelet_id)
            self.road_network_toolbox_ui.successors.set_checked_items([str(lanelet.lanelet_id)])
            self.initialize_predecessor_and_successor_fields()

        self.road_network_toolbox_ui.selected_lanelet_start_position_x.setText(
                str(0.0 if lanelet.center_vertices[0][0] == 1.0e-16 else lanelet.center_vertices[0][0]))
        self.road_network_toolbox_ui.selected_lanelet_start_position_y.setText(
                str(0.0 if lanelet.center_vertices[0][1] == 1.0e-16 else lanelet.center_vertices[0][1]))
        self.road_network_toolbox_ui.selected_lanelet_end_position_x.setText(
                str(0.0 if lanelet.center_vertices[len(lanelet.center_vertices) - 1][0] == 1.0e-16 else
                    lanelet.center_vertices[len(lanelet.center_vertices) - 1][0]))
        self.road_network_toolbox_ui.selected_lanelet_end_position_y.setText(
                str(0.0 if lanelet.center_vertices[len(lanelet.center_vertices) - 1][1] == 1.0e-16 else
                    lanelet.center_vertices[len(lanelet.center_vertices) - 1][1]))
        self.road_network_toolbox_ui.selected_lanelet_width.setText(self.get_width(lanelet))
        self.road_network_toolbox_ui.selected_lanelet_length.setText(self.get_length(lanelet))

        # curved lanelet attributes
        if not self.lanelet_is_straight(lanelet):
            self.road_network_toolbox_ui.selected_curved_checkbox.setChecked(True)
            self.road_network_toolbox_ui.selected_curved_checkbox.box.setMaximumSize(0, 0)
            self.road_network_toolbox_ui.selected_curved_checkbox.button.setDisabled(True)
        else:
            self.road_network_toolbox_ui.selected_curved_checkbox.button.setEnabled(True)
            self.road_network_toolbox_ui.selected_curved_checkbox.setChecked(False)
            self.road_network_toolbox_ui.selected_curved_checkbox.box.setMaximumSize(0, 0)

        self.road_network_toolbox_ui.selected_lanelet_radius.setText("10.0")
        self.road_network_toolbox_ui.selected_lanelet_angle.setText("90.0")

        self.road_network_toolbox_ui.selected_number_vertices.setText(str(len(lanelet.center_vertices)))

        self.road_network_toolbox_ui.selected_line_marking_left.setCurrentText(lanelet.line_marking_left_vertices.value)
        self.road_network_toolbox_ui.selected_line_marking_right.setCurrentText(
                lanelet.line_marking_right_vertices.value)

        self.road_network_toolbox_ui.selected_predecessors.set_checked_items([str(pre) for pre in lanelet.predecessor])
        self.road_network_toolbox_ui.selected_successors.set_checked_items([str(suc) for suc in lanelet.successor])

        self.road_network_toolbox_ui.selected_adjacent_left.setCurrentText(str(lanelet.adj_left))
        self.road_network_toolbox_ui.selected_adjacent_right.setCurrentText(str(lanelet.adj_right))
        self.road_network_toolbox_ui.selected_adjacent_left_same_direction.setChecked(
                lanelet.adj_left_same_direction if lanelet.adj_left_same_direction is not None else False)
        self.road_network_toolbox_ui.selected_adjacent_right_same_direction.setChecked(
                lanelet.adj_right_same_direction if lanelet.adj_right_same_direction is not None else False)

        self.road_network_toolbox_ui.selected_lanelet_type.set_checked_items(
                [str(la_type.value) for la_type in lanelet.lanelet_type])

        self.road_network_toolbox_ui.selected_road_user_oneway.set_checked_items(
                [str(user.value) for user in lanelet.user_one_way])

        self.road_network_toolbox_ui.selected_road_user_bidirectional.set_checked_items(
                [str(user.value) for user in lanelet.user_bidirectional])

        self.road_network_toolbox_ui.selected_lanelet_referenced_traffic_sign_ids.set_checked_items(
                [str(sign) for sign in lanelet.traffic_signs])
        self.road_network_toolbox_ui.selected_lanelet_referenced_traffic_light_ids.set_checked_items(
                [str(light) for light in lanelet.traffic_lights])

        if lanelet.stop_line is not None:
            self.road_network_toolbox_ui.selected_stop_line_box.setChecked(True)
            if all(lanelet.stop_line.start == lanelet.left_vertices[0]) and all(
                    lanelet.stop_line.end == lanelet.right_vertices[0]):
                self.road_network_toolbox_ui.selected_stop_line_beginning.setChecked(True)
                self.road_network_toolbox_ui.adjust_selected_stop_line_position()
            elif all(lanelet.stop_line.start == lanelet.left_vertices[len(lanelet.left_vertices) - 1]) and all(
                    lanelet.stop_line.end == lanelet.right_vertices[len(lanelet.right_vertices) - 1]):
                self.road_network_toolbox_ui.selected_stop_line_end.setChecked(True)
                self.road_network_toolbox_ui.adjust_selected_stop_line_position()
            else:
                self.road_network_toolbox_ui.selected_stop_line_select_position.setChecked(True)
                self.road_network_toolbox_ui.adjust_selected_stop_line_position()
                self.road_network_toolbox_ui.selected_stop_line_start_x.setText(str(lanelet.stop_line.start[0]))
                self.road_network_toolbox_ui.selected_stop_line_start_y.setText(str(lanelet.stop_line.start[1]))
                self.road_network_toolbox_ui.selected_stop_line_end_x.setText(str(lanelet.stop_line.end[0]))
                self.road_network_toolbox_ui.selected_stop_line_end_y.setText(str(lanelet.stop_line.end[1]))
            self.road_network_toolbox_ui.selected_line_marking_stop_line.setCurrentText(
                    str(lanelet.stop_line.line_marking.value))
        else:
            self.road_network_toolbox_ui.selected_stop_line_box.setChecked(True)
            self.road_network_toolbox_ui.selected_stop_line_beginning.setChecked(True)
            self.road_network_toolbox_ui.adjust_selected_stop_line_position()
            self.road_network_toolbox_ui.selected_stop_line_box.setChecked(False)

    def create_adjacent(self):
        """
        Create adjacent lanelet given a selected lanelet
        """
        selected_lanelet = self.selected_lanelet()
        if selected_lanelet is None:
            return
        if selected_lanelet.predecessor:
            self.text_browser.append(selected_lanelet.predecessor.pop())
        if selected_lanelet.successor:
            self.text_browser.append(selected_lanelet.successor.pop())
        if selected_lanelet is None:
            return

        adjacent_left = self.road_network_toolbox_ui.create_adjacent_left_selection.isChecked()
        adjacent_same_direction = self.road_network_toolbox_ui.create_adjacent_same_direction_selection.isChecked()

        lanelet_width = float(self.get_width(selected_lanelet))
        line_marking_left = selected_lanelet.line_marking_left_vertices
        line_marking_right = selected_lanelet.line_marking_right_vertices
        predecessors = selected_lanelet.predecessor
        successors = selected_lanelet.successor
        lanelet_type = selected_lanelet.lanelet_type
        user_one_way = selected_lanelet.user_one_way
        user_bidirectional = selected_lanelet.user_bidirectional
        traffic_signs = selected_lanelet.traffic_signs
        traffic_lights = selected_lanelet.traffic_lights
        stop_line_at_end = False
        stop_line = None
        if selected_lanelet.stop_line is not None:
            stop_line_marking = selected_lanelet.stop_line.line_marking
            if all(selected_lanelet.stop_line.start == selected_lanelet.left_vertices[0]) and all(
                    selected_lanelet.stop_line.end == selected_lanelet.right_vertices[0]):
                # stop line at beginning
                stop_line_at_end = False
                stop_line_at_beginning = True
                stop_line = StopLine(np.array([0, 0]), np.array([0, 0]), stop_line_marking, set(), set())
            elif all(selected_lanelet.stop_line.start == selected_lanelet.left_vertices[
                len(selected_lanelet.left_vertices) - 1]) and all(
                    selected_lanelet.stop_line.end == selected_lanelet.right_vertices[
                        len(selected_lanelet.right_vertices) - 1]):
                stop_line_at_end = True
                stop_line_at_beginning = False
                stop_line = StopLine(np.array([0, 0]), np.array([0, 0]), stop_line_marking, set(), set())
            else:
                stop_line_start_x = selected_lanelet.stop_line.start[0]
                stop_line_end_x = selected_lanelet.stop_line.end[0]
                stop_line_start_y = selected_lanelet.stop_line.start[1]
                stop_line_end_y = selected_lanelet.stop_line.end[1]
                stop_line = StopLine(np.array([stop_line_start_x, stop_line_start_y]),
                                     np.array([stop_line_end_x, stop_line_end_y]), stop_line_marking, set(), set())

        if adjacent_left:
            adjacent_lanelet = MapCreator.create_adjacent_lanelet(adjacent_left, selected_lanelet,
                                                                  self.current_scenario.generate_object_id(),
                                                                  adjacent_same_direction, lanelet_width, lanelet_type,
                                                                  predecessors, successors, user_one_way,
                                                                  user_bidirectional, line_marking_left,
                                                                  line_marking_right, stop_line, traffic_signs,
                                                                  traffic_lights, stop_line_at_end)
        else:
            adjacent_lanelet = MapCreator.create_adjacent_lanelet(adjacent_left, selected_lanelet,
                                                                  self.current_scenario.generate_object_id(),
                                                                  adjacent_same_direction, lanelet_width, lanelet_type,
                                                                  predecessors, successors, user_one_way,
                                                                  user_bidirectional, line_marking_left,
                                                                  line_marking_right, stop_line, traffic_signs,
                                                                  traffic_lights, stop_line_at_end)

        if adjacent_lanelet is not None:
            self.last_added_lanelet_id = adjacent_lanelet.lanelet_id
            self.current_scenario.add_objects(adjacent_lanelet)
            self.set_default_road_network_list_information()
            self.callback(self.current_scenario)
        else:
            self.text_browser.append("Adjacent lanelet already exists.")

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

        width = self.get_float(self.road_network_toolbox_ui.intersection_lanelet_width)
        diameter = int(self.road_network_toolbox_ui.intersection_diameter.text())
        incoming_length = int(self.road_network_toolbox_ui.intersection_incoming_length.text())
        add_traffic_signs = self.road_network_toolbox_ui.intersection_with_traffic_signs.isChecked()
        add_traffic_lights = self.road_network_toolbox_ui.intersection_with_traffic_lights.isChecked()
        country_signs = globals()["TrafficSignID" + SupportedTrafficSignCountry(
                self.current_scenario.scenario_id.country_id).name.capitalize()]

        intersection, new_traffic_signs, new_traffic_lights, new_lanelets = MapCreator.create_four_way_intersection(
                width, diameter, incoming_length, self.current_scenario, add_traffic_signs, add_traffic_lights,
                country_signs)
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
        width = self.get_float(self.road_network_toolbox_ui.intersection_lanelet_width)
        diameter = int(self.road_network_toolbox_ui.intersection_diameter.text())
        incoming_length = int(self.road_network_toolbox_ui.intersection_incoming_length.text())
        add_traffic_signs = self.road_network_toolbox_ui.intersection_with_traffic_signs.isChecked()
        add_traffic_lights = self.road_network_toolbox_ui.intersection_with_traffic_lights.isChecked()
        country_signs = globals()["TrafficSignID" + SupportedTrafficSignCountry(
                self.current_scenario.scenario_id.country_id).name.capitalize()]

        intersection, new_traffic_signs, new_traffic_lights, new_lanelets = MapCreator.create_three_way_intersection(
                width, diameter, incoming_length, self.current_scenario, add_traffic_signs, add_traffic_lights,
                country_signs)

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
                int(self.road_network_toolbox_ui.selected_intersection.currentText()))
        for inc in selected_intersection.incomings:
            self.road_network_toolbox_ui.intersection_incomings_table.setItem(0, 0, inc.incoming_id)

    def add_traffic_sign_element(self):
        """
        Adds traffic sign element to traffic sign.
        Only a default entry is created the user has to specify the traffic sign ID manually afterward.
        """
        if self.current_scenario is None:
            self.text_browser.append("_Warning:_ Create a new file")
            return
        num_rows = self.road_network_toolbox_ui.traffic_sign_element_table.rowCount()
        self.road_network_toolbox_ui.traffic_sign_element_table.insertRow(num_rows)
        combo_box = QComboBox()
        combo_box.addItems([elem.name for elem in globals()["TrafficSignID" + SupportedTrafficSignCountry(
                self.current_scenario.scenario_id.country_id).name.capitalize()]])
        self.road_network_toolbox_ui.traffic_sign_element_table.setCellWidget(num_rows, 0, combo_box)

    def remove_traffic_sign_element(self):
        """
        Removes last entry in traffic sign element table of a traffic sign.
        """
        num_rows = self.road_network_toolbox_ui.traffic_sign_element_table.rowCount()
        self.road_network_toolbox_ui.traffic_sign_element_table.removeRow(num_rows - 1)

    def add_traffic_sign(self, traffic_sign_id: int = None):
        """
        Adds a traffic sign to a CommonRoad scenario.

        @param traffic_sign_id: Id which the new traffic sign should have.
        """
        if self.current_scenario is None:
            self.text_browser.append("_Warning:_ Create a new file")
            return  # Check if list is empty -> Warning
        if len(self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.get_checked_items()) == 0:
            self.text_browser.append("_Warning:_ Add Referenced Lanelets")
            return
        # Check if only 'None' is selected - if yes -> Warning
        if 'None' in self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.get_checked_items() and len(
                self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.get_checked_items()) == 1:
            self.text_browser.append("_Warning:_ Add Referenced Lanelets")
            return
        # Check if 'None' is and other items are selected -> Uncheck 'None'
        elif 'None' in self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.get_checked_items():
            self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.uncheck_items('None')
        country_signs = globals()["TrafficSignID" + SupportedTrafficSignCountry(
                self.current_scenario.scenario_id.country_id).name.capitalize()]
        traffic_sign_elements = []
        referenced_lanelets = {int(la) for la in
                               self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.get_checked_items()}
        first_occurrence = set()  # TODO compute first occurrence
        virtual = self.road_network_toolbox_ui.traffic_sign_virtual_selection.isChecked()
        if self.road_network_toolbox_ui.x_position_traffic_sign.text():
            x_position = self.get_float(self.road_network_toolbox_ui.x_position_traffic_sign)
        else:
            x_position = 0
        if self.road_network_toolbox_ui.y_position_traffic_sign.text():
            y_position = self.get_float(self.road_network_toolbox_ui.y_position_traffic_sign)
        else:
            y_position = 0
        for row in range(self.road_network_toolbox_ui.traffic_sign_element_table.rowCount()):
            sign_id = self.road_network_toolbox_ui.traffic_sign_element_table.cellWidget(row, 0).currentText()
            if self.road_network_toolbox_ui.traffic_sign_element_table.item(row, 1) is None:
                additional_value = []
            else:
                additional_value = [self.road_network_toolbox_ui.traffic_sign_element_table.item(row, 1).text()]
            traffic_sign_elements.append(TrafficSignElement(country_signs[sign_id], additional_value))

        if len(traffic_sign_elements) == 0:
            self.text_browser.append("_Warning:_ No traffic sign element added.")
            return
        traffic_sign_id = traffic_sign_id if traffic_sign_id is not None else self.current_scenario.generate_object_id()
        new_sign = TrafficSign(traffic_sign_id, traffic_sign_elements, first_occurrence,
                               np.array([x_position, y_position]), virtual)

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
        if self.road_network_toolbox_ui.selected_traffic_sign.currentText() not in ["", "None"]:
            selected_traffic_sign_id = int(self.road_network_toolbox_ui.selected_traffic_sign.currentText())
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
        if len(self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.get_checked_items()) == 0:
            self.text_browser.append("_Warning:_ Add Referenced Lanelets")
            return
        # Check if only 'None' is selected - if yes -> Warning
        if 'None' in self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.get_checked_items() and len(
                self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.get_checked_items()) == 1:
            self.text_browser.append("_Warning:_ Add Referenced Lanelets")
            return
        # Check if 'None' is and other items are selected -> Uncheck 'None'
        elif 'None' in self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.get_checked_items():
            self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.uncheck_items('None')
        if self.road_network_toolbox_ui.selected_traffic_sign.currentText() not in ["", "None"]:
            selected_traffic_sign_id = int(self.road_network_toolbox_ui.selected_traffic_sign.currentText())
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
        if self.road_network_toolbox_ui.selected_traffic_sign.currentText() not in ["", "None"]:
            country_signs = globals()["TrafficSignID" + SupportedTrafficSignCountry(
                    self.current_scenario.scenario_id.country_id).name.capitalize()]
            selected_traffic_sign_id = int(self.road_network_toolbox_ui.selected_traffic_sign.currentText())
            traffic_sign = self.current_scenario.lanelet_network.find_traffic_sign_by_id(selected_traffic_sign_id)
            referenced_lanelets = [str(la.lanelet_id) for la in self.current_scenario.lanelet_network.lanelets if
                                   selected_traffic_sign_id in la.traffic_signs]
            self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.set_checked_items(referenced_lanelets)

            self.road_network_toolbox_ui.traffic_sign_virtual_selection.setChecked(traffic_sign.virtual)
            self.road_network_toolbox_ui.x_position_traffic_sign.setText(str(traffic_sign.position[0]))
            self.road_network_toolbox_ui.y_position_traffic_sign.setText(str(traffic_sign.position[1]))
            self.road_network_toolbox_ui.traffic_sign_element_table.setRowCount(0)
            for elem in traffic_sign.traffic_sign_elements:
                self.add_traffic_sign_element()
                num_rows = self.road_network_toolbox_ui.traffic_sign_element_table.rowCount()
                self.road_network_toolbox_ui.traffic_sign_element_table.cellWidget(num_rows - 1, 0).setCurrentText(
                        country_signs(elem.traffic_sign_element_id).name)
                if len(elem.additional_values) > 0:
                    self.road_network_toolbox_ui.traffic_sign_element_table.setItem(num_rows - 1, 1,
                            QTableWidgetItem(str(elem.additional_values[0])))
                else:
                    self.road_network_toolbox_ui.traffic_sign_element_table.setItem(num_rows - 1, 1,
                            QTableWidgetItem(""))
        else:
            self.road_network_toolbox_ui.traffic_sign_virtual_selection.setChecked(False)
            self.road_network_toolbox_ui.x_position_traffic_sign.setText("0.0")
            self.road_network_toolbox_ui.y_position_traffic_sign.setText("0.0")
            self.road_network_toolbox_ui.traffic_sign_element_table.setRowCount(0)

    def add_traffic_light(self, traffic_light_id: int = None):
        """
        Adds a new traffic light to the scenario based on the user selection.

        @param traffic_light_id: Id which the new traffic sign should have.
        """
        if self.current_scenario is None:
            self.text_browser.append("_Warning:_ Create a new file")
            return
        if len(self.road_network_toolbox_ui.referenced_lanelets_traffic_light.get_checked_items()) == 0:
            self.text_browser.append("_Warning:_ Add Referenced Lanelets")
            return
        # Check if only 'None' is selected - if yes -> Warning
        if 'None' in self.road_network_toolbox_ui.referenced_lanelets_traffic_light.get_checked_items() and len(
                self.road_network_toolbox_ui.referenced_lanelets_traffic_light.get_checked_items()) == 1:
            self.text_browser.append("_Warning:_ Add Referenced Lanelets")
            return
        # Check if 'None' is and other items are selected -> Uncheck 'None'
        elif 'None' in self.road_network_toolbox_ui.referenced_lanelets_traffic_light.get_checked_items():
            self.road_network_toolbox_ui.referenced_lanelets_traffic_light.uncheck_items('None')
        referenced_lanelets = {int(la) for la in
                               self.road_network_toolbox_ui.referenced_lanelets_traffic_light.get_checked_items()}
        if self.road_network_toolbox_ui.x_position_traffic_light.text():
            x_position = self.get_float(self.road_network_toolbox_ui.x_position_traffic_light)
        else:
            x_position = 0
        if self.road_network_toolbox_ui.y_position_traffic_light.text():
            y_position = self.get_float(self.road_network_toolbox_ui.y_position_traffic_light)
        else:
            y_position = 0

        traffic_light_direction = TrafficLightDirection(
            self.road_network_toolbox_ui.traffic_light_directions.currentText())
        time_offset = int(self.road_network_toolbox_ui.time_offset.text())
        time_red = int(self.road_network_toolbox_ui.time_red.text())
        time_green = int(self.road_network_toolbox_ui.time_green.text())
        time_yellow = int(self.road_network_toolbox_ui.time_yellow.text())
        time_red_yellow = int(self.road_network_toolbox_ui.time_red_yellow.text())
        time_inactive = int(self.road_network_toolbox_ui.time_inactive.text())
        traffic_light_active = self.road_network_toolbox_ui.traffic_light_active.isChecked()
        traffic_light_cycle_order = self.road_network_toolbox_ui.traffic_light_cycle_order.currentText().split("-")

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

        new_traffic_light = TrafficLight(traffic_light_id, np.array([x_position, y_position]),
                                         TrafficLightCycle(traffic_light_cycle, time_offset=time_offset,
                                                           active=traffic_light_active),
                                         direction=traffic_light_direction, active=traffic_light_active)


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
        if self.road_network_toolbox_ui.selected_traffic_light.currentText() not in ["", "None"]:
            selected_traffic_light_id = int(self.road_network_toolbox_ui.selected_traffic_light.currentText())
        else:
            return
        traffic_light = self.current_scenario.lanelet_network.find_traffic_light_by_id(selected_traffic_light_id)
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
        if len(self.road_network_toolbox_ui.referenced_lanelets_traffic_light.get_checked_items()) == 0:
            self.text_browser.append("_Warning:_ Add Referenced Lanelets")
            return
        # Check if only 'None' is selected - if yes -> Warning
        if 'None' in self.road_network_toolbox_ui.referenced_lanelets_traffic_light.get_checked_items() and len(
                self.road_network_toolbox_ui.referenced_lanelets_traffic_light.get_checked_items()) == 1:
            self.text_browser.append("_Warning:_ Add Referenced Lanelets")
            return  # Check if 'None' is and other items are selected -> Uncheck 'None'
        elif 'None' in self.road_network_toolbox_ui.referenced_lanelets_traffic_light.get_checked_items():
            self.road_network_toolbox_ui.referenced_lanelets_traffic_light.uncheck_items('None')
        if self.road_network_toolbox_ui.selected_traffic_light.currentText() not in ["", "None"]:
            selected_traffic_light_id = int(self.road_network_toolbox_ui.selected_traffic_light.currentText())
        else:
            return
        traffic_light = self.current_scenario.lanelet_network.find_traffic_light_by_id(selected_traffic_light_id)
        self.current_scenario.remove_traffic_light(traffic_light)
        self.add_traffic_light(selected_traffic_light_id)
        self.set_default_road_network_list_information()
        self.callback(self.current_scenario)

    def update_traffic_light_information(self):
        """
        Updates information of traffic light widget based on traffic light ID selected by the user.
        """
        if self.road_network_toolbox_ui.selected_traffic_light.currentText() not in ["", "None"]:
            selected_traffic_light_id = int(self.road_network_toolbox_ui.selected_traffic_light.currentText())
            traffic_light = self.current_scenario.lanelet_network.find_traffic_light_by_id(selected_traffic_light_id)

            self.road_network_toolbox_ui.x_position_traffic_light.setText(str(traffic_light.position[0]))
            self.road_network_toolbox_ui.y_position_traffic_light.setText(str(traffic_light.position[1]))
            self.road_network_toolbox_ui.time_offset.setText(str(traffic_light.time_offset))
            self.road_network_toolbox_ui.traffic_light_active.setChecked(True)

            cycle_order = ""
            for elem in traffic_light.cycle:
                if elem.state is TrafficLightState.RED:
                    cycle_order += "r-"
                    self.road_network_toolbox_ui.time_red.setText(str(elem.duration))
                if elem.state is TrafficLightState.GREEN:
                    cycle_order += "g-"
                    self.road_network_toolbox_ui.time_green.setText(str(elem.duration))
                if elem.state is TrafficLightState.YELLOW:
                    cycle_order += "y-"
                    self.road_network_toolbox_ui.time_yellow.setText(str(elem.duration))
                if elem.state is TrafficLightState.RED_YELLOW:
                    cycle_order += "ry-"
                    self.road_network_toolbox_ui.time_red_yellow.setText(str(elem.duration))
                if elem.state is TrafficLightState.INACTIVE:
                    cycle_order += "in-"
                    self.road_network_toolbox_ui.time_inactive.setText(str(elem.duration))
            cycle_order = cycle_order[:-1]
            self.road_network_toolbox_ui.traffic_light_cycle_order.setCurrentText(cycle_order)

            self.road_network_toolbox_ui.traffic_light_directions.setCurrentText(str(traffic_light.direction.value))

            referenced_lanelets = [str(la.lanelet_id) for la in self.current_scenario.lanelet_network.lanelets if
                                   selected_traffic_light_id in la.traffic_lights]
            self.road_network_toolbox_ui.referenced_lanelets_traffic_light.set_checked_items(referenced_lanelets)

    def create_traffic_lights(self):
        if not SUMO_AVAILABLE:
            self.text_browser.append("SUMO is not installed correctly!")
            return
        lanelet_ids = [int(lanelet_id) for lanelet_id in
                       self.road_network_toolbox_ui.referenced_lanelets_traffic_light.get_checked_items()]
        if not lanelet_ids:
            return
        self.road_network_toolbox_ui.referenced_lanelets_traffic_light.clear()
        converter = CR2SumoMapConverter(self.current_scenario, SumoConfig.from_scenario(self.current_scenario))
        converter.create_sumo_files(self.tmp_folder)
        oks = []
        dt = self.current_scenario.dt
        offset = int(self.road_network_toolbox_ui.time_offset.text())
        red = int(self.road_network_toolbox_ui.time_red.text())
        red_yellow = int(self.road_network_toolbox_ui.time_red_yellow.text())
        green = int(self.road_network_toolbox_ui.time_green.text())
        yellow = int(self.road_network_toolbox_ui.time_yellow.text())
        total = red + red_yellow + green + yellow

        for lanelet_id in lanelet_ids:
            try:
                ok = converter.auto_generate_traffic_light_system(lanelet_id, green_time=int(green * dt),
                                                                  yellow_time=int(yellow * dt), all_red_time=0,
                                                                  left_green_time=math.ceil(0.06 * total * dt),
                                                                  crossing_min_time=math.ceil(0.1 * total * dt),
                                                                  crossing_clearance_time=math.ceil(0.15 * total * dt),
                                                                  time_offset=int(offset * dt))
            except Exception:
                ok = False
            oks.append(ok)
            self.text_browser.append((
                                         "Created" if ok else "ERROR: Could not create") + f" traffic light system "
                                                                                           f"for lanelet {lanelet_id}")

        if any(oks):
            # update lanelet_network and boradcast change
            self.current_scenario.replace_lanelet_network(converter.lanelet_network)
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

        num_rows = self.road_network_toolbox_ui.intersection_incomings_table.rowCount()
        self.road_network_toolbox_ui.intersection_incomings_table.insertRow(num_rows)
        lanelet_ids = [str(la_id) for la_id in self.collect_lanelet_ids()]
        if new_incoming:
            self.road_network_toolbox_ui.intersection_incomings_table.setItem(num_rows, 0,
                    QTableWidgetItem(str(self.current_scenario.generate_object_id())))
        combo_box_lanelets = CheckableComboBox()
        combo_box_lanelets.addItems(lanelet_ids)
        self.road_network_toolbox_ui.intersection_incomings_table.setCellWidget(num_rows, 1, combo_box_lanelets)
        combo_box_successors_left = CheckableComboBox()
        combo_box_successors_left.addItems(lanelet_ids)
        self.road_network_toolbox_ui.intersection_incomings_table.setCellWidget(num_rows, 2, combo_box_successors_left)
        combo_box_successors_straight = CheckableComboBox()
        combo_box_successors_straight.addItems(lanelet_ids)
        self.road_network_toolbox_ui.intersection_incomings_table.setCellWidget(num_rows, 3,
                                                                                combo_box_successors_straight)
        combo_box_successors_right = CheckableComboBox()
        combo_box_successors_right.addItems(lanelet_ids)
        self.road_network_toolbox_ui.intersection_incomings_table.setCellWidget(num_rows, 4, combo_box_successors_right)
        self.update_left_of_combobox(incoming_ids)

    def update_left_of_combobox(self, incoming_ids: List[str] = None):
        """
        Collects all incoming IDs in incoming table and updates left of combobox

        @param incoming_ids: List of available incoming IDs.
        """
        if incoming_ids is None:
            incoming_ids = [self.road_network_toolbox_ui.intersection_incomings_table.item(row, 0).text() for row in
                            range(self.road_network_toolbox_ui.intersection_incomings_table.rowCount())]
        for row in range(self.road_network_toolbox_ui.intersection_incomings_table.rowCount()):
            combo_box_left_of = QComboBox()
            combo_box_left_of.addItems(incoming_ids)
            if row != self.road_network_toolbox_ui.intersection_incomings_table.rowCount() - 1:
                index = self.road_network_toolbox_ui.intersection_incomings_table.cellWidget(row, 5).findText(
                        self.road_network_toolbox_ui.intersection_incomings_table.cellWidget(row, 5).currentText(),
                        Qt.MatchFixedString)
            else:
                index = -1
            self.road_network_toolbox_ui.intersection_incomings_table.setCellWidget(row, 5, combo_box_left_of)
            if index >= 0:
                self.road_network_toolbox_ui.intersection_incomings_table.cellWidget(row, 5).setCurrentIndex(index)

    def remove_intersection(self):
        """
        Removes selected intersection from lanelet network.
        """
        if self.current_scenario is None:
            self.text_browser.append("_Warning:_ Create a new file")
            return

        if self.road_network_toolbox_ui.selected_intersection.currentText() not in ["", "None"]:
            selected_intersection_id = int(self.road_network_toolbox_ui.selected_intersection.currentText())
            intersection = self.current_scenario.lanelet_network.find_intersection_by_id(selected_intersection_id)
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

        if self.road_network_toolbox_ui.selected_intersection.currentText() not in ["", "None"]:
            selected_intersection_id = int(self.road_network_toolbox_ui.selected_intersection.currentText())
            intersection = self.current_scenario.lanelet_network.find_intersection_by_id(selected_intersection_id)
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
        for row in range(self.road_network_toolbox_ui.intersection_incomings_table.rowCount()):
            incoming_id = int(self.road_network_toolbox_ui.intersection_incomings_table.item(row, 0).text())
            incoming_lanelets = {int(item) for item in
                                 self.road_network_toolbox_ui.intersection_incomings_table.cellWidget(row,
                                                                                                      1).get_checked_items()}
            if len(incoming_lanelets) < 1:
                self.text_browser.append("_Warning:_ An incoming must consist at least of one lanelet.")
                print("road_network_toolbox.py/add_intersection: An incoming must consist at least of one lanelet.")
                return
            successor_left = {int(item) for item in
                              self.road_network_toolbox_ui.intersection_incomings_table.cellWidget(row,
                                      2).get_checked_items()}
            successor_straight = {int(item) for item in
                                  self.road_network_toolbox_ui.intersection_incomings_table.cellWidget(row,
                                          3).get_checked_items()}
            successor_right = {int(item) for item in
                               self.road_network_toolbox_ui.intersection_incomings_table.cellWidget(row,
                                       4).get_checked_items()}
            if len(successor_left) + len(successor_right) + len(successor_straight) < 1:
                print("An incoming must consist at least of one successor")
                return
            left_of = int(self.road_network_toolbox_ui.intersection_incomings_table.cellWidget(row,
                                                                                               5).currentText()) if \
                                                                                               self.road_network_toolbox_ui.intersection_incomings_table.cellWidget(
                row, 5).currentText() != "" else None
            incoming = IntersectionIncomingElement(incoming_id, incoming_lanelets, successor_right, successor_straight,
                                                   successor_left, left_of)
            incomings.append(incoming)
        crossings = {int(item) for item in self.road_network_toolbox_ui.intersection_crossings.get_checked_items()}

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
        num_rows = self.road_network_toolbox_ui.intersection_incomings_table.rowCount()
        self.road_network_toolbox_ui.intersection_incomings_table.removeRow(num_rows - 1)
        self.update_left_of_combobox()

    def update_intersection_information(self):
        """
        Updates information of intersection widget based on intersection ID selected by the user.
        """
        if self.road_network_toolbox_ui.selected_intersection.currentText() not in ["", "None"]:
            selected_intersection_id = int(self.road_network_toolbox_ui.selected_intersection.currentText())
            intersection = self.current_scenario.lanelet_network.find_intersection_by_id(selected_intersection_id)
            self.road_network_toolbox_ui.intersection_incomings_table.setRowCount(0)
            incoming_ids = [str(inc.incoming_id) for inc in intersection.incomings]
            for incoming in intersection.incomings:
                self.add_incoming_to_table(False, incoming_ids)
                num_rows = self.road_network_toolbox_ui.intersection_incomings_table.rowCount()
                self.road_network_toolbox_ui.intersection_incomings_table.setItem(num_rows - 1, 0,
                        QTableWidgetItem(str(incoming.incoming_id)))
                self.road_network_toolbox_ui.intersection_incomings_table.cellWidget(num_rows - 1, 1).set_checked_items(
                        [str(la_id) for la_id in incoming.incoming_lanelets])
                self.road_network_toolbox_ui.intersection_incomings_table.cellWidget(num_rows - 1, 2).set_checked_items(
                        [str(la_id) for la_id in incoming.successors_left])
                self.road_network_toolbox_ui.intersection_incomings_table.cellWidget(num_rows - 1, 3).set_checked_items(
                        [str(la_id) for la_id in incoming.successors_straight])
                self.road_network_toolbox_ui.intersection_incomings_table.cellWidget(num_rows - 1, 4).set_checked_items(
                        [str(la_id) for la_id in incoming.successors_right])
                index = self.road_network_toolbox_ui.intersection_incomings_table.cellWidget(num_rows - 1, 5).findText(
                    str(incoming.left_of))
                self.road_network_toolbox_ui.intersection_incomings_table.cellWidget(num_rows - 1, 5).setCurrentIndex(
                    index)
            self.road_network_toolbox_ui.intersection_crossings.set_checked_items(
                    [str(cr) for cr in intersection.crossings])

            self.road_network_toolbox_ui.intersection_lanelet_to_fit.clear()
            self.road_network_toolbox_ui.intersection_lanelet_to_fit.addItems(
                    ["None"] + [str(item) for item in self.collect_incoming_lanelet_ids_from_intersection()])
            self.road_network_toolbox_ui.intersection_lanelet_to_fit.setCurrentIndex(0)

    def connect_lanelets(self):
        """
        Connects two lanelets by adding a new lanelet using cubic spline interpolation.
        """
        selected_lanelet_one = self.selected_lanelet()
        if selected_lanelet_one is None:
            return
        if self.road_network_toolbox_ui.selected_lanelet_two.currentText() != "None":
            selected_lanelet_two = self.current_scenario.lanelet_network.find_lanelet_by_id(
                    int(self.road_network_toolbox_ui.selected_lanelet_two.currentText()))
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
        if self.road_network_toolbox_ui.selected_lanelet_two.currentText() != "None":
            selected_lanelet_two = self.current_scenario.lanelet_network.find_lanelet_by_id(
                    int(self.road_network_toolbox_ui.selected_lanelet_two.currentText()))
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
        rotation_angle = int(self.road_network_toolbox_ui.rotation_angle.text())
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
        x_translation = self.get_float(self.road_network_toolbox_ui.x_translation)
        y_translation = self.get_float(self.road_network_toolbox_ui.y_translation)
        selected_lanelet_one.translate_rotate(np.array([x_translation, y_translation]), 0)

        self.current_scenario.remove_lanelet(selected_lanelet_one)
        self.current_scenario.add_objects(selected_lanelet_one)
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
        if self.road_network_toolbox_ui.selected_intersection.currentText() not in ["",
                                                                                    "None"] and \
                                                                                    self.road_network_toolbox_ui.other_lanelet_to_fit.currentText() not in [
            "", "None"] and self.road_network_toolbox_ui.intersection_lanelet_to_fit.currentText() not in ["", "None"]:
            selected_intersection_id = int(self.road_network_toolbox_ui.selected_intersection.currentText())
            intersection = self.current_scenario.lanelet_network.find_intersection_by_id(selected_intersection_id)

            predecessor_id = int(self.road_network_toolbox_ui.other_lanelet_to_fit.currentText())
            lanelet_predecessor = self.current_scenario.lanelet_network.find_lanelet_by_id(predecessor_id)

            successor_id = int(self.road_network_toolbox_ui.intersection_lanelet_to_fit.currentText())
            lanelet_successor = self.current_scenario.lanelet_network.find_lanelet_by_id(successor_id)

            MapCreator.fit_intersection_to_predecessor(lanelet_predecessor, lanelet_successor, intersection,
                                                       self.current_scenario.lanelet_network)
            self.callback(self.current_scenario)

    def show_aerial_image(self):
        if self.current_scenario is None:
            self.text_browser.append("Please create first a new scenario.")
            return
        if float(self.road_network_toolbox_ui.northern_bound.text()) > 90 or float(
                self.road_network_toolbox_ui.northern_bound.text()) < -90:
            self.text_browser.append("Invalid northern bound. Latitude has to be between -90 and 90.")
            return
        if float(self.road_network_toolbox_ui.southern_bound.text()) > 90 or float(
                self.road_network_toolbox_ui.southern_bound.text()) < -90:
            self.text_browser.append("Invalid southern bound. Latitude has to be between -90 and 90.")
            return
        if float(self.road_network_toolbox_ui.western_bound.text()) > 180 or float(
                self.road_network_toolbox_ui.western_bound.text()) < -180:
            self.text_browser.append("Invalid western bound. Longitude has to be between -180 and 180.")
            return
        if float(self.road_network_toolbox_ui.eastern_bound.text()) > 180 or float(
                self.road_network_toolbox_ui.eastern_bound.text()) < -180:
            self.text_browser.append("Invalid eastern bound. Longitude has to be between -180 and 180.")
            return
        if float(self.road_network_toolbox_ui.southern_bound.text()) >= float(
                self.road_network_toolbox_ui.northern_bound.text()) or float(
                self.road_network_toolbox_ui.western_bound.text()) >= float(
                self.road_network_toolbox_ui.eastern_bound.text()):
            self.text_browser.append("Invalid coordinate limits.")
            return

        if self.road_network_toolbox_ui.bing_selection.isChecked():
            if config_settings.BING_MAPS_KEY == "":
                print("_Warning__: No Bing Maps key specified. Go to settings and set password.")
                warning_dialog = QMessageBox()
                warning_dialog.warning(None, "Warning", "No Bing Maps key specified. Go to settings and set password.",
                                       QMessageBox.Ok, QMessageBox.Ok)
                warning_dialog.close()
                return
        elif self.road_network_toolbox_ui.ldbv_selection.isChecked():
            if config_settings.LDBV_USERNAME == "" or config_settings.LDBV_PASSWORD == "":
                print("_Warning__: LDBV username and password not specified. Go to settings and set them.")
                warning_dialog = QMessageBox()
                warning_dialog.warning(None, "Warning",
                                       "LDBV username and password not specified. Go to settings and set them.",
                                       QMessageBox.Ok, QMessageBox.Ok)
                warning_dialog.close()
                return
            if float(self.road_network_toolbox_ui.southern_bound.text()) > 50.6 or float(
                    self.road_network_toolbox_ui.southern_bound.text()) < 47.2 or float(
                    self.road_network_toolbox_ui.northern_bound.text()) > 50.6 or float(
                    self.road_network_toolbox_ui.northern_bound.text()) < 47.2 or float(
                    self.road_network_toolbox_ui.western_bound.text()) > 13.9 or float(
                    self.road_network_toolbox_ui.western_bound.text()) < 8.9 or float(
                    self.road_network_toolbox_ui.eastern_bound.text()) > 13.9 or float(
                    self.road_network_toolbox_ui.eastern_bound.text()) < 8.9:
                self.text_browser.append(
                    "Coordinates are outside Bavaria. This tool works only for coordinates inside Bavaria.")
                return

        self.startSpinner(self.road_network_toolbox_ui.Spinner)
        runnable = RequestRunnable(self.activate_aerial_image, self)
        QThreadPool.globalInstance().start(runnable)

    def activate_aerial_image(self):
        self.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.activate_aerial_image(
            self.road_network_toolbox_ui.bing_selection.isChecked(),
            float(self.road_network_toolbox_ui.northern_bound.text()),
            float(self.road_network_toolbox_ui.western_bound.text()),
            float(self.road_network_toolbox_ui.southern_bound.text()),
            float(self.road_network_toolbox_ui.eastern_bound.text()))
        self.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.show_aerial_image()

    def remove_aerial_image(self):
        self.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.deactivate_aerial_image()
        self.callback(self.current_scenario)

    @pyqtSlot(str)
    def stopSpinner(self, data):
        print(data)
        self.callback(self.current_scenario)
        self.road_network_toolbox_ui.Spinner.stop()

    def startSpinner(self, spinner: QtWaitingSpinner):
        if (spinner.isSpinning()):
            spinner.stop()
        spinner.start()
