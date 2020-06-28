import signal
import sys
import os
from lxml import etree
import numpy as np
import matplotlib.pyplot as plt

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


class OD2CR(QDialog):
    def __init__(self, parent=None):
        super(OD2CR, self).__init__(parent)
        self.statsText = None
        self.input_filename = None
        self.current_scenario = None
        self.figure = plt.figure(figsize=(10.8, 7.2), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.canvas.mpl_connect('scroll_event', self.zoom)
        self.canvas.mpl_connect('button_press_event', self.zoom)

        self.openOpenDriveFileDialog()

    def openOpenDriveFileDialog(self):
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

        self.load_opendriveFile(path)

    def load_opendriveFile(self, path):
        """

        Args:
          path:

        Returns:

        """

        filename = os.path.basename(path)
        self.input_filename = filename

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
        self.viewConvertedLaneletNetwork()

    def exportAsCommonRoad(self):
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

    def viewConvertedLaneletNetwork(self):
        """ """

        self.current_scenario = self.loadedRoadNetwork.export_commonroad_scenario()

        # temporary fix to get a plotable view of the scenario
        """if args.plot_center:
            plot_center = [int(x) for x in args.plot_center]
        else:"""
        plot_center = self.current_scenario.lanelet_network.lanelets[0].left_vertices[0]
        plt.style.use("classic")
        # plt.figure(figsize=(10, 10))
        plt.gca().axis("equal")
        self.figure.tight_layout()
        plot_displacement_x = plot_displacement_y = 200
        plot_limits = [
            plot_center[0] - plot_displacement_x,
            plot_center[0] + plot_displacement_x,
            plot_center[1] - plot_displacement_y,
            plot_center[1] + plot_displacement_y,
        ]
        draw_object(self.current_scenario, plot_limits=plot_limits)
        self.canvas.show()

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
            self.openOpenDriveFileDialog()
        else:
            self.close

    def closeEvent(self, event):
        result = QMessageBox.question(self, "Warning", "Do you want to exit?",
                                      QMessageBox.Yes | QMessageBox.No)
        if (result == QMessageBox.Yes):
            event.accept()

        else:
            event.ignore()
