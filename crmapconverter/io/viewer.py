# -*- coding: utf-8 -*-
"""Viewer module to visualize the created lanelet scenario."""

import signal
import sys
import os
from lxml import etree
import numpy as np
import matplotlib
from typing import List, Tuple

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.path import Path
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QTableWidget,
    QPushButton,
    QLineEdit,
    QFileDialog,
    QMessageBox,
)
from PyQt5.QtWidgets import (
    QSizePolicy,
    QHBoxLayout,
    QVBoxLayout,
    QTableWidgetItem,
    QAbstractItemView,
)

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.scenario.intersection import Intersection
from commonroad.common.util import Interval
from commonroad.scenario.scenario import Scenario
from commonroad.scenario.lanelet import Lanelet, is_natural_number
from commonroad.visualization.draw_dispatch_cr import draw_object

__author__ = "Benjamin Orthen, Stefan Urban"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "1.2.0"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad-i06@in.tum.de"
__status__ = "Released"

matplotlib.use("Qt5Agg")


class DynamicCanvas(FigureCanvas):
    """Ultimately, this is a QWidget"""
    def __init__(self, parent=None, width=5, height=5, dpi=100):

        self.ax = None
        self.drawer = Figure(figsize=(width, height), dpi=dpi)
        # select pan tool by default
        plt.get_current_fig_manager().toolbar.pan()

        self._handles = {}

        super().__init__(self.drawer)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.mpl_connect('scroll_event', self.zoom)
        self.mpl_connect('button_press_event', self.zoom)

        self.clear_axes()

    def clear_axes(self):
        """ """
        if self.ax:
            self.ax.clear()
        else:
            self.ax = self.drawer.add_subplot(111)

        self.ax.set_aspect("equal", "datalim")
        self.ax.set_axis_off()
        self.draw()

    def get_axes(self):
        """Gives the plots Axes

        :return: matplotlib axis
        """
        return self.ax

    def update_plot(self):
        """Upates the display
        """
        self.draw()

    def zoom(self, event):
        """ realize zoom in / out function in GUI """

        ax = event.inaxes  # get the axes which mouse is now
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()
        scope_x = (x_max - x_min) / 10
        scope_y = (y_max - y_min) / 10
        # xdata = event.xdata  # get event x location
        # ydata = event.ydata  # get event y location

        if event.button == 'up':
            ax.set(xlim=(x_min + scope_x, x_max - scope_x))
            ax.set(ylim=(y_min + scope_y, y_max - scope_y))
            # print('up')
        elif event.button == 'down':
            ax.set(xlim=(x_min - scope_x, x_max + scope_x))
            ax.set(ylim=(y_min - scope_y, y_max + scope_y))
            # print('down')
        self.draw_idle()

    def draw_scenario(self,
                      scenario: Scenario,
                      draw_params=None,
                      plot_limits=None):
        """[summary]

        :param scenario: [description]
        :type scenario: Scenario
        :param draw_params: [description], defaults to None
        :type draw_params: [type], optional
        :param plot_limits: [description], defaults to None
        :type plot_limits: [type], optional
        """
        self.clear_axes()
        draw_object(scenario,
                    ax=self.ax,
                    draw_params=draw_params,
                    plot_limits=plot_limits,
                    handles=self._handles)
        self.ax.autoscale()
        self.ax.set_aspect('equal')

    def update_obstacles(self,
                         scenario: Scenario,
                         draw_params=None,
                         plot_limits=None):
        """
        Redraw only the dynamic obstacles. This gives a large performance boost, when playing an animation
        :param scenario: The scneario containing the dynamic obstacles 
        :param draw_params: CommonRoad draw_object() DrawParams
        :param plot_limits: Matplotlib plot limits
        """
        # # remove dynamic obstacles
        for handles_i in self._handles.values():
            for handle in handles_i:
                if handle:
                    handle.remove()
        self._handles.clear()

        # redraw dynamic obstacles
        obstacles = scenario.obstacles_by_position_intervals([
            Interval(plot_limits[0], plot_limits[1]),
            Interval(plot_limits[2], plot_limits[3])
        ]) if plot_limits else scenario.obstacles

        traffic_lights = scenario.lanelet_network.traffic_lights
        traffic_light_lanelets = [
            lanelet for lanelet in scenario.lanelet_network.lanelets
            if lanelet.traffic_lights
        ]

        for obj in [obstacles, traffic_lights]:
            draw_object(obstacles,
                        ax=self.ax,
                        draw_params=draw_params,
                        plot_limits=plot_limits,
                        handles=self._handles)


class ScenarioElementList(QTableWidget):
    def __init__(self, action_on_click, parent=None):
        super().__init__(parent)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.clicked.connect(self.onClick)
        self.update_action = action_on_click

        self.selected_id: int = None
        self.header_labels: List = None
        self.new = False

    def _update(self, data: List[Tuple]):
        # set dimesions
        if data and not len(self.header_labels) == len(data[0]):
            raise RuntimeError()
        self.setRowCount(len(data))
        self.setColumnCount(len(self.header_labels))
        # set content
        self.setHorizontalHeaderLabels(self.header_labels)
        for y, row in enumerate(data):
            x = 0
            for element in row:
                self.setItem(y, x, QTableWidgetItem(str(element)))
                x += 1

    @pyqtSlot()
    def onClick(self):
        """ """
        selected_item = self.selectedItems()
        if not selected_item:
            self.selected_id = None
            return
        self.selected_id = int(selected_item[0].text())

        self.new = True
        self.update_action()

    def reset_selection(self):
        self.selected_id = None
        self.clearSelection()


class IntersectionList(ScenarioElementList):
    def __init__(self, action_on_click, parent=None):
        super().__init__(action_on_click, parent)
        self.header_labels = ["Intersection-Id", "Description"]

    def update(self, scenario):
        if scenario is None:
            self.close()
        intersection_data = []
        for intersection in scenario.lanelet_network.intersections:
            description = None
            intersection_data.append(
                (intersection.intersection_id, description))
        super()._update(sorted(intersection_data))


class LaneletList(ScenarioElementList):
    def __init__(self, action_on_click, parent=None):
        super().__init__(action_on_click, parent)
        self.header_labels = ["Lanelet-Id", "LaneletType"]

    def update(self, scenario):
        if scenario is None:
            self.close()
        lanelet_data = []
        for lanelet in scenario.lanelet_network.lanelets:
            description = ", ".join([t.value for t in lanelet.lanelet_type])
            lanelet_data.append((lanelet.lanelet_id, description))
        super()._update(sorted(lanelet_data))


class Viewer:
    """ """
    def __init__(self, parent):
        self.xlim1 = float("Inf")
        self.xlim2 = -float("Inf")
        self.ylim1 = float("Inf")
        self.ylim2 = -float("Inf")

        self.dynamic = DynamicCanvas(parent, width=5, height=10, dpi=100)

    def update_plot(self,
                    scenario: Scenario,
                    sel_lanelet: Lanelet = None,
                    sel_intersection: Intersection = None):
        """Update the plot accordinly to the selection of scenario elements

        :param scenario: Scenario to draw
        :type scenario: Scenario
        :param sel_lanelet: selected lanelet, defaults to None
        :type sel_lanelet: Lanelet, optional
        :param sel_intersection: selected intersection, defaults to None
        :type sel_intersection: Intersection, optional
        """

        self.dynamic.clear_axes()

        ax = self.dynamic.get_axes()

        self.xlim1 = float("Inf")
        self.xlim2 = -float("Inf")

        self.ylim1 = float("Inf")
        self.ylim2 = -float("Inf")

        draw_params = {
            'scenario': {
                'dynamic_obstacle': {
                    'trajectory': {
                        'show_label': True,
                        'draw_trajectory': False
                    }
                }
            }
        }
        self.dynamic.draw_scenario(scenario, draw_params=draw_params)

        for lanelet in scenario.lanelet_network.lanelets:

            draw_arrow, color, alpha, zorder, label = self.get_paint_parameters(
                lanelet, sel_lanelet, sel_intersection)
            if color == "gray": continue

            self.draw_lanelet_polygon(lanelet, ax, color, alpha, zorder, label)
            self.draw_lanelet_vertices(lanelet, ax)
            if draw_arrow:
                self.draw_arrow_on_lanelet(lanelet, ax)

        handles, labels = self.dynamic.get_axes().get_legend_handles_labels()
        legend = self.dynamic.get_axes().legend(handles, labels)
        legend.set_zorder(50)

        if (self.xlim1 != float("Inf") and self.xlim2 != float("Inf")
                and self.ylim1 != float("Inf") and self.ylim2 != float("Inf")):
            self.dynamic.get_axes().set_xlim([self.xlim1, self.xlim2])
            self.dynamic.get_axes().set_ylim([self.ylim1, self.ylim2])

        self.dynamic.update_plot()

        self.dynamic.drawer.tight_layout()

    def get_paint_parameters(self, lanelet: Lanelet, selected_lanelet: Lanelet,
                             selected_intersection: Intersection):
        """
        Return the parameters for painting a lanelet regarding the selected lanelet.
        """

        if selected_lanelet:
            draw_arrow = True

            if lanelet.lanelet_id == selected_lanelet.lanelet_id:
                color = "red"
                alpha = 0.7
                zorder = 20
                label = "{} selected".format(lanelet.lanelet_id)

            elif (lanelet.lanelet_id in selected_lanelet.predecessor
                  and lanelet.lanelet_id in selected_lanelet.successor):
                color = "purple"
                alpha = 0.5
                zorder = 10
                label = "{} predecessor and successor of {}".format(
                    lanelet.lanelet_id, selected_lanelet.lanelet_id)

            elif lanelet.lanelet_id in selected_lanelet.predecessor:
                color = "blue"
                alpha = 0.5
                zorder = 10
                label = "{} predecessor of {}".format(
                    lanelet.lanelet_id, selected_lanelet.lanelet_id)
            elif lanelet.lanelet_id in selected_lanelet.successor:
                color = "green"
                alpha = 0.5
                zorder = 10
                label = "{} successor of {}".format(
                    lanelet.lanelet_id, selected_lanelet.lanelet_id)
            elif lanelet.lanelet_id == selected_lanelet.adj_left:
                color = "yellow"
                alpha = 0.5
                zorder = 10
                label = "{} adj left of {} ({})".format(
                    lanelet.lanelet_id,
                    selected_lanelet.lanelet_id,
                    "same" if selected_lanelet.adj_left_same_direction else
                    "opposite",
                )
            elif lanelet.lanelet_id == selected_lanelet.adj_right:
                color = "orange"
                alpha = 0.5
                zorder = 10
                label = "{} adj right of {} ({})".format(
                    lanelet.lanelet_id,
                    selected_lanelet.lanelet_id,
                    "same" if selected_lanelet.adj_right_same_direction else
                    "opposite",
                )
            else:
                color = "gray"
                alpha = 0.3
                zorder = 0
                label = None
                draw_arrow = False

        elif selected_intersection:
            incoming_ids = selected_intersection.map_incoming_lanelets.keys()
            inc_succ_ids = set()
            for inc in selected_intersection.incomings:
                inc_succ_ids |= inc.successors_right
                inc_succ_ids |= inc.successors_left
                inc_succ_ids |= inc.successors_straight

            draw_arrow = True

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
                draw_arrow = False
        else:
            color = "gray"
            alpha = 0.3
            zorder = 0
            label = None
            draw_arrow = False

        return draw_arrow, color, alpha, zorder, label

    def draw_lanelet_polygon(self, lanelet, ax, color, alpha, zorder, label):
        # TODO efficiency
        verts = []
        codes = [Path.MOVETO]

        for x, y in np.vstack(
            [lanelet.left_vertices, lanelet.right_vertices[::-1]]):
            verts.append([x, y])
            codes.append(Path.LINETO)

            # if color != 'gray':
            self.xlim1 = min(self.xlim1, x)
            self.xlim2 = max(self.xlim2, x)

            self.ylim1 = min(self.ylim1, y)
            self.ylim2 = max(self.ylim2, y)

        verts.append(verts[0])
        codes[-1] = Path.CLOSEPOLY

        path = Path(verts, codes)

        ax.add_patch(
            PathPatch(
                path,
                facecolor=color,
                edgecolor="black",
                lw=0.0,
                alpha=alpha,
                zorder=zorder,
                label=label,
            ))

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

    def draw_arrow_on_lanelet(self, lanelet, ax):
        idx = 0
        ml = lanelet.left_vertices[idx]
        mr = lanelet.right_vertices[idx]
        mc = lanelet.center_vertices[min(
            len(lanelet.center_vertices) - 1, idx + 3)]
        ax.plot(
            [ml[0], mr[0], mc[0], ml[0]],
            [ml[1], mr[1], mc[1], ml[1]],
            color="black",
            lw=0.3,
            zorder=15,
        )


class MainWindow(QWidget):
    def __init__(self, parent=None, path=None):
        super().__init__(parent)
        self.filename: str = None
        self.current_scenario = None
        self.viewer = Viewer(self)

        self._initUserInterface()

        if path is not None:
            self.openPath(path)

    def _initUserInterface(self):
        """ """

        self.setWindowTitle("CommonRoad XML Viewer")

        self.setMinimumSize(1000, 600)

        self.loadButton = QPushButton("Load CommonRoad", self)
        self.loadButton.setToolTip(
            "Load a CommonRoad scenario within a *.xml file")
        self.loadButton.clicked.connect(self.openCommonRoadFile)

        self.inputCommonRoadFile = QLineEdit(self)
        self.inputCommonRoadFile.setReadOnly(True)

        hbox = QHBoxLayout()
        hbox.addWidget(self.loadButton)
        hbox.addWidget(self.inputCommonRoadFile)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox, 0)
        vbox.addWidget(self.viewer.dynamic, 1)

        vbox.setAlignment(Qt.AlignTop)

        self.lanelet_list = LaneletList(self.update, self)
        self.intersection_list = IntersectionList(self.update, self)

        hbox2 = QHBoxLayout(self)
        hbox2.addLayout(vbox, 2)
        hbox2.addWidget(self.lanelet_list, 0)
        hbox2.addWidget(self.intersection_list, 1)
        self.setLayout(hbox2)

    def openCommonRoadFile(self):
        """ """

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open a CommonRoad scenario",
            "",
            "CommonRoad scenario files *.xml (*.xml)",
            options=QFileDialog.Options(),
        )

        if not path:
            return

        self.openPath(path)

    def openPath(self, path):
        """ """

        filename = os.path.basename(path)
        self.inputCommonRoadFile.setText(filename)

        try:
            commonroad_reader = CommonRoadFileReader(path)
            scenario, _ = commonroad_reader.open()

        except etree.XMLSyntaxError as e:
            errorMsg = "Syntax Error: {}".format(e)
            QMessageBox.warning(
                self,
                "CommonRoad XML error",
                "There was an error during the loading of the selected CommonRoad file.\n\n{}"
                .format(errorMsg),
                QMessageBox.Ok,
            )
            return
        # except Exception as e:
        #     errorMsg = "{}".format(e)
        #     QMessageBox.warning(
        #         self,
        #         "CommonRoad XML error",
        #         "There was an error during the loading of the selected CommonRoad file.\n\n{}"
        #         .format(errorMsg),
        #         QMessageBox.Ok,
        #     )
        #     return

        self.openScenario(scenario, filename)

    def openScenario(self, new_scenario, filename="new_scenario"):
        """ open a new CommonRoad Scenario and update the viewer"""
        self.filename = filename
        self.current_scenario = new_scenario
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
        self.viewer.update_plot(scenario=self.current_scenario,
                                sel_lanelet=selected_lanelet,
                                sel_intersection=selected_intersection)

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


def find_intersection_by_id(scenario, intersection_id: int) -> Lanelet:
    """
    Finds a intersection for a given intersection_id

    :param intersection_id: The id of the lanelet to find
    :return: The lanelet object if the id exists and None otherwise
    """
    assert is_natural_number(
        intersection_id
    ), '<LaneletNetwork/find_intersection_by_id>: provided id is not valid! id = {}'.format(
        intersection_id)
    intersections = scenario.lanelet_network._intersections
    return intersections[
        intersection_id] if intersection_id in intersections else None


def main():
    # Make it possible to exit application with ctrl+c on console
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Startup application
    app = QApplication(sys.argv)

    if len(sys.argv) >= 2:
        viewer = MainWindow(path=sys.argv[1])
    else:
        viewer = MainWindow()
    viewer.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()