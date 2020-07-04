import signal
import sys
import os
from lxml import etree
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.path import Path
from matplotlib.patches import PathPatch

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.visualization.draw_dispatch_cr import draw_object
from crmapconverter.io.viewer import MainWindow as ViewerWidget
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.scenario import Tag
from crmapconverter.io.V3_0.gui_cr_viewer import Crviewer

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


class OSM2CR(QDialog):
    def __init__(self, parent=None):
        super(OSM2CR, self).__init__(parent)
        self.statsText = None
        self.input_filename = None
        self.current_scenario = None
        self.commonroad_filename = None
        self.path = None

        self.loaded_osm = None

        self.canvas = Canvas(self, width=10.8, height=7.2, dpi=100)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.laneletsList = QTableWidget(self)
        self.laneletsList.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.laneletsList.clicked.connect(self.onClickLanelet)

        self.canvas.mpl_connect('scroll_event', self.zoom)
        self.canvas.mpl_connect('button_press_event', self.zoom)
        self.start()

    def start(self):
        self.osm = MainApp()
        self.osm.start()

        if  self.osm.path != None:
            self.path = self.osm.path
            self.openPath(self.osm.path)

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

        self.openScenario(scenario)

    def openScenario(self, scenario):
        """

        Args:
          scenario:

        Returns:

        """

        self.current_scenario = scenario
        self.update_plot()

    def zoom(self, event):
        """
        realize zoom in / out function in GUI
        Args:
          event
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
        messbox = QMessageBox()
        # self.center(messbox)
        reply = messbox.information(
            self,
            "Information",
            "Please select a CR file",
            QMessageBox.Ok | QMessageBox.No,
            QMessageBox.Ok)

        if reply == QMessageBox.Ok:
            self.openCommonRoadFile()
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

    def closeEvent(self, event):
        result = QMessageBox.question(self, "Warning", "Do you want to exit?",
                                      QMessageBox.Yes | QMessageBox.No)
        if (result == QMessageBox.Yes):
            event.accept()

        else:
            event.ignore()

    def onClickLanelet(self):
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
        self.laneletsList.setHorizontalHeaderLabels(
            ["Lanelet-Id", "Description"])
        # lanelet_data = [
        #     (lanelet.lanelet_id, lanelet.description)
        #     for lanelet in self.current_scenario.lanelet_network.lanelets
        # ]
        lanelet_data = []
        for lanelet in self.current_scenario.lanelet_network.lanelets:
            try:
                lanelet_data.append((lanelet.lanelet_id, lanelet.description))
            except AttributeError:
                lanelet_data.append((lanelet.lanelet_id, None))

        lanelet_data = sorted(lanelet_data)
        for idx, lanelet in enumerate(lanelet_data):

            # set lanelet_id
            self.laneletsList.setItem(
                idx, 0, QTableWidgetItem(f"{lanelet[0]}"))
            try:
                # set lanelet description (old id)
                self.laneletsList.setItem(
                    idx, 1, QTableWidgetItem(f"{lanelet[1]}"))
            except AttributeError:
                self.laneletsList.setItem(idx, 1, QTableWidgetItem("None"))

        self.canvas.fig.tight_layout()

    def osm_cr_lanelets_menu(self):
        """Open the menu for the lanelet conversion between OSM and CR"""
        osmcr_lanelets_window = OSMLaneletsConvertWindow(parent=self)


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
