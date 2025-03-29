from typing import List, Optional

from commonroad.scenario.intersection import Intersection
from commonroad.scenario.lanelet import Lanelet, LaneletNetwork
from commonroad.visualization.mp_renderer import MPRenderer
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from crdesigner.common.config.gui_config import gui_config
from crdesigner.common.sumo_available import SUMO_AVAILABLE
from crdesigner.ui.gui.controller.animated_viewer.dynamic_canvas_controller import (
    DynamicCanvasController,
)
from crdesigner.ui.gui.model.planning_problem_set_model import PlanningProblemSetModel
from crdesigner.ui.gui.utilities.helper import draw_lanelet_polygon

if SUMO_AVAILABLE:
    from crdesigner.map_conversion.sumo_map.config import SumoConfig

from matplotlib.animation import FuncAnimation

from crdesigner.ui.gui.utilities.util import Observable
from crdesigner.ui.gui.view.animated_viewer.animated_viewer_ui import AnimatedViewerUI


def extract_plot_limits(lanelet_network: LaneletNetwork) -> Optional[List[float]]:
    """
    Extracts plot limits from a lanelet network

    :param lanelet_network: CommonRoad lanelet network.
    :return: Plot limits or none if lanelet network is empty.
    """
    margin = 50
    if len(lanelet_network.lanelets) > 0:
        x_lanelet_left = [
            point[0] for lanelet in lanelet_network.lanelets for point in lanelet.left_vertices
        ]
        y_lanelet_left = [
            point[1] for lanelet in lanelet_network.lanelets for point in lanelet.left_vertices
        ]
        x_lanelet_right = [
            point[0] for lanelet in lanelet_network.lanelets for point in lanelet.right_vertices
        ]
        y_lanelet_right = [
            point[1] for lanelet in lanelet_network.lanelets for point in lanelet.right_vertices
        ]

        x_min = min(x_lanelet_left + x_lanelet_right) - margin
        y_min = min(y_lanelet_left + y_lanelet_right) - margin
        x_max = max(x_lanelet_left + x_lanelet_right) + margin
        y_max = max(y_lanelet_left + y_lanelet_right) + margin
        return [x_min, x_max, y_min, y_max]
    else:
        return None


class AnimatedViewerController:
    def __init__(self, mwindow, callback_function, scenario_model):
        # create view object
        self.view = AnimatedViewerUI()

        # self.current_scenario = None
        self.pps_model: PlanningProblemSetModel = mwindow.pps_model
        self.parent = mwindow.mwindow_ui
        self.scenario_model = scenario_model
        self.dynamic = DynamicCanvasController(
            self.parent, self.scenario_model, width=5, height=10, dpi=100, animated_viewer=self
        )
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

    def open_scenario(self, config: Observable = None, new_file_added: bool = None):
        """[summary]
        Open a scenario, setup any configuration.
        :param new_file_added: if a new cr file was created or added
        :param config: [description], defaults to None
        :param planning_problem_set: des,
        """
        self.dynamic.initial_parameter_config_done = (
            False  # reset so that for any map the parameters are set correctly
        )
        # safe here the original scenario -> this is needed for zooming in / out and for moving around

        self.original_lanelet_network = LaneletNetwork.create_from_lanelet_network(
            lanelet_network=self.scenario_model.get_lanelet_network()
        )

        # if we have not subscribed already, subscribe now
        if config is not None:
            if not self._config:

                def set_config(conf):
                    self._config = conf
                    self._calc_max_timestep()

                config.subscribe(set_config)
            self._config = config.value

        plot_limits = extract_plot_limits(self.scenario_model.get_lanelet_network())

        self._calc_max_timestep()
        if self.animation:
            self.animation.event_source.stop()
            self.animation = None
        else:
            self.time_step.value = 0

        if new_file_added:
            self.update_plot(
                clear_artists=True, new_file_added=new_file_added, plot_limits=plot_limits
            )

    def _init_animation(self):
        if not self.scenario_model.scenario_created():
            return

        print("init animation")
        pps = self.pps_model.get_selected_pp()
        self.dynamic.clear_axes(keep_limits=True)

        start = self.min_time_step
        end = self.max_timestep
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
            warning_dialog.warning(
                None,
                "Warning",
                "This Scenario only has one time step!",
                QMessageBox.StandardButton.Ok,
                QMessageBox.StandardButton.Ok,
            )
            warning_dialog.close()

        assert start <= end, (
            "<video/create_scenario_video> time_begin=%i needs to smaller than time_end=%i."
            % (
                start,
                end,
            )
        )

        def draw_frame(draw_params):
            self.time_step.value += 1
            time_start = start + self.time_step.value
            time_end = start + min(anim_frames, self.time_step.value)
            if time_start > time_end:
                self.time_step.value = 0

            draw_params = gui_config.get_draw_params()

            # draw_params.dynamic_obstacle = gui_config.get_obstacle_params()
            draw_params.time_begin = time_start
            draw_params.time_end = time_end
            draw_params.dynamic_obstacle.trajectory.time_begin = time_start
            draw_params.dynamic_obstacle.trajectory.time_end = end
            draw_params.trajectory.time_begin = time_start
            draw_params.trajectory.time_end = end
            self.dynamic.draw_scenario(pps=pps, draw_params=draw_params, draw_dynamic_only=True)

        # Interval determines the duration of each frame in ms
        interval = 1000 * dt
        self.dynamic.clear_axes(keep_limits=True)
        self.animation = FuncAnimation(
            self.dynamic.figure, draw_frame, blit=False, interval=interval, repeat=True
        )

    def play(self):
        """plays the animation if existing"""
        if not self.animation:
            self._init_animation()

        self.dynamic.draw_idle()
        self.animation.event_source.start()
        self.playing = True

    def pause(self):
        """pauses the animation if playing"""
        if not self.animation:
            self._init_animation()
            return

        self.animation.event_source.stop()
        self.playing = False

    def set_timestep(self, timestep: int):
        """sets the animation to the current timestep"""
        print("set timestep: ", timestep)
        if not self.animation:
            self._init_animation()
        self.dynamic.draw_idle()
        # self.animation.event_source.start()
        self.time_step.silent_set(timestep)

    def save_animation(self):
        path, _ = QFileDialog.getSaveFileName(
            caption="QFileDialog.getSaveFileName()",
            directory=self.scenario_model.get_scenario_id().__str__() + ".mp4",
            filter="MP4 (*.mp4);;GIF (*.gif);; AVI (*avi)",
        )
        if not path:
            return

        try:
            rnd = MPRenderer()
            with open(path, "w"):
                QMessageBox.about(
                    None,
                    "Information",
                    "Exporting the video will take few minutes, please wait "
                    "until process is finished!",
                )
                rnd.create_video(
                    [self.scenario_model.get_current_scenario()],
                    path,
                    draw_params=self.dynamic.draw_params,
                )
        except IOError as e:
            QMessageBox.critical(
                self,
                "CommonRoad file not created!",
                "The CommonRoad scenario was not saved as video due to an error.\n\n{}".format(e),
                QMessageBox.StandardButton.Ok,
            )
            return

    def _calc_max_timestep(self) -> int:
        """Calculates maximal time step of current scenario."""
        if not self.scenario_model.scenario_created():
            return 0

        # The maximum time step is usually given by the final time step in the prediction
        # of one of the dynamic obstacles
        max_prediction_final_time_steps = max(
            [
                dynamic_obstacle.prediction.final_time_step
                for dynamic_obstacle in self.scenario_model.get_dynamic_obstacles()
                if dynamic_obstacle.prediction is not None
            ],
            default=0,
        )
        # Additionally, consider the initial time step of each obstacle.
        # This makes sure that obstacles, which only have an initial state, no prediction
        # and enter the scenario after all other obstacles, are also displayed.
        max_initial_time_steps = max(
            [
                dynamic_obstacle.initial_state.time_step
                for dynamic_obstacle in self.scenario_model.get_dynamic_obstacles()
                if dynamic_obstacle.prediction is None
            ],
            default=0,
        )

        self.max_timestep = max(max_prediction_final_time_steps, max_initial_time_steps)

        return self.max_timestep

    def update_plot(
        self,
        sel_lanelets: Lanelet = None,
        sel_intersection: Intersection = None,
        time_step_changed: bool = False,
        time_step: int = 0,
        clear_artists: bool = False,
        new_file_added: bool = False,
        plot_limits: Optional[List[float]] = None,
    ):
        """Update the plot accordingly to the selection of scenario elements
        :param new_file_added: if a new cr file was created or added
        :param sel_lanelets: selected lanelet, defaults to None
        :param sel_intersection: selected intersection, defaults to None
        :param clear_artists: deletes artists from renderer (only required when opening new scenarios)
        :param plot_limits: plot limits (area of axis) which should be visualized
        """
        if not isinstance(sel_lanelets, list) and sel_lanelets:
            sel_lanelets = [sel_lanelets]
        x_lim = self.dynamic.get_axes().get_xlim()
        y_lim = self.dynamic.get_axes().get_ylim()

        self.dynamic.clear_axes(clear_artists=clear_artists)
        ax = self.dynamic.get_axes()
        self.dynamic.drawer.tight_layout(pad=4.5)

        if time_step_changed:
            time_begin = time_step
        else:
            time_begin = max(0, self.time_step.value - 1)

        if new_file_added:
            self.dynamic.show_aerial = False
            self.new_file_added = False
            if plot_limits is not None:
                x_dim = (plot_limits[1] - plot_limits[0]) / 2
                y_dim = (plot_limits[3] - plot_limits[2]) / 2
                gui_config.set_zoom_treshold(x_dim, y_dim)

        self.dynamic.draw_scenario(self.pps_model.get_selected_pp(), time_begin=time_begin)

        for lanelet in self.scenario_model.get_lanelets():
            color, alpha, zorder, label = self.get_paint_parameters(
                lanelet, sel_lanelets, sel_intersection
            )
            if color == "gray":
                continue

            draw_lanelet_polygon(lanelet, ax, color, alpha, zorder, label)
            self.view.draw_lanelet_vertices(lanelet, ax)

        handles, labels = ax.get_legend_handles_labels()
        if sel_lanelets is not None and gui_config.LEGEND:
            legend = ax.legend(handles, labels)
            legend.set_zorder(50)

        if new_file_added and plot_limits is None:
            # initialise the axis to a bigger range
            self.dynamic.set_limits([-50, 50, -50, 50])
            self.dynamic.draw_idle()
        elif new_file_added:
            self.dynamic.set_limits(plot_limits)
        # otherwise keep previous limits (persist zoom)
        else:
            self.dynamic.set_limits([x_lim[0], x_lim[1], y_lim[0], y_lim[1]])
            self.dynamic.draw_idle()

    def get_paint_parameters(
        self, lanelet: Lanelet, selected_lanelets: Lanelet, selected_intersection: Intersection
    ):
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
                    lanelet.lanelet_id in selected_lanelet.predecessor
                    and lanelet.lanelet_id in selected_lanelet.successor
                ):
                    color = "purple"
                    alpha = 0.5
                    zorder = 10
                    label = "{} predecessor and successor of {}".format(
                        lanelet.lanelet_id, selected_lanelet.lanelet_id
                    )

                elif lanelet.lanelet_id in selected_lanelet.predecessor:
                    color = "blue"
                    alpha = 0.5
                    zorder = 10
                    label = "{} predecessor of {}".format(
                        lanelet.lanelet_id, selected_lanelet.lanelet_id
                    )
                elif lanelet.lanelet_id in selected_lanelet.successor:
                    color = "green"
                    alpha = 0.5
                    zorder = 10
                    label = "{} successor of {}".format(
                        lanelet.lanelet_id, selected_lanelet.lanelet_id
                    )
                elif lanelet.lanelet_id == selected_lanelet.adj_left:
                    color = "yellow"
                    alpha = 0.5
                    zorder = 10
                    label = "{} adj left of {} ({})".format(
                        lanelet.lanelet_id,
                        selected_lanelet.lanelet_id,
                        "same" if selected_lanelet.adj_left_same_direction else "opposite",
                    )
                elif lanelet.lanelet_id == selected_lanelet.adj_right:
                    color = "orange"
                    alpha = 0.5
                    zorder = 10
                    label = "{} adj right of {} ({})".format(
                        lanelet.lanelet_id,
                        selected_lanelet.lanelet_id,
                        "same" if selected_lanelet.adj_right_same_direction else "opposite",
                    )
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

    def update_window(self):
        self.dynamic.setStyleSheet(
            "background-color:"
            + self.parent.colorscheme().second_background
            + "; color:"
            + self.parent.colorscheme().color
            + ";font-size: "
            + self.parent.colorscheme().font_size
        )
