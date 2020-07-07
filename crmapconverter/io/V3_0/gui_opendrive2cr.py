import os
from lxml import etree
import numpy as np
from matplotlib.path import Path
from matplotlib.figure import Figure
from matplotlib.patches import PathPatch

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.visualization.draw_dispatch_cr import draw_object
from crmapconverter.io.viewer import MainWindow as ViewerWidget
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.scenario import Tag

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from crmapconverter.opendriveparser.parser import parse_opendrive
from crmapconverter.opendriveconversion.network import Network


from crmapconverter.io.V3_0.GUI_resources.MainWindow import Ui_mainWindow
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

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


class OD2CR(QDialog):
    def __init__(self, parent=None):
        super(OD2CR, self).__init__(parent)
        self.statsText = None
        self.filename = None
        self.current_scenario = None
        self.selected_lanelet_id = None
        self.canvas = Canvas(self, width=10.8, height=7.2, dpi=100)
        self.toolbar = NavigationToolbar(self.canvas, self)


        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.canvas.mpl_connect('scroll_event', self.zoom)
        self.canvas.mpl_connect('button_press_event', self.zoom)

        self.laneletsList = QTableWidget(self)
        self.laneletsList.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.laneletsList.clicked.connect(self.on_click_lanelet)

        self.open_opendrive_file_dialog()

    def open_opendrive_file_dialog(self):
        """ """
        # self.reset_output_elements()

        path, _ = QFileDialog.getOpenFileName(
            self,
            "QFileDialog.getOpenFileName()",
            "",
            "OpenDRIVE files *.xodr (*.xodr)",
            options=QFileDialog.Options(),
        )

        if not path:
            self.NoFileselected()
            return

        self.load_opendrive_file(path)

    def load_opendrive_file(self, path):
        """

        Args:
          path:

        Returns:

        """

        filename = os.path.basename(path)
        self.filename = filename

        # Load road network and print some statistics
        try:
            fh = open(path, "r")
            openDriveXml = parse_opendrive(etree.parse(fh).getroot())
            fh.close()
        except (etree.XMLSyntaxError) as e:
            errorMsg = "XML Syntax Error: {}".format(e)
            QMessageBox.warning(
                self,
                "OpenDRIVE error",
                "There was an error during the loading of the selected OpenDRIVE file.\n\n{}".format(
                    errorMsg
                ),
                QMessageBox.Ok,
            )
            return
        except (TypeError, AttributeError, ValueError) as e:
            errorMsg = "Value Error: {}".format(e)
            QMessageBox.warning(
                self,
                "OpenDRIVE error",
                "There was an error during the loading of the selected OpenDRIVE file.\n\n{}".format(
                    errorMsg
                ),
                QMessageBox.Ok,
            )
            return

        self.loadedRoadNetwork = Network()
        self.loadedRoadNetwork.load_opendrive(openDriveXml)

        self.statsText = (
            """Name: {}<br>Version: {}<br>Date: {}<br><br>OpenDRIVE
            Version {}.{}<br><br>Number of roads: {}<br>Total length
            of road network: {:.2f} meters""".format(
                openDriveXml.header.name
                if openDriveXml.header.name
                else "<i>unset</i>",
                openDriveXml.header.version,
                openDriveXml.header.date,
                openDriveXml.header.revMajor,
                openDriveXml.header.revMinor,
                len(openDriveXml.roads),
                sum([road.length for road in openDriveXml.roads]),
            )
        )

        self.open_scenario()

    def export_as_commonroad(self):
        """ """

        if not self.loadedRoadNetwork:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "QFileDialog.getSaveFileName()",
            "",
            "CommonRoad files *.xml (*.xml)",
            options=QFileDialog.Options(),
        )

        if not path:
            return

        try:
            writer = CommonRoadFileWriter(
                scenario=self.loadedRoadNetwork.export_commonroad_scenario(),
                planning_problem_set=PlanningProblemSet(),
                author="",
                affiliation="",
                source="OpenDRIVE 2 Lanelet Converter",
                tags={Tag.URBAN, Tag.HIGHWAY},
            )
            writer.write_to_file(path, OverwriteExistingFile.ALWAYS)
        except (IOError) as e:
            QMessageBox.critical(
                self,
                "CommonRoad file not created!",
                "The CommonRoad file was not exported due to an error.\n\n{}".format(e),
                QMessageBox.Ok,
            )
            return

        QMessageBox.information(
            self,
            "CommonRoad file created!",
            "The CommonRoad file was successfully exported.",
            QMessageBox.Ok,
        )

    def open_scenario(self):
        """

        Args:
          scenario:

        Returns:

        """
        self.current_scenario = self.loadedRoadNetwork.export_commonroad_scenario()
        self.update_plot()

    def on_click_lanelet(self):
        """ """
        self.canvas.clear_axes()

        selectedLanelets = self.laneletsList.selectedItems()

        if not selectedLanelets:
            self.selected_lanelet_id = None
            return

        self.selected_lanelet_id = int(selectedLanelets[0].text())
        self.update_plot()

    def update_plot(self):
        """"""
        if self.current_scenario is None:
            self.canvas.clear_axes()
            return

        try:
            selected_lanelet = self.current_scenario.lanelet_network.find_lanelet_by_id(
                self.selected_lanelet_id)

        except (AssertionError, KeyError):
            selected_lanelet = None

        ax = self.canvas.get_axes()

        xlim1 = float("Inf")
        xlim2 = -float("Inf")

        ylim1 = float("Inf")
        ylim2 = -float("Inf")

        for lanelet in self.current_scenario.lanelet_network.lanelets:

            # Selected lanelet
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

            else:
                color = "gray"
                alpha = 0.3
                zorder = 0
                label = None
                draw_arrow = False

            verts = []
            codes = [Path.MOVETO]

            # TODO efficiency

            for x, y in np.vstack(
                    [lanelet.left_vertices, lanelet.right_vertices[::-1]]
            ):
                verts.append([x, y])
                codes.append(Path.LINETO)

                # if color != 'gray':
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
                )
            )
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

            if draw_arrow:
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

        handles, labels = self.canvas.get_axes().get_legend_handles_labels()
        self.canvas.get_axes().legend(handles, labels)

        if (
                xlim1 != float("Inf")
                and xlim2 != float("Inf")
                and ylim1 != float("Inf")
                and ylim2 != float("Inf")
        ):
            self.canvas.get_axes().set_xlim([xlim1, xlim2])
            self.canvas.get_axes().set_ylim([ylim1, ylim2])

        self.canvas.update_plot()

        self.laneletsList.setRowCount(
            len(self.current_scenario.lanelet_network.lanelets)
        )
        self.laneletsList.setColumnCount(2)
        self.laneletsList.setHorizontalHeaderLabels(["Lanelet-Id", "LaneletType"])
        # lanelet_data = [
        #     (lanelet.lanelet_id, lanelet.description)
        #     for lanelet in self.current_scenario.lanelet_network.lanelets
        # ]
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

        self.canvas.fig.tight_layout()

    def zoom(self, event):
        """
                realize zoom in / out function in GUI
                Args:
                  event:

                Returns:

                """

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
            print('up')
        elif event.button == 'down':
            ax.set(xlim=(x_min - scope_x, x_max + scope_x))
            ax.set(ylim=(y_min - scope_y, y_max + scope_y))
            print('down')

        self.canvas.draw_idle()

    def NoFileselected(self):
        reply = QMessageBox.information(
            self,
            "Information",
            "Please select a OpenDrive file",
            QMessageBox.Ok | QMessageBox.No,
            QMessageBox.Ok)
        if reply == QMessageBox.Ok:
            self.open_opendrive_file_dialog()
        else:
            self.close

    def closeEvent(self, event):
        result = QMessageBox.question(self, "Warning", "Do you want to exit?",
                                      QMessageBox.Yes | QMessageBox.No)
        if (result == QMessageBox.Yes):
            event.accept()

        else:
            event.ignore()
