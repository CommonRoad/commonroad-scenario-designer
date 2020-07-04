# -*- coding: utf-8 -*-

"""Viewer module to visualize the created lanelet scenario."""

import signal
import sys
import os
from lxml import etree
import numpy as np
import matplotlib

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
from commonroad.scenario.lanelet import Lanelet

__author__ = "Benjamin Orthen, Stefan Urban"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "1.2.0"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad-i06@in.tum.de"
__status__ = "Released"


matplotlib.use("Qt5Agg")


class Canvas(FigureCanvas):
    """Ultimately, this is a QWidget"""

    def __init__(self, parent=None, width=5, height=5, dpi=100):

        self.ax = None

        self.fig = Figure(figsize=(width, height), dpi=dpi)

        super(Canvas, self).__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.clear_axes()

    def clear_axes(self):
        """ """
        if self.ax is not None:
            self.ax.clear()
        else:

            self.ax = self.fig.add_subplot(111)
        self.ax.set_aspect("equal", "datalim")
        self.ax.set_axis_off()

        self.draw()

    def get_axes(self):
        """ """
        return self.ax

    def update_plot(self):
        """ """
        self.draw()


class MainWindow(QWidget):
    """ """

    def __init__(self, parent=None, path=None):
        super().__init__(parent)

        self.current_scenario = None
        self.selected_lanelet_id = None
        self.selected_intersection_id = None

        self._initUserInterface()
        self.show()

        if path is not None:
            self.openPath(path)

    def _initUserInterface(self):
        """ """

        self.setWindowTitle("CommonRoad XML Viewer")

        self.setMinimumSize(1000, 600)

        # self.testButton = QPushButton('test', self)
        # self.testButton.clicked.connect(self.testCmd)

        self.loadButton = QPushButton("Load CommonRoad", self)
        self.loadButton.setToolTip("Load a CommonRoad scenario within a *.xml file")
        self.loadButton.clicked.connect(self.openCommonRoadFile)

        self.inputCommonRoadFile = QLineEdit(self)
        self.inputCommonRoadFile.setReadOnly(True)

        hbox = QHBoxLayout()
        hbox.addWidget(self.loadButton)
        hbox.addWidget(self.inputCommonRoadFile)

        self.dynamic = Canvas(self, width=5, height=10, dpi=100)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox, 0)
        vbox.addWidget(self.dynamic, 1)

        vbox.setAlignment(Qt.AlignTop)

        self.laneletsList = QTableWidget(self)
        self.laneletsList.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.laneletsList.clicked.connect(self.onClickLanelet)

        self.intersection_list = QTableWidget(self)
        self.intersection_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.intersection_list.clicked.connect(self.onClickIntersection)

        hbox2 = QHBoxLayout(self)
        hbox2.addLayout(vbox, 2)
        hbox2.addWidget(self.laneletsList, 0)
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
        """

        Args:
          path:

        Returns:

        """

        filename = os.path.basename(path)
        self.inputCommonRoadFile.setText(filename)

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

        self.openScenario(scenario)

    def openScenario(self, scenario):
        """

        Args:
          scenario:

        Returns:

        """
        self.current_scenario = scenario
        self.update_plot()

    @pyqtSlot()
    def onClickLanelet(self):
        """ """
        self.dynamic.clear_axes()

        selectedLanelets = self.laneletsList.selectedItems()

        if not selectedLanelets:
            self.selected_lanelet_id = None
            return

        self.selected_lanelet_id = int(selectedLanelets[0].text())
        self.selected_intersection_id = None
        self.update_plot()

    def onClickIntersection(self):
        """ """
        self.dynamic.clear_axes()

        selected_intersection = self.intersection_list.selectedItems()

        if not selected_intersection:
            self.selected_intersection_id = None
            return

        self.selected_intersection_id = int(selected_intersection[0].text())
        self.selected_lanelet_id = None
        self.update_plot()

    def update_plot(self):
        """ """

        # update canvas
        if self.current_scenario is None:
            self.dynamic.clear_axes()
            return

        # select intersection xor lanelet
        if self.selected_lanelet_id is not None:
            selected_lanelet = self.current_scenario.lanelet_network.find_lanelet_by_id(
                self.selected_lanelet_id)
            selected_intersection = None
        elif self.selected_intersection_id is not None:
            selected_intersection = self.current_scenario.lanelet_network.find_intersection_by_id(
                self.selected_intersection_id)
            selected_lanelet = None
        else:
            selected_lanelet = None
            selected_intersection = None

        ax = self.dynamic.get_axes()

        self.xlim1 = float("Inf")
        self.xlim2 = -float("Inf")

        self.ylim1 = float("Inf")
        self.ylim2 = -float("Inf")

        for lanelet in self.current_scenario.lanelet_network.lanelets:

            draw_arrow, color, alpha, zorder, label = self.get_paint_parameters(
                lanelet, selected_lanelet, selected_intersection)

            self.draw_lanelet_polygon(
                lanelet, ax, color, alpha, zorder, label)

            self.draw_lanelet_vertices(lanelet, ax)

            if draw_arrow:
                self.draw_arrow_on_lanelet(lanelet, ax)

        handles, labels = self.dynamic.get_axes().get_legend_handles_labels()
        self.dynamic.get_axes().legend(handles, labels)

        if (
            self.xlim1 != float("Inf")
            and self.xlim2 != float("Inf")
            and self.ylim1 != float("Inf")
            and self.ylim2 != float("Inf")
        ):
            self.dynamic.get_axes().set_xlim([self.xlim1, self.xlim2])
            self.dynamic.get_axes().set_ylim([self.ylim1, self.ylim2])

        self.dynamic.update_plot()

        self.update_intersection_list()
        self.update_lanelet_list()

        self.dynamic.fig.tight_layout()


    def get_paint_parameters(self, lanelet: Lanelet, selected_lanelet: Lanelet,
            selected_intersection: Intersection):
        """
        Return the parameters for painting a lanelet regarding the selected lanelet.
        """

        if selected_lanelet is not None:
        
            draw_arrow = True

            if lanelet.lanelet_id == selected_lanelet.lanelet_id:
                color = "red"
                alpha = 0.7
                zorder = 10
                label = "{} selected".format(lanelet.lanelet_id)

            elif (
                lanelet.lanelet_id in selected_lanelet.predecessor
                and lanelet.lanelet_id in selected_lanelet.successor
            ):
                color = "purple"
                alpha = 0.5
                zorder = 5
                label = "{} predecessor and successor of {}".format(
                    lanelet.lanelet_id, selected_lanelet.lanelet_id
                )

            elif lanelet.lanelet_id in selected_lanelet.predecessor:
                color = "blue"
                alpha = 0.5
                zorder = 5
                label = "{} predecessor of {}".format(
                    lanelet.lanelet_id, selected_lanelet.lanelet_id
                )
            elif lanelet.lanelet_id in selected_lanelet.successor:
                color = "green"
                alpha = 0.5
                zorder = 5
                label = "{} successor of {}".format(
                    lanelet.lanelet_id, selected_lanelet.lanelet_id
                )
            elif lanelet.lanelet_id == selected_lanelet.adj_left:
                color = "yellow"
                alpha = 0.5
                zorder = 5
                label = "{} adj left of {} ({})".format(
                    lanelet.lanelet_id,
                    selected_lanelet.lanelet_id,
                    "same"
                    if selected_lanelet.adj_left_same_direction
                    else "opposite",
                )
            elif lanelet.lanelet_id == selected_lanelet.adj_right:
                color = "orange"
                alpha = 0.5
                zorder = 5
                label = "{} adj right of {} ({})".format(
                    lanelet.lanelet_id,
                    selected_lanelet.lanelet_id,
                    "same"
                    if selected_lanelet.adj_right_same_direction
                    else "opposite",
                )
            else:
                color = "gray"
                alpha = 0.3
                zorder = 0
                label = None
                draw_arrow = False

        elif selected_intersection is not None:

            incoming_ids = selected_intersection.map_incoming_lanelets.keys()
            
            draw_arrow = True
            
            if lanelet.lanelet_id in incoming_ids:
                color = "red"
                alpha = 0.7
                zorder = 5
                label = "{} incoming".format(lanelet.lanelet_id)
            elif lanelet.lanelet_id in selected_intersection.crossings:
                color = "blue"
                alpha = 0.5
                zorder = 5
                label = "{} crossing".format(lanelet.lanelet_id)
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
            [lanelet.left_vertices, lanelet.right_vertices[::-1]]
        ):
            verts.append([x, y])
            codes.append(Path.LINETO)

            if color != 'gray':
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
            )
        )

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
        mc = lanelet.center_vertices[
            min(len(lanelet.center_vertices) - 1, idx + 3)
        ]
        ax.plot(
            [ml[0], mr[0], mc[0], ml[0]],
            [ml[1], mr[1], mc[1], ml[1]],
            color="black",
            lw=0.3,
            zorder=15,
        )

    def update_lanelet_list(self):
        self.laneletsList.setRowCount(
            len(self.current_scenario.lanelet_network.lanelets)
        )
        self.laneletsList.setColumnCount(2)
        self.laneletsList.setHorizontalHeaderLabels(["Lanelet-Id", "LaneletType"])
        
        lanelet_data = []
        for lanelet in self.current_scenario.lanelet_network.lanelets:
            description = ", ".join([t.value for t in lanelet.lanelet_type])
            lanelet_data.append((lanelet.lanelet_id, description))

        lanelet_data = sorted(lanelet_data)
        for idx, lanelet in enumerate(lanelet_data):
            
            # set lanelet_id
            self.laneletsList.setItem(idx, 0, QTableWidgetItem(str(lanelet[0])))
            try:
                # set lanelet description (old id)
                self.laneletsList.setItem(idx, 1, QTableWidgetItem(str(lanelet[1])))
            except AttributeError:
                self.laneletsList.setItem(idx, 1, QTableWidgetItem("None"))

    def update_intersection_list(self):
        self.intersection_list.setRowCount(
            len(self.current_scenario.lanelet_network.intersections)
        )
        self.intersection_list.setColumnCount(2)
        self.intersection_list.setHorizontalHeaderLabels(["Intersection-Id", "Description"])
        
        intersection_data = []
        for intersection in self.current_scenario.lanelet_network.intersections:
            description = None
            intersection_data.append((intersection.intersection_id, description))
        
        intersection_data = sorted(intersection_data)
        for idx, intersection in enumerate(intersection_data):
            self.intersection_list.setItem(idx, 0, QTableWidgetItem(str(intersection[0])))
            self.intersection_list.setItem(idx, 1, QTableWidgetItem(str(intersection[1])))



if __name__ == "__main__":
    # Make it possible to exit application with ctrl+c on console
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Startup application
    app = QApplication(sys.argv)

    if len(sys.argv) >= 2:
        ex = MainWindow(path=sys.argv[1])
    else:
        ex = MainWindow()

    sys.exit(app.exec_())
