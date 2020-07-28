# -*- coding: utf-8 -*-
"""Viewer module to visualize and inspect the created lanelet scenario."""

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
from commonroad.geometry.shape import Circle

__author__ = "Benjamin Orthen, Stefan Urban"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "1.2.0"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad-i06@in.tum.de"
__status__ = "Released"

matplotlib.use("Qt5Agg")

ZOOM_FACTOR = 1.2


def _merge_dict(source, destination):
    """deeply merges two dicts
    """
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            _merge_dict(value, node)
        else:
            destination[key] = value
    return destination


class DynamicCanvas(FigureCanvas):
    """ this canvas provides zoom with the mouse wheel """
    def __init__(self, parent=None, width=5, height=5, dpi=100):

        self.ax = None
        self.drawer = Figure(figsize=(width, height), dpi=dpi)

        self.draw_params = {
            'scenario': {
                'dynamic_obstacle': {
                    'trajectory': {
                        'show_label': True,
                        'draw_trajectory': False
                    }
                },
                'lanelet_network': {
                    'traffic_light': {
                        'scale_factor': 0.2
                    },
                    'traffic_sign': {
                        'draw_traffic_signs': True,
                        'show_traffic_signs': 'all',
                        'scale_factor': 0.2
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

    def clear_axes(self, keep_limits=False):
        """ """
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
            new_center_diff_x = (center[0] - mouse_pos[0])/6
            new_center_diff_y = (center[1] - mouse_pos[1])/6
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
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        self.ax.clear()
        self._handles.clear()

        draw_params_merged = _merge_dict(self.draw_params.copy(), draw_params)

        draw_object(scenario,
                    ax=self.ax,
                    draw_params=draw_params_merged,
                    plot_limits=plot_limits,
                    handles=self._handles)
        if not plot_limits:
            self.ax.set(xlim=xlim)
            self.ax.set(ylim=ylim)

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

        draw_params_merged = _merge_dict(self.draw_params.copy(), draw_params)

        for obj in [obstacles, traffic_lights]:
            draw_object(obstacles,
                        ax=self.ax,
                        draw_params=draw_params_merged,
                        plot_limits=plot_limits,
                        handles=self._handles)


class ScenarioElementList(QTableWidget):
    def __init__(self, action_on_click, parent=None):
        """ 
        :param action_on_click: action to call when an list item is clicked.
            reference to self will be passed as first argument
        """
        super().__init__(parent)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.clicked.connect(self.onClick)
        self.update_action = lambda: action_on_click(self)

        self.selected_id: int = None
        self.header_labels: List = None

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

        self.update_action()

    def reset_selection(self):
        """ unselect all elements """
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
    """ functionality to draw a Scenario onto a Canvas """
    def __init__(self, parent):
        self.current_scenario = None
        self.dynamic = DynamicCanvas(parent, width=5, height=10, dpi=100)
        self.dynamic.mpl_connect('button_press_event', self.select_lanelets)

    def open_scenario(self, scenario):
        """ """
        self.current_scenario = scenario
        self.update_plot(focus_on_network=True)

    def update_plot(self,
                    sel_lanelet: Lanelet = None,
                    sel_intersection: Intersection = None,
                    focus_on_network: bool = False):
        """ Update the plot accordinly to the selection of scenario elements
        :param scenario: Scenario to draw
        :type scenario: Scenario
        :param sel_lanelet: selected lanelet, defaults to None
        :type sel_lanelet: Lanelet, optional
        :param sel_intersection: selected intersection, defaults to None
        :type sel_intersection: Intersection, optional
        """

        x_lim = self.dynamic.get_axes().get_xlim()
        y_lim = self.dynamic.get_axes().get_ylim()

        self.dynamic.clear_axes()
        ax = self.dynamic.get_axes()

        network_limits = [
            float("Inf"), -float("Inf"),
            float("Inf"), -float("Inf")
        ]

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
        self.dynamic.draw_scenario(self.current_scenario,
                                   draw_params=draw_params)

        for lanelet in self.current_scenario.lanelet_network.lanelets:

            draw_arrow, color, alpha, zorder, label = self.get_paint_parameters(
                lanelet, sel_lanelet, sel_intersection)
            if color == "gray": continue

            lanelet_limits = self.draw_lanelet_polygon(lanelet, ax, color,
                                                       alpha, zorder, label)
            network_limits[0] = min(network_limits[0], lanelet_limits[0])
            network_limits[1] = max(network_limits[1], lanelet_limits[1])
            network_limits[2] = min(network_limits[2], lanelet_limits[2])
            network_limits[3] = max(network_limits[3], lanelet_limits[3])

            self.draw_lanelet_vertices(lanelet, ax)
            if draw_arrow:
                self.draw_arrow_on_lanelet(lanelet, ax)

        handles, labels = ax.get_legend_handles_labels()
        legend = ax.legend(handles, labels)
        legend.set_zorder(50)

        if focus_on_network:
            # can we focus on a selection?
            if all([abs(l) < float("Inf") for l in network_limits]):
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

    def draw_lanelet_polygon(self, lanelet, ax, color, alpha, zorder,
                             label) -> Tuple[float, float, float, float]:
        # TODO efficiency
        verts = []
        codes = [Path.MOVETO]

        xlim1 = float("Inf")
        xlim2 = -float("Inf")
        ylim1 = float("Inf")
        ylim2 = -float("Inf")

        for x, y in np.vstack(
            [lanelet.left_vertices, lanelet.right_vertices[::-1]]):
            verts.append([x, y])
            codes.append(Path.LINETO)

            xlim1 = min(xlim1, x)
            xlim2 = max(xlim2, x)
            ylim1 = min(ylim1, y)
            ylim2 = max(ylim2, y)

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

        return [xlim1, xlim2, ylim1, ylim2]

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

    def select_lanelets(self, mouse_clicked_event):
        """ 
        Selecet lanelets by clicking on the canvas. Selects only one of the 
        lanelets that contains the click position.
        """
        mouse_pos = np.array(
            [mouse_clicked_event.xdata, mouse_clicked_event.ydata])
        click_shape = Circle(radius=0.01, center=mouse_pos)

        l_network = self.current_scenario.lanelet_network
        selected_l_ids = l_network.find_lanelet_by_shape(click_shape)
        selected_lanelets = [
            l_network.find_lanelet_by_id(lid) for lid in selected_l_ids
        ]
        if selected_lanelets:
            self.update_plot(sel_lanelet=selected_lanelets[0])
        else:
            self.update_plot(sel_lanelet=None)


class MainWindow(QWidget):
    def __init__(self, parent=None, path=None):
        super().__init__(parent)
        self.filename: str = None
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
        """ 
        Open a new CommonRoad Scenario and update the viewer
        """
        self.filename = filename
        self.viewer.open_scenario(new_scenario)
        self.update()

    def update(self, caller=None):
        """ 
        Update all compoments. Reset all other selections if this method was
        triggered by a component.
        """

        # reset selection of all other selectable elements
        if caller is not None:
            if caller is not self.intersection_list:
                self.intersection_list.reset_selection()
            if caller is not self.lanelet_list:
                self.lanelet_list.reset_selection()

        self.lanelet_list.update(self.viewer.current_scenario)
        self.intersection_list.update(self.viewer.current_scenario)

        if self.viewer.current_scenario is None:
            return
        if self.intersection_list.selected_id is not None:
            selected_intersection = find_intersection_by_id(
                self.viewer.current_scenario,
                self.intersection_list.selected_id)
        else:
            selected_intersection = None
        if self.lanelet_list.selected_id is not None:
            selected_lanelet = self.viewer.current_scenario.lanelet_network.find_lanelet_by_id(
                self.lanelet_list.selected_id)
        else:
            selected_lanelet = None
        self.viewer.update_plot(sel_lanelet=selected_lanelet,
                                sel_intersection=selected_intersection,
                                focus_on_network=False)


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
        main_window = MainWindow(path=sys.argv[1])
    else:
        main_window = MainWindow(
            path=
            "/home/max/Desktop/Planning/Maps/cr_files/ped/garching_kreuzung_fixed.xml"
        )
    main_window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()