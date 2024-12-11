from __future__ import annotations

import copy
import math
from typing import TYPE_CHECKING, List, Union

import numpy as np
from commonroad.common.util import Interval
from commonroad.geometry.shape import Circle, Polygon, Rectangle, Shape, ShapeGroup
from commonroad.planning.goal import GoalRegion
from commonroad.planning.planning_problem import PlanningProblem
from commonroad.scenario.scenario import (
    Environment,
    GeoTransformation,
    Location,
    Tag,
    Time,
    TimeOfDay,
    Underground,
    Weather,
)
from commonroad.scenario.state import CustomState, InitialState, TraceState
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDockWidget, QLineEdit, QTableWidgetItem

from crdesigner.common.config import gui_config
from crdesigner.common.logging import logger
from crdesigner.ui.gui.controller.settings.scenario_saving_dialog_controller import (
    get_float_position,
)
from crdesigner.ui.gui.model.planning_problem_set_model import PlanningProblemSetModel
from crdesigner.ui.gui.view.toolboxes.scenario_toolbox.scenario_toolbox_ui import (
    ScenarioToolboxUI,
)

if TYPE_CHECKING:
    from crdesigner.ui.gui.controller.mwindow_controller import MWindowController


class ScenarioToolboxController(QDockWidget):
    """
    The controller for the Scenario Toolbox.
    """

    def __init__(self, mwindow: MWindowController):
        """
        Initialize the controller.
        :param mwindow: The main window controller.
        """
        super().__init__("Scenario Toolbox")
        self.mwindow = mwindow
        self.mwindow_ui = mwindow.mwindow_ui

        self.scenario_toolbox_ui = ScenarioToolboxUI(mwindow)
        self.adjust_ui()

        self.current_scenario = mwindow.scenario_model
        self.pps_model: PlanningProblemSetModel = mwindow.pps_model
        self.text_browser = mwindow.crdesigner_console_wrapper.text_browser
        self.last_added_lanelet_id = None
        self.current_lanelets = []
        self.current_shapes = []
        self.tmp_folder = mwindow.tmp_folder
        # self.selection_changed_callback = selection_changed_callback
        self.initialized = False
        self.update = False
        self.updated_lanelet = False

        self.initialize_toolbox()
        self.connect_gui_elements()
        self.init_settings = False
        self.update_settings()
        self.connect_settings_elements()

        self.current_scenario.subscribe(self.update_settings)
        self.pps_model.new_pps.connect(self.set_planning_problem_information)

    def adjust_ui(self) -> None:
        """Updates GUI properties like width, etc."""
        self.setFloating(True)
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.setWidget(self.scenario_toolbox_ui)
        self.scenario_toolbox_ui.setMinimumWidth(450)

    def initialize_toolbox(self) -> None:
        """Initializes toolbox."""
        self.update_settings()
        self.current_lanelets = []
        self.current_shapes = []
        self.reset_toolbox()
        self.scenario_toolbox_ui.initialize_initial_state()
        self.initialize_goal_state()
        self.scenario_toolbox_ui.goal_states_list_table.setRowCount(0)
        self.scenario_toolbox_ui.goal_states_list_table.clearSelection()

        self.set_planning_problem_information()
        self.initialized = True

    def initialize_goal_state(self) -> None:
        """Initializes goal position GUI elements with information."""
        self.scenario_toolbox_ui.initialize_goal_state_fields()
        self.set_goal_state_information()
        self.set_goal_state_information_toggle_type()

    def lanelet_selection_changed(self) -> None:
        """Updates the selected lanelet."""
        selected_lanelet = self.selected_lanelet()
        if selected_lanelet is not None:
            self.selection_changed_callback(sel_lanelets=selected_lanelet)
            self.update_lanelet_information(selected_lanelet)

    @logger.log
    def _selected_planning_problem_changed(self) -> None:
        row = self.scenario_toolbox_ui.planning_problems_list_table.currentItem()
        if row is not None:
            pp_id = int(row.text())
            self.pps_model.set_selected_pp_id(pp_id)

    def connect_gui_elements(self) -> None:
        """adds functionality to the gui elements like buttons, menus,..."""
        self.initialized = False

        # Planning Problems Overview
        self.scenario_toolbox_ui.planning_problems_list_table.currentCellChanged.connect(
            lambda: self.update_current_planning_problem()
        )
        self.scenario_toolbox_ui.planning_problems_list_table.currentCellChanged.connect(
            lambda: self._selected_planning_problem_changed()
        )

        self.scenario_toolbox_ui.button_add_planning_problems.clicked.connect(
            lambda: self.add_planning_problem()
        )

        self.scenario_toolbox_ui.button_remove_planning_problems.clicked.connect(
            lambda: self.remove_planning_problem()
        )

        """Initial State"""
        self.scenario_toolbox_ui.button_update_initial_state.clicked.connect(
            lambda: self.update_initial_state()
        )

        """Goal States"""
        self.scenario_toolbox_ui.goal_states_list_table.currentCellChanged.connect(
            lambda: self.update_current_goal_state()
        )

        self.scenario_toolbox_ui.type.currentTextChanged.connect(
            lambda: self.set_goal_state_information_toggle_type()
        )

        self.scenario_toolbox_ui.button_add_goal_state.clicked.connect(
            lambda: self.add_goal_state()
        )

        self.scenario_toolbox_ui.button_remove_goal_state.clicked.connect(
            lambda: self.remove_goal_state()
        )

        self.scenario_toolbox_ui.button_update_goal_state.clicked.connect(
            lambda: self.update_goal_state()
        )

    def connect_settings_elements(self) -> None:
        """adds functionality to the gui elements like buttons, menus,..."""
        self.scenario_toolbox_ui.country.currentTextChanged.connect(
            lambda: self.update_scenario_meta_data()
        )
        self.scenario_toolbox_ui.scenario_scene_name.textChanged.connect(
            lambda: self.update_scenario_meta_data()
        )
        self.scenario_toolbox_ui.scenario_scene_id.valueChanged.connect(
            lambda: self.update_scenario_meta_data()
        )
        self.scenario_toolbox_ui.scenario_config_id.valueChanged.connect(
            lambda: self.update_scenario_meta_data()
        )
        self.scenario_toolbox_ui.prediction_type.currentTextChanged.connect(
            lambda: self.update_scenario_meta_data()
        )
        self.scenario_toolbox_ui.scenario_prediction_id.valueChanged.connect(
            lambda: self.update_scenario_meta_data()
        )
        self.scenario_toolbox_ui.cooperative_scenario.stateChanged.connect(
            lambda: self.update_scenario_meta_data()
        )
        self.scenario_toolbox_ui.scenario_tags.currentTextChanged.connect(
            lambda: self.update_scenario_meta_data()
        )
        self.scenario_toolbox_ui.scenario_time_step_size.textChanged.connect(
            lambda: self.update_scenario_meta_data()
        )
        self.scenario_toolbox_ui.scenario_author.textChanged.connect(
            lambda: self.update_scenario_meta_data()
        )
        self.scenario_toolbox_ui.scenario_affiliation.textChanged.connect(
            lambda: self.update_scenario_meta_data()
        )
        self.scenario_toolbox_ui.scenario_source.textChanged.connect(
            lambda: self.update_scenario_meta_data()
        )
        self.scenario_toolbox_ui.location_storage_selection.stateChanged.connect(
            lambda: self.update_scenario_meta_data()
        )

        self.scenario_toolbox_ui.geo_reference.currentTextChanged.connect(
            lambda: self.change_geo_reference()
        )
        self.scenario_toolbox_ui.translate_button.clicked.connect(
            lambda: self.update_scenario_location()
        )

        self.scenario_toolbox_ui.scenario_geo_name_id.textChanged.connect(
            lambda: self.update_scenario_meta_data()
        )
        self.scenario_toolbox_ui.scenario_latitude.textChanged.connect(
            lambda: self.update_scenario_meta_data()
        )
        self.scenario_toolbox_ui.scenario_longitude.textChanged.connect(
            lambda: self.update_scenario_meta_data()
        )
        self.scenario_toolbox_ui.scenario_time_of_day.currentTextChanged.connect(
            lambda: self.update_scenario_meta_data()
        )
        self.scenario_toolbox_ui.scenario_weather.currentTextChanged.connect(
            lambda: self.update_scenario_meta_data()
        )
        self.scenario_toolbox_ui.scenario_underground.currentTextChanged.connect(
            lambda: self.update_scenario_meta_data()
        )
        self.scenario_toolbox_ui.scenario_time_hour.textChanged.connect(
            lambda: self.update_scenario_meta_data()
        )
        self.scenario_toolbox_ui.scenario_time_minute.textChanged.connect(
            lambda: self.update_scenario_meta_data()
        )

    def reset_toolbox(self) -> None:
        """
        Resets toolbox.
        """
        self.scenario_toolbox_ui.goal_states_list_list_table_row_count = 0
        self.scenario_toolbox_ui.planning_problems_list_table_row_count = 0
        self.scenario_toolbox_ui.goal_states_lanelet_list_table_row_count = 0
        self.scenario_toolbox_ui.goal_states_shape_list_table_row_count = 0

    """
    Planing Problem
    """

    def collect_planning_problems(self) -> List[int]:
        """returns list of all planning problem ids"""
        if not self.pps_model.is_empty():
            return list(self.pps_model.get_pps().planning_problem_dict)
        else:
            return []

    """Planning Problem Data Management"""

    @logger.log
    def add_planning_problem(self) -> None:
        """adds a new planning problem to current_pps"""
        if self.mwindow.play_activated:
            self.text_browser.append("Please stop the animation first.")
            return

        if not self.mwindow.scenario_model.scenario_created():
            self.text_browser.append("Please create first a Scenario")
            return

        id = 1
        planning_problem_ids = self.collect_planning_problems()
        while id in planning_problem_ids:
            id += 1

        new_initial_state = InitialState()
        new_initial_state.time_step = 0
        new_initial_state.position = [0.0, 0.0]
        new_initial_state.orientation = 0.0
        new_initial_state.velocity = 0.0
        new_initial_state.acceleration = 0.0
        new_initial_state.yaw_rate = 0.0
        new_initial_state.slip_angle = 0.0

        new_gr = GoalRegion(state_list=[], lanelets_of_goal_position=dict())

        new_pp = PlanningProblem(
            planning_problem_id=id, initial_state=new_initial_state, goal_region=new_gr
        )

        self.pps_model.add_planing_problem(new_pp)
        self.pps_model.set_selected_pp_id(id)
        self.set_planning_problem_information()

    @logger.log
    def remove_planning_problem(self) -> None:
        """removes planning problem"""
        if self.mwindow.play_activated:
            self.text_browser.append("Please stop the animation first.")
            return

        if self.scenario_toolbox_ui.planning_problems_list_table.currentItem() is not None:
            self.pps_model.remove_pp(
                int(self.scenario_toolbox_ui.planning_problems_list_table.currentItem().text())
            )
            self.scenario_toolbox_ui.planning_problems_list_table.clearSelection()
            self.scenario_toolbox_ui.goal_states_list_table.setRowCount(0)
            self.scenario_toolbox_ui.goal_states_list_table.clearSelection()
            self.set_planning_problem_information()

    """Planning Problem GUI Management"""

    def set_planning_problem_information(self) -> None:
        """Load Planning Problems"""
        self.update = True
        planning_problem_ids = self.collect_planning_problems()
        self.mwindow.animated_viewer_wrapper.scenario_saving_dialog.autosave(
            self.current_scenario.get_current_scenario()
        )

        """update Planning Problems table"""
        self.scenario_toolbox_ui.planning_problems_list_table.setRowCount(0)
        for planning_problem_id in planning_problem_ids:
            item = QTableWidgetItem(str(planning_problem_id))
            self.scenario_toolbox_ui.planning_problems_list_table.insertRow(
                self.scenario_toolbox_ui.planning_problems_list_table_row_count
            )
            self.scenario_toolbox_ui.planning_problems_list_table.setItem(
                self.scenario_toolbox_ui.planning_problems_list_table_row_count, 0, item
            )

    @logger.log
    def update_current_planning_problem(self) -> None:
        """sets current planning problem id and the corresponding initial state and goal state or resets
        initial state and goal state if planning problem is deleted"""
        if self.scenario_toolbox_ui.planning_problems_list_table.currentItem() is not None:
            initial_state = self.collect_initial_state(
                planning_problem_id=int(
                    self.scenario_toolbox_ui.planning_problems_list_table.currentItem().text()
                )
            )
            self.scenario_toolbox_ui.set_initial_state_information(initial_state)
            self.set_goal_states_information()
        else:
            """Resets initial state and goal states GUI"""
            self.scenario_toolbox_ui.initialize_initial_state()
            self.initialize_goal_state()

        self.pps_model.notify_all()

    """
    Goal State
    """

    @logger.log
    def update_current_goal_state(self) -> None:
        """sets current goal state id and the corresponding goal state to id and planning problem"""
        self.set_goal_state_information()

    def collect_goal_states(self, planning_problem_id: int) -> List[TraceState]:
        """returns the goal state of selected planning problem"""
        return self.pps_model.get_pp(planning_problem_id).goal.state_list

    """Goal State Data Management"""

    @logger.log
    def add_goal_state(self) -> None:
        """Add goal state to PPl."""
        if self.mwindow.play_activated:
            self.text_browser.append("Please stop the animation first.")
            return

        if not self.mwindow.scenario_model.scenario_created():
            self.text_browser.append("Please create first a Scenario")
            return

        if self.scenario_toolbox_ui.planning_problems_list_table.currentItem() is None:
            """create new planning problem"""
            self.add_planning_problem()
            self.set_planning_problem_information()
            self.scenario_toolbox_ui.planning_problems_list_table.selectRow(0)
        """update initial state of planning problem"""
        current_planning_problem_id = int(
            self.scenario_toolbox_ui.planning_problems_list_table.currentItem().text()
        )
        new_gs = CustomState()
        new_gs.time_step = Interval(start=0, end=0)

        self.collect_goal_states(planning_problem_id=current_planning_problem_id).append(new_gs)
        self.update_goal_state(len(self.collect_goal_states(current_planning_problem_id)) - 1)

    @logger.log
    def remove_goal_state(self) -> None:
        """Removes goal state from PPl."""
        if self.mwindow.play_activated:
            self.text_browser.append("Please stop the animation first.")
            return

        if self.scenario_toolbox_ui.goal_states_list_table.currentItem() is not None:
            current_planning_problem_id = int(
                self.scenario_toolbox_ui.planning_problems_list_table.currentItem().text()
            )
            i = self.scenario_toolbox_ui.goal_states_list_table.currentRow()
            self.collect_goal_states(planning_problem_id=current_planning_problem_id).pop(
                len(self.collect_goal_states(planning_problem_id=current_planning_problem_id))
                - i
                - 1
            )
            self.scenario_toolbox_ui.goal_states_list_table.clearSelection()
            self.set_goal_states_information()
            self.initialize_goal_state()

    @logger.log
    def update_goal_state(self, current_goal_state_id: int = None) -> None:
        """Updates selected goal state or adds a state

        :param current_goal_state_id: ID which was just added and the values of the toolbox are for
        """
        if self.mwindow.play_activated:
            self.text_browser.append("Please stop the animation first.")
            return

        if self.scenario_toolbox_ui.planning_problems_list_table.currentItem() is None:
            self.text_browser.append("Please create and/or select a planning problem.")
            return

        current_planning_problem_id = int(
            self.scenario_toolbox_ui.planning_problems_list_table.currentItem().text()
        )

        if current_goal_state_id is None:
            if self.scenario_toolbox_ui.goal_states_list_table.currentItem() is None:
                self.text_browser.append("Please create and/or select a goal state.")
                return
            current_goal_state_id = (
                len(self.collect_goal_states(planning_problem_id=current_planning_problem_id))
                - self.scenario_toolbox_ui.goal_states_list_table.currentRow()
                - 1
            )

        if self.get_int(self.scenario_toolbox_ui.goal_time_start) > self.get_int(
            self.scenario_toolbox_ui.goal_time_end
        ):
            self.text_browser.append("Start of interval must be <= end. Time is not edited")
        else:
            self.collect_goal_states(planning_problem_id=current_planning_problem_id)[
                current_goal_state_id
            ].time_step = Interval(
                start=self.get_int(self.scenario_toolbox_ui.goal_time_start),
                end=self.get_int(self.scenario_toolbox_ui.goal_time_end),
            )

        if self.scenario_toolbox_ui.goal_velocity_selected.isChecked():
            if self.get_float(self.scenario_toolbox_ui.goal_velocity_start) > self.get_float(
                self.scenario_toolbox_ui.goal_velocity_end
            ):
                self.text_browser.append("Start of interval must be <= end. Velocity is not edited")
            else:
                self.collect_goal_states(planning_problem_id=current_planning_problem_id)[
                    current_goal_state_id
                ].velocity = Interval(
                    start=self.get_float(self.scenario_toolbox_ui.goal_velocity_start),
                    end=self.get_float(self.scenario_toolbox_ui.goal_velocity_end),
                )
        else:
            self.collect_goal_states(planning_problem_id=current_planning_problem_id)[
                current_goal_state_id
            ].velocity = None
            try:
                self.collect_goal_states(planning_problem_id=current_planning_problem_id)[
                    current_goal_state_id
                ].attributes.remove("velocity")
            except KeyError:
                pass

        if self.scenario_toolbox_ui.goal_orientation_selected.isChecked():
            if self.get_float(self.scenario_toolbox_ui.goal_orientation_start) > self.get_float(
                self.scenario_toolbox_ui.goal_orientation_end
            ):
                self.text_browser.append(
                    "Start of interval must be <= end. Orientation is not edited"
                )
            else:
                self.collect_goal_states(planning_problem_id=current_planning_problem_id)[
                    current_goal_state_id
                ].orientation = Interval(
                    start=math.radians(
                        self.get_float(self.scenario_toolbox_ui.goal_orientation_start)
                    ),
                    end=math.radians(self.get_float(self.scenario_toolbox_ui.goal_orientation_end)),
                )
        else:
            self.collect_goal_states(planning_problem_id=current_planning_problem_id)[
                current_goal_state_id
            ].orientation = None
            try:
                self.collect_goal_states(planning_problem_id=current_planning_problem_id)[
                    current_goal_state_id
                ].attributes.remove("orientation")
            except KeyError:
                pass

        if self.scenario_toolbox_ui.type.currentText() == "None":
            try:
                self.collect_goal_states(planning_problem_id=current_planning_problem_id)[
                    current_goal_state_id
                ].attributes.remove("position")
            except KeyError:
                pass
            self.pps_model.remove_lanelet_from_goals(
                int(self.scenario_toolbox_ui.planning_problems_list_table.currentItem().text()),
                current_goal_state_id,
            )

        elif self.scenario_toolbox_ui.type.currentText() == "Shape":
            self.collect_goal_states(planning_problem_id=current_planning_problem_id)[
                current_goal_state_id
            ].add_attribute("position")
            self.collect_goal_states(planning_problem_id=current_planning_problem_id)[
                current_goal_state_id
            ].position = self.shape_group_from_shape(self.current_shapes)
            self.pps_model.remove_lanelet_from_goals(
                int(self.scenario_toolbox_ui.planning_problems_list_table.currentItem().text()),
                current_goal_state_id,
            )

        elif self.scenario_toolbox_ui.type.currentText() == "Lanelet":
            self.collect_goal_states(planning_problem_id=current_planning_problem_id)[
                current_goal_state_id
            ].add_attribute("position")

            self.collect_goal_states(planning_problem_id=current_planning_problem_id)[
                current_goal_state_id
            ].position = self.shape_group_from_lanelets(self.current_lanelets)

            self.pps_model.get_pp(
                int(self.scenario_toolbox_ui.planning_problems_list_table.currentItem().text())
            ).goal.lanelets_of_goal_position[current_goal_state_id] = list(self.current_lanelets)

        self.pps_model.notify_all()
        self.set_goal_states_information()
        self.initialize_goal_state()

    @logger.log
    def add_goal_state_lanelet(self) -> None:
        """Add lanelet to goal state in GUI and backend (current_lanelets)"""
        selected_lanelet_button = (
            self.scenario_toolbox_ui.goal_state_position_lanelet_update.currentText()
        )
        if (
            selected_lanelet_button != "None"
            and int(selected_lanelet_button) not in self.current_lanelets
        ):
            self.current_lanelets.append(int(selected_lanelet_button))
            self.scenario_toolbox_ui.goal_states_lanelet_list_table.insertRow(
                self.scenario_toolbox_ui.goal_states_lanelet_list_table_row_count
            )
            self.scenario_toolbox_ui.goal_states_lanelet_list_table.setItem(
                self.scenario_toolbox_ui.goal_states_lanelet_list_table_row_count,
                0,
                QTableWidgetItem(selected_lanelet_button),
            )

    @logger.log
    def remove_goal_state_lanelet(self) -> None:
        """Removes shape from backend (current_lanelets) and GUI Table."""
        if (
            self.scenario_toolbox_ui.goal_states_list_table.currentRow() is not None
            and self.scenario_toolbox_ui.goal_states_list_table.currentRow() != -1
        ):
            current_goal_state_selected_lanelet = int(
                self.scenario_toolbox_ui.goal_states_lanelet_list_table.currentItem().text()
            )
            self.current_lanelets.remove(current_goal_state_selected_lanelet)
            self.scenario_toolbox_ui.goal_states_lanelet_list_table.removeRow(
                self.scenario_toolbox_ui.goal_states_lanelet_list_table.currentRow()
            )

    @logger.log
    def add_goal_state_shape(self) -> None:
        """Adds created shape to list in backend (self.current_shapes) and GUI. If adding was successful the fields
        are reset."""
        if self.scenario_toolbox_ui.planning_problems_list_table.currentItem() is None:
            self.text_browser.append("Please create and/or select a planning problem.")
            return

        if len(self.current_shapes) > 0 and isinstance(self.current_shapes[0], ShapeGroup):
            self.current_shapes = []
        selected_shape = self.scenario_toolbox_ui.goal_states_shape_selector.currentText()
        if selected_shape == "Rectangle":
            rectangle = Rectangle(
                length=self.get_float(self.scenario_toolbox_ui.rectangle_length),
                width=self.get_float(self.scenario_toolbox_ui.rectangle_width),
                center=np.array(
                    [
                        get_float_position(self.scenario_toolbox_ui.rectangle_x),
                        get_float_position(self.scenario_toolbox_ui.rectangle_y),
                    ]
                ),
                orientation=math.radians(
                    self.get_float(self.scenario_toolbox_ui.rectangle_orientation),
                ),
            )

            self.current_shapes.append(rectangle)

            self.scenario_toolbox_ui.goal_states_shape_list_table.insertRow(
                self.scenario_toolbox_ui.goal_states_shape_list_table_row_count
            )
            self.scenario_toolbox_ui.goal_states_shape_list_table.setItem(
                self.scenario_toolbox_ui.goal_states_shape_list_table_row_count,
                0,
                QTableWidgetItem(selected_shape),
            )
            self.scenario_toolbox_ui.goal_states_shape_list_table.setItem(
                self.scenario_toolbox_ui.goal_states_shape_list_table_row_count,
                1,
                QTableWidgetItem(self.str_center(rectangle.center)),
            )

            self.scenario_toolbox_ui.rectangle_length.clear()
            self.scenario_toolbox_ui.rectangle_width.clear()
            self.scenario_toolbox_ui.rectangle_x.clear()
            self.scenario_toolbox_ui.rectangle_y.clear()
            self.scenario_toolbox_ui.rectangle_orientation.clear()

        elif selected_shape == "Circle":
            circle = Circle(
                radius=self.get_float(self.scenario_toolbox_ui.circle_radius),
                center=np.array(
                    [
                        get_float_position(self.scenario_toolbox_ui.circle_x),
                        get_float_position(self.scenario_toolbox_ui.circle_y),
                    ]
                ),
            )

            self.current_shapes.append(circle)

            self.scenario_toolbox_ui.goal_states_shape_list_table.insertRow(
                self.scenario_toolbox_ui.goal_states_shape_list_table_row_count
            )
            self.scenario_toolbox_ui.goal_states_shape_list_table.setItem(
                self.scenario_toolbox_ui.goal_states_shape_list_table_row_count,
                0,
                QTableWidgetItem(selected_shape),
            )
            self.scenario_toolbox_ui.goal_states_shape_list_table.setItem(
                self.scenario_toolbox_ui.goal_states_shape_list_table_row_count,
                1,
                QTableWidgetItem(self.str_center(circle.center)),
            )

            self.scenario_toolbox_ui.circle_radius.clear()
            self.scenario_toolbox_ui.circle_x.clear()
            self.scenario_toolbox_ui.circle_y.clear()

        elif selected_shape == "Polygon":
            polygon_array = self.polygon_array()
            if polygon_array is None or len(polygon_array) < 3:
                self.text_browser.append("Add at least three verticies.")
                return
            polygon = Polygon(self.polygon_array())
            if polygon is not None:
                self.current_shapes.append(polygon)

                self.scenario_toolbox_ui.goal_states_shape_list_table.insertRow(
                    self.scenario_toolbox_ui.goal_states_shape_list_table_row_count
                )
                self.scenario_toolbox_ui.goal_states_shape_list_table.setItem(
                    self.scenario_toolbox_ui.goal_states_shape_list_table_row_count,
                    0,
                    QTableWidgetItem(selected_shape),
                )
                self.scenario_toolbox_ui.goal_states_shape_list_table.setItem(
                    self.scenario_toolbox_ui.goal_states_shape_list_table_row_count,
                    1,
                    QTableWidgetItem(self.str_center(polygon.center)),
                )

                for i in range(self.scenario_toolbox_ui.amount_vertices):
                    self.scenario_toolbox_ui.vertices_x[i].clear()
                    self.scenario_toolbox_ui.vertices_y[i].clear()

    @logger.log
    def remove_goal_state_shape(self) -> None:
        """Removes shape from backend (current_shapes) and GUI Table."""
        if (
            self.scenario_toolbox_ui.goal_states_shape_list_table.currentRow() is not None
            and self.scenario_toolbox_ui.goal_states_shape_list_table.currentRow() != -1
        ):
            self.current_shapes.pop(
                len(self.current_shapes)
                - self.scenario_toolbox_ui.goal_states_shape_list_table.currentRow()
                - 1
            )
            self.scenario_toolbox_ui.goal_states_shape_list_table.removeRow(
                self.scenario_toolbox_ui.goal_states_shape_list_table.currentRow()
            )

    @logger.log
    def update_goal_state_shape(self) -> None:
        """Updates the selected shape with the new shape values. If no shape is selected a new one is created. Goal
        State is not automatically updated with the new shape values!"""
        if self.scenario_toolbox_ui.planning_problems_list_table.currentItem() is None:
            self.text_browser.append("Please create and/or select a planning problem.")
            return

        self.remove_goal_state_shape()
        self.add_goal_state_shape()

    """Goal State GUI Management"""

    def set_goal_states_information(self) -> None:
        """updates goal states table with data from the selected planning problem"""
        self.scenario_toolbox_ui.goal_states_list_table.setRowCount(0)
        goal_states = self.collect_goal_states(
            planning_problem_id=int(
                self.scenario_toolbox_ui.planning_problems_list_table.currentItem().text()
            )
        )
        index = 0
        for goal_state in goal_states:
            self.scenario_toolbox_ui.goal_states_list_table.insertRow(
                self.scenario_toolbox_ui.goal_states_list_list_table_row_count
            )
            if goal_state.has_value("time_step"):
                self.scenario_toolbox_ui.goal_states_list_table.setItem(
                    self.scenario_toolbox_ui.goal_states_list_list_table_row_count,
                    0,
                    QTableWidgetItem(
                        "["
                        + str(goal_state.time_step.start)
                        + " ; "
                        + str(goal_state.time_step.end)
                        + "]"
                    ),
                )
            else:
                self.scenario_toolbox_ui.goal_states_list_table.setItem(
                    self.scenario_toolbox_ui.goal_states_list_list_table_row_count,
                    0,
                    QTableWidgetItem("None"),
                )
            if goal_state.has_value("position"):
                if self.pps_model.is_position_a_lanelet(
                    int(self.scenario_toolbox_ui.planning_problems_list_table.currentItem().text()),
                    index,
                ):
                    self.scenario_toolbox_ui.goal_states_list_table.setItem(
                        self.scenario_toolbox_ui.goal_states_list_list_table_row_count,
                        1,
                        QTableWidgetItem("Lanelet"),
                    )
                else:
                    self.scenario_toolbox_ui.goal_states_list_table.setItem(
                        self.scenario_toolbox_ui.goal_states_list_list_table_row_count,
                        1,
                        QTableWidgetItem(str(goal_state.position).split(":")[0]),
                    )
            else:
                self.scenario_toolbox_ui.goal_states_list_table.setItem(
                    self.scenario_toolbox_ui.goal_states_list_list_table_row_count,
                    1,
                    QTableWidgetItem("None"),
                )
            if goal_state.has_value("orientation"):
                self.scenario_toolbox_ui.goal_states_list_table.setItem(
                    self.scenario_toolbox_ui.goal_states_list_list_table_row_count,
                    2,
                    QTableWidgetItem(
                        "["
                        + str(math.degrees(goal_state.orientation.start))
                        + " ; "
                        + str(math.degrees(goal_state.orientation.end))
                        + "]"
                    ),
                )
            else:
                self.scenario_toolbox_ui.goal_states_list_table.setItem(
                    self.scenario_toolbox_ui.goal_states_list_list_table_row_count,
                    2,
                    QTableWidgetItem("None"),
                )
            if goal_state.has_value("velocity"):
                self.scenario_toolbox_ui.goal_states_list_table.setItem(
                    self.scenario_toolbox_ui.goal_states_list_list_table_row_count,
                    3,
                    QTableWidgetItem(
                        "["
                        + str(goal_state.velocity.start)
                        + " ; "
                        + str(goal_state.velocity.end)
                        + "]"
                    ),
                )
            else:
                self.scenario_toolbox_ui.goal_states_list_table.setItem(
                    self.scenario_toolbox_ui.goal_states_list_list_table_row_count,
                    3,
                    QTableWidgetItem("None"),
                )
            index += 1

    def set_goal_state_information(self) -> None:
        """updates goal state widget with data from the selected planning problem and goal state"""
        if (
            self.scenario_toolbox_ui.goal_states_list_table.currentItem() is not None
            and self.scenario_toolbox_ui.goal_states_list_table.currentRow() != -1
            and self.scenario_toolbox_ui.planning_problems_list_table.currentItem() is not None
        ):
            current_planning_problem_id = int(
                self.scenario_toolbox_ui.planning_problems_list_table.currentItem().text()
            )

            current_goal_state_id = (
                len(self.collect_goal_states(planning_problem_id=current_planning_problem_id))
                - self.scenario_toolbox_ui.goal_states_list_table.currentRow()
                - 1
            )

            goal_state = self.collect_goal_states(planning_problem_id=current_planning_problem_id)[
                current_goal_state_id
            ]
            if goal_state.has_value("time_step"):
                self.scenario_toolbox_ui.goal_time_start.setText(str(goal_state.time_step.start))
                self.scenario_toolbox_ui.goal_time_end.setText(str(goal_state.time_step.end))
            if goal_state.has_value("velocity"):
                self.scenario_toolbox_ui.goal_velocity_selected.setChecked(True)
                self.scenario_toolbox_ui.goal_velocity_start.setText(str(goal_state.velocity.start))
                self.scenario_toolbox_ui.goal_velocity_end.setText(str(goal_state.velocity.end))
            else:
                self.scenario_toolbox_ui.goal_velocity_selected.setChecked(False)
                self.scenario_toolbox_ui.goal_velocity_start.setText(str(0.0))
                self.scenario_toolbox_ui.goal_velocity_end.setText(str(0.0))
            if goal_state.has_value("orientation"):
                self.scenario_toolbox_ui.goal_orientation_selected.setChecked(True)
                self.scenario_toolbox_ui.goal_orientation_start.setText(
                    str(math.degrees(goal_state.orientation.start))
                )
                self.scenario_toolbox_ui.goal_orientation_end.setText(
                    str(math.degrees(goal_state.orientation.end))
                )
            else:
                self.scenario_toolbox_ui.goal_orientation_selected.setChecked(False)
                self.scenario_toolbox_ui.goal_orientation_start.setText(str(0.0))
                self.scenario_toolbox_ui.goal_orientation_end.setText(str(0.0))
            if goal_state.has_value("position"):
                if goal_state.position is None:
                    self.scenario_toolbox_ui.type.setCurrentText("None")
                elif self.pps_model.is_position_a_lanelet(
                    current_planning_problem_id, current_goal_state_id
                ):
                    self.scenario_toolbox_ui.type.setCurrentText("Lanelet")
                    self.set_goal_state_lanelet_information()
                else:
                    self.scenario_toolbox_ui.type.setCurrentText("Shape")
                    self.set_goal_state_information_toggle_type()
            else:
                self.scenario_toolbox_ui.type.setCurrentText("None")
                self.scenario_toolbox_ui.toggle_goal_state_position_type()

    @logger.log
    def set_goal_state_information_toggle_type(self) -> None:
        """Adds and removes widgets corresponding to the selected type."""
        self.scenario_toolbox_ui.toggle_goal_state_position_type()
        if self.scenario_toolbox_ui.type.currentText() != "Shape":
            self.scenario_toolbox_ui.remove_rectangle_fields()
            self.scenario_toolbox_ui.remove_circle_fields()
            self.scenario_toolbox_ui.remove_polygon_fields()
        if self.scenario_toolbox_ui.type.currentText() == "Lanelet":
            lanelet_ids = self.collect_lanelet_ids()
            if len(lanelet_ids) == 0:
                self.scenario_toolbox_ui.goal_state_position_lanelet_update.addItems(["None"])
            else:
                self.scenario_toolbox_ui.goal_state_position_lanelet_update.addItems(
                    [str(item) for item in lanelet_ids]
                )
            self.current_lanelets = []
            self.scenario_toolbox_ui.goal_state_position_lanelet_update.setCurrentIndex(0)
            self.scenario_toolbox_ui.button_goal_state_position_add_lanelet.clicked.connect(
                lambda: self.add_goal_state_lanelet()
            )
            self.scenario_toolbox_ui.button_goal_state_position_remove_lanelet.clicked.connect(
                lambda: self.remove_goal_state_lanelet()
            )

        elif self.scenario_toolbox_ui.type.currentText() == "Shape":
            if self.scenario_toolbox_ui.planning_problems_list_table.currentItem() is None:
                self.text_browser.append("Select a planning problem first.")
                self.scenario_toolbox_ui.type.setCurrentText("None")
                return

            current_planning_problem_id = int(
                self.scenario_toolbox_ui.planning_problems_list_table.currentItem().text()
            )

            current_goal_state_id = (
                len(self.collect_goal_states(planning_problem_id=current_planning_problem_id))
                - self.scenario_toolbox_ui.goal_states_list_table.currentRow()
                - 1
            )

            if self.scenario_toolbox_ui.goal_states_list_table.currentItem() is not None:
                current_goal_state_id = (
                    len(self.collect_goal_states(planning_problem_id=current_planning_problem_id))
                    - self.scenario_toolbox_ui.goal_states_list_table.currentRow()
                    - 1
                )
                goal_state = self.pps_model.get_pp(current_planning_problem_id).goal.state_list[
                    current_goal_state_id
                ]

                if goal_state.has_value("position"):
                    if isinstance(goal_state.position, ShapeGroup):
                        self.current_shapes = goal_state.position.shapes
                    else:
                        self.current_shapes = [goal_state.position]
                else:
                    self.current_shapes = []
            else:
                self.current_shapes = []

            for shape in self.current_shapes:
                if not isinstance(shape, ShapeGroup):
                    type = ""
                    if isinstance(shape, Rectangle):
                        type = "Rectangle"
                    elif isinstance(shape, Circle):
                        type = "Circle"
                    elif isinstance(shape, Polygon):
                        type = "Polygon"
                    self.scenario_toolbox_ui.goal_states_shape_list_table.insertRow(
                        self.scenario_toolbox_ui.goal_states_shape_list_table_row_count
                    )
                    self.scenario_toolbox_ui.goal_states_shape_list_table.setItem(
                        self.scenario_toolbox_ui.goal_states_shape_list_table_row_count,
                        0,
                        QTableWidgetItem(type),
                    )
                    self.scenario_toolbox_ui.goal_states_shape_list_table.setItem(
                        self.scenario_toolbox_ui.goal_states_shape_list_table_row_count,
                        1,
                        QTableWidgetItem(self.str_center(shape.center)),
                    )
            self.set_goal_state_information_toggle_shape()
            self.scenario_toolbox_ui.goal_states_shape_list_table.currentCellChanged.connect(
                lambda: self.set_goal_state_shape_information()
            )
            self.scenario_toolbox_ui.goal_states_shape_selector.currentTextChanged.connect(
                lambda: self.set_goal_state_information_toggle_shape()
            )
            self.scenario_toolbox_ui.button_goal_state_position_add_shape.clicked.connect(
                lambda: self.add_goal_state_shape()
            )
            self.scenario_toolbox_ui.button_goal_state_position_remove_shape.clicked.connect(
                lambda: self.remove_goal_state_shape()
            )
            self.scenario_toolbox_ui.button_goal_state_position_update_shape.clicked.connect(
                lambda: self.update_goal_state_shape()
            )

    @logger.log
    def set_goal_state_information_toggle_shape(self) -> None:
        """Adds and removes widgets corresponding to the selected shape."""
        self.scenario_toolbox_ui.toggle_sections_shape()

    @logger.log
    def set_goal_state_shape_information(self) -> None:
        """Updates shape information of the selected goal state position."""
        if (
            self.scenario_toolbox_ui.goal_states_shape_list_table.currentRow() is not None
            and self.scenario_toolbox_ui.goal_states_shape_list_table.currentRow() != -1
            and self.scenario_toolbox_ui.planning_problems_list_table.currentRow() is not None
            and self.scenario_toolbox_ui.planning_problems_list_table.currentRow() != -1
        ):
            current_shape = self.current_shapes[
                len(self.current_shapes)
                - self.scenario_toolbox_ui.goal_states_shape_list_table.currentRow()
                - 1
            ]
            if isinstance(current_shape, Rectangle):
                self.scenario_toolbox_ui.goal_states_shape_selector.setCurrentText("Rectangle")
                self.set_goal_state_information_toggle_shape()
                self.scenario_toolbox_ui.rectangle_x.setText(str(current_shape.center[0]))
                self.scenario_toolbox_ui.rectangle_y.setText(str(current_shape.center[1]))
                self.scenario_toolbox_ui.rectangle_length.setText(str(current_shape.length))
                self.scenario_toolbox_ui.rectangle_width.setText(str(current_shape.width))
                self.scenario_toolbox_ui.rectangle_orientation.setText(
                    str(math.degrees(current_shape.orientation))
                )
            elif isinstance(current_shape, Circle):
                self.scenario_toolbox_ui.goal_states_shape_selector.setCurrentText("Circle")
                self.set_goal_state_information_toggle_shape()
                self.scenario_toolbox_ui.circle_radius.setText(str(current_shape.radius))
                self.scenario_toolbox_ui.circle_x.setText(str(current_shape.center[0]))
                self.scenario_toolbox_ui.circle_y.setText(str(current_shape.center[1]))
            elif isinstance(current_shape, Polygon):
                self.scenario_toolbox_ui.goal_states_shape_selector.setCurrentText("Polygon")
                self.set_goal_state_information_toggle_shape()
                index = 0
                for vertice in current_shape.vertices:
                    if index == len(current_shape.vertices) - 1:
                        continue
                    if index >= 3:
                        self.scenario_toolbox_ui.add_vertice()
                    self.scenario_toolbox_ui.vertices_x[index].setText(str(vertice[0]))
                    self.scenario_toolbox_ui.vertices_y[index].setText(str(vertice[1]))
                    index += 1

    @logger.log
    def set_goal_state_lanelet_information(self) -> None:
        """Updates lanelet information of the selected goal state position."""
        if (
            self.scenario_toolbox_ui.goal_states_list_table.currentRow() is not None
            and self.scenario_toolbox_ui.goal_states_list_table.currentRow() != -1
            and self.scenario_toolbox_ui.planning_problems_list_table.currentRow() is not None
            and self.scenario_toolbox_ui.planning_problems_list_table.currentRow() != -1
        ):
            self.set_goal_state_information_toggle_type()

            current_planning_problem_id = int(
                self.scenario_toolbox_ui.planning_problems_list_table.currentItem().text()
            )

            current_goal_state_id = (
                len(self.collect_goal_states(planning_problem_id=current_planning_problem_id))
                - self.scenario_toolbox_ui.goal_states_list_table.currentRow()
                - 1
            )

            self.current_lanelets = self.pps_model.get_pp(
                int(self.scenario_toolbox_ui.planning_problems_list_table.currentItem().text())
            ).goal.lanelets_of_goal_position.get(current_goal_state_id)

            for lanelet in self.current_lanelets:
                item = QTableWidgetItem(str(lanelet))
                self.scenario_toolbox_ui.goal_states_lanelet_list_table.insertRow(
                    self.scenario_toolbox_ui.goal_states_lanelet_list_table_row_count
                )
                self.scenario_toolbox_ui.goal_states_lanelet_list_table.setItem(
                    self.scenario_toolbox_ui.goal_states_lanelet_list_table_row_count,
                    0,
                    item,
                )

    """
    Intial State
    """

    def collect_initial_state(self, planning_problem_id: int) -> InitialState:
        """returns the initial state of selected planning problem"""
        return self.pps_model.get_pp(planning_problem_id).initial_state

    """Initial State Data Management"""

    @logger.log
    def update_initial_state(self) -> None:
        """updates initial state of selected planning problem. If no planning problem is selected new planning
        problem is created"""
        if self.mwindow.play_activated:
            self.text_browser.append("Please stop the animation first.")
            return

        if self.scenario_toolbox_ui.planning_problems_list_table.currentItem() is None:
            self.text_browser.append("Please create and/or select a planning problem.")
            return

        """update initial state of planning problem"""
        current_planning_problem_id = int(
            self.scenario_toolbox_ui.planning_problems_list_table.currentItem().text()
        )
        self.collect_initial_state(planning_problem_id=current_planning_problem_id).position[0] = (
            self.get_float(self.scenario_toolbox_ui.initial_position_x)
        )
        self.collect_initial_state(planning_problem_id=current_planning_problem_id).position[1] = (
            self.get_float(self.scenario_toolbox_ui.initial_position_y)
        )
        self.collect_initial_state(
            planning_problem_id=current_planning_problem_id
        ).velocity = self.get_float(self.scenario_toolbox_ui.initial_velocity)
        self.collect_initial_state(
            planning_problem_id=current_planning_problem_id
        ).orientation = math.radians(self.get_float(self.scenario_toolbox_ui.initial_orientation))
        self.collect_initial_state(
            planning_problem_id=current_planning_problem_id
        ).yaw_rate = self.get_float(self.scenario_toolbox_ui.initial_yawRate)
        self.collect_initial_state(
            planning_problem_id=current_planning_problem_id
        ).slip_angle = self.get_float(self.scenario_toolbox_ui.initial_slipAngle)
        self.collect_initial_state(
            planning_problem_id=current_planning_problem_id
        ).time_step = self.get_int(self.scenario_toolbox_ui.initial_time)
        self.collect_initial_state(
            planning_problem_id=current_planning_problem_id
        ).acceleration = self.get_float(self.scenario_toolbox_ui.initial_acceleration)

        self.pps_model.notify_all()

    """Initial State GUI Managment"""

    def get_float(self, entered_string: QLineEdit) -> float:
        """
        Validates number and replace , with . to be able to insert german floats
        :param entered_string: String containing float
        :return: string argument as valid float if not empty or not - else standard value 0.0
        """
        if entered_string.text() == "-":
            self.text_browser.append(
                "Inserted value of invalid. Standard value 0 will be used instead."
            )
        if entered_string.text() and entered_string.text() != "-":
            return float(entered_string.text().replace(",", "."))
        else:
            return 0.0

    def get_int(self, entered_string: QLineEdit) -> int:
        """
        Validates number and replace , with . to be able to insert int
        :param entered_string: String containing int
        :return: string argument as valid int if not empty or not - else standard value 0.0
        """
        if entered_string.text() == "-":
            self.text_browser.append(
                "Inserted value of invalid. Standard value 0 will be used instead."
            )
        if entered_string.text() and entered_string.text() != "-":
            return int(entered_string.text())
        else:
            return 0

    def collect_lanelet_ids(self) -> List[int]:
        """
        Collects IDs of all lanelets within a CommonRoad scenario.

        :return: List of lanelet IDs.
        """

        if self.current_scenario.get_current_scenario() is not None:
            return sorted(
                [
                    la.lanelet_id
                    for la in self.current_scenario.get_current_scenario().lanelet_network.lanelets
                ]
            )
        else:
            return []

    def str_center(self, center: List[float]) -> str:
        """
        Converts Center to string

        :param center: center
        :return: String of center
        """
        x = str(center[0])
        y = str(center[1])
        return "[" + x + " ; " + y + "]"

    def polygon_array(self) -> Union[List[List[float]], None]:
        """
        Stores values from gui menu as floats (vertice coordinates)

        :return: a list of the vertices from the gui menu
        """
        vertices = []
        for i in range(self.scenario_toolbox_ui.amount_vertices):
            if (
                self.scenario_toolbox_ui.vertices_x[i].text() != ""
                and self.scenario_toolbox_ui.vertices_y[i].text() != ""
            ):
                temp = [
                    get_float_position(self.scenario_toolbox_ui.vertices_x[i]),
                    get_float_position(self.scenario_toolbox_ui.vertices_y[i]),
                ]
                vertices.append(temp)

        if len(vertices) < 3:
            print("At least 3 vertices are needed to create a polygon")
            return

        vertices = np.asarray(vertices)
        return vertices

    @logger.log
    def update_settings(self) -> None:
        """initialize scenario settings widget and updates it"""
        self.init_settings = True
        if self.current_scenario.get_current_scenario() is not None:
            # self.initialized = False
            self.scenario_toolbox_ui.scenario_author.setText(
                self.current_scenario.get_current_scenario().author
            )
            self.scenario_toolbox_ui.scenario_affiliation.setText(
                self.current_scenario.get_current_scenario().affiliation
            )
            self.scenario_toolbox_ui.scenario_source.setText(
                self.current_scenario.get_current_scenario().source
            )
            self.scenario_toolbox_ui.scenario_time_step_size.setText(
                str(self.current_scenario.get_current_scenario().dt)
            )
            self.scenario_toolbox_ui.scenario_tags.set_checked_items(
                [t.value for t in self.current_scenario.get_current_scenario().tags]
                if self.current_scenario.get_current_scenario().tags
                else []
            )
            self.scenario_toolbox_ui.scenario_config_id.setValue(
                self.current_scenario.get_current_scenario().scenario_id.configuration_id
                if self.current_scenario.get_current_scenario().scenario_id.configuration_id
                else 1
            )
            self.scenario_toolbox_ui.cooperative_scenario.setChecked(
                self.current_scenario.get_current_scenario().scenario_id.cooperative
                if self.current_scenario.get_current_scenario().scenario_id.cooperative
                else False
            )
            self.scenario_toolbox_ui.country.setCurrentText(
                self.current_scenario.get_current_scenario().scenario_id.country_id
            )
            self.scenario_toolbox_ui.scenario_scene_id.setValue(
                self.current_scenario.get_current_scenario().scenario_id.map_id
            )
            self.scenario_toolbox_ui.scenario_scene_name.setText(
                self.current_scenario.get_current_scenario().scenario_id.map_name
            )
            self.scenario_toolbox_ui.prediction_type.setCurrentText(
                self.current_scenario.get_current_scenario().scenario_id.obstacle_behavior
            )
            self.scenario_toolbox_ui.scenario_prediction_id.setValue(
                self.current_scenario.get_current_scenario().scenario_id.prediction_id
                if self.current_scenario.get_current_scenario().scenario_id.prediction_id
                else 1
            )

            if self.current_scenario.get_current_scenario().location:
                self.scenario_toolbox_ui.scenario_geo_name_id.setText(
                    str(self.current_scenario.get_current_scenario().location.geo_name_id)
                )
                self.scenario_toolbox_ui.scenario_latitude.setText(
                    str(self.current_scenario.get_current_scenario().location.gps_latitude)
                )
                self.scenario_toolbox_ui.scenario_longitude.setText(
                    str(self.current_scenario.get_current_scenario().location.gps_longitude)
                )

                if self.current_scenario.get_current_scenario().location.geo_transformation:
                    if (
                        self.current_scenario.get_current_scenario().location.geo_transformation.geo_reference
                        in [
                            self.scenario_toolbox_ui.geo_reference.itemText(i)
                            for i in range(self.scenario_toolbox_ui.geo_reference.count())
                        ]
                    ):
                        self.scenario_toolbox_ui.geo_reference.setCurrentText(
                            self.current_scenario.get_current_scenario().location.geo_transformation.geo_reference
                        )
                    else:
                        self.scenario_toolbox_ui.geo_reference.addItem(
                            self.current_scenario.get_current_scenario().location.geo_transformation.geo_reference
                        )
                        self.scenario_toolbox_ui.geo_reference.setCurrentText(
                            self.current_scenario.get_current_scenario().location.geo_transformation.geo_reference
                        )

                    self.scenario_toolbox_ui.x_translation.setText(
                        str(
                            self.current_scenario.get_current_scenario().location.geo_transformation.x_translation
                        )
                    )
                    self.scenario_toolbox_ui.y_translation.setText(
                        str(
                            self.current_scenario.get_current_scenario().location.geo_transformation.y_translation
                        )
                    )

                if self.current_scenario.get_current_scenario().location.environment:
                    self.scenario_toolbox_ui.scenario_time_of_day.setCurrentText(
                        self.current_scenario.get_current_scenario().location.environment.time_of_day.value
                    )
                    self.scenario_toolbox_ui.scenario_weather.setCurrentText(
                        self.current_scenario.get_current_scenario().location.environment.weather.value
                    )
                    self.scenario_toolbox_ui.scenario_underground.setCurrentText(
                        self.current_scenario.get_current_scenario().location.environment.underground.value
                    )
                    self.scenario_toolbox_ui.scenario_time_hour.setValue(
                        self.current_scenario.get_current_scenario().location.environment.time.hours
                    )
                    self.scenario_toolbox_ui.scenario_time_minute.setValue(
                        self.current_scenario.get_current_scenario().location.environment.time.minutes
                    )

                else:
                    self.init_scenario_location_default()
            else:
                self.scenario_toolbox_ui.scenario_geo_name_id.setText("-999")
                self.scenario_toolbox_ui.scenario_latitude.setText("999")
                self.scenario_toolbox_ui.scenario_longitude.setText("999")
                self.init_scenario_location_default()  # self.initialized = True
            self.init_settings = False

    def shape_group_from_lanelets(self, lanelets: List[int]) -> ShapeGroup:
        """Creates a shape group form a list of lanelet ids.

        :param lanelets: List of lanelet ids.
        :return: Shapegroup
        """
        shapes = [
            self.current_scenario.get_current_scenario()
            .lanelet_network.find_lanelet_by_id(i)
            .polygon
            for i in lanelets
        ]
        shape_group = ShapeGroup(shapes=shapes)
        return shape_group

    def shape_group_from_shape(self, shapes: List[Shape]) -> Shape:
        """
        Creates a shape if the list contains only one Shape, otherwise a shapegroup is created

        :param shapes: List of Shapes
        :return: Shapegroup
        """
        if len(shapes) == 1:
            return shapes[0]
        else:
            shape_group = ShapeGroup(shapes=shapes)
            return shape_group

    def init_scenario_location_default(self) -> None:
        """Initializes default values of scenario settings"""
        self.scenario_toolbox_ui.scenario_time_of_day.setCurrentText(TimeOfDay.UNKNOWN.value)
        self.scenario_toolbox_ui.scenario_weather.setCurrentText(Weather.UNKNOWN.value)
        self.scenario_toolbox_ui.scenario_underground.setCurrentText(Underground.UNKNOWN.value)
        self.scenario_toolbox_ui.scenario_time_hour.setValue(0)
        self.scenario_toolbox_ui.scenario_time_minute.setValue(0)

    @logger.log
    def update_scenario_meta_data(self) -> None:
        """Updates the edited meta data in the scenario"""
        if self.mwindow.play_activated:
            self.text_browser.append("Please stop the animation first.")
            self.update_settings()
            return

        if self.init_settings is not True:
            if self.current_scenario.get_current_scenario() is not None:
                author = self.scenario_toolbox_ui.scenario_author.text()
                affiliation = self.scenario_toolbox_ui.scenario_affiliation.text()
                source = self.scenario_toolbox_ui.scenario_source.text()
                tags = [Tag(t) for t in self.scenario_toolbox_ui.scenario_tags.get_checked_items()]
                configuration_id = int(self.scenario_toolbox_ui.scenario_config_id.text())
                cooperative = self.scenario_toolbox_ui.cooperative_scenario.isChecked()
                country_id = self.scenario_toolbox_ui.country.currentText()
                map_id = int(self.scenario_toolbox_ui.scenario_scene_id.text())
                map_name = self.scenario_toolbox_ui.scenario_scene_name.text()
                obstacle_behavior = self.scenario_toolbox_ui.prediction_type.currentText()
                prediction_id = int(self.scenario_toolbox_ui.scenario_prediction_id.text())
                time_step_size = self.get_float(self.scenario_toolbox_ui.scenario_time_step_size)

                self.sl_has_empty_values()
                location = None
                if self.scenario_toolbox_ui.location_storage_selection.isChecked():
                    if self.current_scenario.get_current_scenario().location.geo_transformation:
                        location = Location(
                            int(self.scenario_toolbox_ui.scenario_geo_name_id.text()),
                            float(self.scenario_toolbox_ui.scenario_latitude.text()),
                            float(self.scenario_toolbox_ui.scenario_longitude.text()),
                            environment=Environment(
                                Time(
                                    int(self.scenario_toolbox_ui.scenario_time_hour.text()),
                                    int(self.scenario_toolbox_ui.scenario_time_minute.text()),
                                ),
                                TimeOfDay(
                                    self.scenario_toolbox_ui.scenario_time_of_day.currentText()
                                ),
                                Weather(self.scenario_toolbox_ui.scenario_weather.currentText()),
                                Underground(
                                    self.scenario_toolbox_ui.scenario_underground.currentText()
                                ),
                            ),
                            geo_transformation=GeoTransformation(
                                geo_reference=self.current_scenario.get_current_scenario().location.geo_transformation.geo_reference,
                                x_translation=self.current_scenario.get_current_scenario().location.geo_transformation.x_translation,
                                y_translation=self.current_scenario.get_current_scenario().location.geo_transformation.y_translation,
                            ),
                        )
                    else:
                        location = Location(
                            int(self.scenario_toolbox_ui.scenario_geo_name_id.text()),
                            float(self.scenario_toolbox_ui.scenario_latitude.text()),
                            float(self.scenario_toolbox_ui.scenario_longitude.text()),
                            environment=Environment(
                                Time(
                                    int(self.scenario_toolbox_ui.scenario_time_hour.text()),
                                    int(self.scenario_toolbox_ui.scenario_time_minute.text()),
                                ),
                                TimeOfDay(
                                    self.scenario_toolbox_ui.scenario_time_of_day.currentText()
                                ),
                                Weather(self.scenario_toolbox_ui.scenario_weather.currentText()),
                                Underground(
                                    self.scenario_toolbox_ui.scenario_underground.currentText()
                                ),
                            ),
                            geo_transformation=GeoTransformation(
                                geo_reference=gui_config.pseudo_mercator,
                                x_translation=0.0,
                                y_translation=0.0,
                            ),
                        )

                self.current_scenario.update_meta_data(
                    author,
                    affiliation,
                    source,
                    tags,
                    configuration_id,
                    cooperative,
                    country_id,
                    map_id,
                    map_name,
                    obstacle_behavior,
                    prediction_id,
                    time_step_size,
                    location,
                )

    def sl_has_empty_values(self) -> None:
        """Checks the scenario location for empty values if yes use default values"""
        if self.scenario_toolbox_ui.scenario_geo_name_id.text() == "":
            self.scenario_toolbox_ui.scenario_geo_name_id.setText("-999")
        if self.scenario_toolbox_ui.scenario_latitude.text() == "":
            self.scenario_toolbox_ui.scenario_latitude.setText("999")
        if self.scenario_toolbox_ui.scenario_longitude.text() == "":
            self.scenario_toolbox_ui.scenario_longitude.setText("999")

    def change_geo_reference(self):
        """
        Manages the editable option for the dropdown menu for the geo reference for the sceanrio
        """
        reference = self.scenario_toolbox_ui.geo_reference.currentText()
        if reference in [
            gui_config.utm_default,
            gui_config.pseudo_mercator,
            gui_config.lanelet2_default,
        ]:
            self.scenario_toolbox_ui.geo_reference.setEditable(False)
        else:
            self.scenario_toolbox_ui.geo_reference.setEditable(True)

    def update_scenario_location(self):
        """
        Updates the scenario geo transformation settings and if necessary starts the process for the translation
        """
        x_translation = self.get_float(self.scenario_toolbox_ui.x_translation)
        y_translation = self.get_float(self.scenario_toolbox_ui.y_translation)
        translation = np.array([x_translation, y_translation])

        self.current_scenario.update_translate_scenario(
            translation, copy.deepcopy(self.scenario_toolbox_ui.geo_reference.currentText())
        )
