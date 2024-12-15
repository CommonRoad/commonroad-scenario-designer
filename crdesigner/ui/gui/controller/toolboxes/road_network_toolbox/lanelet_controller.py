import copy
import math
from typing import List, Optional, Union

import numpy as np
from commonroad.scenario.lanelet import (
    Lanelet,
    LaneletType,
    LineMarking,
    RoadUser,
    StopLine,
)
from numpy import ndarray

from crdesigner.common.logging import logger
from crdesigner.ui.gui.model.scenario_model import ScenarioModel
from crdesigner.ui.gui.utilities.map_creator import MapCreator
from crdesigner.ui.gui.view.toolboxes.road_network_toolbox.lanelet_ui import (
    AddLaneletUI,
)
from crdesigner.ui.gui.view.toolboxes.road_network_toolbox.road_network_toolbox_ui.road_network_toolbox_ui import (
    RoadNetworkToolboxUI,
)


class AddLaneletController:
    def __init__(
        self,
        road_network_controller,
        scenario_model: ScenarioModel,
        road_network_toolbox_ui: RoadNetworkToolboxUI,
    ):
        self.scenario_model = scenario_model
        self.road_network_toolbox_ui = road_network_toolbox_ui
        self.road_network_controller = road_network_controller
        self.lanelet_ui = AddLaneletUI(self.scenario_model, self.road_network_toolbox_ui)

    def lanelet_selection_changed(self):
        selected_lanelet = self.selected_lanelet()
        if selected_lanelet is not None:
            self.road_network_controller.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.display_curved_lanelet(
                False
            )
            self.road_network_controller.selection_changed_callback(sel_lanelets=selected_lanelet)
            self.lanelet_ui.update_lanelet_information(selected_lanelet)

    def connect_gui_lanelet(self):
        self.road_network_toolbox_ui.button_add_lanelet.clicked.connect(lambda: self.add_lanelet())
        self.road_network_toolbox_ui.button_update_lanelet.clicked.connect(
            lambda: self.update_lanelet()
        )
        self.road_network_toolbox_ui.selected_lanelet_update.currentIndexChanged.connect(
            lambda: self.lanelet_selection_changed()
        )

        # Lanelet buttons
        self.road_network_toolbox_ui.button_remove_lanelet.clicked.connect(
            lambda: self.remove_lanelet()
        )
        self.road_network_toolbox_ui.button_attach_to_other_lanelet.clicked.connect(
            lambda: self.attach_to_other_lanelet()
        )

        # connect radiobuttons for adding to the adjust_add_sections function which shows and hides choices
        self.road_network_toolbox_ui.place_at_position.clicked.connect(
            lambda: self.road_network_toolbox_ui.add_lanelet_widget.adjust_add_sections()
        )
        self.road_network_toolbox_ui.connect_to_previous_selection.clicked.connect(
            lambda: self.road_network_toolbox_ui.add_lanelet_widget.adjust_add_sections()
        )
        self.road_network_toolbox_ui.connect_to_predecessors_selection.clicked.connect(
            lambda: self.road_network_toolbox_ui.add_lanelet_widget.adjust_add_sections()
        )
        self.road_network_toolbox_ui.connect_to_successors_selection.clicked.connect(
            lambda: self.road_network_toolbox_ui.add_lanelet_widget.adjust_add_sections()
        )
        self.road_network_toolbox_ui.connecting_radio_button_group.buttonClicked.connect(
            lambda: self.lanelet_ui.initialize_basic_lanelet_information(
                self.road_network_controller.last_added_lanelet_id
            )
        )

        self.road_network_toolbox_ui.button_create_adjacent.clicked.connect(
            lambda: self.create_adjacent()
        )
        self.road_network_toolbox_ui.button_connect_lanelets.clicked.connect(
            lambda: self.connect_lanelets()
        )
        self.road_network_toolbox_ui.button_rotate_lanelet.clicked.connect(
            lambda: self.rotate_lanelet()
        )
        self.road_network_toolbox_ui.button_translate_lanelet.clicked.connect(
            lambda: self.translate_lanelet()
        )
        self.road_network_toolbox_ui.button_merge_lanelets.clicked.connect(
            lambda: self.merge_with_successor()
        )

    @logger.log
    def add_lanelet(
        self,
        lanelet_id: int = None,
        left_vertices: np.array = None,
        right_vertices: np.array = None,
    ):
        """
        Adds a lanelet to the scenario based on the selected parameters by the user.

        @param lanelet_id: Id which the new lanelet should have.
        @param update: Boolean indicating whether lanelet is updated or newly created.
        @param left_vertices: Left boundary of lanelet which should be updated.
        @param right_vertices: Right boundary of lanelet which should be updated.
        """
        if not self.scenario_model.scenario_created():
            self.road_network_controller.text_browser.append("Please create first a new scenario.")
            return

        if self.road_network_controller.mwindow.play_activated:
            self.road_network_controller.text_browser.append("Please stop the animation first.")
            return

        if (
            not self.road_network_toolbox_ui.place_at_position.isChecked()
            and not self.road_network_toolbox_ui.connect_to_previous_selection.isChecked()
            and not self.road_network_toolbox_ui.connect_to_successors_selection.isChecked()
            and not self.road_network_toolbox_ui.connect_to_predecessors_selection.isChecked()
        ):
            self.road_network_controller.text_browser.append("Please select an adding option.")
            return

        predecessors = [
            int(pre) for pre in self.road_network_toolbox_ui.predecessors.get_checked_items()
        ]
        successors = [
            int(suc) for suc in self.road_network_toolbox_ui.successors.get_checked_items()
        ]

        place_at_position = self.road_network_toolbox_ui.place_at_position.isChecked()
        connect_to_last_selection = (
            self.road_network_toolbox_ui.connect_to_previous_selection.isChecked()
        )
        connect_to_predecessors_selection = (
            self.road_network_toolbox_ui.connect_to_predecessors_selection.isChecked()
        )
        connect_to_successors_selection = (
            self.road_network_toolbox_ui.connect_to_successors_selection.isChecked()
        )

        if connect_to_last_selection and self.road_network_controller.last_added_lanelet_id is None:
            self.road_network_controller.text_browser.append(
                "__Warning__: Previously add lanelet does not exist anymore. "
                "Change lanelet adding option."
            )
            return
        if connect_to_predecessors_selection and len(predecessors) == 0:
            self.road_network_controller.text_browser.append(
                "__Warning__: No predecessors are selected."
            )
            return
        if connect_to_successors_selection and len(successors) == 0:
            self.road_network_controller.text_browser.append(
                "__Warning__: No successors are selected."
            )
            return

        lanelet_start_pos_x = self.get_x_position_lanelet_start(False)
        lanelet_start_pos_y = self.get_y_position_lanelet_start(False)

        lanelet_width = self.road_network_controller.get_float(
            self.road_network_toolbox_ui.lanelet_width
        )
        line_marking_left = LineMarking(
            self.road_network_toolbox_ui.line_marking_left.currentText()
        )
        line_marking_right = LineMarking(
            self.road_network_toolbox_ui.line_marking_right.currentText()
        )
        num_vertices = int(self.road_network_toolbox_ui.number_vertices.text())
        adjacent_left = (
            int(self.road_network_toolbox_ui.adjacent_left.currentText())
            if self.road_network_toolbox_ui.adjacent_left.currentText() != "None"
            else None
        )
        adjacent_right = (
            int(self.road_network_toolbox_ui.adjacent_right.currentText())
            if self.road_network_toolbox_ui.adjacent_right.currentText() != "None"
            else None
        )
        adjacent_left_same_direction = (
            self.road_network_toolbox_ui.adjacent_left_same_direction.isChecked()
        )
        adjacent_right_same_direction = (
            self.road_network_toolbox_ui.adjacent_right_same_direction.isChecked()
        )
        lanelet_type = {
            LaneletType(ty)
            for ty in self.road_network_toolbox_ui.lanelet_type.get_checked_items()
            if ty != "None"
        }
        user_one_way = {
            RoadUser(user)
            for user in self.road_network_toolbox_ui.road_user_oneway.get_checked_items()
            if user != "None"
        }
        user_bidirectional = {
            RoadUser(user)
            for user in self.road_network_toolbox_ui.road_user_bidirectional.get_checked_items()
            if user != "None"
        }

        traffic_signs = {
            int(sign)
            for sign in self.road_network_toolbox_ui.lanelet_referenced_traffic_sign_ids.get_checked_items()
        }
        traffic_lights = {
            int(light)
            for light in self.road_network_toolbox_ui.lanelet_referenced_traffic_light_ids.get_checked_items()
        }
        if self.road_network_toolbox_ui.stop_line_check_box.isChecked():
            if self.road_network_toolbox_ui.stop_line_beginning.isChecked():
                stop_line_at_end = False
                stop_line_at_beginning = True
                stop_line_marking = LineMarking(
                    self.road_network_toolbox_ui.line_marking_stop_line.currentText()
                )
                stop_line = StopLine(
                    np.array([0, 0]), np.array([0, 0]), stop_line_marking, set(), set()
                )
            elif self.road_network_toolbox_ui.stop_line_end.isChecked():
                stop_line_at_end = True
                stop_line_at_beginning = False
                stop_line_marking = LineMarking(
                    self.road_network_toolbox_ui.line_marking_stop_line.currentText()
                )
                stop_line = StopLine(
                    np.array([0, 0]), np.array([0, 0]), stop_line_marking, set(), set()
                )
        else:
            stop_line_at_end = False
            stop_line_at_beginning = False
            stop_line = None

        lanelet_length = self.road_network_controller.get_float(
            self.road_network_toolbox_ui.lanelet_length
        )
        lanelet_radius = self.road_network_controller.get_float(
            self.road_network_toolbox_ui.lanelet_radius
        )
        lanelet_angle = np.deg2rad(
            self.road_network_controller.get_float(self.road_network_toolbox_ui.lanelet_angle)
        )
        add_curved_selection = self.road_network_toolbox_ui.curved_check_button.button.isChecked()

        if lanelet_id is None:
            lanelet_id = self.scenario_model.generate_object_id()
        if add_curved_selection:
            lanelet = MapCreator.create_curve(
                lanelet_width,
                lanelet_radius,
                lanelet_angle,
                num_vertices,
                lanelet_id,
                lanelet_type,
                predecessors,
                successors,
                adjacent_left,
                adjacent_right,
                adjacent_left_same_direction,
                adjacent_right_same_direction,
                user_one_way,
                user_bidirectional,
                line_marking_left,
                line_marking_right,
                stop_line,
                traffic_signs,
                traffic_lights,
                stop_line_at_end,
                stop_line_at_beginning,
            )
        else:
            lanelet = MapCreator.create_straight(
                lanelet_width,
                lanelet_length,
                num_vertices,
                lanelet_id,
                lanelet_type,
                predecessors,
                successors,
                adjacent_left,
                adjacent_right,
                adjacent_left_same_direction,
                adjacent_right_same_direction,
                user_one_way,
                user_bidirectional,
                line_marking_left,
                line_marking_right,
                stop_line,
                traffic_signs,
                traffic_lights,
                stop_line_at_end,
                stop_line_at_beginning,
            )

        if connect_to_last_selection:
            last_lanelet = self.scenario_model.find_lanelet_by_id(
                self.road_network_controller.last_added_lanelet_id
            )
            lanelet.translate_rotate(
                np.array(
                    [last_lanelet.center_vertices[-1][0], last_lanelet.center_vertices[-1][1]]
                ),
                0,
            )
            MapCreator.fit_to_predecessor(last_lanelet, lanelet)
        elif connect_to_predecessors_selection:
            if len(predecessors) > 0:
                predecessor = self.scenario_model.find_lanelet_by_id(predecessors[0])
                lanelet.translate_rotate(
                    np.array(
                        [predecessor.center_vertices[-1][0], predecessor.center_vertices[-1][1]]
                    ),
                    0,
                )
                MapCreator.fit_to_predecessor(predecessor, lanelet)
        elif connect_to_successors_selection:
            if len(successors) > 0:
                successor = self.scenario_model.find_lanelet_by_id(successors[0])

                x_start = successor.center_vertices[0][0] - lanelet_length
                y_start = successor.center_vertices[0][1]

                lanelet.translate_rotate(np.array([x_start, y_start]), 0)
                MapCreator.fit_to_successor(successor, lanelet)
        elif place_at_position:
            lanelet.translate_rotate(np.array([lanelet_start_pos_x, lanelet_start_pos_y]), 0)
            if not self.road_network_toolbox_ui.horizontal.isChecked():
                if self.road_network_toolbox_ui.select_end_position.isChecked():
                    rotation_angle = math.degrees(
                        math.asin(
                            (self.get_y_position_lanelet_end() - lanelet_start_pos_y)
                            / lanelet_length
                        )
                    )
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

        self.road_network_controller.last_added_lanelet_id = lanelet_id

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

        self.scenario_model.add_lanelet(lanelet)
        self.road_network_controller.initialize_road_network_toolbox()
        self.road_network_toolbox_ui.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.display_curved_lanelet(
            False
        )

    @logger.log
    def update_lanelet(self, new_lanelet: Optional[Lanelet] = None):
        """
        Updates a given lanelet based on the information configured by the user.

        :param new_lanelet: new lanelet which replaces the old lanelet
        """
        if self.road_network_controller.mwindow.play_activated:
            self.road_network_controller.text_browser.append("Please stop the animation first.")
            return

        if new_lanelet is None:
            selected_lanelet = self.selected_lanelet()
            if selected_lanelet is None:
                return
            new_lanelet = self.update_lanelet_information(self.selected_lanelet())
        else:
            selected_lanelet = new_lanelet

        self.road_network_controller.updated_lanelet = True
        self.scenario_model.update_lanelet(selected_lanelet, new_lanelet)
        self.road_network_controller.set_default_road_network_list_information()
        self.road_network_toolbox_ui.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.display_curved_lanelet(
            False
        )

    def update_lanelet_information(self, lanelet) -> Lanelet:
        """
        Checks whether the lanelet has a constatn curvature, and if yes it changes the attributes, otherwise a new
         lanelet with the properties is added through the add_editable_updated_lanelet_method

         :param lanelet: selected Lanelet on which the operstions should be applied
         :return: Lanelet with the updsted params
        """
        if self.lanelet_ui.lanelet_has_constant_curvature(lanelet):
            return self.add_editable_updated_lanelet(
                lanelet.lanelet_id, lanelet.left_vertices, lanelet.right_vertices
            )

        lanelet = copy.deepcopy(lanelet)
        lanelet.predecessor = [
            int(pre)
            for pre in self.road_network_toolbox_ui.selected_predecessors.get_checked_items()
        ]
        lanelet.successor = [
            int(suc) for suc in self.road_network_toolbox_ui.selected_successors.get_checked_items()
        ]

        lanelet.line_marking_left_vertices = LineMarking(
            self.road_network_toolbox_ui.selected_line_marking_left.currentText()
        )
        lanelet.line_marking_right_vertices = LineMarking(
            self.road_network_toolbox_ui.selected_line_marking_right.currentText()
        )
        lanelet.adj_left = (
            int(self.road_network_toolbox_ui.selected_adjacent_left.currentText())
            if self.road_network_toolbox_ui.selected_adjacent_left.currentText() != "None"
            else None
        )
        lanelet.adj_right = (
            int(self.road_network_toolbox_ui.selected_adjacent_right.currentText())
            if self.road_network_toolbox_ui.selected_adjacent_right.currentText() != "None"
            else None
        )
        lanelet.adj_left_same_direction = (
            self.road_network_toolbox_ui.selected_adjacent_left_same_direction.isChecked()
        )
        lanelet.adj_right_same_direction = (
            self.road_network_toolbox_ui.selected_adjacent_right_same_direction.isChecked()
        )
        lanelet.lanelet_type = {
            LaneletType(ty)
            for ty in self.road_network_toolbox_ui.selected_lanelet_type.get_checked_items()
            if ty != "None"
        }
        lanelet.user_one_way = {
            RoadUser(user)
            for user in self.road_network_toolbox_ui.selected_road_user_oneway.get_checked_items()
            if user != "None"
        }
        lanelet.user_bidirectional = {
            RoadUser(user)
            for user in self.road_network_toolbox_ui.selected_road_user_bidirectional.get_checked_items()
            if user != "None"
        }

        lanelet.traffic_signs = {
            int(sign)
            for sign in self.road_network_toolbox_ui.selected_lanelet_referenced_traffic_sign_ids.get_checked_items()
        }
        lanelet.traffic_lights = {
            int(light)
            for light in self.road_network_toolbox_ui.selected_lanelet_referenced_traffic_light_ids.get_checked_items()
        }

        if self.road_network_toolbox_ui.selected_stop_line_box.isChecked():
            if lanelet.stop_line is None:
                if self.road_network_toolbox_ui.selected_stop_line_beginning.isChecked():
                    stop_line_marking = LineMarking(
                        self.road_network_toolbox_ui.selected_line_marking_stop_line.currentText()
                    )
                    lanelet.stop_line = StopLine(
                        lanelet.left_vertices[0],
                        lanelet.right_vertices[0],
                        stop_line_marking,
                        set(),
                        set(),
                    )
                elif self.road_network_toolbox_ui.selected_stop_line_end.isChecked():
                    stop_line_marking = LineMarking(
                        self.road_network_toolbox_ui.selected_line_marking_stop_line.currentText()
                    )
                    lanelet.stop_line = StopLine(
                        lanelet.left_vertices[-1],
                        lanelet.right_vertices[-1],
                        stop_line_marking,
                        set(),
                        set(),
                    )
                else:
                    stop_line_start_x = self.road_network_controller.get_float(
                        self.road_network_toolbox_ui.selected_stop_line_start_x
                    )
                    stop_line_end_x = self.road_network_controller.get_float(
                        self.road_network_toolbox_ui.selected_stop_line_end_x
                    )
                    stop_line_start_y = self.road_network_controller.get_float(
                        self.road_network_toolbox_ui.selected_stop_line_start_y
                    )
                    stop_line_end_y = self.road_network_controller.get_float(
                        self.road_network_toolbox_ui.selected_stop_line_end_y
                    )
                    stop_line_marking = LineMarking(
                        self.road_network_toolbox_ui.selected_line_marking_stop_line.currentText()
                    )
                    lanelet.stop_line = StopLine(
                        np.array([stop_line_start_x, stop_line_start_y]),
                        np.array([stop_line_end_x, stop_line_end_y]),
                        stop_line_marking,
                        set(),
                        set(),
                    )
            else:
                if self.road_network_toolbox_ui.selected_stop_line_beginning.isChecked():
                    lanelet.stop_line.start = lanelet.left_vertices[0]
                    lanelet.stop_line.end = lanelet.right_vertices[0]
                elif self.road_network_toolbox_ui.selected_stop_line_end.isChecked():
                    lanelet.stop_line.start = lanelet.left_vertices[-1]
                    lanelet.stop_line.end = lanelet.right_vertices[-1]
                else:
                    stop_line_start_x = self.road_network_controller.get_float(
                        self.road_network_toolbox_ui.selected_stop_line_start_x
                    )
                    stop_line_end_x = self.road_network_controller.get_float(
                        self.road_network_toolbox_ui.selected_stop_line_end_x
                    )
                    stop_line_start_y = self.road_network_controller.get_float(
                        self.road_network_toolbox_ui.selected_stop_line_start_y
                    )
                    stop_line_end_y = self.road_network_controller.get_float(
                        self.road_network_toolbox_ui.selected_stop_line_end_y
                    )
                    lanelet.stop_line.start = np.array([stop_line_start_x, stop_line_start_y])
                    lanelet.stop_line.end = np.array([stop_line_end_x, stop_line_end_y])

                lanelet.stop_line.line_marking = LineMarking(
                    self.road_network_toolbox_ui.selected_line_marking_stop_line.currentText()
                )

        if lanelet.lanelet_id != 0:
            self.road_network_controller.last_added_lanelet_id = lanelet.lanelet_id
        return lanelet

    def add_editable_updated_lanelet(
        self, lanelet_id: int, left_vertices: np.array = None, right_vertices: np.array = None
    ) -> Lanelet:
        """
                Adds an updated lanelet to the scenario based on the selected parameters by the user.
                The original lanelet has to be removed beforewards.

        @param lanelet_id: Id which the new lanelet should have.
        @param update: Boolean indicating whether lanelet is updated or newly created.
        @param left_vertices: Left boundary of lanelet which should be updated.
        @param right_vertices: Right boundary of lanelet which should be updated.

        :return: Lanelet to be added
        """
        predecessors = [
            int(pre)
            for pre in self.road_network_toolbox_ui.selected_predecessors.get_checked_items()
        ]
        successors = [
            int(suc) for suc in self.road_network_toolbox_ui.selected_successors.get_checked_items()
        ]

        lanelet_start_pos_x = self.get_x_position_lanelet_start(True)
        lanelet_start_pos_y = self.get_y_position_lanelet_start(True)

        lanelet_width = self.road_network_controller.get_float(
            self.road_network_toolbox_ui.selected_lanelet_width
        )
        line_marking_left = LineMarking(
            self.road_network_toolbox_ui.selected_line_marking_left.currentText()
        )
        line_marking_right = LineMarking(
            self.road_network_toolbox_ui.selected_line_marking_right.currentText()
        )
        num_vertices = int(self.road_network_toolbox_ui.selected_number_vertices.text())
        adjacent_left = (
            int(self.road_network_toolbox_ui.selected_adjacent_left.currentText())
            if self.road_network_toolbox_ui.selected_adjacent_left.currentText() != "None"
            else None
        )
        adjacent_right = (
            int(self.road_network_toolbox_ui.selected_adjacent_right.currentText())
            if self.road_network_toolbox_ui.selected_adjacent_right.currentText() != "None"
            else None
        )
        adjacent_left_same_direction = (
            self.road_network_toolbox_ui.selected_adjacent_left_same_direction.isChecked()
        )
        adjacent_right_same_direction = (
            self.road_network_toolbox_ui.selected_adjacent_right_same_direction.isChecked()
        )
        lanelet_type = {
            LaneletType(ty)
            for ty in self.road_network_toolbox_ui.selected_lanelet_type.get_checked_items()
            if ty != "None"
        }
        user_one_way = {
            RoadUser(user)
            for user in self.road_network_toolbox_ui.selected_road_user_oneway.get_checked_items()
            if user != "None"
        }
        user_bidirectional = {
            RoadUser(user)
            for user in self.road_network_toolbox_ui.selected_road_user_bidirectional.get_checked_items()
            if user != "None"
        }

        traffic_signs = {
            int(sign)
            for sign in self.road_network_toolbox_ui.selected_lanelet_referenced_traffic_sign_ids.get_checked_items()
        }
        traffic_lights = {
            int(light)
            for light in self.road_network_toolbox_ui.selected_lanelet_referenced_traffic_light_ids.get_checked_items()
        }
        if self.road_network_toolbox_ui.selected_stop_line_box.isChecked():
            if self.road_network_toolbox_ui.selected_stop_line_beginning.isChecked():
                stop_line_at_end = False
                stop_line_at_beginning = True
                stop_line_marking = LineMarking(
                    self.road_network_toolbox_ui.selected_line_marking_stop_line.currentText()
                )
                stop_line = StopLine(
                    np.array([0, 0]), np.array([0, 0]), stop_line_marking, set(), set()
                )
            elif self.road_network_toolbox_ui.selected_stop_line_end.isChecked():
                stop_line_at_end = True
                stop_line_at_beginning = False
                stop_line_marking = LineMarking(
                    self.road_network_toolbox_ui.selected_line_marking_stop_line.currentText()
                )
                stop_line = StopLine(
                    np.array([0, 0]), np.array([0, 0]), stop_line_marking, set(), set()
                )
            else:
                stop_line_start_x = self.road_network_controller.get_float(
                    self.road_network_toolbox_ui.selected_stop_line_start_x
                )
                stop_line_end_x = self.road_network_controller.get_float(
                    self.road_network_toolbox_ui.selected_stop_line_end_x
                )
                stop_line_start_y = self.road_network_controller.get_float(
                    self.road_network_toolbox_ui.selected_stop_line_start_y
                )
                stop_line_end_y = self.road_network_controller.get_float(
                    self.road_network_toolbox_ui.selected_stop_line_end_y
                )
                stop_line_marking = LineMarking(
                    self.road_network_toolbox_ui.selected_line_marking_stop_line.currentText()
                )
                stop_line_at_end = False
                stop_line_at_beginning = False
                stop_line = StopLine(
                    np.array([stop_line_start_x, stop_line_start_y]),
                    np.array([stop_line_end_x, stop_line_end_y]),
                    stop_line_marking,
                    set(),
                    set(),
                )
        else:
            stop_line_at_end = False
            stop_line_at_beginning = False
            stop_line = None

        lanelet_length = self.road_network_controller.get_float(
            self.road_network_toolbox_ui.selected_lanelet_length
        )
        lanelet_radius = self.road_network_controller.get_float(
            self.road_network_toolbox_ui.selected_lanelet_radius
        )
        lanelet_angle = np.deg2rad(
            self.road_network_controller.get_float(
                self.road_network_toolbox_ui.selected_lanelet_angle
            )
        )
        add_curved_selection = (
            self.road_network_toolbox_ui.selected_curved_checkbox.button.isChecked()
        )

        if stop_line is not None:
            stop_line_start = stop_line.start
            stop_line_end = stop_line.end

        if add_curved_selection:
            lanelet = MapCreator.create_curve(
                lanelet_width,
                lanelet_radius,
                lanelet_angle,
                num_vertices,
                lanelet_id,
                lanelet_type,
                predecessors,
                successors,
                adjacent_left,
                adjacent_right,
                adjacent_left_same_direction,
                adjacent_right_same_direction,
                user_one_way,
                user_bidirectional,
                line_marking_left,
                line_marking_right,
                stop_line,
                traffic_signs,
                traffic_lights,
                stop_line_at_end,
                stop_line_at_beginning,
            )

        else:
            lanelet = MapCreator.create_straight(
                lanelet_width,
                lanelet_length,
                num_vertices,
                lanelet_id,
                lanelet_type,
                predecessors,
                successors,
                adjacent_left,
                adjacent_right,
                adjacent_left_same_direction,
                adjacent_right_same_direction,
                user_one_way,
                user_bidirectional,
                line_marking_left,
                line_marking_right,
                stop_line,
                traffic_signs,
                traffic_lights,
                stop_line_at_end,
                stop_line_at_beginning,
            )

        lanelet.translate_rotate(np.array([lanelet_start_pos_x, lanelet_start_pos_y]), 0)

        rotation_angle = self._calc_angle(
            np.array([0, 1]), np.array([0, 0]), left_vertices[0], right_vertices[0]
        )

        initial_vertex = lanelet.center_vertices[0]
        lanelet.translate_rotate(np.array([0, 0]), np.deg2rad(rotation_angle))
        lanelet.translate_rotate(initial_vertex - lanelet.center_vertices[0], 0.0)

        # rotation destroys position of stop line therefore save stop line position and afterwards set stop line
        # position again to right value
        if stop_line is not None and not stop_line_at_end and not stop_line_at_beginning:
            lanelet.stop_line.start = stop_line_start
            lanelet.stop_line.end = stop_line_end

        if lanelet_id != 0:
            self.road_network_controller.last_added_lanelet_id = lanelet_id
        return lanelet

    @logger.log
    def remove_lanelet(self):
        """
        Removes a selected lanelet from the scenario.
        """
        if self.road_network_controller.mwindow.play_activated:
            self.road_network_controller.text_browser.append("Please stop the animation first.")
            return

        selected_lanelet = self.selected_lanelet()
        if selected_lanelet is None:
            return

        if selected_lanelet.lanelet_id == self.road_network_controller.last_added_lanelet_id:
            self.road_network_controller.last_added_lanelet_id = None

        self.road_network_controller.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.display_curved_lanelet(
            False
        )

        self.scenario_model.remove_lanelet(selected_lanelet.lanelet_id)
        self.road_network_controller.set_default_road_network_list_information()

    @logger.log
    def attach_to_other_lanelet(self):
        """
        Attaches a lanelet to another lanelet.
        @return:
        """
        if self.road_network_controller.mwindow.play_activated:
            self.road_network_controller.text_browser.append("Please stop the animation first.")
            return

        selected_lanelet_one = self.selected_lanelet(True)
        if selected_lanelet_one is None:
            return
        if self.road_network_toolbox_ui.selected_lanelet_two.currentText() != "None":
            selected_lanelet_two = self.scenario_model.find_lanelet_by_id(
                int(self.road_network_toolbox_ui.selected_lanelet_two.currentText())
            )
        else:
            self.road_network_controller.text_browser.append("No lanelet selected for [2].")
            return

        self.road_network_controller.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.display_curved_lanelet(
            False
        )

        self.scenario_model.attach_to_other_lanelet(selected_lanelet_one, selected_lanelet_two)
        self.lanelet_ui.set_default_lanelet_operation_information()

    @logger.log
    def create_adjacent(self, selected_lanelets: List[Lanelet] = None, adj_left: bool = True):
        """
        Create adjacent lanelet given a selected lanelet

        @param selected_lanelets: List of Lanelets that should be added to the scenario
        @param adj_left: Indicator whether to add the lanelet on the left or right side of the lanelet
        """
        if selected_lanelets is None:
            selected_lanelets = []
        if self.road_network_controller.mwindow.play_activated:
            self.road_network_controller.text_browser.append("Please stop the animation first.")
            return
        if len(selected_lanelets) > 0:
            adjacent_left = adj_left
        else:
            selected_lanelets.append(self.selected_lanelet(True))
            adjacent_left = self.road_network_toolbox_ui.create_adjacent_left_selection.isChecked()

        added_lanelets = []

        for selected_lanelet in selected_lanelets:
            if selected_lanelet is None:
                return
            if selected_lanelet.predecessor:
                self.road_network_controller.text_browser.append(str(selected_lanelet.predecessor))
            if selected_lanelet.successor:
                self.road_network_controller.text_browser.append(str(selected_lanelet.successor))
            if (selected_lanelet.adj_left is not None and adjacent_left) or (
                selected_lanelet.adj_right is not None and not adjacent_left
            ):
                self.road_network_controller.text_browser.append(
                    "The Lanelet has already an adjacent Lanelet"
                )
                return

            self.road_network_controller.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.display_curved_lanelet(
                False
            )

            adjacent_same_direction = (
                self.road_network_toolbox_ui.create_adjacent_same_direction_selection.isChecked()
            )
            lanelet_width = float(
                str(
                    np.linalg.norm(
                        selected_lanelet.left_vertices[0] - selected_lanelet.right_vertices[0]
                    )
                )
            )
            line_marking_left = selected_lanelet.line_marking_left_vertices
            line_marking_right = selected_lanelet.line_marking_right_vertices
            lanelet_type = selected_lanelet.lanelet_type
            user_one_way = selected_lanelet.user_one_way
            user_bidirectional = selected_lanelet.user_bidirectional
            traffic_signs = selected_lanelet.traffic_signs
            traffic_lights = selected_lanelet.traffic_lights
            stop_line_at_end = False
            stop_line = None
            if selected_lanelet.stop_line is not None:
                stop_line_marking = selected_lanelet.stop_line.line_marking
                if all(
                    selected_lanelet.stop_line.start == selected_lanelet.left_vertices[0]
                ) and all(selected_lanelet.stop_line.end == selected_lanelet.right_vertices[0]):
                    # stop line at beginning
                    stop_line_at_end = False
                    stop_line = StopLine(
                        np.array([0, 0]), np.array([0, 0]), stop_line_marking, set(), set()
                    )
                elif all(
                    selected_lanelet.stop_line.start
                    == selected_lanelet.left_vertices[len(selected_lanelet.left_vertices) - 1]
                ) and all(
                    selected_lanelet.stop_line.end
                    == selected_lanelet.right_vertices[len(selected_lanelet.right_vertices) - 1]
                ):
                    stop_line_at_end = True
                    stop_line = StopLine(
                        np.array([0, 0]), np.array([0, 0]), stop_line_marking, set(), set()
                    )
                else:
                    stop_line_start_x = selected_lanelet.stop_line.start[0]
                    stop_line_end_x = selected_lanelet.stop_line.end[0]
                    stop_line_start_y = selected_lanelet.stop_line.start[1]
                    stop_line_end_y = selected_lanelet.stop_line.end[1]
                    stop_line = StopLine(
                        np.array([stop_line_start_x, stop_line_start_y]),
                        np.array([stop_line_end_x, stop_line_end_y]),
                        stop_line_marking,
                        set(),
                        set(),
                    )
            id_of_new_lanelet = self.scenario_model.generate_object_id()

            predecessors = []
            successors = []

            for pre_id in selected_lanelet.predecessor:
                predecessor = self.scenario_model.find_lanelet_by_id(int(pre_id))
                if predecessor.adj_left is not None and adjacent_left:
                    if predecessor.adj_left_same_direction != adjacent_same_direction:
                        self.road_network_controller.text_browser.append(
                            "The adjacents predecessor has not the same" " direction!"
                        )
                        return
                    if predecessor.adj_left_same_direction:
                        predecessors.append(predecessor.adj_left)
                        self.scenario_model.add_successor_to_lanelet(
                            predecessor.adj_left, id_of_new_lanelet
                        )
                    else:
                        successors.append(predecessor.adj_left)
                        self.scenario_model.add_predecessor_to_lanelet(
                            predecessor.adj_left, id_of_new_lanelet
                        )
                elif predecessor.adj_right is not None and not adjacent_left:
                    if predecessor.adj_right_same_direction != adjacent_same_direction:
                        self.road_network_controller.text_browser.append(
                            "The adjacents predecessor has not the same" " direction!"
                        )
                        return
                    if predecessor.adj_right_same_direction:
                        predecessors.append(predecessor.adj_right)
                        self.scenario_model.add_successor_to_lanelet(
                            predecessor.adj_right, id_of_new_lanelet
                        )
                    else:
                        successors.append(predecessor.adj_right)
                        self.scenario_model.add_predecessor_to_lanelet(
                            predecessor.adj_right, id_of_new_lanelet
                        )

            for suc_id in selected_lanelet.successor:
                successor = self.scenario_model.find_lanelet_by_id(int(suc_id))
                if successor.adj_left is not None and adjacent_left:
                    if successor.adj_left_same_direction != adjacent_same_direction:
                        self.road_network_controller.text_browser.append(
                            "The adjacents successor has not the same" " direction!"
                        )
                        return
                    if successor.adj_left_same_direction:
                        successors.append(successor.adj_left)
                        self.scenario_model.add_predecessor_to_lanelet(
                            successor.adj_left, id_of_new_lanelet
                        )
                    else:
                        predecessors.append(successor.adj_left)
                        self.scenario_model.add_successor_to_lanelet(
                            successor.adj_left, id_of_new_lanelet
                        )
                elif successor.adj_right is not None and not adjacent_left:
                    if successor.adj_right_same_direction != adjacent_same_direction:
                        self.road_network_controller.text_browser.append(
                            "The adjacents successor has not the same" " direction!"
                        )
                        return
                    if successor.adj_right_same_direction:
                        successors.append(successor.adj_right)
                        self.scenario_model.add_predecessor_to_lanelet(
                            successor.adj_right, id_of_new_lanelet
                        )
                    else:
                        predecessors.append(successor.adj_right)
                        self.scenario_model.add_successor_to_lanelet(
                            successor.adj_right, id_of_new_lanelet
                        )

            if adjacent_left:
                adjacent_lanelet = MapCreator.create_adjacent_lanelet(
                    adjacent_left,
                    selected_lanelet,
                    id_of_new_lanelet,
                    adjacent_same_direction,
                    lanelet_width,
                    lanelet_type,
                    predecessors,
                    successors,
                    user_one_way,
                    user_bidirectional,
                    line_marking_left,
                    line_marking_right,
                    stop_line,
                    traffic_signs,
                    traffic_lights,
                    stop_line_at_end,
                )
            else:
                adjacent_lanelet = MapCreator.create_adjacent_lanelet(
                    adjacent_left,
                    selected_lanelet,
                    id_of_new_lanelet,
                    adjacent_same_direction,
                    lanelet_width,
                    lanelet_type,
                    predecessors,
                    successors,
                    user_one_way,
                    user_bidirectional,
                    line_marking_left,
                    line_marking_right,
                    stop_line,
                    traffic_signs,
                    traffic_lights,
                    stop_line_at_end,
                )
            added_lanelets.append(adjacent_lanelet)

        if len(added_lanelets) > 0:
            self.last_added_lanelet_id = added_lanelets[len(added_lanelets) - 1].lanelet_id
            self.scenario_model.add_lanelet(added_lanelets)
            self.road_network_controller.set_default_road_network_list_information()
            self.lanelet_ui.set_default_lanelet_operation_information()
        else:
            self.road_network_controller.text_browser.append("Adjacent lanelet already exists.")

    @logger.log
    def connect_lanelets(self):
        """
        Connects two lanelets by adding a new lanelet using cubic spline interpolation.
        """
        if self.road_network_controller.mwindow.play_activated:
            self.road_network_controller.text_browser.append("Please stop the animation first.")
            return

        selected_lanelet_one = self.selected_lanelet(True)
        if selected_lanelet_one is None:
            return
        if self.road_network_toolbox_ui.selected_lanelet_two.currentText() != "None":
            selected_lanelet_two = self.scenario_model.find_lanelet_by_id(
                int(self.road_network_toolbox_ui.selected_lanelet_two.currentText())
            )
        else:
            self.road_network_controller.text_browser.append("No lanelet selected for [2].")
            return

        self.road_network_controller.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.display_curved_lanelet(
            False
        )

        connected_lanelet = MapCreator.connect_lanelets(
            selected_lanelet_one, selected_lanelet_two, self.scenario_model.generate_object_id()
        )

        self.road_network_controller.last_added_lanelet_id = connected_lanelet.lanelet_id
        self.scenario_model.add_lanelet(connected_lanelet)
        self.road_network_controller.set_default_road_network_list_information()
        self.lanelet_ui.set_default_lanelet_operation_information()

    @logger.log
    def rotate_lanelet(self):
        """
        Rotates lanelet by a user-defined angle.
        """
        if self.road_network_controller.mwindow.play_activated:
            self.road_network_controller.text_browser.append("Please stop the animation first.")
            return

        selected_lanelet_one = self.selected_lanelet(True)
        if selected_lanelet_one is None:
            return

        self.road_network_controller.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.display_curved_lanelet(
            False
        )
        rotation_angle = int(self.road_network_toolbox_ui.rotation_angle.text())
        self.scenario_model.rotate_lanelet(selected_lanelet_one.lanelet_id, rotation_angle)
        self.lanelet_ui.set_default_lanelet_operation_information()

    @logger.log
    def translate_lanelet(self):
        """
        Translates lanelet by user-defined x- and y-values.
        """
        if self.road_network_controller.mwindow.play_activated:
            self.road_network_controller.text_browser.append("Please stop the animation first.")
            return

        selected_lanelet_one = self.selected_lanelet(True)
        if selected_lanelet_one is None:
            return

        self.road_network_controller.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.display_curved_lanelet(
            False
        )
        x_translation = self.road_network_controller.get_float(
            self.road_network_toolbox_ui.x_translation
        )
        y_translation = self.road_network_controller.get_float(
            self.road_network_toolbox_ui.y_translation
        )
        selected_lanelet_one.translate_rotate(np.array([x_translation, y_translation]), 0)

        self.scenario_model.translate_lanelet(selected_lanelet_one)
        self.lanelet_ui.set_default_lanelet_operation_information()

    def get_lanelet_from_toolbox(self, new_lanelet: bool) -> Lanelet:
        """
        Collects the information of the properties of the lanelet of the toolbox and creates with it a Lanelet
        which is than returned

        :return: Lanelet with the information given in the toolbox
        """
        if not self.scenario_model.scenario_created():
            self.road_network_controller.text_browser.append("Please create first a new scenario.")
            return

        if not new_lanelet:
            selected_lanelet = self.selected_lanelet()
            if selected_lanelet is None:
                return None
            return self.add_editable_updated_lanelet(
                0, selected_lanelet.left_vertices, selected_lanelet.right_vertices
            )

        predecessors = [
            int(pre) for pre in self.road_network_toolbox_ui.predecessors.get_checked_items()
        ]
        successors = [
            int(suc) for suc in self.road_network_toolbox_ui.successors.get_checked_items()
        ]

        place_at_position = self.road_network_toolbox_ui.place_at_position.isChecked()
        connect_to_last_selection = (
            self.road_network_toolbox_ui.connect_to_previous_selection.isChecked()
        )
        connect_to_predecessors_selection = (
            self.road_network_toolbox_ui.connect_to_predecessors_selection.isChecked()
        )
        connect_to_successors_selection = (
            self.road_network_toolbox_ui.connect_to_successors_selection.isChecked()
        )

        if connect_to_last_selection and self.road_network_controller.last_added_lanelet_id is None:
            self.road_network_controller.text_browser.append(
                "__Warning__: Previously add lanelet does not exist anymore. "
                "Change lanelet adding option."
            )
            return None
        if connect_to_predecessors_selection and len(predecessors) == 0:
            self.road_network_controller.text_browser.append(
                "__Warning__: No predecessors are selected."
            )
            return None
        if connect_to_successors_selection and len(successors) == 0:
            self.road_network_controller.text_browser.append(
                "__Warning__: No successors are selected."
            )
            return None

        lanelet_start_pos_x = self.get_x_position_lanelet_start(False)
        lanelet_start_pos_y = self.get_y_position_lanelet_start(False)

        lanelet_width = self.road_network_controller.get_float(
            self.road_network_toolbox_ui.lanelet_width
        )
        line_marking_left = LineMarking(
            self.road_network_toolbox_ui.line_marking_left.currentText()
        )
        line_marking_right = LineMarking(
            self.road_network_toolbox_ui.line_marking_right.currentText()
        )
        num_vertices = int(self.road_network_toolbox_ui.number_vertices.text())
        adjacent_left = (
            int(self.road_network_toolbox_ui.adjacent_left.currentText())
            if self.road_network_toolbox_ui.adjacent_left.currentText() != "None"
            else None
        )
        adjacent_right = (
            int(self.road_network_toolbox_ui.adjacent_right.currentText())
            if self.road_network_toolbox_ui.adjacent_right.currentText() != "None"
            else None
        )
        adjacent_left_same_direction = (
            self.road_network_toolbox_ui.adjacent_left_same_direction.isChecked()
        )
        adjacent_right_same_direction = (
            self.road_network_toolbox_ui.adjacent_right_same_direction.isChecked()
        )
        lanelet_type = {
            LaneletType(ty)
            for ty in self.road_network_toolbox_ui.lanelet_type.get_checked_items()
            if ty != "None"
        }
        user_one_way = {
            RoadUser(user)
            for user in self.road_network_toolbox_ui.road_user_oneway.get_checked_items()
            if user != "None"
        }
        user_bidirectional = {
            RoadUser(user)
            for user in self.road_network_toolbox_ui.road_user_bidirectional.get_checked_items()
            if user != "None"
        }

        traffic_signs = {
            int(sign)
            for sign in self.road_network_toolbox_ui.lanelet_referenced_traffic_sign_ids.get_checked_items()
        }
        traffic_lights = {
            int(light)
            for light in self.road_network_toolbox_ui.lanelet_referenced_traffic_light_ids.get_checked_items()
        }
        if self.road_network_toolbox_ui.stop_line_check_box.isChecked():
            if self.road_network_toolbox_ui.stop_line_beginning.isChecked():
                stop_line_at_end = False
                stop_line_at_beginning = True
                stop_line_marking = LineMarking(
                    self.road_network_toolbox_ui.line_marking_stop_line.currentText()
                )
                stop_line = StopLine(
                    np.array([0, 0]), np.array([0, 0]), stop_line_marking, set(), set()
                )
            elif self.road_network_toolbox_ui.stop_line_end.isChecked():
                stop_line_at_end = True
                stop_line_at_beginning = False
                stop_line_marking = LineMarking(
                    self.road_network_toolbox_ui.line_marking_stop_line.currentText()
                )
                stop_line = StopLine(
                    np.array([0, 0]), np.array([0, 0]), stop_line_marking, set(), set()
                )
        else:
            stop_line_at_end = False
            stop_line_at_beginning = False
            stop_line = None

        lanelet_length = self.road_network_controller.get_float(
            self.road_network_toolbox_ui.lanelet_length
        )
        lanelet_radius = self.road_network_controller.get_float(
            self.road_network_toolbox_ui.lanelet_radius
        )
        lanelet_angle = np.deg2rad(
            self.road_network_controller.get_float(self.road_network_toolbox_ui.lanelet_angle)
        )

        lanelet_id = 0

        lanelet = MapCreator.create_curve(
            lanelet_width,
            lanelet_radius,
            lanelet_angle,
            num_vertices,
            lanelet_id,
            lanelet_type,
            predecessors,
            successors,
            adjacent_left,
            adjacent_right,
            adjacent_left_same_direction,
            adjacent_right_same_direction,
            user_one_way,
            user_bidirectional,
            line_marking_left,
            line_marking_right,
            stop_line,
            traffic_signs,
            traffic_lights,
            stop_line_at_end,
            stop_line_at_beginning,
        )

        if connect_to_last_selection:
            last_lanelet = self.scenario_model.find_lanelet_by_id(
                self.road_network_controller.last_added_lanelet_id
            )
            lanelet.translate_rotate(
                np.array(
                    [last_lanelet.center_vertices[-1][0], last_lanelet.center_vertices[-1][1]]
                ),
                0,
            )
            MapCreator.fit_to_predecessor(last_lanelet, lanelet)
        elif connect_to_predecessors_selection:
            if len(predecessors) > 0:
                predecessor = self.scenario_model.find_lanelet_by_id(predecessors[0])
                lanelet.translate_rotate(
                    np.array(
                        [predecessor.center_vertices[-1][0], predecessor.center_vertices[-1][1]]
                    ),
                    0,
                )
                MapCreator.fit_to_predecessor(predecessor, lanelet)
        elif connect_to_successors_selection:
            if len(successors) > 0:
                successor = self.scenario_model.find_lanelet_by_id(successors[0])

                x_start = successor.center_vertices[0][0] - lanelet_length
                y_start = successor.center_vertices[0][1]

                lanelet.translate_rotate(np.array([x_start, y_start]), 0)
                MapCreator.fit_to_successor(successor, lanelet)
        elif place_at_position:
            lanelet.translate_rotate(np.array([lanelet_start_pos_x, lanelet_start_pos_y]), 0)
            if not self.road_network_toolbox_ui.horizontal.isChecked():
                if self.road_network_toolbox_ui.select_end_position.isChecked():
                    rotation_angle = math.degrees(
                        math.asin(
                            (self.get_y_position_lanelet_end() - lanelet_start_pos_y)
                            / lanelet_length
                        )
                    )
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
        return lanelet

    @logger.log
    def merge_with_successor(self):
        """
        Merges a lanelet with its successor. If several successors exist, a new lanelet is created for each successor.
        """
        if self.road_network_controller.mwindow.play_activated:
            self.road_network_controller.text_browser.append("Please stop the animation first.")
            return

        selected_lanelet_one = self.selected_lanelet(True)
        if selected_lanelet_one is None:
            return

        self.road_network_controller.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.display_curved_lanelet(
            False
        )
        self.scenario_model.merge_with_successor(selected_lanelet_one)
        self.lanelet_ui.set_default_lanelet_operation_information()

    def get_x_position_lanelet_start(self, update=False) -> float:
        """
        Extracts lanelet x-position of first center vertex.

        @return: x-position [m]
        """
        if not update:
            if (
                self.road_network_toolbox_ui.place_at_position.isChecked()
                and self.road_network_toolbox_ui.lanelet_start_position_x.text()
                and self.road_network_toolbox_ui.lanelet_start_position_x.text() != "-"
            ):
                return float(
                    self.road_network_toolbox_ui.lanelet_start_position_x.text().replace(",", ".")
                )
            else:
                return 0
        else:
            if (
                self.road_network_toolbox_ui.selected_lanelet_start_position_x.text()
                and self.road_network_toolbox_ui.selected_lanelet_start_position_x.text() != "-"
            ):
                return float(
                    self.road_network_toolbox_ui.selected_lanelet_start_position_x.text().replace(
                        ",", "."
                    )
                )
            else:
                return 0

    def get_y_position_lanelet_start(self, update=False) -> float:
        """
        Extracts lanelet y-position of first center vertex.

        @return: y-position [m]
        """
        if not update:
            if (
                self.road_network_toolbox_ui.place_at_position.isChecked()
                and self.road_network_toolbox_ui.lanelet_start_position_y.text()
                and self.road_network_toolbox_ui.lanelet_start_position_y.text() != "-"
            ):
                return float(
                    self.road_network_toolbox_ui.lanelet_start_position_y.text().replace(",", ".")
                )
            else:
                return 0
        else:
            if (
                self.road_network_toolbox_ui.selected_lanelet_start_position_y.text()
                and self.road_network_toolbox_ui.selected_lanelet_start_position_y.text() != "-"
            ):
                return float(
                    self.road_network_toolbox_ui.selected_lanelet_start_position_y.text().replace(
                        ",", "."
                    )
                )
            else:
                return 0

    def get_x_position_lanelet_end(self, update=False) -> float:
        """
        Extracts lanelet x-position of last center vertex.

        @return: x-position [m]
        """
        if not update:
            if (
                self.road_network_toolbox_ui.lanelet_end_position_x.text()
                and self.road_network_toolbox_ui.lanelet_end_position_x.text() != "-"
            ):
                return float(
                    self.road_network_toolbox_ui.lanelet_end_position_x.text().replace(",", ".")
                )
            else:
                return 0
        else:
            if (
                self.road_network_toolbox_ui.selected_lanelet_end_position_x.text()
                and self.road_network_toolbox_ui.selected_lanelet_end_position_x.text() != "-"
            ):
                return float(
                    self.road_network_toolbox_ui.selected_lanelet_end_position_x.text().replace(
                        ",", "."
                    )
                )
            else:
                return 0

    def get_y_position_lanelet_end(self, update=False) -> float:
        """
        Extracts lanelet y-position of last center vertex.

        @return: y-position [m]
        """
        if not update:
            if (
                self.road_network_toolbox_ui.lanelet_end_position_y.text()
                and self.road_network_toolbox_ui.lanelet_end_position_y.text() != "-"
            ):
                return float(
                    self.road_network_toolbox_ui.lanelet_end_position_y.text().replace(",", ".")
                )
            else:
                return 0
        else:
            if (
                self.road_network_toolbox_ui.selected_lanelet_end_position_y.text()
                and self.road_network_toolbox_ui.selected_lanelet_end_position_y.text() != "-"
            ):
                return float(
                    self.road_network_toolbox_ui.selected_lanelet_end_position_y.text().replace(
                        ",", "."
                    )
                )
            else:
                return 0

    def _calc_angle(
        self,
        left_vertice_point_one: ndarray,
        right_vertice_point_one: ndarray,
        left_vertice_point_two: ndarray,
        right_vertice_point_two: ndarray,
    ) -> float:
        """
        Calculates the angle between two given lines

        :param left_vertice_point_one: left point of the first line
        :param right_vertice_point_one: right point of the first line
        :param left_vertice_point_two: left point of the second line
        :param right_vertice_point_two: right point of the second line

        :return: Angle between the 2 lines as a float
        """
        line_origin = left_vertice_point_one[:2] - right_vertice_point_one[:2]
        line_lanelet = left_vertice_point_two[:2] - right_vertice_point_two[:2]
        norm_predecessor = np.linalg.norm(line_origin)
        norm_lanelet = np.linalg.norm(line_lanelet)
        dot_prod = np.dot(line_origin, line_lanelet)
        sign = line_lanelet[1] * line_origin[0] - line_lanelet[0] * line_origin[1]
        angle = np.arccos(dot_prod / (norm_predecessor * norm_lanelet))
        if sign > 0:
            angle = 2 * np.pi - angle
        return 360 - angle * (180 / math.pi)

    def selected_lanelet(self, lanelet_operation: bool = False) -> Union[Lanelet, None]:
        """
        Extracts the selected lanelet one
        :param lanelet_operation: is set to true if the request comes from the lanelet_opeartions widgete

        @return: Selected lanelet object.
        """
        if not self.road_network_controller.initialized:
            return
        if not self.scenario_model.scenario_created():
            self.road_network_controller.text_browser.append("create a new file")
            return None

        if lanelet_operation:
            if self.road_network_toolbox_ui.selected_lanelet_one.currentText() not in ["None", ""]:
                selected_lanelet = self.scenario_model.find_lanelet_by_id(
                    int(self.road_network_toolbox_ui.selected_lanelet_one.currentText())
                )
                return selected_lanelet
            elif (
                self.road_network_toolbox_ui.selected_lanelet_one.currentText() in ["None", ""]
                and not self.road_network_controller.update
            ):
                self.road_network_controller.text_browser.append("No lanelet selected.")
                return None

        else:
            if self.road_network_toolbox_ui.selected_lanelet_update.currentText() not in [
                "None",
                "",
            ]:
                selected_lanelet = self.scenario_model.find_lanelet_by_id(
                    int(self.road_network_toolbox_ui.selected_lanelet_update.currentText())
                )
                return selected_lanelet
            elif (
                self.road_network_toolbox_ui.selected_lanelet_update.currentText() in ["None", ""]
                and not self.road_network_controller.update
            ):
                self.road_network_controller.text_browser.append("No lanelet selected.")
                return None
