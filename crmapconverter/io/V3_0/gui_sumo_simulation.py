import copy
import os
import sys
from lxml import etree
from typing import List, Union
from ffpyplayer.player import MediaPlayer
from celluloid import Camera

from commonroad.visualization.util import approximate_bounding_box_dyn_obstacles
from matplotlib.animation import FuncAnimation
from matplotlib import animation
from numpy import arange, sin, pi
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from commonroad.common.file_writer import CommonRoadFileWriter
from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.visualization.video import create_scenario_video
from commonroad.visualization.draw_dispatch_cr import draw_object, plottable_types
from IPython import display

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPixmap, QImage, QImageReader
from PyQt5.QtCore import QTimer

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt


class DynamicCanvas(FigureCanvas):
    """A canvas that updates itself every second with a new plot."""

    def __init__(self, parent=None, width=10.8, height=7.2, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        #self.axes = fig.add_subplot(111)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlim(0, 600)
        self.ax.set_ylim(0, 600)
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def clear_axes(self):
        """ """
        if self.ax is not None:
            self.ax.clear()
        else:

            self.ax = self.fig.add_subplot(111)
        self.ax.set_aspect("equal", "datalim")
        self.ax.set_axis_off()
        self.draw()


class Sumo_simulation_play(QWidget):

    def __init__(self, path, parent=None, current_scenario=None):
        super(Sumo_simulation_play, self).__init__()
        self.main_widget = QWidget(self)
        self.current_scenario = None
        self.commonroad_filename = None
        self.canvas = DynamicCanvas(self.main_widget)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.path = path

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.canvas.fig.tight_layout()
        if self.path == None:
            self.openCommonRoadFile()
        else:
            self.openPath(self.path)

    def openCommonRoadFile(self):
        """ """
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open a from SUMO converted CommonRoad scenario",
            "",
            "CommonRoad scenario files *.xml (*.xml)",
            options=QFileDialog.Options(),
        )

        if not path:
            self.NoFileselected()
            return
        self.path = path
        self.openPath(path)

    def openPath(self, path):
        """
        Args:
          path:

        Returns:
        """

        filename = os.path.basename(path)
        self.commonroad_filename = filename

        try:
            # fh = open(path, "rb")
            # data = fh.read()
            # fh.close()
            commonroad_reader = CommonRoadFileReader(path)
            scenario, _ = commonroad_reader.open()

        except etree.XMLSyntaxError as e:
            errorMsg = "Syntax Error: {}".format(e)
            QMessageBox.warning(
                self,
                "CommonRoad XML error",
                "There was an error during the loading of the selected CommonRoad file.\n\n{}".format(
                    errorMsg
                ),
                QMessageBox.Ok,
            )
            return
        except Exception as e:
            errorMsg = "{}".format(e)
            QMessageBox.warning(
                self,
                "CommonRoad XML error",
                "There was an error during the loading of the selected CommonRoad file.\n\n{}".format(
                    errorMsg
                ),
                QMessageBox.Ok,
            )
            return

        self.play(scenario)

    def play(self, current_scenario):
        self.current_scenario = current_scenario
        time_begin: int = 0
        time_end: int = 50
        delta_time_steps: int = 1
        plotting_horizon = 0
        plot_limits: Union[list, None, str] = None
        draw_params: Union[dict, None] = {}
        fig_size: Union[list, None] = None
        dt = 0.1
        ps: int = 25
        dpi = 120
        ln, = self.canvas.ax.plot([], [], animated=True)

        assert time_begin < time_end, '<video/create_scenario_video> time_begin=%i needs to smaller than time_end=%i.' % (
            time_begin, time_end)

        def update(frame=0):
            # plot frame
            self.canvas.ax.clear()
            draw_params.update({
                'time_begin': time_begin + delta_time_steps * frame,
                'time_end': time_begin + min(frame_count, delta_time_steps * frame + plotting_horizon)
            })
            plot_limits_tmp = None if plot_limits == 'auto' else plot_limits

            draw_object(
                current_scenario,
                ax=self.canvas.ax,
                draw_params=draw_params,
                plot_limits=plot_limits_tmp)
            self.canvas.ax.autoscale()
            self.canvas.ax.set_aspect('equal')

            return ln,

        frame_count = (time_end - time_begin) // delta_time_steps
        # Interval determines the duration of each frame
        interval = 1.0 / dt
        self.ani = FuncAnimation(
            self.canvas.figure,
            update,
            frames=frame_count,
            init_func=update,
            blit=False,
            interval=interval,
            repeat=True)

    def saveanimation(self, save_file):
        self.ani._stop()
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
                    self.ani.save(path, dpi=120, writer=writer)

            except (IOError) as e:
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
                    self.ani.save(path, writer='imagemagick', fps=30)

            except (IOError) as e:
                QMessageBox.critical(
                    self,
                    "CommonRoad file not created!",
                    "The CommonRoad file was not saved due to an error.\n\n{}".format(e),
                    QMessageBox.Ok,
                )
                return

    def NoFileselected(self):
        messbox = QMessageBox()
        reply = messbox.information(
            self,
            "Information",
            "Please select a Sumo-CR Scenario",
            QMessageBox.Ok | QMessageBox.No,
            QMessageBox.Ok)

        if reply == QMessageBox.Ok:
            self.openCommonRoadFile()
        else:
            messbox.close()


class Sumo_simulation_step_play(QWidget):

    def __init__(self, path, parent=None, current_scenario=None):
        super(Sumo_simulation_step_play, self).__init__()
        self.path = path
        self.main_widget = QWidget(self)
        self.current_scenario = None
        self.commonroad_filename = None
        self.canvas = DynamicCanvas(self.main_widget)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.canvas.mpl_connect('scroll_event', self.zoom)
        self.canvas.mpl_connect('button_press_event', self.zoom)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.canvas.fig.tight_layout()
        self.openCommonRoadFile()

    def openCommonRoadFile(self):
        """ """
        if self.path != None:
            self.openPath(self.path)

    def openPath(self, path):
        """

        Args:
          path:

        Returns:

        """

        filename = os.path.basename(path)
        self.commonroad_filename = filename

        try:
            # fh = open(path, "rb")
            # data = fh.read()
            # fh.close()
            commonroad_reader = CommonRoadFileReader(path)
            scenario, _ = commonroad_reader.open()

        except etree.XMLSyntaxError as e:
            errorMsg = "Syntax Error: {}".format(e)
            QMessageBox.warning(
                self,
                "CommonRoad XML error",
                "There was an error during the loading of the selected CommonRoad file.\n\n{}".format(
                    errorMsg
                ),
                QMessageBox.Ok,
            )
            return
        except Exception as e:
            errorMsg = "{}".format(e)
            QMessageBox.warning(
                self,
                "CommonRoad XML error",
                "There was an error during the loading of the selected CommonRoad file.\n\n{}".format(
                    errorMsg
                ),
                QMessageBox.Ok,
            )
            return

        self.current_scenario = scenario

    def play_timesteps(self, current_scenario, timesteps):
        self.canvas.clear_axes()
        draw_object(
            current_scenario,
            ax=self.canvas.ax,
            draw_params={'time_begin': timesteps})
        self.canvas.ax.autoscale()
        self.canvas.ax.set_aspect('equal')
        self.canvas.draw()


    def zoom(self, event):
        """
                realize zoom in / out function in GUI
                Args:
                  event:

                Returns:

                """

        ax = event.inaxes   # get the axes which mouse is now
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()
        scope_x = (x_max - x_min) / 10
        scope_y = (y_max - y_min) / 10
        # xdata = event.xdata  # get event x location
        # ydata = event.ydata  # get event y location

        if event.button == 'up':
            ax.set(xlim=(x_min + scope_x, x_max - scope_x))
            ax.set(ylim=(y_min + scope_y, y_max - scope_y))
            print('up')
        elif event.button == 'down':
            ax.set(xlim=(x_min - scope_x, x_max + scope_x))
            ax.set(ylim=(y_min - scope_y, y_max + scope_y))
            print('down')

        self.canvas.draw_idle()
