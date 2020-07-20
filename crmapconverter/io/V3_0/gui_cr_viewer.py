""" """

from typing import Union
from matplotlib import animation

from matplotlib.backends.backend_qt5agg import (
    NavigationToolbar2QT as NavigationToolbar
)

from matplotlib.animation import FuncAnimation
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from crmapconverter.io.viewer import (
    LaneletList,
    IntersectionList,
    Viewer,
    find_intersection_by_id
)


class Observable:
    def __init__(self, value, observers=[]):
        self._value = value
        self._observers = observers

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        for obs in self._observers:
            obs(value)
        self._value = value

    def silent_set(self, value):
        self._value = value

    def subscribe(self, observer):
        self._observers.append(observer)


class CrViewer(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.viewer = Viewer(self)
        
        self.current_scenario = None
        self.max_step = 0
        # current time ste
        self.timestep = Observable(0)
        # FuncAnimation object
        self.animation = None
        # if playing or not
        self.playing = False

        self._init_user_interface()

    def _init_user_interface(self):
        self.toolbar = NavigationToolbar(self.viewer.dynamic, self)
        self.setWindowFlag(Qt.WindowCloseButtonHint)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.viewer.dynamic)
        self.setLayout(layout)

        self.lanelet_list = LaneletList(self.update, self)
        self.intersection_list = IntersectionList(self.update, self)

    def open_scenario(self, scenario):
        """ """
        self.current_scenario = scenario
        self.calc_max_timestep()
        self.update()

    def update(self):
        """ update all compoments """
        self.make_trigger_exclusive()
        self.lanelet_list.update(self.current_scenario)
        self.intersection_list.update(self.current_scenario)

        if self.current_scenario is None:
            return
        if self.intersection_list.selected_id is not None:
            selected_intersection = find_intersection_by_id(
                self.current_scenario, self.intersection_list.selected_id)
        else:
            selected_intersection = None
        if self.lanelet_list.selected_id is not None:
            selected_lanelet = self.current_scenario.lanelet_network.find_lanelet_by_id(
                self.lanelet_list.selected_id)
        else:
            selected_lanelet = None
        self.viewer.update_plot(
            scenario=self.current_scenario,
            sel_lanelet=selected_lanelet,
            sel_intersection=selected_intersection
        )

    def make_trigger_exclusive(self):
        """ 
        Only one component can trigger the plot update
        """
        if self.lanelet_list.new:
            self.lanelet_list.new = False
            self.intersection_list.reset_selection()
        elif self.intersection_list.new:
            self.intersection_list.new = False
            self.lanelet_list.reset_selection()
        else:
            # triggered by click on canvas
            self.lanelet_list.reset_selection()
            self.intersection_list.reset_selection()

    def _init_animation(self):
        print('init animation')
        scenario = self.current_scenario
        self.viewer.dynamic.ax.clear()

        start: int = 0
        end: int = self.max_step
        delta_time_steps: int = 1
        plotting_horizon = 0
        plot_limits: Union[list, None, str] = None
        dt = 0.1
        # ps = 25
        # dpi = 120
        # ln, = self.viewer.dynamic.ax.plot([], [], animated=True)

        if scenario is not None:
            if start == end:
                warning_dia = QMessageBox()
                reply = warning_dia.warning(self, "Warning",
                                            "This Scenario only has one time step!",
                                            QMessageBox.Ok,
                                            QMessageBox.Ok)
                if reply == QMessageBox.Ok:
                    warning_dia.close()

            assert start <= end, '<video/create_scenario_video> time_begin=%i needs to smaller than time_end=%i.' % (
                start, end)

            def draw_frame(draw_params):
                print('next frame')
                time_begin = start + delta_time_steps * self.timestep.value
                time_end = start + min(
                    frame_count,
                    delta_time_steps * self.timestep.value + plotting_horizon)
                self.timestep.value += 1
                if time_begin > time_end:
                    self.timestep.value=0

                draw_params = {'time_begin': time_begin, 'time_end': time_end}
                print("draw frame ", self.timestep.value, draw_params)
                # plot frame
                self.viewer.dynamic.draw_object(
                    scenario,
                    draw_params=draw_params,
                    plot_limits=None if plot_limits == 'auto' else plot_limits)

            frame_count = (end - start) // delta_time_steps
            # Interval determines the duration of each frame in ms
            interval = 1000 * dt
            self.animation = FuncAnimation(self.viewer.dynamic.figure,
                                           draw_frame,
                                           blit=False,
                                           interval=interval,
                                           repeat=True)

    def play(self):
        """ plays the animation if existing """
        if not self.animation:
            self._init_animation()
        self.viewer.dynamic.update_plot()
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
        self.viewer.dynamic.update_plot()
        #self.animation.event_source.start()
        self.timestep.silent_set(timestep)

    def save_animation(self, save_file: str):
        if save_file == "Save as mp4":
            if not self.current_scenario:
                return
            path, _ = QFileDialog.getSaveFileName(
                self,
                "QFileDialog.getSaveFileName()",
                ".mp4",
                "CommonRoad scenario video *.mp4 (*.mp4)",
                options=QFileDialog.Options(),
            )

            if not path:
                self.NoFilenamed()
                return

            try:
                with open(path, "w") as fh:
                    FFMpegWriter = animation.writers['ffmpeg']
                    writer = FFMpegWriter()
                    self.animation.save(path, dpi=120, writer=writer)

            except IOError as e:
                QMessageBox.critical(
                    self,
                    "CommonRoad file not created!",
                    "The CommonRoad file was not saved due to an error.\n\n{}".format(e),
                    QMessageBox.Ok,
                )
                return

        elif save_file == "Save as gif":
            if not self.current_scenario:
                return
            path, _ = QFileDialog.getSaveFileName(
                self,
                "QFileDialog.getSaveFileName()",
                ".gif",
                "CommonRoad scenario video *.gif (*.gif)",
                options=QFileDialog.Options(),
            )

            if not path:
                self.NoFilenamed()
                return

            try:
                with open(path, "w") as fh:
                    self.animation.save(path, writer='imagemagick', fps=30)

            except (IOError) as e:
                QMessageBox.critical(
                    self,
                    "CommonRoad file not created!",
                    "The CommonRoad file was not saved due to an error.\n\n{}".format(e),
                    QMessageBox.Ok,
                )
                return

    def calc_max_timestep(self):
        """calculate maximal time step of current scenario"""
        max_num = 0
        for obstacle in self.current_scenario.dynamic_obstacles:
            num = obstacle.prediction.occupancy_set[-1].time_step
            if num > max_num:
                max_num = num
        self.max_step = max_num

    # def load_empty_scenario(self):
    #     """ called by button new scenario """
    #     scenario = Scenario(0.1, 'new scenario')
    #     net = LaneletNetwork()
    #     scenario.lanelet_network = net
    #     self.open_scenario(scenario)