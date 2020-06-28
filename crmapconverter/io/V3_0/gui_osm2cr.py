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

import crmapconverter.osm2cr.converter_modules.converter as converter
import crmapconverter.osm2cr.converter_modules.cr_operations.export as ex
from crmapconverter.osm2cr import config
from crmapconverter.osm2cr.converter_modules.intermediate_format.intermediate_format import IntermediateFormat
from crmapconverter.osm2cr.converter_modules.osm_operations.downloader import (
    download_around_map,
)
from crmapconverter.osm2cr.converter_modules.gui_modules.gui_embedding import MainApp
from crmapconverter.osm2cr.main import start_gui


from crmapconverter.io.V3_0.GUI_resources.MainWindow import Ui_mainWindow
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class OSM2CR(QDialog):
    def __init__(self, parent=None):
        super(OSM2CR, self).__init__(parent)
        self.statsText = None
        self.input_filename = None
        self.current_scenario = None

        self.loaded_osm = None
        self.loaded_scenario = None

        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.canvas.mpl_connect('scroll_event', self.zoom)
        self.canvas.mpl_connect('button_press_event', self.zoom)
        start_gui(self)

    def osm_cr_lanelets_menu(self):
        """Open the menu for the lanelet conversion between OSM and CR"""
        osmcr_lanelets_window = OSMLaneletsConvertWindow(parent=self)

    """def viewConvertedLaneletNetwork(self):
        """ """

        self.current_scenario = self.loadedRoadNetwork.export_commonroad_scenario()

        # temporary fix to get a plotable view of the scenario


        plot_center = self.current_scenario.lanelet_network.lanelets[0].left_vertices[0]
        # plt.style.use("classic")
        # plt.figure(figsize=(10, 10))
        plt.gca().axis("equal")
        plot_displacement_x = plot_displacement_y = 200
        plot_limits = [
            plot_center[0] - plot_displacement_x,
            plot_center[0] + plot_displacement_x,
            plot_center[1] - plot_displacement_y,
            plot_center[1] + plot_displacement_y,
        ]
        draw_object(self.current_scenario, plot_limits=plot_limits)
        self.canvas.show()"""

    def zoom(self, event):
        """
                realize zoom in / out function in GUI
                Args:
                  event:

                Returns:

                """

        ax = event.inaxes  # get the axes which mouse is now
        base_scale = 2
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()
        scope_x = (x_max - x_min) / 1.5
        scope_y = (y_max - y_min) / 1.5
        xdata = event.xdata  # get event x location
        ydata = event.ydata  # get event y location

        if event.button == 'up':
            ax.set(
                xlim=(
                    xdata -
                    scope_x /
                    base_scale,
                    xdata +
                    scope_x /
                    base_scale))
            ax.set(
                ylim=(
                    ydata -
                    scope_y /
                    base_scale,
                    ydata +
                    scope_y /
                    base_scale))
            print('up')
        elif event.button == 'down':
            ax.set(
                xlim=(
                    xdata -
                    scope_x *
                    base_scale,
                    xdata +
                    scope_x *
                    base_scale))
            ax.set(
                ylim=(
                    ydata -
                    scope_y *
                    base_scale,
                    ydata +
                    scope_y *
                    base_scale))
            print('down')

        self.canvas.draw_idle()

    def NoFileselected(self):
        reply = QMessageBox.information(
            self,
            "Information",
            "Please select a OSM file",
            QMessageBox.Ok | QMessageBox.No,
            QMessageBox.Ok)
        if reply == QMessageBox.Ok:
            self.openOpenDriveFileDialog()
        else:
            self.close


class OSMLaneletsConvertWindow(QWidget):
    """Window for conversion between OSM and CommonRoad lanelets."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.loaded_osm = None
        self.loaded_scenario = None

        self._init_user_interface()
        self.show()

    def _init_user_interface(self):
        """Build the user interface."""

        self.setWindowTitle("Lanelets CommonRoad <-> OSM Converter")

        # self.setFixedSize(560, 345)

        form_layout = QFormLayout(self)

        self.load_button = QPushButton("Load file", self)
        self.load_button.setToolTip("Load a Lanelets map")
        # self.load_button.move(10, 10)
        # self.load_button.resize(130, 35)
        self.load_button.clicked.connect(self.open_file_dialog)

        self.input_file = QLineEdit(self)
        # self.input_file.move(150, 10)
        # self.input_file.resize(400, 35)
        self.input_file.setReadOnly(True)
        form_layout.addRow(self.load_button, self.input_file)

        self.proj_string_line = QLineEdit(self)
        # self.proj_string_line.move(150, 100)
        # self.proj_string_line.resize(400, 35)
        form_layout.addRow(QLabel("Proj-string"), self.proj_string_line)

        self.direction_checkbox = QCheckBox("Use file ending")
        self.direction_checkbox.setChecked(True)
        # self.direction_checkbox.move(150, 150)
        form_layout.addRow(
            QLabel("Method to detect conversion direction"),
            self.direction_checkbox)
        self.export_to_cr_file = QPushButton("Export as CommonRoad", self)
        # self.export_to_cr_file.move(200, 300)
        # self.export_to_cr_file.resize(170, 35)
        self.export_to_cr_file.setDisabled(True)
        self.export_to_cr_file.clicked.connect(self.export_as_commonroad)

        self.export_to_osm_file = QPushButton("Export as OSM", self)
        # self.export_to_osm_file.move(10, 300)
        # self.export_to_osm_file.resize(170, 35)
        self.export_to_osm_file.setDisabled(True)
        self.export_to_osm_file.clicked.connect(self.export_as_osm)
        export_button_qhbox = QHBoxLayout(self)
        export_button_qhbox.addWidget(self.export_to_cr_file)
        export_button_qhbox.addWidget(self.export_to_osm_file)

        conversion_direction_hbox = QHBoxLayout()
        self.osm_to_cr_button = QRadioButton("OSM to CR")
        self.cr_to_osm_button = QRadioButton("CR to OSM")
        conversion_direction_hbox.addWidget(self.osm_to_cr_button)
        conversion_direction_hbox.addWidget(self.cr_to_osm_button)
        form_layout.addRow(
            QLabel("Conversion direction"),
            conversion_direction_hbox)

        self.status_qlabel = QLabel("")
        form_layout.addRow(QLabel("Status:"), self.status_qlabel)
        form_layout.addRow(export_button_qhbox)

        # self.viewOutputButton = QPushButton("View Road Network", self)
        # self.viewOutputButton.move(190, 300)
        # self.viewOutputButton.resize(170, 35)
        # self.viewOutputButton.setDisabled(True)

    def reset_output_elements(self):
        """"""
        self.export_to_cr_file.setDisabled(True)
        self.export_to_osm_file.setDisabled(True)
        self.loaded_osm = None
        self.loaded_scenario = None
        self.set_status("")

    def set_status(self, text):
        self.status_qlabel.setText(text)

    def open_file_dialog(self):
        """"""
        self.reset_output_elements()

        path, _ = QFileDialog.getOpenFileName(
            self,
            "QFileDialog.getOpenFileName()",
            "",
            "Lanelet map files (*.osm *.xml)",
            options=QFileDialog.Options(),
        )

        if not path:
            return

        filename = os.path.basename(path)
        self.input_file.setText(filename)

        if self.direction_checkbox.isChecked():
            file_ending = path.rpartition(".")[2]
            if file_ending == "osm":
                self.osm_to_cr_button.setChecked(True)
            elif file_ending == "xml":
                self.cr_to_osm_button.setChecked(True)

        if self.osm_to_cr_button.isChecked():
            with open(path) as file_in:
                parser = OSMParser(etree.parse(file_in).getroot())
            self.loaded_osm = parser.parse()
            self.export_to_cr_file.setDisabled(False)

        elif self.cr_to_osm_button.isChecked():
            try:
                commonroad_reader = CommonRoadFileReader(path)
                self.loaded_scenario, _ = commonroad_reader.open()
                self.export_to_osm_file.setDisabled(False)

            except (etree.XMLSyntaxError, AssertionError) as err:
                print(f"SyntaxError: {err}")
                self.set_status(
                    "There was an error during the loading of the selected CommonRoad file.\n"
                )

        if self.loaded_scenario or self.loaded_osm:
            self.set_status("Loaded file.")

    def export_as_commonroad(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "QFileDialog.getSaveFileName()",
            "",
            "CommonRoad files (*.xml)",
            options=QFileDialog.Options(),
        )

        if not path:
            return

        self.set_status("Converting.")
        osm2l = OSM2LConverter(proj_string=self.proj_string_line.text())
        scenario = osm2l(self.loaded_osm)
        if scenario:
            writer = CommonRoadFileWriter(
                scenario=self.loadedRoadNetwork.export_commonroad_scenario(),
                planning_problem_set=PlanningProblemSet(),
                author="",
                affiliation="",
                source="OpenDRIVE 2 Lanelet Converter",
                tags={Tag.URBAN, Tag.HIGHWAY},
            )
            writer.write_to_file(path, OverwriteExistingFile.ALWAYS)

        else:
            print("Could not convert from OSM to CommonRoad format!")

        self.set_status("Finished.")

    def export_as_osm(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "QFileDialog.getSaveFileName()",
            "",
            "OSM files (*.osm)",
            options=QFileDialog.Options(),
        )

        if not path:
            return

        self.set_status("Converting.")
        l2osm = L2OSMConverter(proj_string=self.proj_string_line.text())
        osm = l2osm(self.loaded_scenario)
        with open(f"{path}", "wb") as file_out:
            file_out.write(
                etree.tostring(
                    osm,
                    xml_declaration=True,
                    encoding="UTF-8",
                    pretty_print=True))

        self.set_status("Finished.")
