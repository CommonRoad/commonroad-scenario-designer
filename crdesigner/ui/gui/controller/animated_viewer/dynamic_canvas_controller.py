import copy
import math
import warnings
from typing import List, Union

import numpy as np
import PyQt6
from commonroad.geometry.shape import Circle, Rectangle
from commonroad.planning.planning_problem import PlanningProblem
from commonroad.scenario.lanelet import Lanelet, LaneletType
from commonroad.scenario.obstacle import DynamicObstacle, StaticObstacle
from commonroad.visualization.draw_params import (
    DynamicObstacleParams,
    StaticObstacleParams,
)
from commonroad.visualization.mp_renderer import MPRenderer
from matplotlib import patches
from matplotlib import pyplot as plt
from matplotlib.backend_bases import MouseButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from numpy import ndarray
from PyQt6 import QtCore
from PyQt6.QtCore import QPoint
from PyQt6.QtGui import QCursor, QMouseEvent
from PyQt6.QtWidgets import QSizePolicy

from crdesigner.common.config.gui_config import DrawParamsCustom, gui_config
from crdesigner.common.logging import logger
from crdesigner.ui.gui.utilities.aerial_data import (
    get_aerial_image_bing,
    get_aerial_image_ldbv,
    get_aerial_image_limits,
)
from crdesigner.ui.gui.utilities.helper import (
    _merge_dict,
    angle_between,
    calculate_closest_vertices,
    calculate_euclidean_distance,
    draw_lanelet_polygon,
)
from crdesigner.ui.gui.utilities.map_creator import MapCreator
from crdesigner.ui.gui.utilities.scenario_resizer import resize_lanelet_network
from crdesigner.ui.gui.utilities.toolbox_ui import PosB

ZOOM_FACTOR = 1.2


class DynamicCanvasController(FigureCanvas):
    """
    This canvas provides zoom with the mouse wheel.
    """

    obstacle_color_array = []
    control_key = False
    show_aerial = False

    def __init__(
        self, parent=None, scenario_model=None, width=5, height=5, dpi=100, animated_viewer=None
    ):
        self.scenario_model = scenario_model
        self.image_limits = None
        self.current_aerial_image = None
        self.initial_limits = None
        self.flag = False
        if parent is not None:
            self.flag = True
        self.animated_viewer = animated_viewer
        self.ax = None
        self.drawer = Figure(figsize=(width, height), dpi=dpi)
        self.drawer.set_facecolor("None")
        self.drawer.set_edgecolor("None")
        self.rnd = MPRenderer(ax=self.ax)
        # Ignore the warning which shows up if the figure layout has changed produced by the method drawer.tight_layout()
        warnings.filterwarnings("ignore", message="The figure layout has changed to tight")

        self._handles = {}
        self.initial_parameter_config_done = (
            False  # This is used to only once set the parameter based on the scenario
        )
        self.draw_params = None  # needed later - here for reference
        # used for efficiently monitoring of we switched from detailed to undetailed params
        self.selected_l_ids = []
        self.selected_lanelets = []
        self.last_changed_sth = False
        self.latest_mouse_pos = (
            None  # used to store the last mouse position where a lanelet was clicked
        )
        self.motion_notify_event_cid = None  # store mpl function to (dis-)connect event

        self.preview_line_object = None  # preview line when splitting a lanelet
        self.split_index = None  # index at which to split in the array

        self.draw_lanelet_first_point = None  # drawing mode
        self.draw_lanelet_first_point_object = None
        self.draw_lanelet_preview = None
        self.draw_append_lanelet_preview = None
        self.add_to_selected_preview = None
        self.add_to_selected = None

        self.draw_temporary_points = {}
        self.num_lanelets = 0
        self.aerial_map_bounds = (48.263864, 11.655410, 48.261424, 11.660930)
        self.show_aerial = False

        # Cropping mode rectangle
        self.coordinates_rectangle = [[0, 0], [0, 0]]
        self.rectangle_crop = None

        super().__init__(self.drawer)

        self._parent = parent
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Set focus on canvas to detect key press events
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
        self.setFocus()
        # any callbacks for interaction per mouse
        self.button_press_event_cid = self.mpl_connect(
            "button_press_event", self.dynamic_canvas_click_callback
        )
        self.button_release_event_cid = self.mpl_connect(
            "button_release_event", self.dynamic_canvas_release_callback
        )
        self.mpl_connect("scroll_event", self.zoom)

        # any callbacks for interaction per keyboard
        self.mpl_connect("key_press_event", self.dynamic_canvas_ctrl_press_callback)
        self.mpl_connect("key_release_event", self.dynamic_canvas_ctrl_release_callback)

        # initializes mouse coordinates
        self.mouse_coordinates = QPoint(0, 0)

        self.clear_axes()

        # Parameters for curved lanelet adding
        self.button_is_checked = False
        self.current_edited_lanelet_scenario = None
        self.temp_edited_lanelet = None
        self.circle_radius = None
        self.circle_angle = None
        self.new_lanelet = False

        # Parameters for show vertices
        self.right_scatter = None
        self.left_scatter = None
        self.left_vertices = None
        self.right_vertices = None

        gui_config.sub_curved(self.enable)

    def parent(self):
        return self._parent

    @logger.log
    def keyPressEvent(self, event):
        """
        On key press activate an event
        :param event: key press event
        :return:
        """
        if self.flag is True:
            # on backspace delete selected lanelet
            if event.key() == QtCore.Qt.Key.Key_Backspace:
                self._parent.road_network_toolbox.lanelet_controller.remove_lanelet()
                return
            # on DEL key delete selected lanelet
            elif event.key() == QtCore.Qt.Key.Key_Delete:
                self._parent.road_network_toolbox.lanelet_controller.remove_lanelet()
                return

    def clear_axes(self, keep_limits=False, clear_artists=False):
        if clear_artists:
            self.rnd.clear()

        if self.ax:
            limits = self.get_limits()
            self.ax.clear()
        else:
            limits = None
            self.ax = self.drawer.add_subplot(111)

        self.ax.set_aspect("equal", "datalim")
        self.ax.set_axis_off()
        self.draw_idle()
        if keep_limits and limits:
            self.set_limits(limits)
            self.draw_idle()

    def get_axes(self):
        return self.ax

    def get_limits(self) -> List[float]:
        x_lim = self.ax.get_xlim()
        y_lim = self.ax.get_ylim()
        return [x_lim[0], x_lim[1], y_lim[0], y_lim[1]]

    def set_limits(self, limits: List[float] = None):
        """
        sets the limits of the plot axis to the given parameter
        :param limits: array in the form [x_min, x_max, y_min, y_max] indicating the axis limits
        """
        self.ax.set(xlim=limits[0:2], ylim=limits[2:4])

    @logger.log
    def zoom(self, event):
        """
        Zoom in / out function in Dynamic Canvas by using mouse wheel.
        """
        if self.animated_viewer.original_lanelet_network is None:
            return  # if no scenario was loaded or no map was created yet

        center, x_dim, y_dim, _, _ = self.get_center_and_axes_values()

        # enlarge / shrink limits
        if event.button == "up":
            new_x_dim = x_dim / ZOOM_FACTOR
            new_y_dim = y_dim / ZOOM_FACTOR
        elif event.button == "down":
            new_x_dim = x_dim * ZOOM_FACTOR
            new_y_dim = y_dim * ZOOM_FACTOR
        else:
            return

        # new center sensitive to mouse position of zoom event
        mouse_pos = (event.xdata, event.ydata)
        if mouse_pos[0] and mouse_pos[1]:
            new_center_diff_x = (center[0] - mouse_pos[0]) / 6
            new_center_diff_y = (center[1] - mouse_pos[1]) / 6
            if event.button == "up":
                new_center_x = center[0] - new_center_diff_x
                new_center_y = center[1] - new_center_diff_y
            else:
                new_center_x = center[0] + new_center_diff_x
                new_center_y = center[1] + new_center_diff_y
            # new limits should include old limits if zooming out
            # old limits should include new limits if zooming in
            dim_diff_x = abs(new_x_dim - x_dim)
            dim_diff_y = abs(new_y_dim - y_dim)
            new_center_x = min(max(center[0] - dim_diff_x, new_center_x), center[0] + dim_diff_x)
            new_center_y = min(max(center[1] - dim_diff_y, new_center_y), center[1] + dim_diff_y)
        else:
            new_center_x = center[0]
            new_center_y = center[1]
        # update the parameters for drawing based on the zoom -> this is for performance,
        # not all details need to be rendered when you are zoomed out
        gui_config.set_zoom_treshold(x=new_x_dim, y=new_y_dim)
        lanelet_network, resized_lanelet_network = resize_lanelet_network(
            original_lanelet_network=self.animated_viewer.original_lanelet_network,
            center_x=new_center_x,
            center_y=new_center_y,
            dim_x=new_x_dim,
            dim_y=new_y_dim,
        )
        self.scenario_model.replace_lanelet_network(copy.deepcopy(lanelet_network))
        self.set_limits(
            [
                new_center_x - new_x_dim,
                new_center_x + new_x_dim,
                new_center_y - new_y_dim,
                new_center_y + new_y_dim,
            ]
        )
        self.draw_idle()
        if resized_lanelet_network or self.last_changed_sth:
            if self.latest_mouse_pos is None:
                self.animated_viewer.update_plot()
            self._select_lanelet(True)

        self.last_changed_sth = resized_lanelet_network
        # now also show any selected
        # self._select_lanelet(True)

    def draw_scenario(
        self,
        pps: PlanningProblem = None,
        draw_params: DrawParamsCustom = DrawParamsCustom(),
        plot_limits=None,
        draw_dynamic_only: bool = False,
        time_begin=None,
    ):
        """[summary]
        :param pps: PlanningProblem of the scenario, defaults to None
        :param draw_params: [description], defaults to None
        :param plot_limits: [description], defaults to None
        :param draw_dynamic_only: reuses static artists
        """
        if self.current_edited_lanelet_scenario is None:
            current_scenario = self.scenario_model.get_current_scenario()
        else:
            current_scenario = self.current_edited_lanelet_scenario
        # want to update immediatly if change gui settings
        lanelet_count = len(current_scenario.lanelet_network.lanelets)
        traffic_signs_count = len(current_scenario.lanelet_network.traffic_signs)
        if not draw_dynamic_only:
            draw_params = gui_config.get_draw_params()
            if time_begin is not None:
                draw_params.time_begin = time_begin
            else:
                draw_params.time_begin = max(
                    0, self.parent().animated_viewer_wrapper.cr_viewer.time_step.value
                )
            draw_params.time_end = draw_params.time_begin

        lanelet_params = gui_config.get_undetailed_params(lanelet_count, traffic_signs_count)

        if lanelet_params is not None:
            draw_params.lanelet_network.lanelet = lanelet_params

        if not gui_config.show_dynamic_obstacles():
            draw_params.time_begin = -1
            draw_params.dynamic_obstacle.trajectory.draw_trajectory = False

        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        # update the parameters based on the number of lanelets and traffic signs - but only once during starting
        if not self.initial_parameter_config_done:
            self.draw_params = gui_config.get_draw_params()
            self.initial_parameter_config_done = True
        if draw_dynamic_only is True:
            self.rnd.remove_dynamic()  # self.rnd.ax.clear()  # self.ax.clear()
        else:
            self.ax.clear()

        draw_params_merged = copy.deepcopy(draw_params)
        self.rnd.plot_limits = plot_limits
        self.rnd.ax = self.ax
        if draw_dynamic_only:
            current_scenario.draw(renderer=self.rnd, draw_params=draw_params_merged)
            self.draw_obstacles(draw_params=draw_params_merged)
            self.rnd.render(keep_static_artists=True)
        else:
            current_scenario.draw(renderer=self.rnd, draw_params=draw_params_merged)
            if pps is not None:
                pps.draw(renderer=self.rnd, draw_params=draw_params_merged)
            self.draw_obstacles(draw_params=draw_params_merged)
            self.rnd.render(keep_static_artists=False)

        if not plot_limits:
            self.ax.set(xlim=xlim)
            self.ax.set(ylim=ylim)

        self.rnd.ax.set_facecolor(draw_params.color_schema.second_background)

        if draw_params.color_schema.axis == "Left/ Bottom":
            self.ax.spines["bottom"].set_color(draw_params.color_schema.color)
            self.ax.spines["left"].set_color(draw_params.color_schema.color)
            self.ax.spines["top"].set_color(draw_params.color_schema.second_background)
            self.ax.spines["right"].set_color(draw_params.color_schema.second_background)
            self.ax.tick_params(axis="x", colors=draw_params.color_schema.color)
            self.ax.tick_params(axis="y", colors=draw_params.color_schema.color)

        elif draw_params.color_schema.axis == "None":
            self.ax.spines["bottom"].set_color(draw_params.color_schema.second_background)
            self.ax.spines["left"].set_color(draw_params.color_schema.second_background)
            self.ax.spines["top"].set_color(draw_params.color_schema.second_background)
            self.ax.spines["right"].set_color(draw_params.color_schema.second_background)
            self.ax.tick_params(axis="x", colors=draw_params.color_schema.second_background)
            self.ax.tick_params(axis="y", colors=draw_params.color_schema.second_background)
        else:
            self.ax.spines["bottom"].set_color(draw_params.color_schema.color)
            self.ax.spines["left"].set_color(draw_params.color_schema.color)
            self.ax.spines["top"].set_color(draw_params.color_schema.color)
            self.ax.spines["right"].set_color(draw_params.color_schema.color)
            self.ax.tick_params(axis="x", colors=draw_params.color_schema.color)
            self.ax.tick_params(axis="y", colors=draw_params.color_schema.color)

        if self.show_aerial:
            self.show_aerial_image()
        if (
            self.current_edited_lanelet_scenario is not None
            and self.temp_edited_lanelet is not None
            and self.left_vertices is None
        ):
            self.draw_moving_points()

    def update_obstacles(self, draw_params=None, plot_limits=None):
        """
        Redraw only the dynamic obstacles. This gives a large performance boost, when playing an animation
        :param scenario: The scenario containing the dynamic obstacles
        :param draw_params: CommonRoad DrawParams for visualization
        :param plot_limits: Matplotlib plot limits
        """
        # redraw dynamic obstacles
        obstacles = self.scenario_model.get_obstacles_by_position_intervals(plot_limits)

        draw_params_merged = _merge_dict(self.draw_params.copy(), draw_params)

        self.rnd.ax = self.ax
        for obj in obstacles:
            obj.draw(renderer=self.rnd, draw_params=draw_params_merged)
            self.rnd.render(show=True)

    @logger.log
    def dynamic_canvas_click_callback(self, mouse_clicked_event):
        """
        General callback for clicking in the dynamic canvas, two things are checked:
        1. If the lanelet network of the current network should be resized.
        2. When a lanelet was selected execute the logger.logic behind it.
        b) Select lanelets by clicking on the canvas. Selects only one of the lanelets that contains the click
        position.
        3. Check for rightclicked. If rightclicked and lanelet selected open context menu
        This order is important - first the resizing and then the lanelet selection - otherwise the lanelets of the old
        map are selected and then not visualized.

        :params mouse_clicked_event:
        """

        # when the mouse is clicked we remember where this was -> use this for lanelet selection
        self.latest_mouse_pos = np.array([mouse_clicked_event.xdata, mouse_clicked_event.ydata])
        # update the map
        self._update_map()
        # now do the lanelet selection
        lanelet = self._select_lanelet()
        # call callback_function with latest mouse position to check if a position button is pressed
        temp_point_updated = self.animated_viewer.callback_function(
            PosB(str(self.latest_mouse_pos[0]), str(self.latest_mouse_pos[1])),
            "",
            self.draw_temporary_points,
        )
        if temp_point_updated:
            self.draw_temporary_point()
        # on right mouse click
        if mouse_clicked_event.button == 3:
            if self.flag:
                self.mouse_coordinates = QPoint(QCursor.pos().x(), QCursor.pos().y())
                # if lanelet selected
                if self._parent.road_network_toolbox.selected_lanelet() is not None:
                    # create menu
                    menu = PyQt6.QtWidgets.QMenu()
                    edit = menu.addAction("Edit Attributes")
                    edit_vertices = menu.addAction("Edit Vertices")
                    remove = menu.addAction("Remove Lanelet")
                    # open menu at mouse coordinates
                    action = menu.exec((self.mouse_coordinates))
                    # removes selected lanelet
                    if action == remove:
                        self._parent.road_network_toolbox.lanelet_controller.remove_lanelet()
                    # opens edit attributes of lanelet
                    if action == edit:
                        self._parent.road_network_toolbox.road_network_toolbox_ui.tree.collapseItem(
                            self._parent.road_network_toolbox.road_network_toolbox_ui.tree.itemAt(
                                1, 0
                            )
                        )
                        self._parent.road_network_toolbox.road_network_toolbox_ui.tree.expandItem(
                            self._parent.road_network_toolbox.road_network_toolbox_ui.tree.itemAt(
                                7, 30
                            )
                        )
                        if not self._parent.road_network_toolbox.road_network_toolbox_ui.attributes_button.toggle_checked:
                            self._parent.road_network_toolbox.road_network_toolbox_ui.attributes_button.pressed()
                    if action == edit_vertices:
                        self.show_vertices(lanelet=lanelet)

    def dynamic_canvas_release_callback(self, mouse_clicked_event):
        """
        When the mouse button is released update the map and also select lanelets (with old mouse pos).
        :params mouse_clicked_event:
        """
        # update the map
        self._update_map()
        # now do the lanelet selection
        self._select_lanelet(release=True)

    def dynamic_canvas_ctrl_press_callback(self, key_event):
        """
        Check whether control key is pressed
        """
        if key_event.key == "control":
            self.control_key = True

    def dynamic_canvas_ctrl_release_callback(self, key_event):
        if key_event.key == "control":
            self.control_key = False

    def _update_map(self):
        """
        Resized the map if necessary for performance improvement.
        """

        if self.initial_parameter_config_done:
            center, x_dim, y_dim, _, _ = self.get_center_and_axes_values()
            resized_lanelet_network, resize_necessary = resize_lanelet_network(
                original_lanelet_network=self.animated_viewer.original_lanelet_network,
                center_x=center[0],
                center_y=center[1],
                dim_x=x_dim,
                dim_y=y_dim,
            )
            if resize_necessary:
                self.scenario_model.replace_lanelet_network(resized_lanelet_network)
                self.animated_viewer.update_plot()

    def _select_lanelet(self, release: bool = False, lane_ids: list = None):
        """
        Select a lanelet and display the details in the GUI.

        :param release Boolean indicating whether function is called by click release callback
        :param lane_ids List indicating to select specified lanelets
        """
        if not self.scenario_model.scenario_created():
            return

        # as long as no new lanelet is added after adding a temporary position, no lanelet can be selected (because
        # calling update_plot removes all temporary lanelets)
        if (
            len(self.scenario_model.get_lanelets()) - self.num_lanelets != 0
            or self._parent.road_network_toolbox.updated_lanelet
        ):
            self._parent.road_network_toolbox.updated_lanelet = False
            self.draw_temporary_points = {}

        if not lane_ids:
            # check if any mousepos was setted before or the mouse position is not within the canvas
            if self.latest_mouse_pos is None or self.latest_mouse_pos[0] is None:
                return
            click_shape = Circle(radius=0.01, center=self.latest_mouse_pos)
            selected_l_id = self.scenario_model.find_lanelet_by_shape(click_shape)

            if not self.control_key:
                self.selected_l_ids = []

            if selected_l_id not in self.selected_l_ids and selected_l_id:
                self.selected_l_ids.append(selected_l_id)
                self.selected_l_ids = sorted(self.selected_l_ids)
        else:
            self.selected_l_ids = lane_ids

        self.enable_lanelet_operations(len(self.selected_l_ids))
        self.selected_lanelets = [
            self.scenario_model.find_lanelet_by_id(lid[0]) for lid in self.selected_l_ids
        ]
        selected_obstacles = [
            obs
            for obs in self.scenario_model.get_obstacles()
            if obs.occupancy_at_time(self.animated_viewer.time_step.value) is not None
            and obs.occupancy_at_time(self.animated_viewer.time_step.value).shape.contains_point(
                self.latest_mouse_pos
            )
        ]
        if len(self.selected_lanelets) > 0 and len(selected_obstacles) == 0:
            self.animated_viewer.update_plot(
                sel_lanelets=self.selected_lanelets, time_step=self.animated_viewer.time_step.value
            )
        else:
            self.animated_viewer.update_plot(
                sel_lanelets=None, time_step=self.animated_viewer.time_step.value
            )

        if not release:
            if len(self.selected_lanelets) + len(selected_obstacles) > 1:
                output = "__Info__: More than one object can be selected! Lanelets: "
                if len(self.selected_lanelets) > 0:
                    for la in self.selected_lanelets:
                        output += str(la.lanelet_id) + ", "
                output = output[: len(output) - 1]
                if len(selected_obstacles) > 0:
                    output += ". Obstacles: "
                    for obs in selected_obstacles:
                        output += str(obs.obstacle_id) + ", "
                output = output[: len(output) - 1]
                output += "."
            else:
                output = ""

            if len(selected_obstacles) > 0:
                selection = (
                    " Obstacle with ID " + str(selected_obstacles[0].obstacle_id) + " is selected."
                )
                self.animated_viewer.callback_function(selected_obstacles[0], output + selection)
            elif len(self.selected_lanelets) == 1:
                selection = (
                    " Lanelet with ID "
                    + str(self.selected_lanelets[0].lanelet_id)
                    + " is selected."
                )
                self.animated_viewer.callback_function(
                    self.selected_lanelets[0], output + selection
                )
                return self.selected_lanelets[0]
        if len(self.selected_lanelets) == 0:
            self.parent().road_network_toolbox.lanelet_controller.lanelet_ui.set_default_lanelet_information()
        self.draw_temporary_point()

    def get_center_and_axes_values(
        self,
    ) -> ((float, float), float, float, (float, float), (float, float)):
        """
        Used to get the new dimensions of the current Dynamic Canvas and other meta-data about it.

        :returns :
        center := tuple (x,y) of center,
        x_dim := half size of x-axis,
        y_dim := half size of y-axis,
        xlim := tuple of x-axis limits (x_min, x_max),
        ylim := tuple of y-axis limits (y_min, y_max)
        """
        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()
        center = ((x_min + x_max) / 2, (y_min + y_max) / 2)
        x_dim = (x_max - x_min) / 2
        y_dim = (y_max - y_min) / 2
        return center, x_dim, y_dim, (x_min, x_max), (y_min, y_max)

    def draw_obstacles(self, draw_params: DrawParamsCustom = None):
        """
        draws the obstacles
        :param scenario: current scenario
        :param: draw_params: scenario draw params, Note: does not contain
            dynamic obstacle related parameters
        """
        for obj in self.scenario_model.get_obstacles():
            # this is for getting the index of where the object_id is located
            try:
                result = next(
                    c
                    for c in DynamicCanvasController.obstacle_color_array
                    if c[0] == obj.obstacle_id
                )
                if isinstance(obj, DynamicObstacle):
                    draw_params.dynamic_obstacle.vehicle_shape.occupancy.shape.facecolor = result[2]
                elif isinstance(obj, StaticObstacle):
                    draw_params.static_obstacle.occupancy.shape.facecolor = result[2]
                draw_params_merged = draw_params

            except Exception:
                draw_params_merged = draw_params
            obj.draw(renderer=self.rnd, draw_params=draw_params_merged)

    def set_static_obstacle_color(self, obstacle_id: int, color: str = None):
        """
        sets static_obstacle color
        :param obstacle_id: id of obstacle that is to be added/updated
        :param color: color of the obstacle, None if default color
        """
        if not color:
            color = "#d95558"

        DynamicCanvasController.obstacle_color_array.append(
            [obstacle_id, self.create_static_obstacle_draw_params(color), color]
        )

    def create_static_obstacle_draw_params(self, color: str) -> StaticObstacleParams:
        """
        Creates draw parameters for static obstacle.

        :param color: Desired color of obstacle
        """
        draw_params = StaticObstacleParams()
        draw_params.occupancy.shape.facecolor = color

        return draw_params

    def create_dyn_obstacle_draw_params(self, color: str) -> DynamicObstacleParams:
        """
        Creates draw parameters for dynamic obstacle.

        :param color: Desired color of obstacle
        """
        draw_params = DynamicObstacleParams()
        draw_params.occupancy.shape.facecolor = color
        draw_params.show_label = gui_config.DRAW_OBSTACLE_LABELS
        draw_params.draw_icon = gui_config.DRAW_OBSTACLE_ICONS
        draw_params.draw_direction = gui_config.DRAW_OBSTACLE_DIRECTION
        draw_params.draw_signals = gui_config.DRAW_OBSTACLE_SIGNALS

        return draw_params

    def set_dynamic_obstacle_color(self, obstacle_id: int, color: str = None):
        """
        Sets dynamic_obstacle color.

        :param obstacle_id: id of obstacle that is to be added/updated
        :param color: color of the obstacle, None if default color
        """
        if not color:
            color = "#1d7eea"
        DynamicCanvasController.obstacle_color_array.append(
            [obstacle_id, self.create_dyn_obstacle_draw_params(color), color]
        )

    def update_obstacle_trajectory_params(self):
        """
        updates obstacles' draw params when gui settings are changed
        """

        if self.scenario_model.scenario_created():
            for obj in self.scenario_model.get_obstacles():
                try:  # check if obstacle is in obstacle_color_array
                    result = next(
                        c
                        for c in DynamicCanvasController.obstacle_color_array
                        if c[0] == obj.obstacle_id
                    )
                    color = result[2]
                    if isinstance(obj, DynamicObstacle):
                        draw_params = self.create_dyn_obstacle_draw_params(color)
                    elif isinstance(obj, StaticObstacle):
                        draw_params = self.create_static_obstacle_draw_params(color)

                    i = DynamicCanvasController.obstacle_color_array.index(result)
                    DynamicCanvasController.obstacle_color_array.pop(i)
                    DynamicCanvasController.obstacle_color_array.append(
                        [obj.obstacle_id, draw_params, color]
                    )

                except Exception:
                    if isinstance(obj, DynamicObstacle):
                        color = "#1d7eea"
                        draw_params = self.create_dyn_obstacle_draw_params(color)
                    elif isinstance(obj, StaticObstacle):
                        color = "#d95558"
                        draw_params = self.create_static_obstacle_draw_params(color)
                    DynamicCanvasController.obstacle_color_array.append(
                        [obj.obstacle_id, draw_params, color]
                    )

    def get_color(self, obstacle_id: int) -> Union[int, bool]:
        """
        :param obstacle_id: id of selected obstacle
        :return: color of current selected obstacle
        """
        try:
            result = next(c for c in self.obstacle_color_array if c[0] == obstacle_id)
            i = DynamicCanvasController.obstacle_color_array.index(result)
            return DynamicCanvasController.obstacle_color_array[i][2]
        except Exception:  # if scenario loaded and obstacle id doesn't exist in the array
            return False

    def remove_obstacle(self, obstacle_id: int):
        """
        removes obstacle from obstacle_color_array

        :param obstacle_id id of obstacle to be removed
        """
        try:
            result = next(c for c in self.obstacle_color_array if c[0] == obstacle_id)
            i = DynamicCanvasController.obstacle_color_array.index(result)
            DynamicCanvasController.obstacle_color_array.pop(i)
        except Exception:  # if scenario loaded and obstacle id doesn't exist in the array
            pass

    def activate_split_lanelet(self, is_checked: bool):
        if self.parent().play_activated:
            self.parent().road_network_toolbox.text_browser.append("Please stop the animation")
            return

        if is_checked:
            self.mpl_disconnect(self.button_press_event_cid)
            self.mpl_disconnect(self.button_release_event_cid)
            self.motion_notify_event_cid = self.mpl_connect("motion_notify_event", self.draw_line)
            self.button_press_event_cid = self.mpl_connect("button_press_event", self.split_lane)
        else:
            if self.preview_line_object:
                self.preview_line_object.pop(0).remove()
                self.draw_idle()
            self.mpl_disconnect(self.motion_notify_event_cid)
            self.mpl_disconnect(self.button_press_event_cid)
            self.button_release_event_cid = self.mpl_connect(
                "button_release_event", self.dynamic_canvas_release_callback
            )
            self.button_press_event_cid = self.mpl_connect(
                "button_press_event", self.dynamic_canvas_click_callback
            )

    def draw_line(self, mouse_move_event):
        x = mouse_move_event.xdata
        y = mouse_move_event.ydata

        if x and y and self.selected_l_ids:
            mouse_pos = np.array([x, y])
            mouse_shape = Circle(radius=0.01, center=mouse_pos)
            hovered_lanes_ids = self.scenario_model.find_lanelet_by_shape(mouse_shape)

            # Do not draw as long as we do not hover the selected Lanelet
            if not hovered_lanes_ids or hovered_lanes_ids[0] != self.selected_l_ids[0][0]:
                self.remove_line()
                return
            selected_lane = self.scenario_model.find_lanelet_by_id(self.selected_l_ids[0][0])
            shortest_distance_index = calculate_closest_vertices(
                [x, y], selected_lane.left_vertices
            )
            if (
                self.split_index == shortest_distance_index
            ):  # No need to redraw line if split index stays the same
                return
            self.remove_line()
            if (
                shortest_distance_index == 0
                or shortest_distance_index == len(selected_lane.left_vertices) - 1
            ):
                # when we hover the first or last index we are not able to split
                return

            self.split_index = shortest_distance_index
            left_adj_lane = selected_lane
            while left_adj_lane.adj_left:
                left_adj_lane = self.scenario_model.find_lanelet_by_id(left_adj_lane.adj_left)

            right_adj_lane = selected_lane
            while right_adj_lane.adj_right:
                right_adj_lane = self.scenario_model.find_lanelet_by_id(right_adj_lane.adj_right)

            left_vertex = left_adj_lane.left_vertices[self.split_index]
            right_vertex = right_adj_lane.right_vertices[self.split_index]

            self.preview_line_object = self.ax.plot(
                [left_vertex[0], right_vertex[0]],
                [left_vertex[1], right_vertex[1]],
                linestyle="dashed",
                color="blue",
                linewidth=5,
                zorder=21,
            )
            self.draw_idle()

        elif self.preview_line_object:
            self.remove_line()

    def remove_line(self):
        self.split_index = None
        if not self.preview_line_object:
            return
        self.preview_line_object.pop(0).remove()
        self.draw_idle()

    def split_lane(self, mouse_click):
        if self.split_index:
            current_lanelet = self.scenario_model.find_lanelet_by_id(self.selected_l_ids[0][0])
            MapCreator.split_lanelet(
                current_lanelet,
                self.split_index,
                self.scenario_model.get_current_scenario(),
                self.scenario_model.get_lanelet_network(),
            )
            self.scenario_model.notify_all()
            self.reset_toolbar()
            self.parent().road_network_toolbox.initialize_road_network_toolbox()

    def enable_lanelet_operations(self, number_of_selected_lanelets):
        """
        Enable or disable operations depending on the number of lanelets selected
        """
        self._parent.top_bar.toolbar_wrapper.tool_bar_ui.enable_toolbar(number_of_selected_lanelets)

    def reset_toolbar(self):
        self._parent.top_bar.toolbar_wrapper.tool_bar_ui.reset_toolbar()

    def add_adjacent(self, left_adj: bool):
        """
        Adds an adjacent lanelet to the selected lanelet

        @param left_adj: Indicator if the lanelet should be added on the left or right side of the selected lanelet
        """

        if self.parent().play_activated:
            self.parent().road_network_toolbox.text_browser.append("Please stop the animation")
            return
        if len(self.selected_lanelets) > 0:
            self._parent.road_network_toolbox.lanelet_controller.create_adjacent(
                self.selected_lanelets, left_adj
            )

    def merge_lanelets(self):
        if self.parent().play_activated:
            self.parent().road_network_toolbox.text_browser.append("Please stop the animation")
            return
        neighboured_lanelets = self.selected_lanelets.copy()
        last_merged_index = self.scenario_model.merge_lanelets_dynamic_canvas(neighboured_lanelets)

        if last_merged_index:
            self._select_lanelet(False, [[last_merged_index]])
        self.scenario_model.notify_all()
        self.parent().road_network_toolbox.initialize_road_network_toolbox()

    def activate_crop_map(self, is_active: bool) -> None:
        """
        Enables the user to draw a rectangle and keep everything inside of it

        Maps left-click to the draw_rectangle_function if the button is clicked and active, beforehand it sets the
        selected lanelets to 0 and disables the lanelet operations, otherwise it disconnect
        the callback and checks if the last_added lanelet is still in the scenario
        Afterwards initializes the toolboxes

        :param is_active: Boolean which gives the information if the button is clicked or not
        """
        if self.parent().play_activated:
            self.parent().road_network_toolbox.text_browser.append("Please stop the animation")
            return

        if is_active:
            self.selected_l_ids = []
            self.selected_lanelets = []
            self.enable_lanelet_operations(len(self.selected_l_ids))
            self.mpl_disconnect(self.button_press_event_cid)
            self.mpl_disconnect(self.button_release_event_cid)
            self.button_press_event_cid = self.mpl_connect(
                "button_press_event", self.draw_rectangle_for_cropping
            )
        else:
            self.mpl_disconnect(self.button_press_event_cid)
            self.button_release_event_cid = self.mpl_connect(
                "button_release_event", self.dynamic_canvas_release_callback
            )
            self.button_press_event_cid = self.mpl_connect(
                "button_press_event", self.dynamic_canvas_click_callback
            )
            if (
                self._parent.road_network_toolbox.last_added_lanelet_id
                not in self.scenario_model.collect_lanelet_ids()
            ):
                self._parent.road_network_toolbox.last_added_lanelet_id = None
            self.reset_toolbar()
            self._parent.road_network_toolbox.initialize_road_network_toolbox()
            self._parent.obstacle_toolbox.obstacle_toolbox_ui.initialize_obstacle_information()

    def draw_rectangle_for_cropping(self, mouse_event: QMouseEvent) -> None:
        """
        When first clicked, it sets the first corner of the rectangle and maps the Function on_mottion_rectangle
        to the mouse-movement.
        The second time it saves the second corner and calls the crop_map Function in the scenario_model

        :param mouse_event: event of the mouse -> Gives the coordinates of the mouse
        """
        if mouse_event.xdata is not None and mouse_event.ydata is not None:
            if self.rectangle_crop is None:
                x_coordinate = mouse_event.xdata
                y_coordinate = mouse_event.ydata
                self.coordinates_rectangle[0][0] = x_coordinate
                self.coordinates_rectangle[0][1] = y_coordinate
                self.rectangle_crop = patches.Rectangle(
                    (x_coordinate, y_coordinate), 0, 0, color="blue", alpha=0.3
                )
                self.ax.add_patch(self.rectangle_crop)
                self.draw_idle()
                self.motion_notify_event_cid = self.mpl_connect(
                    "motion_notify_event", self.on_motion_rectangle
                )
            else:
                self.coordinates_rectangle[1][0] = mouse_event.xdata
                self.coordinates_rectangle[1][1] = mouse_event.ydata
                length = self.coordinates_rectangle[1][0] - self.coordinates_rectangle[0][0]
                width = self.coordinates_rectangle[1][1] - self.coordinates_rectangle[0][1]
                x1, y1 = self.coordinates_rectangle[0]
                x2, y2 = self.coordinates_rectangle[1]
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                center_point = np.array([center_x, center_y])
                shape = Rectangle(length=length, width=width, center=center_point)
                self.mpl_disconnect(self.motion_notify_event_cid)
                self.rectangle_crop = None
                self.scenario_model.crop_map(shape)

    def on_motion_rectangle(self, mouse_event: QMouseEvent) -> None:
        """
        Tracks the mouse and shows the rectangle accordingly

        :param mouse_event: event of the mouse -> Gives the coordinates of the mouse
        """
        if mouse_event.xdata is not None and mouse_event.ydata is not None:
            self.coordinates_rectangle[1][0] = mouse_event.xdata
            self.coordinates_rectangle[1][1] = mouse_event.ydata
            width = self.coordinates_rectangle[1][0] - self.coordinates_rectangle[0][0]
            height = self.coordinates_rectangle[1][1] - self.coordinates_rectangle[0][1]
            self.rectangle_crop.set_width(width)
            self.rectangle_crop.set_height(height)
            self.rectangle_crop.set_xy(
                (self.coordinates_rectangle[0][0], self.coordinates_rectangle[0][1])
            )
            self.draw_idle()

    def activate_drawing_mode(self, is_active):
        if self.parent().play_activated:
            self.parent().road_network_toolbox.text_browser.append("Please stop the animation")
            return

        if is_active:
            self.mpl_disconnect(self.button_press_event_cid)
            self.mpl_disconnect(self.button_release_event_cid)
            self.button_press_event_cid = self.mpl_connect("button_press_event", self.draw_lanelet)
            self.motion_notify_event_cid = self.mpl_connect(
                "motion_notify_event", self.drawing_mode_preview_line
            )
        else:
            if self.draw_lanelet_preview:
                self.draw_lanelet_preview.pop(0).remove()
                self.draw_lanelet_first_point_object.pop(0).remove()
                self.draw_lanelet_first_point = None
                self.add_to_selected = None
            self.mpl_disconnect(self.button_press_event_cid)
            self.mpl_disconnect(self.motion_notify_event_cid)
            self.button_release_event_cid = self.mpl_connect(
                "button_release_event", self.dynamic_canvas_release_callback
            )
            self.button_press_event_cid = self.mpl_connect(
                "button_press_event", self.dynamic_canvas_click_callback
            )
            self.reset_toolbar()
            self.draw_idle()

    def draw_lanelet(self, mouse_event):
        x = mouse_event.xdata
        y = mouse_event.ydata

        if mouse_event.button == MouseButton.RIGHT:
            self.activate_drawing_mode(False)
            return

        if not self.draw_lanelet_first_point:
            if self.add_to_selected_preview:
                append_point = self.add_to_selected_preview.center_vertices[-1]
                x = append_point[0]
                y = append_point[1]
                self.add_to_selected = self.add_to_selected_preview
            self.draw_lanelet_first_point_object = self.ax.plot(
                x, y, marker="x", color="blue", zorder=21
            )
            self.draw_lanelet_first_point = [x, y]
            self.draw_idle()
        else:
            lanelet_type = {LaneletType(ty) for ty in ["None"] if ty != "None"}
            draw_lanelet_second_point = [x, y]
            lanelet_length = calculate_euclidean_distance(
                self.draw_lanelet_first_point, draw_lanelet_second_point
            )
            num_vertices = max([1, round(lanelet_length * 2)])
            try:
                if self.add_to_selected:
                    created_lanelet = MapCreator.create_straight(
                        3.0, lanelet_length, num_vertices, 10000, lanelet_type
                    )
                else:
                    created_lanelet = MapCreator.create_straight(
                        3.0,
                        lanelet_length,
                        num_vertices,
                        self.scenario_model.generate_object_id(),
                        lanelet_type,
                    )
            except AssertionError:
                output = "Length of Lanelet must be at least 1"
                self._parent.crdesigner_console_wrapper.text_browser.append(output)
                return

            drawn_vector = [
                draw_lanelet_second_point[0] - self.draw_lanelet_first_point[0],
                draw_lanelet_second_point[1] - self.draw_lanelet_first_point[1],
            ]
            horizontal_vector = [1, 0]
            angle = angle_between(drawn_vector, horizontal_vector)

            created_lanelet.translate_rotate(np.array([0, 0]), angle)
            if self.add_to_selected:
                created_lanelet.translate_rotate(np.array(draw_lanelet_second_point), 0)
                created_lanelet = MapCreator.connect_lanelets(
                    self.add_to_selected, created_lanelet, self.scenario_model.generate_object_id()
                )
                created_lanelet.successor = []
                self.add_to_selected.add_successor(created_lanelet.lanelet_id)
            else:
                created_lanelet.translate_rotate(np.array(self.draw_lanelet_first_point), 0)
            self.add_to_selected = created_lanelet
            self.scenario_model.add_lanelet([created_lanelet])
            self.parent().road_network_toolbox.initialize_road_network_toolbox()
            self._parent.road_network_toolbox.last_added_lanelet_id = created_lanelet.lanelet_id

            self.draw_lanelet_first_point = draw_lanelet_second_point
            self.draw_lanelet_first_point_object.pop(0).remove()
            self.draw_lanelet_first_point_object = self.ax.plot(
                x, y, marker="x", color="blue", zorder=21
            )

            self.draw_idle()

    def drawing_mode_preview_line(self, mouse_move_event):
        x = mouse_move_event.xdata
        y = mouse_move_event.ydata
        if not x:
            return
        if self.draw_append_lanelet_preview:
            self.draw_append_lanelet_preview.pop(0).remove()
            self.draw_append_lanelet_preview = None
            self.add_to_selected_preview = None
            self.draw_idle()
        if self.draw_lanelet_preview or (self.draw_lanelet_preview and not x and not y):
            self.draw_lanelet_preview.pop(0).remove()
        if self.draw_lanelet_first_point:
            self.draw_lanelet_preview = self.ax.plot(
                [x, self.draw_lanelet_first_point[0]],
                [y, self.draw_lanelet_first_point[1]],
                color="blue",
                zorder=21,
            )
        else:
            self.latest_mouse_pos = np.array([x, y])
            click_shape = Circle(radius=0.01, center=self.latest_mouse_pos)
            selected_l_ids = self.scenario_model.find_lanelet_by_shape(click_shape)
            if not selected_l_ids:
                return
            selected_l_id = selected_l_ids[0]
            selected_l = self.scenario_model.find_lanelet_by_id(selected_l_id)
            if not selected_l.successor:
                center_distance = calculate_euclidean_distance(
                    self.latest_mouse_pos, selected_l.center_vertices[-1]
                )
                left_distance = calculate_euclidean_distance(
                    self.latest_mouse_pos, selected_l.left_vertices[-1]
                )
                right_distance = calculate_euclidean_distance(
                    self.latest_mouse_pos, selected_l.right_vertices[-1]
                )
                if center_distance <= 1 or left_distance <= 1 or right_distance <= 1:
                    left_v = selected_l.left_vertices[-1]
                    right_v = selected_l.right_vertices[-1]
                    self.add_to_selected_preview = selected_l
                    self.draw_append_lanelet_preview = self.ax.plot(
                        [left_v[0], right_v[0]],
                        [left_v[1], right_v[1]],
                        linewidth=3,
                        color="blue",
                        zorder=21,
                    )
        self.draw_idle()

    def draw_temporary_point(self):
        if self.parent().play_activated:
            self.parent().road_network_toolbox.text_browser.append("Please stop the animation")
            return

        if not self.scenario_model.scenario_created():
            return
        for key in self.draw_temporary_points:
            (x, y) = self.draw_temporary_points[key]
            self.ax.plot(x, y, marker="x", color="blue", zorder=21)
        self.draw_idle()
        self.num_lanelets = len(self.scenario_model.get_lanelets())

    def show_aerial_image(self, new_image_added: bool = False):
        """
        shows the current (previously loaded) aerial image in the plot as a background

        :param new_image_added: Indicator if a new image has been displayed
        """
        self.ax.imshow(
            self.current_aerial_image, aspect="equal", extent=self.image_limits, alpha=0.75
        )
        if new_image_added:
            self.ax.set_xlim(self.image_limits[0], self.image_limits[1])
            self.ax.set_ylim(self.image_limits[2], self.image_limits[3])

    def activate_aerial_image(self, bing: bool, lat1: float, lon1: float, lat2: float, lon2: float):
        """
        loads the aerial image with the following gps coordinates...
        :param bing: whether image should be loaded from bing
        :param lat1: northern bound
        :param lon1: western bound
        :param lat2: southern bound
        :param lon2: eastern bound
        ...and gets the corresponding plot limits for the image
        and activates its showing in the background by setting show_aerial on True
        """
        self.update_aerial_image(lat1, lon1, lat2, lon2)
        extent = self.aerial_map_bounds
        if bing:
            self.current_aerial_image, extent = get_aerial_image_bing(self.aerial_map_bounds)
        else:
            self.current_aerial_image = get_aerial_image_ldbv(self.aerial_map_bounds)
        self.image_limits = get_aerial_image_limits(
            extent, self.scenario_model.get_current_scenario()
        )

        self.show_aerial = True

    def update_aerial_image(self, lat1: float, lon1: float, lat2: float, lon2: float):
        """
        updates the gps coordinates of the aerial image to be loaded then shown
        :param lat1: northern bound
        :param lon1: western bound
        :param lat2: southern bound
        :param lon2: eastern bound
        """
        self.aerial_map_bounds = lat1, lon1, lat2, lon2

    def deactivate_aerial_image(self):
        """
        deactivate the showing of the aerial image, called when user clicks on Remove button in road network toolbox
        """
        self.show_aerial = False
        self._update_map()

    def enable(self, enable_curved_lanelet):
        if self.parent() is not None:
            self.display_curved_lanelet(enable_curved_lanelet, self.new_lanelet)

    @logger.log
    def display_curved_lanelet(
        self, is_checked: bool, new_lanelet: bool = True, mouse_event: QMouseEvent = None
    ) -> None:
        """
        Initializes the show of the curved_lanelet preview or disables it.

        :param is_checked: boolean if the button is checked and therefore the lanelet view should be shown
        :param new_lanelet: Indicator if the lanelet already exists or is added as a new lanelet
        :param mouse_event: Mouse parameters -> to prevent if you select a lanelet in the GUI to click twice to deselect
        """
        if self.parent().play_activated:
            self.parent().road_network_toolbox.text_browser.append("Please stop the animation")
            return

        if not self.scenario_model.scenario_created():
            self.parent().road_network_toolbox.text_browser.append(
                "Please create first a new scenario"
            )
            return

        if self.parent().road_network_toolbox.road_network_toolbox_ui.connect_to_successors_selection.isChecked():
            self.parent().road_network_toolbox.text_browser.append("Preview not available yet!")
            return

        if is_checked and gui_config.enabled_curved_lanelet():
            self.button_is_checked = True
            self.new_lanelet = new_lanelet
            self.current_edited_lanelet_scenario = self.scenario_model.get_copy_of_scenario()
            self.temp_edited_lanelet = (
                self.parent().road_network_toolbox.lanelet_controller.get_lanelet_from_toolbox(
                    self.new_lanelet
                )
            )
            if self.temp_edited_lanelet is None:
                self.parent().road_network_toolbox.text_browser.append(
                    "Something went wrong! Please ensure that the information of the lanlet is given"
                )
                return
            if not new_lanelet:
                self.selected_lanelets = []
                selected_lanelet = self.scenario_model.find_lanelet_by_id(
                    int(
                        self.parent().road_network_toolbox.road_network_toolbox_ui.selected_lanelet_update.currentText()
                    )
                )
                self.selected_lanelets.append(selected_lanelet)
                self.current_edited_lanelet_scenario.remove_lanelet(selected_lanelet)
            if (
                self.current_edited_lanelet_scenario.lanelet_network.find_lanelet_by_id(
                    self.temp_edited_lanelet.lanelet_id
                )
                is not None
            ):
                self.current_edited_lanelet_scenario.remove_lanelet(self.temp_edited_lanelet)
            middle_lanelet = self.temp_edited_lanelet.center_vertices
            count_vertices = len(middle_lanelet)
            self.current_edited_lanelet_scenario.add_objects(self.temp_edited_lanelet)
            self.circle_radius = plt.Circle(
                middle_lanelet[round(count_vertices / 2)], 0.25, color="blue", zorder=100
            )
            # Code for connect to successor to change the angle dot of the angle
            # if self.parent().road_network_toolbox.road_network_toolbox_ui.connect_to_successors_selection.isChecked():
            #     self.circle_angle = plt.Circle(middle_lanelet[0], 0.25, color='blue', zorder=100)
            self.circle_angle = plt.Circle(
                middle_lanelet[count_vertices - 1], 0.25, color="blue", zorder=100
            )
            self.draw_editable_lanelet()
            self.mpl_disconnect(self.button_press_event_cid)
            self.mpl_disconnect(self.motion_notify_event_cid)
            self.button_press_event_cid = self.mpl_connect(
                "button_press_event", self.click_on_curved_lanelet
            )
            self.motion_notify_event_cid = self.mpl_connect(
                "motion_notify_event", self.move_cursor_curved_lanelet
            )
        else:
            if self.left_vertices is not None:
                return
            self.button_is_checked = False
            self.current_edited_lanelet_scenario = None
            self.mpl_disconnect(self.button_press_event_cid)
            self.mpl_disconnect(self.button_release_event_cid)
            self.mpl_disconnect(self.motion_notify_event_cid)
            self.button_release_event_cid = self.mpl_connect(
                "button_release_event", self.dynamic_canvas_release_callback
            )
            self.button_press_event_cid = self.mpl_connect(
                "button_press_event", self.dynamic_canvas_click_callback
            )
            if mouse_event is not None:
                self.dynamic_canvas_click_callback(mouse_event)
                self.dynamic_canvas_release_callback(mouse_event)
            self.draw_scenario()
            self.draw()

    def draw_editable_lanelet(self) -> None:
        """
        Draws the temporary scenario with the curved lanelet. Collects the information of the lanelet of the
        lanelet-Controller, deletes the old temporary lanelet of the temmporary scenario and adds it with the updated
        properties.
        """
        if self.temp_edited_lanelet is None or self.current_edited_lanelet_scenario is None:
            return
        if self.right_vertices is None:
            self.temp_edited_lanelet = (
                self.parent().road_network_toolbox.lanelet_controller.get_lanelet_from_toolbox(
                    self.new_lanelet
                )
            )

        if (
            self.current_edited_lanelet_scenario.lanelet_network.find_lanelet_by_id(
                self.temp_edited_lanelet.lanelet_id
            )
            is not None
        ):
            self.current_edited_lanelet_scenario.remove_lanelet(self.temp_edited_lanelet)

        self.current_edited_lanelet_scenario.add_objects(self.temp_edited_lanelet)
        self.draw_scenario()

        if not self.new_lanelet:
            for lanelet in self.scenario_model.get_lanelets():
                color, alpha, zorder, label = self.animated_viewer.get_paint_parameters(
                    lanelet, self.selected_lanelets, None
                )
                if lanelet.lanelet_id == self.selected_lanelets[0].lanelet_id:
                    draw_lanelet_polygon(
                        self.temp_edited_lanelet, self.ax, color, alpha, zorder, label
                    )
                    self.animated_viewer.view.draw_lanelet_vertices(
                        self.temp_edited_lanelet, self.ax
                    )
                else:
                    if color == "gray":
                        continue

                    draw_lanelet_polygon(lanelet, self.ax, color, alpha, zorder, label)
                    self.animated_viewer.view.draw_lanelet_vertices(lanelet, self.ax)

            handles, labels = self.ax.get_legend_handles_labels()

            legend = self.ax.legend(handles, labels)
            legend.set_zorder(50)
            self.draw_idle()

    def draw_moving_points(self) -> None:
        """
        Draw the Points to manipulate the radius or angle of the lanelet
        """
        middle_lanelet = self.temp_edited_lanelet.center_vertices
        count_vertices = len(middle_lanelet)
        self.circle_radius.set_center(middle_lanelet[round(count_vertices / 2)])

        # Code for adding a successor
        # if self.parent().road_network_toolbox.road_network_toolbox_ui.connect_to_successors_selection.isChecked():
        #     self.circle_angle.set_center(middle_lanelet[0])
        self.circle_angle.set_center(middle_lanelet[count_vertices - 1])

        self.ax.add_patch(self.circle_radius)
        self.ax.add_patch(self.circle_angle)
        self.draw()

    def change_direction_of_curve(self) -> None:
        """
        changes direction of a curved lanelet

        :param left_curve: boolean if the curve should be a left turn. If False it is a right turn
        """
        if self.new_lanelet:
            lanelet_angle = self.parent().road_network_toolbox.get_float(
                self.parent().road_network_toolbox.road_network_toolbox_ui.lanelet_angle
            )
            if lanelet_angle < 0:
                self.parent().road_network_toolbox.road_network_toolbox_ui.lanelet_angle.setText(
                    str(abs(lanelet_angle))
                )
            else:
                self.parent().road_network_toolbox.road_network_toolbox_ui.lanelet_angle.setText(
                    "-" + str(abs(lanelet_angle))
                )
        else:
            lanelet_angle = self.parent().road_network_toolbox.get_float(
                self.parent().road_network_toolbox.road_network_toolbox_ui.selected_lanelet_angle
            )
            if lanelet_angle < 0:
                self.parent().road_network_toolbox.road_network_toolbox_ui.selected_lanelet_angle.setText(
                    str(abs(lanelet_angle))
                )
            else:
                self.parent().road_network_toolbox.road_network_toolbox_ui.selected_lanelet_angle.setText(
                    "-" + str(abs(lanelet_angle))
                )

    def click_on_curved_lanelet(self, mouse_event: QMouseEvent) -> None:
        """
        Method which handles the event if you click with the mouse in the coordinate system. Decides if the cursor is
        on the angle or the radius buttton

        :param mouse_event: mouse parameters
        """
        if self.circle_radius.contains(mouse_event)[0]:
            self.circle_radius.set_color("lightblue")
            self.mpl_disconnect(self.motion_notify_event_cid)
            self.mpl_disconnect(self.button_release_event_cid)
            self.setCursor(QtCore.Qt.CursorShape.SizeAllCursor)
            rotation_lanelet = self.calc_angle(
                np.array([0, 1]),
                np.array([0, 0]),
                self.temp_edited_lanelet.left_vertices[0],
                self.temp_edited_lanelet.right_vertices[0],
            )
            count_vertices = len(self.temp_edited_lanelet.left_vertices)
            angle_25_lanelet = self.calc_angle(
                self.temp_edited_lanelet.left_vertices[0],
                self.temp_edited_lanelet.right_vertices[0],
                self.temp_edited_lanelet.left_vertices[round(count_vertices * 0.25)],
                self.temp_edited_lanelet.right_vertices[round(count_vertices * 0.25)],
            )
            self.motion_notify_event_cid = self.mpl_connect(
                "motion_notify_event",
                lambda event: self.on_motion_radius(event, angle_25_lanelet, rotation_lanelet),
            )
            self.button_release_event_cid = self.mpl_connect(
                "button_release_event", self.on_release_curved_lanelet
            )
            self.draw_editable_lanelet()

        elif self.circle_angle.contains(mouse_event)[0]:
            self.circle_angle.set_color("lightblue")
            self.mpl_disconnect(self.motion_notify_event_cid)
            self.mpl_disconnect(self.button_release_event_cid)
            rotation_lanelet = self.calc_angle(
                np.array([0, 1]),
                np.array([0, 0]),
                self.temp_edited_lanelet.left_vertices[0],
                self.temp_edited_lanelet.right_vertices[0],
            )
            self.setCursor(QtCore.Qt.CursorShape.SizeAllCursor)
            self.motion_notify_event_cid = self.mpl_connect(
                "motion_notify_event", lambda event: self.on_motion_angle(event, rotation_lanelet)
            )
            self.button_release_event_cid = self.mpl_connect(
                "button_release_event", self.on_release_curved_lanelet
            )

        elif not self.new_lanelet:
            self.display_curved_lanelet(False, False, mouse_event)

    def on_motion_radius(
        self, mouse_event: QMouseEvent, angle_25_lanelet: float, rotation_lanelet: float
    ) -> None:
        """
        Handles the moment, when you drag the radius circle

        :param mouse_event: Parameter with the information about the mouse
        :param angle_25_lanelet: Angle of the off 25% of the lanelet to gain an intuitive way to drag the mouse
        :param rotation_lanelet: Offset of the lanelet to the origin
        """
        start_x = self.circle_radius.get_center()[0]
        start_y = self.circle_radius.get_center()[1]
        self.setCursor(QtCore.Qt.CursorShape.SizeAllCursor)

        if mouse_event.xdata is not None and mouse_event.ydata is not None:
            # Calculate the angle of mouse movement
            dx = mouse_event.xdata - start_x
            dy = mouse_event.ydata - start_y
            angle = math.degrees(math.atan2(dy, dx))

            # Ensure angle is between 0 and 360
            if angle < 0:
                angle += 360

            angle = angle - rotation_lanelet

            if self.new_lanelet:
                old_radius = self.parent().road_network_toolbox.get_float(
                    self.parent().road_network_toolbox.road_network_toolbox_ui.lanelet_radius
                )
            else:
                old_radius = self.parent().road_network_toolbox.get_float(
                    self.parent().road_network_toolbox.road_network_toolbox_ui.selected_lanelet_radius
                )

            # Code to change the radius when adding to successor selection
            # if self.parent().road_network_toolbox.road_network_toolbox_ui.connect_to_successors_selection.isChecked():
            #     if self._is_within_growth(angle_lanelet, angle):
            #         new_radius = old_radius - self._calculate_distance(start_x, start_y, mouse_event.xdata,
            #                                                            mouse_event.ydata)
            #     else:
            #         new_radius = old_radius + self._calculate_distance(start_x, start_y, mouse_event.xdata,
            #                                                            mouse_event.ydata)
            # else:
            if self._in_same_direction(angle_25_lanelet, angle):
                new_radius = old_radius + self._calculate_distance(
                    start_x, start_y, mouse_event.xdata, mouse_event.ydata
                )
            else:
                new_radius = old_radius - self._calculate_distance(
                    start_x, start_y, mouse_event.xdata, mouse_event.ydata
                )
            if new_radius > 0:
                if self.new_lanelet:
                    self.parent().road_network_toolbox.road_network_toolbox_ui.lanelet_radius.setText(
                        str(new_radius)
                    )
                else:
                    self.parent().road_network_toolbox.road_network_toolbox_ui.selected_lanelet_end_position_x.setText(
                        str(self.temp_edited_lanelet.center_vertices[-1][0])
                    )
                    self.parent().road_network_toolbox.road_network_toolbox_ui.selected_lanelet_end_position_y.setText(
                        str(self.temp_edited_lanelet.center_vertices[-1][1])
                    )
                    self.parent().road_network_toolbox.road_network_toolbox_ui.selected_lanelet_radius.setText(
                        str(new_radius)
                    )
            else:
                self.parent().road_network_toolbox.text_browser.append(
                    "The radius has to be greater than 0"
                )

    def on_motion_angle(self, mouse_event: QMouseEvent, rotation_lanelet: float) -> None:
        """
        Handles the moment, when you drag the angle circle

        :param mouse_event: Parameter with the information about the mouse
        :param rotation_lanelet: Offset of the lanelet to the origin
        """
        start_x = self.circle_angle.get_center()[0]
        start_y = self.circle_angle.get_center()[1]
        self.setCursor(QtCore.Qt.CursorShape.SizeAllCursor)

        if mouse_event.xdata is not None and mouse_event.ydata is not None:
            # Calculate the angle of mouse movement
            dx = mouse_event.xdata - start_x
            dy = mouse_event.ydata - start_y
            angle = math.degrees(math.atan2(dy, dx))

            # Ensure angle is between 0 and 360
            if angle < 0:
                angle += 360

            angle_lanelet = self.calc_angle(
                self.temp_edited_lanelet.left_vertices[0],
                self.temp_edited_lanelet.right_vertices[0],
                self.temp_edited_lanelet.left_vertices[-1],
                self.temp_edited_lanelet.right_vertices[-1],
            )
            if self.new_lanelet:
                old_angle = self.parent().road_network_toolbox.get_float(
                    self.parent().road_network_toolbox.road_network_toolbox_ui.lanelet_angle
                )
            else:
                old_angle = self.parent().road_network_toolbox.get_float(
                    self.parent().road_network_toolbox.road_network_toolbox_ui.selected_lanelet_angle
                )

            # Code for adding to successor to change the angle -> Could contain errors due to the fact that the feature
            # could not be tested
            # if self.parent().road_network_toolbox.road_network_toolbox_ui.connect_to_successors_selection.isChecked() \
            #         and self.new_lanelet:
            #     if self._is_within_growth(angle_lanelet, angle) and old_angle > 0:
            #         new_angle = old_angle + self._calculate_distance(start_x, start_y, mouse_event.xdata,
            #                                                          mouse_event.ydata)
            #     elif not self._is_within_growth(angle_lanelet, angle) and old_angle > 0:
            #         new_angle = old_angle - self._calculate_distance(start_x, start_y, mouse_event.xdata,
            #                                                          mouse_event.ydata)
            #     elif self._is_within_growth(angle_lanelet, angle) and old_angle < 0:
            #         new_angle = old_angle - self._calculate_distance(start_x, start_y, mouse_event.xdata,
            #                                                          mouse_event.ydata)
            #     else:
            #         new_angle = old_angle + self._calculate_distance(start_x, start_y, mouse_event.xdata,
            #                                                          mouse_event.ydata)
            # else:
            angle = angle - rotation_lanelet
            if self._in_same_direction(angle_lanelet, angle) and old_angle > 0:
                new_angle = old_angle + self._calculate_distance(
                    start_x, start_y, mouse_event.xdata, mouse_event.ydata
                )
            elif not self._in_same_direction(angle_lanelet, angle) and old_angle > 0:
                new_angle = old_angle - self._calculate_distance(
                    start_x, start_y, mouse_event.xdata, mouse_event.ydata
                )
            elif self._in_same_direction(angle_lanelet, angle) and old_angle < 0:
                new_angle = old_angle - self._calculate_distance(
                    start_x, start_y, mouse_event.xdata, mouse_event.ydata
                )
            else:
                new_angle = old_angle + self._calculate_distance(
                    start_x, start_y, mouse_event.xdata, mouse_event.ydata
                )
            if abs(new_angle) > 360:
                self.parent().road_network_toolbox.text_browser.append(
                    "The angle can't be greater than 360 or smaller" " than -360"
                )
            else:
                if self.new_lanelet:
                    self.parent().road_network_toolbox.road_network_toolbox_ui.lanelet_angle.setText(
                        str(new_angle)
                    )
                else:
                    self.parent().road_network_toolbox.road_network_toolbox_ui.selected_lanelet_end_position_x.setText(
                        str(self.temp_edited_lanelet.center_vertices[-1][0])
                    )
                    self.parent().road_network_toolbox.road_network_toolbox_ui.selected_lanelet_end_position_y.setText(
                        str(self.temp_edited_lanelet.center_vertices[-1][1])
                    )
                    self.parent().road_network_toolbox.road_network_toolbox_ui.selected_lanelet_angle.setText(
                        str(new_angle)
                    )

    def move_cursor_curved_lanelet(self, mouse_event: QMouseEvent) -> None:
        """
        Shows a moveable Cursor if the mouse hovers over a point which is moveable

        :param mouse_event: Datastructure which contains information about the mouse
        """
        if self.circle_radius.contains(mouse_event)[0]:
            self.setCursor(QtCore.Qt.CursorShape.SizeAllCursor)
        elif self.circle_angle.contains(mouse_event)[0]:
            self.setCursor(QtCore.Qt.CursorShape.SizeAllCursor)
        else:
            self.setCursor(QtCore.Qt.CursorShape.ArrowCursor)

    def on_release_curved_lanelet(self, mouse_event: QMouseEvent) -> None:
        """
        Handles the moment, when you release the mouse button,to deactive the movement

        :param mouse_event: Parameter with the Information about the mouse
        """
        self.mpl_disconnect(self.motion_notify_event_cid)
        self.circle_angle.set_color("blue")
        self.circle_radius.set_color("blue")
        self.draw_editable_lanelet()
        self.motion_notify_event_cid = self.mpl_connect(
            "motion_notify_event", self.move_cursor_curved_lanelet
        )

    def calc_angle(
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
        line_origin = left_vertice_point_one - right_vertice_point_one
        line_lanelet = left_vertice_point_two - right_vertice_point_two
        norm_predecessor = np.linalg.norm(line_origin)
        norm_lanelet = np.linalg.norm(line_lanelet)
        dot_prod = np.dot(line_origin, line_lanelet)
        sign = line_lanelet[1] * line_origin[0] - line_lanelet[0] * line_origin[1]
        angle = np.arccos(dot_prod / (norm_predecessor * norm_lanelet))
        if sign > 0:
            angle = 2 * np.pi - angle
        return 360 - angle * (180 / math.pi)

    def _calculate_distance(
        self, start_x: float, start_y: float, end_x: float, end_y: float
    ) -> float:
        """
        Calculates the distance between two given points

        :param start_x: x-Coordinate of the start point
        :param start_y: y-Coordinate of the start point
        :param end_x: x-Coordinate of the end point
        :param end_y: y-Coordinate of the end point

        :returns: Distance as a float
        """
        dx = end_x - start_x
        dy = end_y - start_y
        distance = math.sqrt(dx**2 + dy**2)

        return distance

    def _in_same_direction(self, first_angle: float, second_angle: float) -> bool:
        """
        Calculates if the second angle is within 90 degrees to the left or right of the first_angle

        :param first_angle: Angle of which the direction is handled
        :param second_angle: Angle to check if it is within 180 degrees
        :return: boolean if the angle is within the 90 degrees to both sides
        """
        first_angle = first_angle % 360
        second_angle = second_angle % 360
        diff = abs(first_angle - second_angle)

        if diff <= 90 or diff >= 270:
            return True
        else:
            return False

    @logger.log
    def show_vertices(self, lanelet: Lanelet):
        """
        Enables the display of the point of each vertice of the lanelet to allow for a manipulation of the user

        @param lanelet: Lanelet, which vertices should be shown.
        """
        self.mpl_disconnect(self.button_press_event_cid)
        self.mpl_disconnect(self.button_release_event_cid)
        self.mpl_disconnect(self.motion_notify_event_cid)
        self.current_edited_lanelet_scenario = self.scenario_model.get_copy_of_scenario()
        self.temp_edited_lanelet = copy.deepcopy(lanelet)
        self.new_lanelet = False

        self.parent().top_bar.toolbar_wrapper.tool_bar_ui.cancel_edit_vertices.setVisible(True)

        self.left_vertices = copy.deepcopy(lanelet.left_vertices)
        self.right_vertices = copy.deepcopy(lanelet.right_vertices)

        self.left_scatter = Line2D(
            self.left_vertices[:, 0],
            self.left_vertices[:, 1],
            c="g",
            marker="o",
            picker=True,
            zorder=10,
        )

        self.right_scatter = Line2D(
            self.right_vertices[:, 0],
            self.right_vertices[:, 1],
            c="b",
            marker="o",
            picker=True,
            zorder=10,
        )

        self.button_press_event_cid = self.ax.figure.canvas.mpl_connect(
            "button_press_event", lambda event: self.on_pick(event, lanelet)
        )

        self.draw_editable_lanelet()
        self.ax.add_line(self.left_scatter)
        self.ax.add_line(self.right_scatter)
        self.draw()

    def cancel_edit_vertices(self):
        """
        Disables the show of vertices and disconnects the respective functions
        """
        self.mpl_disconnect(self.button_press_event_cid)
        self.mpl_disconnect(self.button_release_event_cid)
        self.mpl_disconnect(self.motion_notify_event_cid)

        self.button_release_event_cid = self.mpl_connect(
            "button_release_event", self.dynamic_canvas_release_callback
        )
        self.button_press_event_cid = self.mpl_connect(
            "button_press_event", self.dynamic_canvas_click_callback
        )

        self.left_vertices = None
        self.right_vertices = None
        self.current_edited_lanelet_scenario = None
        self.temp_edited_lanelet = None
        self.parent().top_bar.toolbar_wrapper.tool_bar_ui.cancel_edit_vertices.setVisible(False)
        self.draw_scenario()
        self.draw()

    def on_pick(self, event: QMouseEvent, lanelet: Lanelet):
        """
        Function that determines the action depending on the mouse click. Whether it initiates the movement of a vertice
        or Saves the new layout of the new lanelet

        @param event: Event of the Mouse
        @param lanelet: the editable lanelet
        """
        max_distance_to_point = 0.5
        if event.button == MouseButton.RIGHT:
            menu = PyQt6.QtWidgets.QMenu()
            x, y = event.xdata, event.ydata
            left = np.sum((self.left_vertices - np.array([x, y])) ** 2, axis=1)
            right = np.sum((self.right_vertices - np.array([x, y])) ** 2, axis=1)
            if min(left) < max_distance_to_point or min(right) < max_distance_to_point:
                add_vertice = menu.addAction("Add Vertice")
                if len(self.left_vertices) > 2:
                    delete_vertice = menu.addAction("Delete Vertice")
                else:
                    delete_vertice = None
            else:
                add_vertice = None
                delete_vertice = None
            safe_changes = menu.addAction("Safe Changes")
            remove_changes = menu.addAction("Remove Changes")
            continue_editing = menu.addAction("Continue Editing")

            action = menu.exec((self.mouse_coordinates))

            if action == continue_editing:
                return
            elif action == safe_changes:
                self.create_temp_lanelet_vertices()
                self.parent().road_network_toolbox.lanelet_controller.update_lanelet(
                    self.temp_edited_lanelet
                )

            elif (add_vertice is not None and action == add_vertice) or (
                delete_vertice is not None and action == delete_vertice
            ):
                if min(left) < min(right):
                    ind = np.argmin(left)
                    index = ind
                else:
                    ind = np.argmin(right)
                    index = ind
                if action == add_vertice:
                    self.add_vertice(index)
                else:
                    self.delete_vertice(index)
                self.create_temp_lanelet_vertices()
                self.draw_editable_lanelet()
                self.ax.add_line(self.left_scatter)
                self.ax.add_line(self.right_scatter)
                self.draw()

            if action == remove_changes or action == safe_changes:
                self.cancel_edit_vertices()

        if event.inaxes == self.ax and event.button == MouseButton.LEFT:
            x, y = event.xdata, event.ydata
            left = np.sum((self.left_vertices - np.array([x, y])) ** 2, axis=1)
            right = np.sum((self.right_vertices - np.array([x, y])) ** 2, axis=1)
            if min(left) > max_distance_to_point and min(right) > max_distance_to_point:
                return
            if min(left) < min(right):
                ind = np.argmin(left)
                self.left_dragging_point = ind
                self.motion_notify_event_cid = self.mpl_connect(
                    "motion_notify_event", self.on_left_motion
                )
                self.button_release_event_cid = self.mpl_connect(
                    "button_release_event", self.on_left_release
                )
            else:
                ind = np.argmin(right)
                self.right_dragging_point = ind
                self.motion_notify_event_cid = self.mpl_connect(
                    "motion_notify_event", self.on_right_motion
                )
                self.button_release_event_cid = self.mpl_connect(
                    "button_release_event", self.on_right_release
                )

            self.draw()

    def create_temp_lanelet_vertices(self):
        """
        Creates temporary lanelet and saves it. For the edit vertices.
        """
        center_vertices = copy.deepcopy(self.left_vertices)

        for i in range(len(self.left_vertices)):
            center_vertices[i] = np.array(
                [
                    (self.left_vertices[i][0] + self.right_vertices[i][0]) / 2,
                    (self.left_vertices[i][1] + self.right_vertices[i][1]) / 2,
                ]
            )

        self.temp_edited_lanelet = Lanelet(
            self.left_vertices,
            center_vertices,
            self.right_vertices,
            self.temp_edited_lanelet.lanelet_id,
            self.temp_edited_lanelet.predecessor,
            self.temp_edited_lanelet.successor,
            self.temp_edited_lanelet.adj_left,
            self.temp_edited_lanelet.adj_left_same_direction,
            self.temp_edited_lanelet.adj_right,
            self.temp_edited_lanelet.adj_right_same_direction,
            self.temp_edited_lanelet.line_marking_left_vertices,
            self.temp_edited_lanelet.line_marking_right_vertices,
            self.temp_edited_lanelet.stop_line,
            self.temp_edited_lanelet.lanelet_type,
            self.temp_edited_lanelet.user_one_way,
            self.temp_edited_lanelet.user_bidirectional,
            self.temp_edited_lanelet.traffic_signs,
            self.temp_edited_lanelet.traffic_lights,
            self.temp_edited_lanelet.adjacent_areas,
        )

    def calculate_direction(self, x1: float, y1: float, x2: float, y2: float) -> float:
        """
        Calculates the direction in which 2 points point

        @param x1: x-Coordinate of first point
        @param y1: y-Coordinate of first point
        @param x2: x-Coordinate of second point
        @param y2: y-Coordinate of second point

        @returns:
        """
        delta_x = x2 - x1
        delta_y = y2 - y1
        angle = math.atan2(delta_y, delta_x)
        return angle

    def get_new_coordinate(self, x: float, y: float, direction: float, distance: float = 1) -> []:
        """
        returns a new coordintate with a specific distance to the given point

        @param x: x-Coordinate of the point of which the new point should be created
        @param y: y-Coordinate of the point of which the new point should be created
        @param direction: in which direction of the point should the new one be created
        @param distance: With what distance should the new point be created (Default = 1)

        @returns: List with the new coordinates
        """
        new_x = x + distance * math.cos(direction)
        new_y = y + distance * math.sin(direction)

        return [new_x, new_y]

    def add_vertice(self, index: int):
        """
        Adds a new vertice after the given index

        @param index: Index after which place the new point should be created
        """

        if index == len(self.left_vertices) - 1:  # If selected index is the last point
            direction = self.calculate_direction(
                self.left_vertices[-2][0],
                self.left_vertices[-2][1],
                self.left_vertices[-1][0],
                self.left_vertices[-1][1],
            )
            new_left_point = self.get_new_coordinate(
                self.left_vertices[-1][0], self.left_vertices[-1][1], direction
            )
            new_right_point = self.get_new_coordinate(
                self.right_vertices[-1][0], self.right_vertices[-1][1], direction
            )

            self.left_vertices = np.vstack([self.left_vertices, new_left_point])
            self.right_vertices = np.vstack([self.right_vertices, new_right_point])

        elif 0 <= index < len(self.left_vertices) - 1:  # If selected index is in between vertices
            new_left_point = 0.5 * (self.left_vertices[index] + self.left_vertices[index + 1])
            new_right_point = 0.5 * (self.right_vertices[index] + self.right_vertices[index + 1])

            self.left_vertices = np.insert(self.left_vertices, index + 1, new_left_point, axis=0)
            self.right_vertices = np.insert(self.right_vertices, index + 1, new_right_point, axis=0)

        # Update vertice lines
        self.left_scatter.set_data(self.left_vertices[:, 0], self.left_vertices[:, 1])
        self.right_scatter.set_data(self.right_vertices[:, 0], self.right_vertices[:, 1])

    def delete_vertice(self, index: int):
        """
        Deletes the given vertices of the given index

        @param index: Index of the deleted vertice
        """
        self.left_vertices = np.delete(self.left_vertices, index, axis=0)
        self.right_vertices = np.delete(self.right_vertices, index, axis=0)
        self.left_scatter.set_data(self.left_vertices[:, 0], self.left_vertices[:, 1])
        self.right_scatter.set_data(self.right_vertices[:, 0], self.right_vertices[:, 1])

    def on_left_motion(self, event: QMouseEvent):
        """
        Handles the motion procedure if a left vertice is dragged

        @param event: MouseEvent of the movement
        """
        if hasattr(self, "left_dragging_point"):
            self.left_vertices[self.left_dragging_point] = [event.xdata, event.ydata]
            self.left_scatter.set_data(self.left_vertices[:, 0], self.left_vertices[:, 1])
            self.draw()

    def on_left_release(self, event: QMouseEvent):
        """
        Handles the disconnection procedure if a left vertice is dragged

        @param event: MouseEvent of the movement
        """
        if hasattr(self, "left_dragging_point"):
            delattr(self, "left_dragging_point")
            self.mpl_disconnect(self.motion_notify_event_cid)
            self.mpl_disconnect(self.button_release_event_cid)

            self.create_temp_lanelet_vertices()
            self.draw_editable_lanelet()
            self.ax.add_line(self.left_scatter)
            self.ax.add_line(self.right_scatter)
            self.draw()

    def on_right_motion(self, event):
        """
        Handles the motion procedure if a right vertice is dragged

        @param event: MouseEvent of the movement
        """
        if hasattr(self, "right_dragging_point"):
            self.right_vertices[self.right_dragging_point] = [event.xdata, event.ydata]
            self.right_scatter.set_data(self.right_vertices[:, 0], self.right_vertices[:, 1])
            self.draw()

    def on_right_release(self, event: QMouseEvent):
        """
        Handles the disconnection procedure if a right vertice is dragged

        @param event: MouseEvent of the movement
        """
        if hasattr(self, "right_dragging_point"):
            delattr(self, "right_dragging_point")
            self.mpl_disconnect(self.motion_notify_event_cid)
            self.mpl_disconnect(self.button_release_event_cid)

            self.create_temp_lanelet_vertices()
            self.draw_editable_lanelet()
            self.ax.add_line(self.left_scatter)
            self.ax.add_line(self.right_scatter)
            self.draw()
