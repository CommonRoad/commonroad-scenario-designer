from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.animation import FuncAnimation
from typing import Union

from PyQt5.QtWidgets import (
    QTableWidget,
    QLineEdit,
    QFileDialog,
    QMessageBox,
    QVBoxLayout,
    QAbstractItemView,
    QDesktopWidget
)
from PyQt5.QtCore import Qt

from commonroad.visualization.draw_dispatch_cr import draw_object

from crmapconverter.io.V3_0.GUI_resources.MainWindow import Ui_mainWindow
from crmapconverter.io import viewer


class MyCanvas(viewer.Canvas):
    """Ultimately, this is a QWidget."""

    def draw_object(self, scenario, draw_params, plot_limits):
        self.ax.clear()
        draw_object(scenario,
                    ax=self.ax,
                    draw_params=draw_params,
                    plot_limits=plot_limits)
        self.ax.autoscale()
        self.ax.set_aspect('equal')


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


class CrViewer(viewer.MainWindow):
    """ """
    def __init__(self, parent=None):
        super().__init__(parent)

        # FuncAnimation object
        self.animation = None
        # if playing or not
        self.playing = False
        # current time ste
        self.timestep = Observable(0)

    def build_window(self):
        """overwrites method that is call by constructor of viewer.MainWindow"""
        
        self.canvas = MyCanvas(self, width=10.8, height=7.2, dpi=100)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.setWindowFlag(Qt.WindowCloseButtonHint)

        # exists for parent class methods -> don't show
        self.inputCommonRoadFile = QLineEdit(self)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.laneletsList = QTableWidget(self)
        self.laneletsList.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.laneletsList.clicked.connect(self.on_click_lanelet)

        self.intersection_list = QTableWidget(self)
        self.intersection_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.intersection_list.clicked.connect(self.on_click_intersection)

    def open_commonroad_file(self):
        """ overwrites """
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open a CommonRoad scenario",
            "",
            "CommonRoad scenario files *.xml (*.xml)",
            options=QFileDialog.Options(),
        )

        if not path:
            self.no_file_selected()
            return

        self.open_path(path)

    def no_file_selected(self):
        messbox = QMessageBox()
        # self.center(messbox)
        reply = messbox.information(self, "Information",
                                    "Please select a CR file",
                                    QMessageBox.Ok | QMessageBox.No,
                                    QMessageBox.Ok)

        if reply == QMessageBox.Ok:
            self.open_commonroad_file()
        else:
            self.close

    def center(self, x):
        screen = QDesktopWidget().screenGeometry()
        size = x.geometry()
        print(screen)
        print(size)
        x.move((screen.width() - size.width()) / 2,
               (screen.height() - size.height()) / 2)
        print((screen.width() - size.width()) / 100)
        print((screen.height() - size.height()) / 2)

    def _init_animation(self):
        print('init animation')
        scenario = self.current_scenario

        start: int = 0
        end: int = 50
        delta_time_steps: int = 1
        plotting_horizon = 0
        plot_limits: Union[list, None, str] = None
        dt = 0.1
        # ps = 25
        # dpi = 120
        # ln, = self.canvas.ax.plot([], [], animated=True)

        assert start < end, '<video/create_scenario_video> time_begin=%i needs to smaller than time_end=%i.' % (
            start, end)

        def draw_frame(draw_params):
            print('next frame')
            time_begin = start + delta_time_steps * self.timestep.value
            time_end = start + min(
                frame_count,
                delta_time_steps * self.timestep.value + plotting_horizon)
            self.timestep.value += 1

            draw_params = {'time_begin': time_begin, 'time_end': time_end}
            print("draw frame ", self.timestep.value, draw_params)
            # plot frame
            self.canvas.draw_object(
                scenario,
                draw_params=draw_params,
                plot_limits=None if plot_limits == 'auto' else plot_limits)

        frame_count = (end - start) // delta_time_steps
        # Interval determines the duration of each frame in ms
        interval = 1000 * dt
        self.animation = FuncAnimation(self.canvas.figure,
                                       draw_frame,
                                       blit=False,
                                       interval=interval,
                                       repeat=True)

    def play(self):
        """ plays the animation if existing """
        if not self.animation:
            self._init_animation()

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
        self.timestep.silent_set(timestep)

    def closeEvent(self, event):
        messbox = QMessageBox()
        reply = messbox.question(
            self, "Warning",
            "Do you want to close the window? Please make sure you have saved your work",
            QMessageBox.Yes | QMessageBox.No)
        if (reply == QMessageBox.Yes):
            event.accept()
        else:
            event.ignore()
