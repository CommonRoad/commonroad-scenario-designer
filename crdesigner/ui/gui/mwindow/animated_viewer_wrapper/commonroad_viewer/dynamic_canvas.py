from typing import List

from PyQt5.QtWidgets import QSizePolicy
from commonroad.planning.planning_problem import PlanningProblemSet

from commonroad.common.util import Interval
from commonroad.scenario.scenario import Scenario
from commonroad.visualization.mp_renderer import MPRenderer
from .helper import _merge_dict

from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.gui_sumo_simulation import SUMO_AVAILABLE
if SUMO_AVAILABLE:
    from crdesigner.map_conversion.sumo_map.config import SumoConfig

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


__author__ = "Benjamin Orthen, Stefan Urban, Max Winklhofer, Guyue Huang, Max Fruehauf, Sebastian Maierhofer"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles, BMW Car@TUM"]
__version__ = "0.4"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad@lists.lrz.de"
__status__ = "Released"

ZOOM_FACTOR = 1.2


class DynamicCanvas(FigureCanvas):
    """ this canvas provides zoom with the mouse wheel """
    def __init__(self, parent=None, width=5, height=5, dpi=100):

        self.ax = None
        self.drawer = Figure(figsize=(width, height), dpi=dpi)
        self.rnd = MPRenderer(ax=self.ax)

        self.draw_params = {
            'scenario': {
                'dynamic_obstacle': {
                    'trajectory': {
                        'show_label': True,
                        'draw_trajectory': False
                    }
                },
                'lanelet_network': {
                    'traffic_sign': {
                        'draw_traffic_signs': True,
                        'show_traffic_signs': 'all',
                    },
                    'intersection': {
                        'draw_intersections': False,
                        'draw_incoming_lanelets': True,
                        'incoming_lanelets_color': '#3ecbcf',
                        'draw_crossings': True,
                        'crossings_color': '#b62a55',
                        'draw_successors': True,
                        'successors_left_color': '#ff00ff',
                        'successors_straight_color': 'blue',
                        'successors_right_color': '#ccff00',
                        'show_label': True,
                    },
                }
            }
        }

        self.draw_params_dynamic_only = {
            'scenario': {
                'dynamic_obstacle': {
                    'trajectory': {
                        'show_label': True,
                        'draw_trajectory': False
                    }
                },
                'lanelet_network': {
                    'intersection': {'draw_intersections': False},
                    'lanelet': {
                        'draw_border_vertices': False,
                        'draw_start_and_direction': False,
                        'draw_stop_line': False,
                        'draw_center_bound': False,
                        'draw_right_bound': False,
                        'draw_left_bound': False
                    },
                    # 'traffic_light': {
                    #     'scale_factor': 0.2
                    # },
                    'traffic_sign': {
                        'draw_traffic_signs': True,
                        'show_traffic_signs': 'all',
                        # 'scale_factor': 0.2
                    },
                }
            }
        }

        self._handles = {}

        super().__init__(self.drawer)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.mpl_connect('scroll_event', self.zoom)

        self.clear_axes()

    def clear_axes(self, keep_limits=False, clear_artists=False):
        """ """
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
        """Gives the plots Axes

        :return: matplotlib axis
        """
        return self.ax

    def get_limits(self) -> List[float]:
        """ return the current limits of the canvas """
        x_lim = self.ax.get_xlim()
        y_lim = self.ax.get_ylim()
        return [x_lim[0], x_lim[1], y_lim[0], y_lim[1]]

    def update_plot(self, limits: List[float] = None):
        """ draw the canvas. optional with new limits"""
        if limits:
            self.ax.set(xlim=limits[0:2])
            self.ax.set(ylim=limits[2:4])
        self.draw_idle()

    def zoom(self, event):
        """ zoom in / out function in GUI by using mouse wheel """
        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()
        center = ((x_min + x_max) / 2, (y_min + y_max) / 2)
        x_dim = (x_max - x_min) / 2
        y_dim = (y_max - y_min) / 2

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
            # TODO enhance zoom center
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

        self.update_plot([
            new_center_x - new_x_dim, new_center_x + new_x_dim,
            new_center_y - new_y_dim, new_center_y + new_y_dim
        ])

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
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

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
            print(draw_params_merged)
            scenario.draw(renderer=self.rnd, draw_params=draw_params_merged)

            self.rnd.render(keep_static_artists=True)

        else:
            scenario.draw(renderer=self.rnd, draw_params=draw_params_merged)
            if pps is not None:
                pps.draw(renderer=self.rnd, draw_params=draw_params_merged)
            self.rnd.render(keep_static_artists=True)

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
