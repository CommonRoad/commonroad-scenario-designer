""" """

from typing import Union
import numpy as np
from matplotlib import animation

from PyQt5.QtWidgets import (
    QMessageBox,
    QFileDialog,
)
from matplotlib.animation import FuncAnimation
from crmapconverter.io.viewer import Viewer
from crmapconverter.sumo_map.config import SumoConfig
from crmapconverter.io.V3_0.observable import Observable


class AnimatedViewer(Viewer):
    def __init__(self, parent):
        super().__init__(parent)

        # sumo config giving dt etc
        self._config: SumoConfig = None
        self.current_scenario = None
        self.min_timestep = 0
        self.max_timestep = 0
        # current time step
        self.timestep = Observable(0)
        # FuncAnimation object
        self.animation: FuncAnimation = None
        # if playing or not
        self.playing = False

    def open_scenario(self, scenario, config: SumoConfig):
        """[summary]

        :param scenario: [description]
        :type scenario: [type]
        :param config: [description], defaults to None
        :type config: SumoConfig, optional
        """
        self.current_scenario = scenario
        self._config = config if config else self._config

        self._calc_max_timestep()
        if self.animation:
            self.timestep.value = 0
            self.animation.event_source.stop()
            self.animation = None
        self.update_plot(scenario)

    def _init_animation(self):
        if not self.current_scenario:
            return

        print('init animation')
        scenario = self.current_scenario
        self.dynamic.clear_axes(keep_limits=True)

        start = self.min_timestep
        end = self.max_timestep
        plot_limits: Union[list, None, str] = None
        dt = self._config.dt
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
            time_start = start + self.timestep.value
            time_end = start + min(anim_frames, self.timestep.value)
            self.timestep.value += 1
            if time_start > time_end:
                self.timestep.value = 0

            draw_params = {
                'time_begin': time_start,
                'time_end': time_end,
                'antialiased': True,
                'dynamic_obstacle': {
                    'show_label': True
                }
            }

            # plot dynamic obstracles
            if self.timestep.value == 1:
                self.dynamic.draw_scenario(
                    scenario,
                    draw_params=draw_params,
                    plot_limits=None if plot_limits == 'auto' else plot_limits)
            else:
                self.dynamic.update_obstacles(
                    scenario,
                    draw_params=draw_params,
                    plot_limits=None if plot_limits == 'auto' else plot_limits)

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

    def set_time_step(self, timestep: int):
        """ sets the animation to the current timestep """
        print("set timestep: ", timestep)
        if not self.animation:
            self._init_animation()
        self.dynamic.update_plot()
        #self.animation.event_source.start()
        self.timestep.silent_set(timestep)

    def save_animation(self, save_file: str):
        if self.animation is None:
            print("no animation loaded")
            return
        if save_file == "Save as mp4":
            if not self.current_scenario:
                return
            path, _ = QFileDialog.getSaveFileName(
                None,
                "QFileDialog.getSaveFileName()",
                ".mp4",
                "CommonRoad scenario video *.mp4 (*.mp4)",
                options=QFileDialog.Options(),
            )

            if not path:
                return

            try:
                with open(path, "w"):
                    FFMpegWriter = animation.writers['ffmpeg']
                    writer = FFMpegWriter()
                    self.animation.save(path, dpi=120, writer=writer)

            except IOError as e:
                QMessageBox.critical(
                    None,
                    "CommonRoad file not created!",
                    "The CommonRoad file was not saved due to an error.\n\n{}".
                    format(e),
                    QMessageBox.Ok,
                )
                return

        elif save_file == "Save as gif":
            if not self.current_scenario:
                return
            path, _ = QFileDialog.getSaveFileName(
                None,
                "QFileDialog.getSaveFileName()",
                ".gif",
                "CommonRoad scenario video *.gif (*.gif)",
                options=QFileDialog.Options(),
            )

            if not path:
                return

            try:
                with open(path, "w"):
                    self.animation.save(path, writer='imagemagick', fps=30)

            except IOError as e:
                QMessageBox.critical(
                    self,
                    "CommonRoad file not created!",
                    "The CommonRoad file was not saved due to an error.\n\n{}".
                    format(e),
                    QMessageBox.Ok,
                )
                return

    def _calc_max_timestep(self):
        """calculate maximal time step of current scenario"""
        print('_calc_max_timestep')
        timesteps = [
            obstacle.prediction.occupancy_set[-1].time_step
            for obstacle in self.current_scenario.dynamic_obstacles
        ]
        self.max_timestep = np.max(timesteps) if timesteps else 0
        return self.max_timestep
