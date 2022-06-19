from typing import List, Union
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtCore import Qt
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.common.util import Interval
from commonroad.scenario.scenario import Scenario
from commonroad.visualization.mp_renderer import MPRenderer
from commonroad.geometry.shape import Circle
from commonroad.scenario.obstacle import StaticObstacle, DynamicObstacle

from .helper import _merge_dict
from .service_layer import update_draw_params_dynamic_only_based_on_zoom
from .service_layer import update_draw_params_based_on_zoom
from .service_layer import update_draw_params_based_on_scenario
from .service_layer import update_draw_params_dynamic_based_on_scenario
from .service_layer import resize_lanelet_network
from crdesigner.ui.gui.mwindow.service_layer import config


__author__ = "Benjamin Orthen, Stefan Urban, Max Winklhofer, Guyue Huang, Max Fruehauf, Sebastian Maierhofer"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles, BMW Car@TUM"]
__version__ = "0.5"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad@lists.lrz.de"
__status__ = "Released"

ZOOM_FACTOR = 1.2


class DynamicCanvas(FigureCanvas):
    """
    This canvas provides zoom with the mouse wheel.
    """
    obstacle_color_array = []
    scenario = None

    def __init__(self, parent=None, width=5, height=5, dpi=100, animated_viewer=None):
        self.animated_viewer = animated_viewer
        self.ax = None
        self.drawer = Figure(figsize=(width, height), dpi=dpi)
        self.rnd = MPRenderer(ax=self.ax)

        self._handles = {}
        self.initial_parameter_config_done = False  # This is used to only once set the parameter based on the scenario
        self.draw_params = None  # needed later - here for reference
        self.draw_params_dynamic_only = None  # needed later - here for reference
        # used for efficiently monitoring of we switched from detailed to undetailed params
        self.last_changed_sth = False
        self.latest_mouse_pos = None  # used to store the last mouse position where a lanelet was clicked

        super().__init__(self.drawer)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # any callbacks for interaction per mouse
        self.mpl_connect('button_press_event', self.dynamic_canvas_click_callback)
        self.mpl_connect('button_release_event', self.dynamic_canvas_release_callback)
        self.mpl_connect('scroll_event', self.zoom)
        # callbacks for interaction via keyboard, used for creation of trajectories of dynamic obstacles
        self.mpl_connect('key_release_event', self._on_key_release)
        self.setFocusPolicy(Qt.ClickFocus)
        self.setFocus()

        self.clear_axes()

    def test(self, key):
        print("sos")

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
            self.update_plot(limits)

    def get_axes(self):
        return self.ax

    def get_limits(self) -> List[float]:
        x_lim = self.ax.get_xlim()
        y_lim = self.ax.get_ylim()
        return [x_lim[0], x_lim[1], y_lim[0], y_lim[1]]

    def update_plot(self, limits: List[float] = None):
        if limits:
            self.ax.set(xlim=limits[0:2])
            self.ax.set(ylim=limits[2:4])
        self.draw_idle()

    def zoom(self, event):
        """
        Zoom in / out function in Dynamic Canvas by using mouse wheel.
        """
        center, x_dim, y_dim, _, _ = self.get_center_and_axes_values()

        # enlarge / shrink limits
        if event.button == 'up':
            new_x_dim = x_dim / ZOOM_FACTOR
            new_y_dim = y_dim / ZOOM_FACTOR
        elif event.button == 'down':
            new_x_dim = x_dim * ZOOM_FACTOR
            new_y_dim = y_dim * ZOOM_FACTOR
        else:
            return

        # new center sensitive to mouse position of zoom event
        mouse_pos = (event.xdata, event.ydata)
        if mouse_pos[0] and mouse_pos[1]:
            new_center_diff_x = (center[0] - mouse_pos[0]) / 6
            new_center_diff_y = (center[1] - mouse_pos[1]) / 6
            if event.button == 'up':
                new_center_x = center[0] - new_center_diff_x
                new_center_y = center[1] - new_center_diff_y
            else:
                new_center_x = center[0] + new_center_diff_x
                new_center_y = center[1] + new_center_diff_y
            # new limits should include old limits if zooming out
            # old limits should include new limits if zooming in
            dim_diff_x = abs(new_x_dim - x_dim)
            dim_diff_y = abs(new_y_dim - y_dim)
            new_center_x = min(max(center[0] - dim_diff_x, new_center_x),
                               center[0] + dim_diff_x)
            new_center_y = min(max(center[1] - dim_diff_y, new_center_y),
                               center[1] + dim_diff_y)
        else:
            new_center_x = center[0]
            new_center_y = center[1]
        # update the parameters for drawing based on the zoom -> this is for performance,
        # not all details need to be rendered when you are zoomed out
        self.draw_params = update_draw_params_based_on_zoom(x=new_x_dim, y=new_y_dim)
        self.draw_params_dynamic_only = update_draw_params_dynamic_only_based_on_zoom(x=new_x_dim, y=new_y_dim)
        self.animated_viewer.current_scenario.lanelet_network, resized_lanelet_network = resize_lanelet_network(
            original_lanelet_network=self.animated_viewer.original_lanelet_network,
            center_x=new_center_x,
            center_y=new_center_y,
            dim_x=x_dim,
            dim_y=y_dim)
        self.update_plot([
            new_center_x - new_x_dim, new_center_x + new_x_dim,
            new_center_y - new_y_dim, new_center_y + new_y_dim
        ])
        if resized_lanelet_network or self.last_changed_sth:
            self.animated_viewer.update_plot()
        self.last_changed_sth = resized_lanelet_network
        # now also show any selected
        self._select_lanelet()

    def draw_scenario(self,
                      scenario: Scenario,
                      pps: PlanningProblemSet = None,
                      draw_params=None,
                      plot_limits=None,
                      draw_dynamic_only=False):
        """[summary]
        :param scenario: [description]
        :param pps: PlanningProblemSet of the scenario,defaults to None
        :type pps: PlanningProblemSet
        :type scenario: Scenario
        :param draw_params: [description], defaults to None
        :type draw_params: [type], optional
        :param plot_limits: [description], defaults to None
        :type plot_limits: [type], optional
        :param draw_dynamic_only: reuses static artists
        """
        # want to update immediatly if change gui settings
        self.draw_params = update_draw_params_based_on_scenario(
                    lanelet_count=len(scenario.lanelet_network.lanelets),
                    traffic_sign_count=len(scenario.lanelet_network.traffic_signs))

        DynamicCanvas.scenario = scenario
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        # update the parameters based on the number of lanelets and traffic signs - but only once during starting
        if not self.initial_parameter_config_done:
            self.draw_params = update_draw_params_based_on_scenario(
                    lanelet_count=len(scenario.lanelet_network.lanelets),
                    traffic_sign_count=len(scenario.lanelet_network.traffic_signs))
            self.draw_params_dynamic_only = update_draw_params_dynamic_based_on_scenario(
                    lanelet_count=len(scenario.lanelet_network.lanelets),
                    traffic_sign_count=len(scenario.lanelet_network.traffic_signs))
            self.initial_parameter_config_done = True
        if draw_dynamic_only is True:
            self.rnd.remove_dynamic()
            # self.rnd.ax.clear()
            # self.ax.clear()
        else:
            self.ax.clear()
        draw_params_merged = _merge_dict(self.draw_params.copy(), draw_params)
        self.rnd.plot_limits = plot_limits
        self.rnd.ax = self.ax
        if draw_dynamic_only is True:
            draw_params_merged = _merge_dict(self.draw_params_dynamic_only.copy(), draw_params)
            scenario.draw(renderer=self.rnd, draw_params=draw_params_merged)
            self.draw_obstacles(scenario=scenario, draw_params=draw_params_merged)
            self.rnd.render(keep_static_artists=True)
        else:
            scenario.draw(renderer=self.rnd, draw_params=draw_params_merged)
            if pps is not None:
                pps.draw(renderer=self.rnd, draw_params=draw_params_merged)
            self.draw_obstacles(scenario=scenario, draw_params=draw_params_merged)
            self.rnd.render(keep_static_artists=False)

        if not plot_limits:
            self.ax.set(xlim=xlim)
            self.ax.set(ylim=ylim)

    def update_obstacles(self,
                         scenario: Scenario,
                         draw_params=None,
                         plot_limits=None):
        """
        Redraw only the dynamic obstacles. This gives a large performance boost, when playing an animation
        :param scenario: The scenario containing the dynamic obstacles
        :param draw_params: CommonRoad DrawParams for visualization
        :param plot_limits: Matplotlib plot limits
        """
        # redraw dynamic obstacles
        obstacles = scenario.obstacles_by_position_intervals([
            Interval(plot_limits[0], plot_limits[1]),
            Interval(plot_limits[2], plot_limits[3])
        ]) if plot_limits else scenario.obstacles

        draw_params_merged = _merge_dict(self.draw_params.copy(), draw_params)

        self.rnd.ax = self.ax
        for obj in obstacles:
            obj.draw(renderer=self.rnd, draw_params=draw_params_merged)
            self.rnd.render(show=True)

    def dynamic_canvas_click_callback(self, mouse_clicked_event):
        """
        General callback for clicking in the dynamic canvas, two things are checked:
            1. If the lanelet network of the current network should be resized.
            2. When a lanelet was selected execute the logic behind it.
                a) Select lanelets by clicking on the canvas. Selects only one of the lanelets that contains the click
                   position.
        This order is important - first the resizing and then the lanelet selection - otherwise the lanelets of the old
        map are selected and then not visualized.
        :params mouse_clicked_event:
        """
        # when the mouse is clicked we remember where this was -> use this for lanelet selection
        self.latest_mouse_pos = np.array([mouse_clicked_event.xdata, mouse_clicked_event.ydata])
        # update the map
        self._update_map()
        # now do the lanelet selection
        self._select_lanelet()

    def dynamic_canvas_release_callback(self, mouse_clicked_event):
        """
        When the mouse button is released update the map and also select lanelets (with old mouse pos).
        :params mouse_clicked_event:
        """
        # update the map
        self._update_map()
        # now do the lanelet selection
        self._select_lanelet(release=True)

    def _update_map(self):
        """
        Resized the map if necessary for performance improvement.
        """
        if self.initial_parameter_config_done:
            center, x_dim, y_dim, _, _ = self.get_center_and_axes_values()
            self.animated_viewer.current_scenario.lanelet_network, resized_lanelet_network = resize_lanelet_network(
                    original_lanelet_network=self.animated_viewer.original_lanelet_network, center_x=center[0],
                    center_y=center[1], dim_x=x_dim, dim_y=y_dim)
            if resized_lanelet_network:
                self.animated_viewer.update_plot()

    def _on_key_release(self, key_released_event):
        if key_released_event.key == 'up':
            print("up")
        else:
            print("none")

    def _select_lanelet(self, release: bool = False):
        """
        Select a lanelet and display the details in the GUI.

        :param release Boolean indicating whether function is called by click release callback
        """
        # check if any mousepos was setted before
        if self.latest_mouse_pos is None:
            return
        click_shape = Circle(radius=0.01, center=self.latest_mouse_pos)

        if self.animated_viewer.current_scenario is None:
            return
        l_network = self.animated_viewer.current_scenario.lanelet_network
        selected_l_ids = l_network.find_lanelet_by_shape(click_shape)
        selected_lanelets = [l_network.find_lanelet_by_id(lid) for lid in selected_l_ids]
        selected_obstacles = [obs for obs in self.animated_viewer.current_scenario.obstacles if obs.occupancy_at_time(
            self.animated_viewer.time_step.value) is not None and obs.occupancy_at_time(
            self.animated_viewer.time_step.value).shape.contains_point(self.latest_mouse_pos)]

        if len(selected_lanelets) > 0 and len(selected_obstacles) == 0:
            self.animated_viewer.update_plot(sel_lanelet=selected_lanelets[0],
                                             time_step=self.animated_viewer.time_step.value)
        else:
            self.animated_viewer.update_plot(sel_lanelet=None, time_step=self.animated_viewer.time_step.value)

        if not release:
            if len(selected_lanelets) + len(selected_obstacles) > 1:
                output = "__Info__: More than one object can be selected! Lanelets: "
                if len(selected_lanelets) > 0:
                    for la in selected_lanelets:
                        output += str(la.lanelet_id) + ", "
                output = output[:len(output) - 1]
                if len(selected_obstacles) > 0:
                    output += ". Obstacles: "
                    for obs in selected_obstacles:
                        output += str(obs.obstacle_id) + ", "
                output = output[:len(output) - 1]
                output += "."
            else:
                output = ""

            if len(selected_obstacles) > 0:
                selection = " Obstacle with ID " + str(selected_obstacles[0].obstacle_id) + " is selected."
                self.animated_viewer.callback_function(selected_obstacles[0], output + selection)
            elif len(selected_lanelets) > 0:
                selection = " Lanelet with ID " + str(selected_lanelets[0].lanelet_id) + " is selected."
                self.animated_viewer.callback_function(selected_lanelets[0], output + selection)

    def get_center_and_axes_values(self) -> ((float, float), float, float, (float, float), (float, float)):
        """
        Used to get the new dimensions of the current Dynamic Canvas and other meta data about it.
        :returns : center := touple (x,y) of center,
                   x_dim := absolut size of x axis,
                   y_dim := absolut size of y axis,
                   xlim := touple of x axis limits (x_min, x_max),
                   ylim := touple of y axis limits (y_min, y_max)
        """
        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()
        center = ((x_min + x_max) / 2, (y_min + y_max) / 2)
        x_dim = (x_max - x_min) / 2
        y_dim = (y_max - y_min) / 2
        return center, x_dim, y_dim, (x_min, x_max), (y_min, y_max)

    def draw_obstacles(self, scenario: Scenario, draw_params: str = None):
        """
        draws the obstacles
        :param scenario: current scenario
        :param: draw_params: scenario draw params, Note: does not contain
            dynamic obstacle related parameters
        """
        for obj in scenario.obstacles:
            # this is for getting the index of where the object_id is located
            try:
                result = next(c for c in DynamicCanvas.obstacle_color_array if c[0] == obj.obstacle_id)
                obstacle_draw_params = result[1]
                draw_params_merged = _merge_dict(draw_params.copy(), obstacle_draw_params.copy())
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
        draw_params = {"static_obstacle": {"occupancy": {"shape": {
            "polygon": {"facecolor": color},
            "rectangle": {"facecolor": color},
            "circle": {"facecolor": color}}}}}
        DynamicCanvas.obstacle_color_array.append([obstacle_id, draw_params, color])

    def set_dynamic_obstacle_color(self, obstacle_id: int, color: str = None):
        """
        sets dynamic_obstacle color
        :param obstacle_id: id of obstacle that is to be added/updated
        :param color: color of the obstacle, None if default color
        """
        if not color:
            color = "#1d7eea"
        draw_params = {"dynamic_obstacle": {
                            "vehicle_shape": {"occupancy": {"shape": {
                                            "polygon": {"facecolor": color},
                                            "rectangle": {"facecolor": color},
                                            "circle": {"facecolor": color}}}},
                            'show_label': config.DRAW_OBSTACLE_LABELS,
                            'draw_icon': config.DRAW_OBSTACLE_ICONS,
                            'draw_direction': config.DRAW_OBSTACLE_DIRECTION,
                            'draw_signals': config.DRAW_OBSTACLE_SIGNALS
                    }}
        DynamicCanvas.obstacle_color_array.append([obstacle_id, draw_params, color])

    def update_obstacle_trajectory_params(self):
        """
        updates obstacles' draw params when gui settings are changed
        """

        if DynamicCanvas.scenario is not None:
            for obj in DynamicCanvas.scenario.obstacles:
                try:  # check if obstacle is in obstacle_color_array
                    result = next(c for c in DynamicCanvas.obstacle_color_array if c[0] == obj.obstacle_id)
                    color = result[2]
                    if isinstance(obj, DynamicObstacle):
                        draw_params = {"dynamic_obstacle": {
                            "vehicle_shape": {"occupancy": {"shape": {
                                "polygon": {"facecolor": color},
                                "rectangle": {"facecolor": color},
                                "circle": {"facecolor": color}}}},
                            'show_label': config.DRAW_OBSTACLE_LABELS,
                            'draw_icon': config.DRAW_OBSTACLE_ICONS,
                            'draw_direction': config.DRAW_OBSTACLE_DIRECTION,
                            'draw_signals': config.DRAW_OBSTACLE_SIGNALS
                                                }}
                    elif isinstance(obj, StaticObstacle):
                        draw_params = {"static_obstacle": {
                            "occupancy": {"shape": {
                                "polygon": {"facecolor": color},
                                "rectangle": {"facecolor": color},
                                "circle": {"facecolor": color}}}}}

                    i = DynamicCanvas.obstacle_color_array.index(result)
                    DynamicCanvas.obstacle_color_array.pop(i)
                    DynamicCanvas.obstacle_color_array.append([obj.obstacle_id, draw_params, color])

                except Exception:
                    if isinstance(obj, DynamicObstacle):
                        color = "#1d7eea"
                        draw_params = {"dynamic_obstacle": {
                            "vehicle_shape": {"occupancy": {"shape": {
                                "polygon": {"facecolor": color},
                                "rectangle": {"facecolor": color},
                                "circle": {"facecolor": color}}}},
                            'show_label': config.DRAW_OBSTACLE_LABELS,
                            'draw_icon': config.DRAW_OBSTACLE_ICONS,
                            'draw_direction': config.DRAW_OBSTACLE_DIRECTION,
                            'draw_signals': config.DRAW_OBSTACLE_SIGNALS
                        }}
                    elif isinstance(obj, StaticObstacle):
                        color = "#d95558"
                        draw_params = {"static_obstacle": {
                                        "occupancy": {"shape": {
                                                "polygon": {"facecolor": color},
                                                "rectangle": {"facecolor": color},
                                                "circle": {"facecolor": color}}}}}
                    DynamicCanvas.obstacle_color_array.append([obj.obstacle_id, draw_params, color])

    def get_color(self, obstacle_id: int) -> Union[int, bool]:
        """
        :param obstacle_id: id of selected obstacle
        :return: color of current selected obstacle
        """
        try:
            result = next(c for c in self.obstacle_color_array if c[0] == obstacle_id)
            i = DynamicCanvas.obstacle_color_array.index(result)
            return DynamicCanvas.obstacle_color_array[i][2]
        except Exception:  # if scenario loaded and obstacle id doesn't exist in the array
            return False

    def remove_obstacle(self, obstacle_id: int):
        """
        removes obstacle from obstacle_color_array

        :param: id of obstacle to be removed
        """
        try:
            result = next(c for c in self.obstacle_color_array if c[0] == obstacle_id)
            i = DynamicCanvas.obstacle_color_array.index(result)
            DynamicCanvas.obstacle_color_array.pop(i)
        except Exception:  # if scenario loaded and obstacle id doesn't exist in the array
            pass
