import math

import numpy as np
from commonroad.geometry.polyline_util import compute_polyline_curvatures
from commonroad.scenario.lanelet import Lanelet, LaneletType, LineMarking, RoadUser
from numpy import ndarray
from PyQt6.QtCore import Qt

from crdesigner.common.logging import logger
from crdesigner.ui.gui.model.scenario_model import ScenarioModel
from crdesigner.ui.gui.utilities.helper import angle_between
from crdesigner.ui.gui.view.toolboxes.road_network_toolbox.road_network_toolbox_ui.road_network_toolbox_ui import (
    RoadNetworkToolboxUI,
)


class AddLaneletUI:
    def __init__(
        self, scenario_model: ScenarioModel, road_network_toolbox_ui: RoadNetworkToolboxUI
    ):
        self.road_network_toolbox_ui = road_network_toolbox_ui
        self.scenario_model = scenario_model

    # TODO check for deletion
    # def lanelet_selection_changed(self):
    #     return
    @logger.log
    def initialize_basic_lanelet_information(self, last_added_lanelet_id):
        """
        Initializes lanelet GUI elements with lanelet information.
        """

        if (
            not self.road_network_toolbox_ui.place_at_position.isChecked()
            and not self.road_network_toolbox_ui.connect_to_previous_selection.isChecked()
            and not self.road_network_toolbox_ui.connect_to_predecessors_selection.isChecked()
            and not self.road_network_toolbox_ui.connect_to_successors_selection.isChecked()
        ):
            self.road_network_toolbox_ui.adding_method = ""
            return

        if self.road_network_toolbox_ui.connect_to_predecessors_selection.isChecked():
            self.road_network_toolbox_ui.predecessors.view().pressed.connect(
                self.initialize_predecessor_and_successor_fields
            )
        elif self.road_network_toolbox_ui.connect_to_successors_selection.isChecked():
            self.road_network_toolbox_ui.successors.view().pressed.connect(
                self.initialize_predecessor_and_successor_fields
            )

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
            if last_added_lanelet_id is not None:
                last_lanelet = self.scenario_model.find_lanelet_by_id(last_added_lanelet_id)
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
                        item.setCheckState(Qt.CheckState.Checked)
                    else:
                        item.setCheckState(Qt.CheckState.Unchecked)

                list_oneway = [e.value for e in last_lanelet.user_one_way]
                for i in range(0, len(road_user_list) - 1):
                    self.road_network_toolbox_ui.road_user_oneway.addItem(road_user_list[i])
                    item = self.road_network_toolbox_ui.road_user_oneway.model().item(i, 0)
                    if road_user_list[i] in list_oneway:
                        item.setCheckState(Qt.CheckState.Checked)
                    else:
                        item.setCheckState(Qt.CheckState.Unchecked)

                list_types = [e.value for e in last_lanelet.lanelet_type]
                for i in range(0, len(lanelet_type_list) - 1):
                    self.road_network_toolbox_ui.lanelet_type.addItem(lanelet_type_list[i])
                    item = self.road_network_toolbox_ui.lanelet_type.model().item(i, 0)
                    if lanelet_type_list[i] in list_types:
                        item.setCheckState(Qt.CheckState.Checked)
                    else:
                        item.setCheckState(Qt.CheckState.Unchecked)

            else:
                self.road_network_toolbox_ui.previous_lanelet.addItem("None")
        else:
            # Length and width
            self.road_network_toolbox_ui.lanelet_length.setText("10.0")
            self.road_network_toolbox_ui.lanelet_width.setText("3.0")
            self.road_network_toolbox_ui.line_marking_right.setCurrentIndex(10)
            self.road_network_toolbox_ui.line_marking_left.setCurrentIndex(10)

            # Advanced fields
            for i in range(0, len(road_user_list) - 1):
                self.road_network_toolbox_ui.road_user_bidirectional.addItem(road_user_list[i])
                item = self.road_network_toolbox_ui.road_user_bidirectional.model().item(i, 0)
                item.setCheckState(Qt.CheckState.Unchecked)

            for i in range(0, len(road_user_list) - 1):
                self.road_network_toolbox_ui.road_user_oneway.addItem(road_user_list[i])
                item = self.road_network_toolbox_ui.road_user_oneway.model().item(i, 0)
                item.setCheckState(Qt.CheckState.Unchecked)

            for i in range(0, len(lanelet_type_list) - 1):
                self.road_network_toolbox_ui.lanelet_type.addItem(lanelet_type_list[i])
                item = self.road_network_toolbox_ui.lanelet_type.model().item(i, 0)
                item.setCheckState(Qt.CheckState.Unchecked)

        line_markings_stop_line = [
            e.value
            for e in LineMarking
            if e.value not in [LineMarking.UNKNOWN.value, LineMarking.NO_MARKING.value]
        ]
        self.road_network_toolbox_ui.line_marking_stop_line.addItems(line_markings_stop_line)

        # Neighboring fields
        self.road_network_toolbox_ui.predecessors.clear()
        self.road_network_toolbox_ui.predecessors.addItems(
            ["None"] + [str(item) for item in self.scenario_model.collect_lanelet_ids()]
        )
        self.road_network_toolbox_ui.predecessors.setCurrentIndex(0)

        self.road_network_toolbox_ui.successors.clear()
        self.road_network_toolbox_ui.successors.addItems(
            ["None"] + [str(item) for item in self.scenario_model.collect_lanelet_ids()]
        )
        self.road_network_toolbox_ui.successors.setCurrentIndex(0)

        self.road_network_toolbox_ui.adjacent_right.clear()
        self.road_network_toolbox_ui.adjacent_right.addItems(
            ["None"] + [str(item) for item in self.scenario_model.collect_lanelet_ids()]
        )
        self.road_network_toolbox_ui.adjacent_right.setCurrentIndex(0)

        self.road_network_toolbox_ui.adjacent_left.clear()
        self.road_network_toolbox_ui.adjacent_left.addItems(
            ["None"] + [str(item) for item in self.scenario_model.collect_lanelet_ids()]
        )
        self.road_network_toolbox_ui.adjacent_left.setCurrentIndex(0)

        # Advanced
        self.road_network_toolbox_ui.lanelet_referenced_traffic_sign_ids.clear()
        self.road_network_toolbox_ui.lanelet_referenced_traffic_sign_ids.addItems(
            ["None"] + [str(item) for item in self.scenario_model.collect_traffic_sign_ids()]
        )
        self.road_network_toolbox_ui.lanelet_referenced_traffic_sign_ids.setCurrentIndex(0)

        self.road_network_toolbox_ui.lanelet_referenced_traffic_light_ids.clear()
        self.road_network_toolbox_ui.lanelet_referenced_traffic_light_ids.addItems(
            ["None"] + [str(item) for item in self.scenario_model.collect_traffic_light_ids()]
        )
        self.road_network_toolbox_ui.lanelet_referenced_traffic_light_ids.setCurrentIndex(0)

    def set_default_lanelet_information(self):
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
            ["None"] + [str(item) for item in self.scenario_model.collect_lanelet_ids()]
        )
        self.road_network_toolbox_ui.selected_predecessors.setCurrentIndex(0)

        self.road_network_toolbox_ui.selected_successors.clear()
        self.road_network_toolbox_ui.selected_successors.addItems(
            ["None"] + [str(item) for item in self.scenario_model.collect_lanelet_ids()]
        )
        self.road_network_toolbox_ui.selected_successors.setCurrentIndex(0)

        self.road_network_toolbox_ui.selected_adjacent_right.clear()
        self.road_network_toolbox_ui.selected_adjacent_right.addItems(
            ["None"] + [str(item) for item in self.scenario_model.collect_lanelet_ids()]
        )
        self.road_network_toolbox_ui.selected_adjacent_right.setCurrentIndex(0)

        self.road_network_toolbox_ui.selected_adjacent_left.clear()
        self.road_network_toolbox_ui.selected_adjacent_left.addItems(
            ["None"] + [str(item) for item in self.scenario_model.collect_lanelet_ids()]
        )
        self.road_network_toolbox_ui.selected_adjacent_left.setCurrentIndex(0)

        self.road_network_toolbox_ui.selected_lanelet_referenced_traffic_sign_ids.clear()
        self.road_network_toolbox_ui.selected_lanelet_referenced_traffic_sign_ids.addItems(
            ["None"] + [str(item) for item in self.scenario_model.collect_traffic_sign_ids()]
        )
        self.road_network_toolbox_ui.selected_lanelet_referenced_traffic_sign_ids.setCurrentIndex(0)

        self.road_network_toolbox_ui.selected_lanelet_referenced_traffic_light_ids.clear()
        self.road_network_toolbox_ui.selected_lanelet_referenced_traffic_light_ids.addItems(
            ["None"] + [str(item) for item in self.scenario_model.collect_traffic_light_ids()]
        )
        self.road_network_toolbox_ui.selected_lanelet_referenced_traffic_light_ids.setCurrentIndex(
            0
        )

        self.road_network_toolbox_ui.selected_lanelet_update.clear()
        self.road_network_toolbox_ui.selected_lanelet_update.addItems(
            ["None"] + [str(item) for item in self.scenario_model.collect_lanelet_ids()]
        )
        self.road_network_toolbox_ui.selected_lanelet_update.setCurrentIndex(0)

        self.road_network_toolbox_ui.selected_lanelet_one.clear()
        self.road_network_toolbox_ui.selected_lanelet_one.addItems(
            ["None"] + [str(item) for item in self.scenario_model.collect_lanelet_ids()]
        )
        self.road_network_toolbox_ui.selected_lanelet_one.setCurrentIndex(0)

        self.road_network_toolbox_ui.selected_lanelet_two.clear()
        self.road_network_toolbox_ui.selected_lanelet_two.addItems(
            ["None"] + [str(item) for item in self.scenario_model.collect_lanelet_ids()]
        )
        self.road_network_toolbox_ui.selected_lanelet_two.setCurrentIndex(0)

        self.road_network_toolbox_ui.selected_lanelet_start_position_x.setEnabled(True)
        self.road_network_toolbox_ui.selected_lanelet_start_position_y.setEnabled(True)
        self.road_network_toolbox_ui.selected_lanelet_end_position_x.setEnabled(True)
        self.road_network_toolbox_ui.selected_lanelet_end_position_y.setEnabled(True)
        self.road_network_toolbox_ui.selected_lanelet_width.setEnabled(True)
        self.road_network_toolbox_ui.selected_lanelet_length.setEnabled(True)

    def initialize_predecessor_and_successor_fields(self):
        """
        Initializes lanelet information fields according to the selected predecessor / successor when connect to
        predecessor / successor is selected
        selects always the first in the list of predecessors / successors
        """
        if (
            len(self.road_network_toolbox_ui.predecessors.get_checked_items()) == 0
            and len(self.road_network_toolbox_ui.successors.get_checked_items()) == 0
        ):
            return
        if self.road_network_toolbox_ui.connect_to_predecessors_selection.isChecked():
            pred = self.road_network_toolbox_ui.predecessors.get_checked_items()[0]
            if not pred.isdigit():
                return
            lanelet = self.scenario_model.find_lanelet_by_id(int(pred))
        elif self.road_network_toolbox_ui.connect_to_successors_selection.isChecked():
            suc = self.road_network_toolbox_ui.successors.get_checked_items()[0]
            if not suc.isdigit():
                return
            lanelet = self.scenario_model.find_lanelet_by_id(int(suc))
        if lanelet is None:
            return

        self.road_network_toolbox_ui.lanelet_width.setText(self.get_width(lanelet))
        self.road_network_toolbox_ui.lanelet_length.setText(self.get_length(lanelet))

        self.road_network_toolbox_ui.number_vertices.setText(str(len(lanelet.center_vertices)))

        self.road_network_toolbox_ui.line_marking_left.setCurrentText(
            lanelet.line_marking_left_vertices.value
        )
        self.road_network_toolbox_ui.line_marking_right.setCurrentText(
            lanelet.line_marking_right_vertices.value
        )

        self.road_network_toolbox_ui.lanelet_type.set_checked_items(
            [str(la_type.value) for la_type in lanelet.lanelet_type]
        )

        self.road_network_toolbox_ui.road_user_oneway.set_checked_items(
            [str(user.value) for user in lanelet.user_one_way]
        )

        self.road_network_toolbox_ui.road_user_bidirectional.set_checked_items(
            [str(user.value) for user in lanelet.user_bidirectional]
        )

    def get_width(self, lanelet: Lanelet = None):
        """
        Calculates width of the lanelet.

        @param lanelet: Lanelet of which the width should be calculated.
        @return: width of lanelet
        """
        return str(np.linalg.norm(lanelet.left_vertices[0] - lanelet.right_vertices[0]))

    def get_length(self, lanelet: Lanelet = None):
        """
        Calculates length of the lanelet.

        @param lanelet: Lanelet of which the length should be calculated.
        @return: length of lanelet
        """
        return str(
            np.linalg.norm(
                lanelet.center_vertices[0]
                - lanelet.center_vertices[len(lanelet.center_vertices) - 1]
            )
        )

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

        self.road_network_toolbox_ui.selected_lanelet_start_position_x.setEnabled(True)
        self.road_network_toolbox_ui.selected_lanelet_start_position_y.setEnabled(True)
        self.road_network_toolbox_ui.selected_lanelet_end_position_x.setEnabled(True)
        self.road_network_toolbox_ui.selected_lanelet_end_position_y.setEnabled(True)
        self.road_network_toolbox_ui.selected_lanelet_width.setEnabled(True)
        self.road_network_toolbox_ui.selected_lanelet_length.setEnabled(True)

        self.road_network_toolbox_ui.selected_lanelet_start_position_x.setText(
            str(
                0.0
                if lanelet.center_vertices[0][0] == 1.0e-16
                else round(lanelet.center_vertices[0][0], 4)
            )
        )
        self.road_network_toolbox_ui.selected_lanelet_start_position_y.setText(
            str(
                0.0
                if lanelet.center_vertices[0][1] == 1.0e-16
                else round(lanelet.center_vertices[0][1], 4)
            )
        )
        self.road_network_toolbox_ui.selected_lanelet_end_position_x.setText(
            str(
                0.0
                if lanelet.center_vertices[len(lanelet.center_vertices) - 1][0] == 1.0e-16
                else round(lanelet.center_vertices[len(lanelet.center_vertices) - 1][0], 4)
            )
        )
        self.road_network_toolbox_ui.selected_lanelet_end_position_y.setText(
            str(
                0.0
                if lanelet.center_vertices[len(lanelet.center_vertices) - 1][1] == 1.0e-16
                else round(lanelet.center_vertices[len(lanelet.center_vertices) - 1][1], 4)
            )
        )
        self.road_network_toolbox_ui.selected_lanelet_width.setText(self.get_width(lanelet))
        self.road_network_toolbox_ui.selected_lanelet_length.setText(self.get_length(lanelet))

        self.road_network_toolbox_ui.selected_lanelet_radius.setText("10.0")
        self.road_network_toolbox_ui.selected_lanelet_angle.setText("90.0")
        self.road_network_toolbox_ui.selected_number_vertices.setText(
            str(len(lanelet.center_vertices))
        )

        self.road_network_toolbox_ui.selected_line_marking_left.setCurrentText(
            lanelet.line_marking_left_vertices.value
        )
        self.road_network_toolbox_ui.selected_line_marking_right.setCurrentText(
            lanelet.line_marking_right_vertices.value
        )

        self.road_network_toolbox_ui.selected_predecessors.set_checked_items(
            [str(pre) for pre in lanelet.predecessor]
        )
        self.road_network_toolbox_ui.selected_successors.set_checked_items(
            [str(suc) for suc in lanelet.successor]
        )

        self.road_network_toolbox_ui.selected_adjacent_left.setCurrentText(str(lanelet.adj_left))
        self.road_network_toolbox_ui.selected_adjacent_right.setCurrentText(str(lanelet.adj_right))
        self.road_network_toolbox_ui.selected_adjacent_left_same_direction.setChecked(
            lanelet.adj_left_same_direction
            if lanelet.adj_left_same_direction is not None
            else False
        )
        self.road_network_toolbox_ui.selected_adjacent_right_same_direction.setChecked(
            lanelet.adj_right_same_direction
            if lanelet.adj_right_same_direction is not None
            else False
        )

        self.road_network_toolbox_ui.selected_lanelet_type.set_checked_items(
            [str(la_type.value) for la_type in lanelet.lanelet_type]
        )

        self.road_network_toolbox_ui.selected_road_user_oneway.set_checked_items(
            [str(user.value) for user in lanelet.user_one_way]
        )

        self.road_network_toolbox_ui.selected_road_user_bidirectional.set_checked_items(
            [str(user.value) for user in lanelet.user_bidirectional]
        )

        self.road_network_toolbox_ui.selected_lanelet_referenced_traffic_sign_ids.set_checked_items(
            [str(sign) for sign in lanelet.traffic_signs]
        )
        self.road_network_toolbox_ui.selected_lanelet_referenced_traffic_light_ids.set_checked_items(
            [str(light) for light in lanelet.traffic_lights]
        )

        if not self.lanelet_is_straight(lanelet):
            if self.lanelet_has_constant_curvature(lanelet):
                angle = self.calculate_angle(lanelet)
                self.road_network_toolbox_ui.selected_curved_checkbox.button.setEnabled(True)
                self.road_network_toolbox_ui.selected_curved_checkbox.setChecked(True)
                self.road_network_toolbox_ui.selected_curved_checkbox.box.setMaximumSize(1000, 1000)
                radius = self.calculate_curve_radius(
                    angle, lanelet.center_vertices[0], lanelet.center_vertices[-1]
                )
                self.road_network_toolbox_ui.selected_lanelet_radius.setText(str(radius))
                self.road_network_toolbox_ui.selected_lanelet_angle.setText(str(angle))
                self.road_network_toolbox_ui.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.display_curved_lanelet(
                    True, False
                )

            else:
                self.road_network_toolbox_ui.selected_curved_checkbox.setChecked(True)
                self.road_network_toolbox_ui.selected_curved_checkbox.box.setMaximumSize(0, 0)
                self.road_network_toolbox_ui.selected_curved_checkbox.button.setDisabled(True)
                self.road_network_toolbox_ui.selected_lanelet_start_position_x.setDisabled(True)
                self.road_network_toolbox_ui.selected_lanelet_start_position_y.setDisabled(True)
                self.road_network_toolbox_ui.selected_lanelet_end_position_x.setDisabled(True)
                self.road_network_toolbox_ui.selected_lanelet_end_position_y.setDisabled(True)
                self.road_network_toolbox_ui.selected_lanelet_width.setDisabled(True)
                self.road_network_toolbox_ui.selected_lanelet_length.setDisabled(True)

        else:
            self.road_network_toolbox_ui.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.display_curved_lanelet(
                False
            )
            self.road_network_toolbox_ui.selected_curved_checkbox.button.setEnabled(True)
            self.road_network_toolbox_ui.selected_curved_checkbox.setChecked(False)
            self.road_network_toolbox_ui.selected_curved_checkbox.box.setMaximumSize(0, 0)

        if lanelet.stop_line is not None:
            self.road_network_toolbox_ui.selected_stop_line_box.setChecked(True)
            if all(lanelet.stop_line.start == lanelet.left_vertices[0]) and all(
                lanelet.stop_line.end == lanelet.right_vertices[0]
            ):
                self.road_network_toolbox_ui.selected_stop_line_beginning.setChecked(True)
                self.road_network_toolbox_ui.lanelet_attributes_widget.adjust_selected_stop_line_position()
            elif all(
                lanelet.stop_line.start == lanelet.left_vertices[len(lanelet.left_vertices) - 1]
            ) and all(
                lanelet.stop_line.end == lanelet.right_vertices[len(lanelet.right_vertices) - 1]
            ):
                self.road_network_toolbox_ui.selected_stop_line_end.setChecked(True)
                self.road_network_toolbox_ui.lanelet_attributes_widget.adjust_selected_stop_line_position()
            else:
                self.road_network_toolbox_ui.selected_stop_line_select_position.setChecked(True)
                self.road_network_toolbox_ui.lanelet_attributes_widget.adjust_selected_stop_line_position()
                self.road_network_toolbox_ui.selected_stop_line_start_x.setText(
                    str(lanelet.stop_line.start[0])
                )
                self.road_network_toolbox_ui.selected_stop_line_start_y.setText(
                    str(lanelet.stop_line.start[1])
                )
                self.road_network_toolbox_ui.selected_stop_line_end_x.setText(
                    str(lanelet.stop_line.end[0])
                )
                self.road_network_toolbox_ui.selected_stop_line_end_y.setText(
                    str(lanelet.stop_line.end[1])
                )
            self.road_network_toolbox_ui.selected_line_marking_stop_line.setCurrentText(
                str(lanelet.stop_line.line_marking.value)
            )
        else:
            self.road_network_toolbox_ui.selected_stop_line_box.setChecked(True)
            self.road_network_toolbox_ui.selected_stop_line_beginning.setChecked(True)
            self.road_network_toolbox_ui.lanelet_attributes_widget.adjust_selected_stop_line_position()
            self.road_network_toolbox_ui.selected_stop_line_box.setChecked(False)

    def set_default_lanelet_operation_information(self):
        """
        Resets the fields to the default values.
        """
        self.road_network_toolbox_ui.create_adjacent_left_selection.setChecked(True)
        self.road_network_toolbox_ui.create_adjacent_left_selection.setChecked(False)
        self.road_network_toolbox_ui.create_adjacent_same_direction_selection.setChecked(True)
        self.road_network_toolbox_ui.rotation_angle.setValue(0)
        self.road_network_toolbox_ui.x_translation.setText("")
        self.road_network_toolbox_ui.y_translation.setText("")

    def lanelet_is_straight(self, lanelet: Lanelet) -> bool:
        """
        Checks whether lanelet is straight

        @param lanelet: Lanelet of which it should be checked whether it is straight.
        @return: bool value of result
        """
        x_start = round(lanelet.left_vertices[0][0] - lanelet.right_vertices[0][0], 3)
        y_start = round(lanelet.left_vertices[0][1] - lanelet.right_vertices[0][1], 3)
        x_end = round(
            lanelet.left_vertices[len(lanelet.left_vertices) - 1][0]
            - lanelet.right_vertices[len(lanelet.right_vertices) - 1][0],
            3,
        )
        y_end = round(
            lanelet.left_vertices[len(lanelet.left_vertices) - 1][1]
            - lanelet.right_vertices[len(lanelet.right_vertices) - 1][1],
            3,
        )
        return np.isclose(x_start, x_end, 0.01) and np.isclose(y_start, y_end, 0.01)

    def lanelet_has_constant_curvature(self, lanelet: Lanelet) -> bool:
        """
        calculates if the given lanelet has a constant curvature and can be therefore edited

        :param lanelet: Lanelet of witch checks if the curvature is constant
        :return: Boolean if the lanelet has a constant curvature
        """
        if len(lanelet.center_vertices) < 10:
            return False
        curvature = compute_polyline_curvatures(lanelet.right_vertices)
        curvature = curvature[2:-2]  # Ignore the first 2 and las 2 Entries
        rounded_values_curvature = [round(x, 3) for x in curvature]
        if len(set(rounded_values_curvature)) == 1:
            return True
        else:
            return False

    def calculate_angle(self, lanelet: Lanelet) -> float:
        """
        Calculates the angle of a given Lanelet, with vectors of the start and end of the lanelet.

        :param lanelet: lanelet of which the angle should be computed
        :return: Degrees of the angle of the lanelet
        """
        vertices_middle = round(len(lanelet.center_vertices) / 2)

        vec_start = [
            lanelet.left_vertices[0][0] - lanelet.right_vertices[0][0],
            lanelet.left_vertices[0][1] - lanelet.right_vertices[0][1],
        ]

        vec_mid = [
            lanelet.left_vertices[vertices_middle][0] - lanelet.right_vertices[vertices_middle][0],
            lanelet.left_vertices[vertices_middle][1] - lanelet.right_vertices[vertices_middle][1],
        ]

        vec_end = [
            lanelet.left_vertices[-1][0] - lanelet.right_vertices[-1][0],
            lanelet.left_vertices[-1][1] - lanelet.right_vertices[-1][1],
        ]

        angle_mid = math.degrees(angle_between(vec_mid, vec_start))
        angle_total = math.degrees(angle_between(vec_end, vec_start))
        direction = 1
        if angle_mid < 0:
            direction = -1

        if abs(angle_mid) > 90:
            return direction * (180 + (180 - abs(angle_total)))
        else:
            return angle_total

    def calculate_curve_radius(
        self, angle: float, start_point: ndarray, end_point: ndarray
    ) -> float:
        """
        Calculates the radius of a given angle, start and endpoint of a lanelet

        :param angle: angle in degrees of the lanelet
        :param start_point: Start Point of the lanelet
        :param end_point: End Point of the lanelet
        :return: radius as a float
        """
        distance = math.sqrt(
            (end_point[0] - start_point[0]) ** 2 + (end_point[1] - start_point[1]) ** 2
        )

        radius = distance / (2 * math.sin(math.radians(abs(angle) / 2)))

        return radius
