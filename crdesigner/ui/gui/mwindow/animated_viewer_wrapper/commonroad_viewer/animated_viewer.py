from typing import Union
import numpy as np

from PyQt5.QtWidgets import QFileDialog, QMessageBox
from commonroad.planning.planning_problem import PlanningProblemSet

from commonroad.scenario.intersection import Intersection
from commonroad.scenario.scenario import Scenario
from commonroad.scenario.lanelet import Lanelet, LaneletNetwork
from commonroad.visualization.mp_renderer import MPRenderer

from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.gui_sumo_simulation import SUMO_AVAILABLE
from .service_layer.draw_params_updater import DrawParamsCustom
from ...service_layer import config

if SUMO_AVAILABLE:
    from crdesigner.map_conversion.sumo_map.config import SumoConfig
from crdesigner.ui.gui.mwindow.service_layer.util import Observable

from matplotlib.animation import FuncAnimation

from .dynamic_canvas import DynamicCanvas
from .helper import draw_lanelet_polygon


class AnimatedViewer:
    def __init__(self, parent, callback_function):

        self.current_scenario = None
        self.current_pps = None
        self.parent = parent
        self.dynamic = DynamicCanvas(parent, width=5, height=10, dpi=100, animated_viewer=self)
        self.callback_function = callback_function
        self.original_lanelet_network = None
        self.update_window()

        # sumo config giving dt etc
        self._config: SumoConfig = None
        self.min_time_step = 0
        self.max_time_step = 0
        # current time step
        self.time_step = Observable(0)
        # FuncAnimation object
        self.animation: FuncAnimation = None
        # if playing or not
        self.playing = False

    def open_scenario(self, scenario: Scenario, config: Observable = None,
                      planning_problem_set: PlanningProblemSet = None):
        """[summary]
        Open a scenario, setup any configuration.
        :param scenario: [description]
        :type scenario: [type]
        :param config: [description], defaults to None
        :type config: SumoConfig, optional
        :param planning_problem_set: des,
        :type planning_problem_set: PlanningProblemSet
        """
        self.dynamic.initial_parameter_config_done = False  # reset so that for any map the parameters are set correctly
        self.current_scenario = scenario
        # safe here the original scenario -> this is needed for zooming in / out and for moving around
        self.original_lanelet_network = LaneletNetwork.create_from_lanelet_network(
                lanelet_network=scenario.lanelet_network)
        self.current_pps = planning_problem_set

        # initialize lanelet network
        self.dynamic.l_network = self.current_scenario.lanelet_network

        # if we have not subscribed already, subscribe now
        if config is not None:
            if not self._config:
                def set_config(conf):
                    self._config = conf
                    self._calc_max_timestep()
                config.subscribe(set_config)
            self._config = config.value

        self._calc_max_timestep()
        if self.animation:
            self.time_step.value = 0
            self.animation.event_source.stop()
            self.animation = None
        self.update_plot(focus_on_network=True, clear_artists=True)

    def _init_animation(self):
        if not self.current_scenario:
            return

        print('init animation')
        scenario = self.current_scenario
        pps = self.current_pps
        self.dynamic.clear_axes(keep_limits=True)

        start = self.min_time_step
        end = self.max_timestep
        plot_limits: Union[list, None, str] = None
        if self._config is not None:
            dt = self._config.dt
        else:
            dt = 0
        # ps = 25
        # dpi = 120
        # ln, = self.dynamic.ax.plot([], [], animated=True)
        anim_frames = end - start

        if start == end:
            warning_dialog = QMessageBox()
            warning_dialog.warning(None, "Warning",
                                   "This Scenario only has one time step!",
                                   QMessageBox.Ok, QMessageBox.Ok)
            warning_dialog.close()

        assert start <= end, '<video/create_scenario_video> time_begin=%i needs to smaller than time_end=%i.' % (
            start, end)

        def draw_frame(draw_params):
            self.time_step.value += 1
            time_start = start + self.time_step.value
            time_end = start + min(anim_frames, self.time_step.value)
            if time_start > time_end:
                self.time_step.value = 0

            draw_params = DrawParamsCustom(time_begin=time_start, time_end=time_end)
            draw_params.dynamic_obstacle.time_begin = draw_params.time_begin
            draw_params.dynamic_obstacle.time_end = draw_params.time_end
            draw_params.dynamic_obstacle.trajectory.draw_trajectory = False
            self.dynamic.draw_scenario(scenario=scenario, pps=pps, draw_params=draw_params)

        # Interval determines the duration of each frame in ms
        interval = 1000 * dt
        self.dynamic.clear_axes(keep_limits=True)
        self.animation = FuncAnimation(self.dynamic.figure,
                                       draw_frame,
                                       blit=False,
                                       interval=interval,
                                       repeat=True)

    def play(self):
        """ plays the animation if existing """
        if not self.animation:
            self._init_animation()

        self.dynamic.update_plot()
        self.animation.event_source.start()

    def pause(self):
        """ pauses the animation if playing """
        if not self.animation:
            self._init_animation()
            return

        self.animation.event_source.stop()

    def set_timestep(self, timestep: int):
        """ sets the animation to the current timestep """
        print("set timestep: ", timestep)
        if not self.animation:
            self._init_animation()
        self.dynamic.update_plot()
        # self.animation.event_source.start()
        self.time_step.silent_set(timestep)

    def save_animation(self):
        path, _ = QFileDialog.getSaveFileName(
            caption="QFileDialog.getSaveFileName()",
            directory=self.current_scenario.scenario_id.__str__() + ".mp4",
            filter="MP4 (*.mp4);;GIF (*.gif);; AVI (*avi)",
            options=QFileDialog.Options(),
        )
        if not path:
            return

        try:
            rnd = MPRenderer()
            with open(path, "w"):
                QMessageBox.about(None, "Information",
                                  "Exporting the video will take few minutes, please wait until process is finished!")
                rnd.create_video([self.current_scenario], path, draw_params=self.dynamic.draw_params)
                print("finished")
        except IOError as e:
            QMessageBox.critical(
                self,
                "CommonRoad file not created!",
                "The CommonRoad scenario was not saved as video due to an error.\n\n{}".format(e),
                QMessageBox.Ok,
            )
            return

    def _calc_max_timestep(self) -> int:
        """Calculates maximal time step of current scenario."""
        if self.current_scenario is None:
            return 0

        if len(self.current_scenario.dynamic_obstacles) > 0 \
                and self.current_scenario.dynamic_obstacles[0].prediction is not None:
            time_steps = [
                obstacle.prediction.occupancy_set[-1].time_step
                for obstacle in self.current_scenario.dynamic_obstacles
            ]
            self.max_timestep = np.max(time_steps) if time_steps else 0
        else:
            self.max_timestep = 0

        return self.max_timestep

    def update_plot(self,
                    sel_lanelets: Lanelet = None,
                    sel_intersection: Intersection = None,
                    time_step_changed: bool = False,
                    focus_on_network: bool = False,
                    time_step: int = 0,
                    clear_artists=False):
        """ Update the plot accordingly to the selection of scenario elements
        :param sel_lanelets: selected lanelet, defaults to None
        :param sel_intersection: selected intersection, defaults to None
        :param clear_artists: deletes artists from renderer (only required when opening new scenarios)
        """
        if not isinstance(sel_lanelets, list) and sel_lanelets:
            sel_lanelets = [sel_lanelets]

        x_lim = self.dynamic.get_axes().get_xlim()
        y_lim = self.dynamic.get_axes().get_ylim()

        self.dynamic.clear_axes(clear_artists=clear_artists)
        ax = self.dynamic.get_axes()


        network_limits = [
            float("Inf"), -float("Inf"),
            float("Inf"), -float("Inf")
        ]

        if time_step_changed:
            draw_params = DrawParamsCustom(time_begin=time_step, color_schema=self.parent.colorscheme())
        else:
            draw_params = DrawParamsCustom(time_begin=self.time_step.value - 1, color_schema=self.parent.colorscheme())
        draw_params.dynamic_obstacle.trajectory.draw_trajectory = False
        self.dynamic.draw_scenario(self.current_scenario, self.current_pps, draw_params=draw_params)

        for lanelet in self.current_scenario.lanelet_network.lanelets:

            color, alpha, zorder, label = self.get_paint_parameters(
                lanelet, sel_lanelets, sel_intersection)
            if color == "gray":
                continue

            lanelet_limits = draw_lanelet_polygon(lanelet, ax, color, alpha, zorder, label)
            network_limits[0] = min(network_limits[0], lanelet_limits[0])
            network_limits[1] = max(network_limits[1], lanelet_limits[1])
            network_limits[2] = min(network_limits[2], lanelet_limits[2])
            network_limits[3] = max(network_limits[3], lanelet_limits[3])

            self.draw_lanelet_vertices(lanelet, ax)

        handles, labels = ax.get_legend_handles_labels()
        if sel_lanelets != None and config.LEGEND:
            legend = ax.legend(handles, labels)
            legend.set_zorder(50)

        if focus_on_network:
            # can we focus on a selection?
            if all([abs(lim) < float("Inf") for lim in network_limits]):
                # enlarge limits
                border_x = (network_limits[1] - network_limits[0]) * 0.1 + 1
                border_y = (network_limits[3] - network_limits[2]) * 0.1 + 1
                network_limits[0] -= border_x
                network_limits[1] += border_x
                network_limits[2] -= border_y
                network_limits[3] += border_y
                self.dynamic.update_plot(network_limits)
            # otherwise focus on the network
            else:
                self.dynamic.ax.autoscale()
        else:
            self.dynamic.update_plot([x_lim[0], x_lim[1], y_lim[0], y_lim[1]])

        self.dynamic.drawer.tight_layout()

    def get_paint_parameters(self, lanelet: Lanelet, selected_lanelets: Lanelet,
                             selected_intersection: Intersection):
        """
        Return the parameters for painting a lanelet regarding the selected lanelet.
        """
        if selected_lanelets:
            if len(selected_lanelets) == 1:
                selected_lanelet = selected_lanelets[0]
                if lanelet.lanelet_id == selected_lanelet.lanelet_id:
                    color = "red"
                    alpha = 0.7
                    zorder = 20
                    label = "{} selected".format(lanelet.lanelet_id)

                elif (
                        lanelet.lanelet_id in selected_lanelet.predecessor and lanelet.lanelet_id in
                        selected_lanelet.successor):
                    color = "purple"
                    alpha = 0.5
                    zorder = 10
                    label = "{} predecessor and successor of {}".format(lanelet.lanelet_id, selected_lanelet.lanelet_id)

                elif lanelet.lanelet_id in selected_lanelet.predecessor:
                    color = "blue"
                    alpha = 0.5
                    zorder = 10
                    label = "{} predecessor of {}".format(lanelet.lanelet_id, selected_lanelet.lanelet_id)
                elif lanelet.lanelet_id in selected_lanelet.successor:
                    color = "green"
                    alpha = 0.5
                    zorder = 10
                    label = "{} successor of {}".format(lanelet.lanelet_id, selected_lanelet.lanelet_id)
                elif lanelet.lanelet_id == selected_lanelet.adj_left:
                    color = "yellow"
                    alpha = 0.5
                    zorder = 10
                    label = "{} adj left of {} ({})".format(lanelet.lanelet_id, selected_lanelet.lanelet_id,
                            "same" if selected_lanelet.adj_left_same_direction else "opposite", )
                elif lanelet.lanelet_id == selected_lanelet.adj_right:
                    color = "orange"
                    alpha = 0.5
                    zorder = 10
                    label = "{} adj right of {} ({})".format(lanelet.lanelet_id, selected_lanelet.lanelet_id,
                            "same" if selected_lanelet.adj_right_same_direction else "opposite", )
                else:
                    color = "gray"
                    alpha = 0.3
                    zorder = 0
                    label = None
            else:
                if any(lanelet.lanelet_id == lane.lanelet_id for lane in selected_lanelets):
                    color = "red"
                    alpha = 0.7
                    zorder = 20
                    label = "{} selected".format(lanelet.lanelet_id)
                else:
                    color = "gray"
                    alpha = 0.3
                    zorder = 0
                    label = None
        elif selected_intersection:
            incoming_ids = selected_intersection.map_incoming_lanelets.keys()
            inc_succ_ids = set()
            for inc in selected_intersection.incomings:
                inc_succ_ids |= inc.successors_right
                inc_succ_ids |= inc.successors_left
                inc_succ_ids |= inc.successors_straight

            if lanelet.lanelet_id in incoming_ids:
                color = "red"
                alpha = 0.7
                zorder = 10
                label = "{} incoming".format(lanelet.lanelet_id)
            elif lanelet.lanelet_id in selected_intersection.crossings:
                color = "blue"
                alpha = 0.5
                zorder = 10
                label = "{} crossing".format(lanelet.lanelet_id)
            elif lanelet.lanelet_id in inc_succ_ids:
                color = "green"
                alpha = 0.3
                zorder = 10
                label = "{} intersection".format(lanelet.lanelet_id)
            else:
                color = "gray"
                alpha = 0.3
                zorder = 0
                label = None
        else:
            color = "gray"
            alpha = 0.3
            zorder = 0
            label = None

        return color, alpha, zorder, label

    def draw_lanelet_vertices(self, lanelet, ax):
        ax.plot(
            [x for x, y in lanelet.left_vertices],
            [y for x, y in lanelet.left_vertices],
            color="black",
            lw=0.1,
        )
        ax.plot(
            [x for x, y in lanelet.right_vertices],
            [y for x, y in lanelet.right_vertices],
            color="black",
            lw=0.1,
        )

    def update_window(self):
        self.dynamic.setStyleSheet('background-color:' + self.parent.colorscheme().second_background + '; color:' + self.parent.colorscheme().color + ';font-size: ' + self.parent.colorscheme().font_size)
