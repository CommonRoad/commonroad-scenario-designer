""" main window of the GUI Scenario Designer """

import logging
import os
import sys
from argparse import ArgumentParser

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QKeySequence, QDesktopServices

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.scenario.scenario import Scenario
from commonroad.scenario.traffic_sign import *
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from crmapconverter.io.scenario_designer.converter_modules.opendrive_interface import OpenDRIVEInterface
from crmapconverter.io.scenario_designer.converter_modules.osm_interface import OSMInterface
from crmapconverter.io.scenario_designer.gui.gui_settings import GUISettings
from crmapconverter.io.scenario_designer.gui.gui_viewer import LaneletList, IntersectionList, find_intersection_by_id, \
    AnimatedViewer
from crmapconverter.io.scenario_designer.gui_resources.MainWindow import Ui_mainWindow
from crmapconverter.io.scenario_designer.toolboxes.gui_sumo_simulation import SUMO_AVAILABLE
from crmapconverter.io.scenario_designer.toolboxes.road_network_toolbox import RoadNetworkToolbox, ObstacleToolbox, \
    MapConversionToolbox

if SUMO_AVAILABLE:
    from crmapconverter.io.scenario_designer.settings.sumo_settings import SUMOSettings
    from crmapconverter.io.scenario_designer.toolboxes.gui_sumo_simulation import SUMOSimulation

from crmapconverter.io.scenario_designer.settings import config
from crmapconverter.io.scenario_designer.misc import util
from crmapconverter.io.scenario_designer.misc.map_creator import MapCreator

from crmapconverter.io.scenario_designer.road_network_element_settings.traffic_signs_settings import \
    TrafficSignsSettings, TrafficSignsSelection, TrafficLightSelection, DeleteTrafficElement, EditTrafficLight
from crmapconverter.io.scenario_designer.road_network_element_settings.intersection_settings import *


class MWindow(QMainWindow, Ui_mainWindow):
    """The Main window of the CR Scenario Designer."""

    def __init__(self, path=None):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon(':/icons/cr.ico'))
        self.setWindowTitle("CommonRoad Designer")
        self.centralwidget.setStyleSheet('background-color:rgb(150,150,150)')
        self.setWindowFlag(True)

        # attributes
        self.filename = None
        self.crviewer = AnimatedViewer(self)
        self.lanelet_list = None
        self.intersection_list = None
        self.count = 0
        self.timer = None
        self.ani_path = None
        self.slider_clicked = False

        # Scenario + Lanelet variables
        self.selected_lanelet = None
        self.last_added_lanelet_id = None

        # GUI attributes
        self.road_network_toolbox_widget = None
        self.obstacle_toolbox_widget = None
        self.console = None
        self.play_activated = False
        self.textBrowser = None
        if SUMO_AVAILABLE:
            self.sumobox = SUMOSimulation()
        else:
            self.sumobox = None
        self.viewer_dock = None
        self.lanelet_list_dock = None
        self.intersection_list_dock = None
        self.sumo_settings = None
        self.gui_settings = None
        self.lanelet_settings = None

        if SUMO_AVAILABLE:
            # when the current scenario was simulated, load it in the gui
            self.sumobox.simulated_scenario.subscribe(self.open_scenario)
            # when the maximum simulation steps change, update the slider
            self.sumobox.config.subscribe(
                lambda config: self.update_max_step(config.simulation_steps))

        # build and connect GUI
        self.create_file_actions()
        self.create_import_actions()
        self.create_export_actions()
        self.create_setting_actions()
        self.create_help_actions()
        self.create_viewer_dock()
        self.create_toolbar()
        self.create_console()
        self.create_road_network_toolbox()
        self.create_obstacle_toolbox()
        self.create_converter_toolbox()

        self.status = self.statusbar
        self.status.showMessage("Welcome to CR Scenario Designer")

        menu_bar = self.menuBar()  # instant of menu
        menu_file = menu_bar.addMenu('File')  # add menu 'file'
        menu_file.addAction(self.fileNewAction)
        menu_file.addAction(self.fileOpenAction)
        menu_file.addAction(self.fileSaveAction)
        menu_file.addAction(self.separator)
        menu_file.addAction(self.exitAction)

        menu_import = menu_bar.addMenu('Import')  # add menu 'Import'
        menu_import.addAction(self.importfromOpendrive)
        menu_import.addAction(self.importfromOSM)
        # menu_import.addAction(self.importfromSUMO)

        menu_export = menu_bar.addMenu('Export')  # add menu 'Export'
        menu_export.addAction(self.exportAsCommonRoad)
        menu_export.addAction(self.exportAsOpendrive)

        menu_setting = menu_bar.addMenu('Setting')  # add menu 'Setting'
        menu_setting.addAction(self.gui_settings)
        menu_setting.addAction(self.sumo_settings)
        menu_setting.addAction(self.osm_settings)
        # menu_setting.addAction(self.opendrive_settings)

        menu_help = menu_bar.addMenu('Help')  # add menu 'Help'
        menu_help.addAction(self.open_web)

        self.center()

        if path:
            self.open_path(path)

    def show_osm_settings(self):
        osm_interface = OSMInterface(self)
        osm_interface.show_settings()

    def show_opendrive_settings(self):
        opendrive_interface = OpenDRIVEInterface(self)
        opendrive_interface.show_settings()

    def show_gui_settings(self):
        self.gui_settings = GUISettings(self)

    def create_obstacle_toolbox(self):
        """ Create the obstacle toolbox."""
        self.obstacle_toolbox = ObstacleToolbox()
        self.obstacle_toolbox_widget = QDockWidget("Obstacle Toolbox")
        self.obstacle_toolbox_widget.setFloating(True)
        self.obstacle_toolbox_widget.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.obstacle_toolbox_widget.setAllowedAreas(Qt.RightDockWidgetArea)
        self.obstacle_toolbox_widget.setWidget(self.obstacle_toolbox)
        self.addDockWidget(Qt.RightDockWidgetArea, self.obstacle_toolbox_widget)

    def create_converter_toolbox(self):
        """ Create the obstacle toolbox."""
        self.converter_toolbox = MapConversionToolbox()
        self.converter_toolbox_widget = QDockWidget("Map Converter Toolbox")
        self.converter_toolbox_widget.setFloating(True)
        self.converter_toolbox_widget.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.converter_toolbox_widget.setAllowedAreas(Qt.RightDockWidgetArea)
        self.converter_toolbox_widget.setWidget(self.converter_toolbox)
        self.addDockWidget(Qt.RightDockWidgetArea, self.converter_toolbox_widget)

    def create_road_network_toolbox(self):
        """ Create the Road network toolbox."""
        self.road_network_toolbox = RoadNetworkToolbox()

        self.road_network_toolbox_widget = QDockWidget("Road Network Toolbox")
        self.road_network_toolbox_widget.setFloating(True)
        self.road_network_toolbox_widget.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.road_network_toolbox_widget.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.road_network_toolbox_widget.setWidget(self.road_network_toolbox)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.road_network_toolbox_widget)
        self.road_network_toolbox.setMinimumWidth(375)

        self.initialize_lanelet_information()
        self.initialize_intersection_information()

        self.road_network_toolbox.button_add_lanelet.clicked.connect(lambda: self.add_lanelet())
        self.road_network_toolbox.button_update_lanelet.clicked.connect(lambda: self.update_lanelet())

        self.road_network_toolbox.button_remove_lanelet.clicked.connect(lambda: self.remove_lanelet())
        self.road_network_toolbox.button_fit_to_predecessor.clicked.connect(lambda: self.fit_to_predecessor())
        self.road_network_toolbox.button_create_adjacent.clicked.connect(lambda: self.create_adjacent())
        self.road_network_toolbox.button_connect_lanelets.clicked.connect(lambda: self.connect_lanelets())
        self.road_network_toolbox.button_rotate_lanelet.clicked.connect(lambda: self.rotate_lanelet())
        self.road_network_toolbox.button_translate_lanelet.clicked.connect(lambda: self.translate_lanelet())

        self.road_network_toolbox.button_add_traffic_sign_element.clicked.connect(
            lambda: self.add_traffic_sign_element())
        self.road_network_toolbox.button_remove_traffic_sign_element.clicked.connect(
            lambda: self.remove_traffic_sign_element())
        self.road_network_toolbox.button_add_traffic_sign.clicked.connect(
            lambda: self.add_traffic_sign())
        #self.road_network_toolbox.button_traffic_light.clicked.connect(lambda: self.traffic_light())
        #self.road_network_toolbox.delete_traffic_sign.clicked.connect(lambda: self.delete_traffic_element())
        #self.road_network_toolbox.edit_button_traffic_light.clicked.connect(lambda: self.edittrafficlight())

        self.road_network_toolbox.button_four_way_intersection.clicked.connect(lambda: self.add_four_way_intersection())
        self.road_network_toolbox.button_three_way_intersection.clicked.connect(
            lambda: self.add_three_way_intersection())
#        self.road_network_toolbox.selected_intersection.mousePressEvent.connect(
    #       lambda: self.update_incomings())
      #  self.road_network_toolbox.button_.clicked.connect(lambda: self.fit_intersection())

    def show_sumo_settings(self):
        self.sumo_settings = SUMOSettings(self, config=self.sumobox.config)

    def get_x_position_start(self) -> float:
        """
        Extracts lanelet x-position of first center vertex.

        @return: x-position [m]
        """
        if self.road_network_toolbox.x_position_lanelet_start.text():
            return float(self.road_network_toolbox.x_position_lanelet_start.text())
        else:
            return 0

    def get_y_position_start(self) -> float:
        """
        Extracts lanelet y-position of first center vertex.

        @return: y-position [m]
        """
        if self.road_network_toolbox.y_position_lanelet_start.text():
            return float(self.road_network_toolbox.y_position_lanelet_start.text())
        else:
            return 0

    def collect_lanelet_ids(self) -> List[int]:
        """
        Collects IDs of all lanelets within a CommonRoad scenario.
        @return: List of lanelet IDs.
        """
        if self.crviewer.current_scenario is not None:
            return [la.lanelet_id for la in self.crviewer.current_scenario.lanelet_network.lanelets]
        else:
            return []

    def collect_traffic_sign_ids(self) -> List[int]:
        """
        Collects IDs of all traffic signs within a CommonRoad scenario.
        @return:
        """
        if self.crviewer.current_scenario is not None:
            return [ts.traffic_sign_id for ts in self.crviewer.current_scenario.lanelet_network.traffic_signs]
        else:
            return []

    def collect_traffic_light_ids(self) -> List[int]:
        """
        Collects IDs of all traffic lights within a CommonRoad scenario.
        @return:
        """
        if self.crviewer.current_scenario is not None:
            return [tl.traffic_light_id for tl in self.crviewer.current_scenario.lanelet_network.traffic_lights]
        else:
            return []

    def collect_intersection_ids(self) -> List[int]:
        """
        Collects IDs of all intersection within a CommonRoad scenario.
        @return:
        """
        if self.crviewer.current_scenario is not None:
            return [inter.intersection_id for inter in self.crviewer.current_scenario.lanelet_network.intersections]
        else:
            return []

    def initialize_lanelet_information(self):
        """
        Initializes GUI elements with lanelet information.
        """
        self.road_network_toolbox.x_position_lanelet_start.setText("0.0")
        self.road_network_toolbox.y_position_lanelet_start.setText("0.0")
        self.road_network_toolbox.lanelet_width.setText("3.0")
        self.road_network_toolbox.line_marking_left.setCurrentIndex(4)
        self.road_network_toolbox.line_marking_right.setCurrentIndex(4)
        self.road_network_toolbox.number_vertices.setText("20")
        self.road_network_toolbox.lanelet_length.setText("10.0")
        self.road_network_toolbox.lanelet_radius.setText("10.0")
        self.road_network_toolbox.lanelet_angle.setText("90.0")
        self.update_list_information()

    def initialize_intersection_information(self):
        """
        Initializes GUI elements with intersection information.
        """
        self.road_network_toolbox.intersection_diameter.setText("10")
        self.road_network_toolbox.intersection_lanelet_width.setText("3.0")
        self.update_list_information()

    def update_list_information(self):
        """
        Initializes Combobox GUI elements with lanelet information.
        """
        self.road_network_toolbox.predecessors.clear()
        self.road_network_toolbox.predecessors.addItems(["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox.predecessors.setCurrentIndex(0)

        self.road_network_toolbox.successors.clear()
        self.road_network_toolbox.successors.addItems(["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox.successors.setCurrentIndex(0)

        self.road_network_toolbox.adjacent_right.clear()
        self.road_network_toolbox.adjacent_right.addItems(["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox.adjacent_right.setCurrentIndex(0)

        self.road_network_toolbox.adjacent_left.clear()
        self.road_network_toolbox.adjacent_left.addItems(["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox.adjacent_left.setCurrentIndex(0)

        self.road_network_toolbox.lanelet_referenced_traffic_sign_ids.clear()
        self.road_network_toolbox.lanelet_referenced_traffic_sign_ids.addItems(
            ["None"] + [str(item) for item in self.collect_traffic_sign_ids()])
        self.road_network_toolbox.lanelet_referenced_traffic_sign_ids.setCurrentIndex(0)

        self.road_network_toolbox.lanelet_referenced_traffic_light_ids.clear()
        self.road_network_toolbox.lanelet_referenced_traffic_light_ids.addItems(
            ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox.lanelet_referenced_traffic_light_ids.setCurrentIndex(0)

        self.road_network_toolbox.selected_lanelet_one.clear()
        self.road_network_toolbox.selected_lanelet_one.addItems(
            ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox.selected_lanelet_one.setCurrentIndex(0)

        self.road_network_toolbox.selected_lanelet_two.clear()
        self.road_network_toolbox.selected_lanelet_two.addItems(
            ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox.selected_lanelet_two.setCurrentIndex(0)

        self.road_network_toolbox.selected_intersection.clear()
        self.road_network_toolbox.selected_intersection.addItems(
            ["None"] + [str(item) for item in self.collect_intersection_ids()])
        self.road_network_toolbox.selected_lanelet_two.setCurrentIndex(0)

        self.road_network_toolbox.referenced_lanelets_traffic_sign.clear()
        self.road_network_toolbox.referenced_lanelets_traffic_sign.addItems(
            ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox.referenced_lanelets_traffic_sign.setCurrentIndex(0)

        self.road_network_toolbox.referenced_lanelets_traffic_light.clear()
        self.road_network_toolbox.referenced_lanelets_traffic_light.addItems(
            ["None"] + [str(item) for item in self.collect_lanelet_ids()])
        self.road_network_toolbox.referenced_lanelets_traffic_light.setCurrentIndex(0)

    def add_lanelet(self):
        """
        Adds a lanelet to the scenario based on the selected parameters by the user.
        """
        if self.crviewer.current_scenario is None:
            self.textBrowser.append("Please create first a new scenario.")
            return

        lanelet_pos_x = self.get_x_position_start()
        lanelet_pos_y = self.get_y_position_start()
        lanelet_width = float(self.road_network_toolbox.lanelet_width.text())
        line_marking_left = LineMarking(self.road_network_toolbox.line_marking_left.currentText())
        line_marking_right = LineMarking(self.road_network_toolbox.line_marking_right.currentText())
        num_vertices = int(self.road_network_toolbox.number_vertices.text())
        predecessors = [int(pre) for pre in self.road_network_toolbox.predecessors.get_checked_items()]
        successors = [int(suc) for suc in self.road_network_toolbox.successors.get_checked_items()]
        if self.road_network_toolbox.adjacent_left.currentText() != "None":
            adjacent_left = int(self.road_network_toolbox.adjacent_left.currentText())
        else:
            adjacent_left = None
        if self.road_network_toolbox.adjacent_right.currentText() != "None":
            adjacent_right = int(self.road_network_toolbox.adjacent_right.currentText())
        else:
            adjacent_right = None
        adjacent_left_same_direction = self.road_network_toolbox.adjacent_left_same_direction.isChecked()
        adjacent_right_same_direction = self.road_network_toolbox.adjacent_right_same_direction.isChecked()
        lanelet_type = {LaneletType(ty) for ty in self.road_network_toolbox.lanelet_type.get_checked_items()
                        if ty is not "None"}
        user_one_way = {RoadUser(user) for user in self.road_network_toolbox.road_user_oneway.get_checked_items()
                        if user is not "None"}
        user_bidirectional = \
            {RoadUser(user) for user in self.road_network_toolbox.road_user_bidirectional.get_checked_items()
             if user is not "None"}
        traffic_signs = None
        traffic_lights = None
        stop_line_start = None
        stop_line_end = None
        stop_line_marking = None
        lanelet_length = float(self.road_network_toolbox.lanelet_length.text())
        lanelet_radius = float(self.road_network_toolbox.lanelet_radius.text())
        lanelet_angle = np.deg2rad(float(self.road_network_toolbox.lanelet_angle.text()))
        add_curved_selection = self.road_network_toolbox.curved_lanelet_selection.isChecked()
        connect_to_last_selection = self.road_network_toolbox.connect_to_previous_selection.isChecked()
        connect_to_predecessors_selection = self.road_network_toolbox.connect_to_predecessors_selection.isChecked()
        connect_to_successors_selection = self.road_network_toolbox.connect_to_successors_selection.isChecked()

        lanelet_id = self.crviewer.current_scenario.generate_object_id()
        if add_curved_selection:
            lanelet = MapCreator.create_curve(lanelet_width, lanelet_radius, lanelet_angle, num_vertices, lanelet_id,
                                              lanelet_type, predecessors, successors, adjacent_left, adjacent_right,
                                              adjacent_left_same_direction, adjacent_right_same_direction,
                                              user_one_way, user_bidirectional, line_marking_left,
                                              line_marking_right)
        else:
            lanelet = MapCreator.create_straight(lanelet_width, lanelet_length, num_vertices, lanelet_id, lanelet_type,
                                                 predecessors, successors, adjacent_left, adjacent_right,
                                                 adjacent_left_same_direction, adjacent_right_same_direction,
                                                 user_one_way, user_bidirectional, line_marking_left,
                                                 line_marking_right)
        if connect_to_last_selection:
            if self.last_added_lanelet_id is not None:
                MapCreator.fit_to_predecessor(
                    self.crviewer.current_scenario.lanelet_network.find_lanelet_by_id(self.last_added_lanelet_id),
                    lanelet)
        elif connect_to_predecessors_selection:
            if len(predecessors) > 0:
                MapCreator.fit_to_predecessor(
                    self.crviewer.current_scenario.lanelet_network.find_lanelet_by_id(predecessors[0]), lanelet)
        elif connect_to_successors_selection:
            if len(successors) > 0:
                MapCreator.fit_to_successor(
                    self.crviewer.current_scenario.lanelet_network.find_lanelet_by_id(successors[0]), lanelet)
        self.last_added_lanelet_id = lanelet_id
        self.crviewer.current_scenario.lanelet_network.add_lanelet(lanelet=lanelet)

        lanelet.translate_rotate(np.array([lanelet_pos_x, lanelet_pos_y]), 0)
        self.update_view(focus_on_network=True)
        self.update_list_information()

    def update_lanelet(self):
        """
        Updates a given lanelet based on the information configured by the user.
        """
        if self.crviewer.current_scenario is None:
            self.textBrowser.append("Please create first a new scenario.")
            return
        selected_lanelet = self.crviewer.current_scenario.lanelet_network.find_lanelet_by_id(
            int(self.road_network_toolbox.selected_lanelet_one.currentText()))

    def create_adjacent(self):
        """
        Create adjacent lanelet given a selected lanelet
        """
        if self.crviewer.current_scenario == None:
            self.textBrowser.append("Create a new file!")
            return
        if self.road_network_toolbox.selected_lanelet_one.currentText() != "None":
            selected_lanelet = self.crviewer.current_scenario.lanelet_network.find_lanelet_by_id(
                int(self.road_network_toolbox.selected_lanelet_one.currentText()))
        else:
            self.textBrowser.append("No lanelet selected for [1].")
            return
        adjacent_left = self.road_network_toolbox.create_adjacent_left_selection.isChecked()
        adjacent_same_direction = self.road_network_toolbox.create_adjacent_same_direction_selection.isChecked()

        lanelet_width = float(self.road_network_toolbox.lanelet_width.text())
        line_marking_left = LineMarking(self.road_network_toolbox.line_marking_left.currentText())
        line_marking_right = LineMarking(self.road_network_toolbox.line_marking_right.currentText())
        predecessors = [int(pre) for pre in self.road_network_toolbox.predecessors.get_checked_items()]
        successors = [int(suc) for suc in self.road_network_toolbox.successors.get_checked_items()]
        lanelet_type = {LaneletType(ty) for ty in self.road_network_toolbox.lanelet_type.get_checked_items()
                        if ty is not "None"}
        user_one_way = {RoadUser(user) for user in self.road_network_toolbox.road_user_oneway.get_checked_items()
                        if user is not "None"}
        user_bidirectional = \
            {RoadUser(user) for user in self.road_network_toolbox.road_user_bidirectional.get_checked_items()
             if user is not "None"}
        traffic_signs = None
        traffic_lights = None
        stop_line_start = None
        stop_line_end = None
        stop_line_marking = None

        if adjacent_left:
            adjacent_lanelet = MapCreator.create_adjacent_lanelet(adjacent_left, selected_lanelet,
                                                                        self.crviewer.current_scenario.generate_object_id(),
                                                                        adjacent_same_direction,
                                                                        lanelet_width, lanelet_type,
                                                                        predecessors, successors, user_one_way,
                                                                        user_bidirectional, line_marking_left,
                                                                        line_marking_right)
        else:
            adjacent_lanelet = MapCreator.create_adjacent_lanelet(adjacent_left, selected_lanelet,
                                                                        self.crviewer.current_scenario.generate_object_id(),
                                                                        adjacent_same_direction,
                                                                        lanelet_width, lanelet_type,
                                                                        predecessors, successors, user_one_way,
                                                                        user_bidirectional, line_marking_left,
                                                                        line_marking_right)

        self.last_added_lanelet_id = adjacent_lanelet.lanelet_id
        self.crviewer.current_scenario.lanelet_network.add_lanelet(lanelet=adjacent_lanelet)
        self.update_view(focus_on_network=True)
        self.update_list_information()

    def remove_lanelet(self):
        """
        Removes a selected lanelet from the scenario.
        """
        if self.crviewer.current_scenario == None:
            self.textBrowser.append("Create a new file")
            return
        if self.road_network_toolbox.selected_lanelet_one.currentText() != "None":
            selected_lanelet = int(self.road_network_toolbox.selected_lanelet_one.currentText())
        else:
            self.textBrowser.append("No lanelet selected for [1].")
            return

        MapCreator.remove_lanelet(selected_lanelet, self.crviewer.current_scenario.lanelet_network)
        self.update_view(focus_on_network=True)
        self.update_list_information()

    def add_four_way_intersection(self):
        """
        Adds a four-way intersection to the scenario.
        """
        if self.crviewer.current_scenario == None:
            self.textBrowser.append("_Warning:_ Create a new file")
            return

        width = float(self.road_network_toolbox.intersection_lanelet_width.text())
        diameter = int(self.road_network_toolbox.intersection_diameter.text())

        intersection, new_lanelets = MapCreator.create_four_way_intersection(width, diameter,
                                                                             self.crviewer.current_scenario)
        self.crviewer.current_scenario.add_objects(intersection)
        self.crviewer.current_scenario.add_objects(new_lanelets)
        self.update_list_information()
        self.update_view(focus_on_network=True)

    def add_three_way_intersection(self):
        """
        Adds a three-way intersection to the scenario.
        @return:
        """
        if self.crviewer.current_scenario == None:
            self.textBrowser.append("_Warning:_ Create a new file")
            return
        width = float(self.road_network_toolbox.intersection_lanelet_width.text())
        diameter = int(self.road_network_toolbox.intersection_diameter.text())

        intersection, new_lanelets = MapCreator.create_three_way_crossing(width, diameter,
                                                                          self.crviewer.current_scenario)

        self.crviewer.current_scenario.add_objects(intersection)
        self.crviewer.current_scenario.add_objects(new_lanelets)
        self.update_list_information()
        self.update_view(focus_on_network=True)

    def update_incomings(self):
        """Updates incoming table information."""

        selected_intersection = self.crviewer.current_scenario.lanelet_network.find_intersection_by_id(
            int(self.road_network_toolbox.selected_intersection.currentText()))
        for inc in selected_intersection.incomings:
            self.road_network_toolbox.intersection_incomings_table.setItem(0, 0, inc.incoming_id)

    def add_traffic_sign_element(self):
        """
        Adds traffic sign element to traffic sign.
        Only a default entry is created the user has to specify the traffic sign ID manually afterward.
        """
        if self.crviewer.current_scenario == None:
            self.textBrowser.append("_Warning:_ Create a new file")
            return
        selected_country = self.road_network_toolbox.country.currentText()
        num_rows = self.road_network_toolbox.traffic_sign_element_table.rowCount()
        self.road_network_toolbox.traffic_sign_element_table.insertRow(num_rows)
        comboBox = QComboBox()
        comboBox.addItems([elem.name for elem in globals()["TrafficSignID"
                                                           + SupportedTrafficSignCountry(selected_country).name.capitalize()]])
        self.road_network_toolbox.traffic_sign_element_table.setCellWidget(num_rows, 0, comboBox)

    def remove_traffic_sign_element(self):
        """
        Removes last entry in traffic sign element table of a traffic sign.
        """
        num_rows = self.road_network_toolbox.traffic_sign_element_table.rowCount()
        self.road_network_toolbox.traffic_sign_element_table.removeRow(num_rows - 1)

    def table_comobox_connection(self):
        row = sorted(self.road_network_toolbox.traffic_sign_element_table.selectionModel().selectedIndexes())[0].row()
        self.road_network_toolbox.traffic_sign_element_table.item(row, 0).setText()

    def add_traffic_sign(self):
        if self.crviewer.current_scenario == None:
            self.textBrowser.append("_Warning:_ Create a new file")
            return
        selected_country = self.road_network_toolbox.country.currentText()
        country_signs = globals()["TrafficSignID" + SupportedTrafficSignCountry(selected_country).name.capitalize()]
        traffic_sign_elements = []
        referenced_lanelets = \
            [int(la) for la in self.road_network_toolbox.referenced_lanelets_traffic_sign.get_checked_items()]
        first_occurence = set()
        virtual = False
        for row in range(self.road_network_toolbox.traffic_sign_element_table.rowCount()):
            sign_id = self.road_network_toolbox.traffic_sign_element_table.cellWidget(row, 0).currentText()
            if self.road_network_toolbox.traffic_sign_element_table.item(row, 1) is None:
                additional_value = []
            else:
                additional_value = [self.road_network_toolbox.traffic_sign_element_table.item(row, 1).text()]
            traffic_sign_elements.append(TrafficSignElement(country_signs[sign_id], additional_value))

        if len(traffic_sign_elements) == 0:
            self.textBrowser.append("_Warning:_ No traffic sign element added.")
            return
        new_sign = TrafficSign(self.crviewer.current_scenario.generate_object_id(), traffic_sign_elements,
                               first_occurence, np.array([0, 0]), virtual)

        self.crviewer.current_scenario.add_objects(new_sign, referenced_lanelets)
        self.update_list_information()
        self.update_view(focus_on_network=True)

    def connect_lanelets(self):
        if self.crviewer.current_scenario == None:
            self.textBrowser.append("create a new file")
            return

        if self.road_network_toolbox.selected_lanelet_one.currentText() != "None":
            selected_lanelet_one = self.crviewer.current_scenario.lanelet_network.find_lanelet_by_id(
                int(self.road_network_toolbox.selected_lanelet_one.currentText()))
        else:
            self.textBrowser.append("No lanelet selected for [1].")
            return
        if self.road_network_toolbox.selected_lanelet_two.currentText() != "None":
            selected_lanelet_two = self.crviewer.current_scenario.lanelet_network.find_lanelet_by_id(
                int(self.road_network_toolbox.selected_lanelet_two.currentText()))
        else:
            self.textBrowser.append("No lanelet selected for [2].")
            return

        connected_lanelet = MapCreator.connect_lanelets(selected_lanelet_one, selected_lanelet_two,
                                                        self.crviewer.current_scenario.generate_object_id())
        self.last_added_lanelet_id = connected_lanelet.lanelet_id
        self.crviewer.current_scenario.lanelet_network.add_lanelet(lanelet=connected_lanelet)
        self.update_view(focus_on_network=True)
        self.update_list_information()

    def fit_to_predecessor(self):
        if self.crviewer.current_scenario == None:
            self.textBrowser.append("create a new file")
            return

        if self.road_network_toolbox.selected_lanelet_one.currentText() != "None":
            selected_lanelet_one = self.crviewer.current_scenario.lanelet_network.find_lanelet_by_id(
                int(self.road_network_toolbox.selected_lanelet_one.currentText()))
        else:
            self.textBrowser.append("No lanelet selected for [1].")
            return
        if self.road_network_toolbox.selected_lanelet_two.currentText() != "None":
            selected_lanelet_two = self.crviewer.current_scenario.lanelet_network.find_lanelet_by_id(
                int(self.road_network_toolbox.selected_lanelet_two.currentText()))
        else:
            self.textBrowser.append("No lanelet selected for [2].")
            return

        MapCreator.fit_to_predecessor(selected_lanelet_two, selected_lanelet_one)
        self.update_view(focus_on_network=True)

    def rotate_lanelet(self):
        if self.crviewer.current_scenario == None:
            self.textBrowser.append("create a new file")
            return
        if self.road_network_toolbox.selected_lanelet_one.currentText() != "None":
            selected_lanelet_one = self.crviewer.current_scenario.lanelet_network.find_lanelet_by_id(
                int(self.road_network_toolbox.selected_lanelet_one.currentText()))
        else:
            self.textBrowser.append("No lanelet selected for [1].")
            return
        rotation_angle = int(self.road_network_toolbox.rotation_angle.text())
        selected_lanelet_one.translate_rotate(np.array([0, 0]), np.deg2rad(rotation_angle))
        self.update_view(focus_on_network=True)

    def translate_lanelet(self):
        if self.crviewer.current_scenario == None:
            self.textBrowser.append("create a new file")
            return
        if self.road_network_toolbox.selected_lanelet_one.currentText() != "None":
            selected_lanelet_one = self.crviewer.current_scenario.lanelet_network.find_lanelet_by_id(
                int(self.road_network_toolbox.selected_lanelet_one.currentText()))
        else:
            self.textBrowser.append("No lanelet selected for [1].")
            return
        x_translation = float(self.road_network_toolbox.x_translation.text())
        y_translation = float(self.road_network_toolbox.y_translation.text())
        selected_lanelet_one.translate_rotate(np.array([x_translation, y_translation]), 0)
        self.update_view(focus_on_network=True)


    def fit_intersection(self):
        self.FI.exec()
        predecessor_ID = self.FI.get_Predecessor_Id()
        successor_ID = self.FI.get_Successor_Id()
        intersection_ID = self.FI.get_Intersection_Id()

        lanelet_predecessor = self.crviewer.current_scenario.lanelet_network.find_lanelet_by_id(predecessor_ID)
        lanelet_successor = self.crviewer.current_scenario.lanelet_network.find_lanelet_by_id(successor_ID)
        intersection = self.crviewer.current_scenario.lanelet_network.find_intersection_by_id(intersection_ID)

        self.map_creator.fit_intersection_to_predecessor(lanelet_predecessor, lanelet_successor, intersection,
                                                         self.crviewer.current_scenario.lanelet_network,
                                                         self.crviewer.current_scenario)
        self.update_view(focus_on_network=True)

    def create_lanelet_list(self):
        """Create the lanelet_list and put it into right Dockwidget area."""

        def remove_selection_and_close(_):
            """ remove selection from plot when list is closed"""
            self.lanelet_list.reset_selection()
            self.update_view()

        if self.lanelet_list_dock is not None:
            self.lanelet_list_dock.close()
            self.lanelet_list_dock = None
        self.lanelet_list_dock = QDockWidget("Lanelets")
        self.lanelet_list_dock.setFloating(True)
        self.lanelet_list_dock.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.lanelet_list_dock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.lanelet_list_dock.setWidget(self.lanelet_list)
        self.lanelet_list_dock.closeEvent = remove_selection_and_close
        self.addDockWidget(Qt.RightDockWidgetArea, self.lanelet_list_dock)

    def show_lanelet_list(self):
        """Function connected with button 'Lanelets List' to show the lanelets list."""
        if self.lanelet_list_dock is None:
            if self.crviewer.current_scenario is None:
                messbox = QMessageBox()
                messbox.warning(
                    self, "Warning",
                    "Please load or convert a CR Scenario firstly",
                    QtWidgets.QMessageBox.Ok)
                messbox.close()
            else:
                self.lanelet_list_dock.show()
        else:
            self.lanelet_list_dock.show()

    def create_intersection_list(self):
        """Create the lanelet_list and put it into right Dockwidget area."""

        def remove_selection_and_close(_):
            """ remove selection from plot when list is closed"""
            self.intersection_list.reset_selection()
            self.update_view()

        if self.intersection_list_dock is not None:
            self.intersection_list_dock.close()
            self.intersection_list_dock = None
        self.intersection_list_dock = QDockWidget("Intersections")
        self.intersection_list_dock.setFloating(True)
        self.intersection_list_dock.setFeatures(
            QDockWidget.AllDockWidgetFeatures)
        self.intersection_list_dock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.intersection_list_dock.setWidget(self.intersection_list)
        self.intersection_list_dock.closeEvent = remove_selection_and_close
        self.addDockWidget(Qt.RightDockWidgetArea, self.intersection_list_dock)

    def show_intersection_list(self):
        """Function connected with button 'Lanelets List' to show the lanelets list."""
        if self.intersection_list_dock is None:
            if self.crviewer.current_scenario is None:
                messbox = QMessageBox()
                messbox.warning(
                    self, "Warning",
                    "Please load or convert a CR Scenario or first",
                    QtWidgets.QMessageBox.Ok)
                messbox.close()
            else:
                self.intersection_list_dock.show()
        else:
            self.intersection_list_dock.show()

    def create_laneletinformation(self):
        """ Create the Upper toolbox."""
        self.lowertoolBox = LaneletInformationToolbox()

        self.obstacle_toolbox_widget = QDockWidget("Lanelet Information")
        self.obstacle_toolbox_widget.setFloating(True)
        self.obstacle_toolbox_widget.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.obstacle_toolbox_widget.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.obstacle_toolbox_widget.setWidget(self.lowertoolBox)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.obstacle_toolbox_widget)
        self.lowertoolBox.refresh_button.clicked.connect(lambda: self.refresh_information())
        self.obstacle_toolbox_widget.setMaximumHeight(400)
        self.lowertoolBox.edit_button.clicked.connect(lambda: self.edit_lanelet())

    #        if self.crviewer.selected_lanelet_use[0]:
    #           self.selected_lanelet = self.crviewer.selected_lanelet_use[0]

    # selected_lanelet = self.crviewer.current_scenario.lanelet_network.find_lanelet_by_id(
    #  self.lanelet_list.selected_id)

    def refresh_information(self):
        if self.crviewer.current_scenario is None:
            messbox = QMessageBox()
            messbox.warning(
                self, "Warning",
                "Please load or convert a CR Scenario firstly",
                QtWidgets.QMessageBox.Ok)
            messbox.close()
        else:
            if self.crviewer.selected_lanelet_use != None:
                self.selected_lanelet = self.crviewer.selected_lanelet_use[0]
                id = str(self.selected_lanelet._lanelet_id)
                self.selected_id = int(id)
                num_vertices = len(self.selected_lanelet.center_vertices)
                length = self.selected_lanelet.center_vertices[0] - self.selected_lanelet.center_vertices[-1]
                length = np.linalg.norm(length)
                width_array = self.selected_lanelet.left_vertices[0] - self.selected_lanelet.right_vertices[0]
                width = np.linalg.norm(width_array)
                self.lowertoolBox.laneletID.clear()
                self.lowertoolBox.laneletID.insert(id)
                self.lowertoolBox.number_vertices.clear()
                self.lowertoolBox.number_vertices.insert(str(num_vertices))
                self.lowertoolBox.length.clear()
                self.lowertoolBox.length.insert(str(int(length)))
                self.lowertoolBox.width.clear()
                self.lowertoolBox.width.insert((str(int(width))))
                self.lowertoolBox.angle.clear()
                angle = self.map_creator.calc_angle_between2(self.selected_lanelet)
                angle = (angle / np.pi) * 180
                self.lowertoolBox.radius.clear()
                rad = self.map_creator.calc_radius(self.selected_lanelet)
                self.lowertoolBox.traffic_sign_ids.clear()
                traffic_ids = self.selected_lanelet.traffic_signs
                for t in traffic_ids:
                    t = str(t)
                    self.lowertoolBox.traffic_sign_ids.insert(t)
                    self.lowertoolBox.traffic_sign_ids.insert(", ")
                self.lowertoolBox.traffic_light_ids.clear()
                trafficlight_ids = self.selected_lanelet.traffic_lights
                for t in trafficlight_ids:
                    t = str(t)
                    self.lowertoolBox.traffic_light_ids.insert(t)
                    self.lowertoolBox.traffic_light_ids.insert(", ")
                if int(angle) != 0:
                    self.lowertoolBox.angle.clear()
                    self.lowertoolBox.angle.insert(str(int(angle)))
                    self.lowertoolBox.length.clear()
                    self.lowertoolBox.radius.clear()
                    self.lowertoolBox.radius.insert(str(int(rad)))
            else:
                self.textBrowser.append("_Warning: Select a lanelet")
                return

    def edit_lanelet(self):

        if self.crviewer.current_scenario is None:
            messbox = QMessageBox()
            messbox.warning(
                self, "Warning",
                "Please load or convert a CR Scenario firstly",
                QtWidgets.QMessageBox.Ok)
            messbox.close()
            return

        posX = 0
        posY = 0
        if self.crviewer.current_scenario == None:
            self.textBrowser.append("create a new file")
            return

        if self.lowertoolBox.width.text():
            self.selected_width = int(self.lowertoolBox.width.text())
        else:
            self.textBrowser.append("define a vaild width")
            return

        if self.lowertoolBox.length.text():
            self.selected_length = int(self.lowertoolBox.length.text())
        else:
            self.selected_length = 0

        if self.lowertoolBox.angle.text():
            self.selected_angle = int(self.lowertoolBox.angle.text())
        else:
            self.selected_angle = 0

        if self.lowertoolBox.radius.text():
            self.selected_radius = int(self.lowertoolBox.radius.text())
        else:
            self.selected_radius = 0

        if self.lowertoolBox.number_vertices.text():
            self.selected_vertices = int(self.lowertoolBox.number_vertices.text())
        else:
            self.selected_vertices = 20

        indexlist = self.lowertoolBox.getLaneletType()
        lanelettype = set()
        for i in range(0, len(indexlist)):
            lt = LaneletType(indexlist[i])
            lanelettype.add(LaneletType(indexlist[i]))

        # Roaduser one-way:
        indexlist2 = self.lowertoolBox.getOnewayRoadUser()
        roaduser_oneway = set()
        for i in range(0, len(indexlist2)):
            ro = RoadUser(indexlist2[i])
            roaduser_oneway.add(RoadUser(indexlist2[i]))

        # Roaduser bidirectional:
        indexlist3 = self.lowertoolBox.getBidirectionalRoadUser()
        roaduser_bidirectional = set()
        for i in range(0, len(indexlist3)):
            ro = RoadUser(indexlist3[i])
            roaduser_bidirectional.add(RoadUser(indexlist3[i]))

        if int((self.selected_angle)) == 0:
            self.roaduser_oneway = set()
            lanelet = self.map_creator.edit_straight(self.selected_id, self.selected_width, self.selected_length,
                                                     self.selected_vertices,
                                                     self.crviewer.current_scenario.lanelet_network,
                                                     self.crviewer.current_scenario, self.pred, lanelettype,
                                                     roaduser_oneway, roaduser_bidirectional, self.linemarkingleft,
                                                     self.linemarkingright, backwards=self.backwards)
            lanelet.translate_rotate(np.array([posX, posY]), self.rot_angle_straight)
        else:
            curve = self.map_creator.edit_curve(self.selected_id, self.selected_width, self.selected_radius,
                                                np.deg2rad(self.selected_angle), self.selected_vertices,
                                                self.crviewer.current_scenario.lanelet_network,
                                                self.crviewer.current_scenario, self.pred, self.lanelettype,
                                                self.roaduser, self.linemarkingleft, self.linemarkingright)

        self.update_view(focus_on_network=True)

    def create_sumobox(self):
        """Function to create the sumo toolbox(bottom toolbox)."""
        self.obstacle_toolbox_widget = QDockWidget("Sumo Simulation", self)
        self.obstacle_toolbox_widget.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.obstacle_toolbox_widget.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.obstacle_toolbox_widget.setWidget(self.sumobox)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.obstacle_toolbox_widget)
        self.obstacle_toolbox_widget.setMaximumHeight(400)

    def detect_slider_clicked(self):
        self.slider_clicked = True
        self.crviewer.pause()
        self.crviewer.dynamic.update_plot()

    def detect_slider_release(self):
        self.slider_clicked = False
        self.crviewer.pause()

    def timestep_change(self, value):
        if self.crviewer.current_scenario:
            self.crviewer.set_timestep(value)
            self.label1.setText('  Frame: ' + str(value))
            self.crviewer.animation.event_source.start()

    def play_pause_animation(self):
        """Function connected with the play button in the sumo-toolbox."""
        if not self.crviewer.current_scenario:
            messbox = QMessageBox()
            reply = messbox.warning(
                self, "Warning",
                "Please load an animation before attempting to play",
                QMessageBox.Ok | QMessageBox.No, QMessageBox.Ok)
            if (reply == QtWidgets.QMessageBox.Ok):
                self.open_commonroad_file()
            return
        if not self.play_activated:
            self.crviewer.play()
            self.textBrowser.append("Playing the animation")
            self.button_play_pause.setIcon(QIcon(":/icons/pause.png"))
            self.play_activated = True
        else:
            self.crviewer.pause()
            self.textBrowser.append("Pause the animation")
            self.button_play_pause.setIcon(QIcon(":/icons/play.png"))
            self.play_activated = False

    def save_animation(self):
        """Function connected with the save button in the Toolbar."""
        if not self.crviewer.current_scenario:
            messbox = QMessageBox()
            reply = messbox.warning(self, "Warning",
                                    "Please load an animation before saving",
                                    QMessageBox.Ok | QMessageBox.No,
                                    QMessageBox.Ok)
            if (reply == QtWidgets.QMessageBox.Ok):
                self.open_commonroad_file()
            else:
                messbox.close()
        else:
            self.textBrowser.append("Exporting animation: " +
                                    self.road_network_toolbox.save_menu.currentText() +
                                    " ...")
            self.crviewer.save_animation(
                self.road_network_toolbox.save_menu.currentText())
            self.textBrowser.append("Exporting finished")

    def create_console(self):
        """Function to create the console."""
        self.console = QDockWidget(self)
        self.console.setTitleBarWidget(QWidget(
            self.console))  # no title of Dock
        self.textBrowser = QtWidgets.QTextBrowser()
        self.textBrowser.setMaximumHeight(80)
        self.textBrowser.setObjectName("textBrowser")
        self.console.setWidget(self.textBrowser)
        self.console.setFloating(False)  # set if console can float
        self.console.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.console)

    def create_toolbar(self):
        """Function to create toolbar of the main Window."""
        tb1 = self.addToolBar("File")
        action_new = QAction(QIcon(":/icons/new_file.png"), "new CR File",
                             self)
        tb1.addAction(action_new)
        action_new.triggered.connect(self.file_new)
        action_open = QAction(QIcon(":/icons/open_file.png"), "open CR File",
                              self)
        tb1.addAction(action_open)
        action_open.triggered.connect(self.open_commonroad_file)
        action_save = QAction(QIcon(":/icons/save_file.png"), "save CR File",
                              self)
        tb1.addAction(action_save)
        action_save.triggered.connect(self.file_save)

        # TODO: undo button
        """action_undo = QAction(QIcon(":/icons/save_file.png"), "undo last action", self)
        tb1.addAction(action_undo)"""

        tb1.addSeparator()
        tb2 = self.addToolBar("Road Network Toolbox")
        toolbox = QAction(QIcon(":/icons/tools.ico"),
                          "show Toolbox for CR Scenario", self)
        tb2.addAction(toolbox)
        toolbox.triggered.connect(self.road_network_toolbox_show)
        tb2.addSeparator()
        lanelet_list = QAction(QIcon(":/icons/lanelet_list.ico"),
                               "show Lanelet list", self)
        intersection_list = QAction(QIcon(":/icons/intersection_list.ico"),
                                    "show Intersection list", self)
        tb2.addAction(lanelet_list)
        lanelet_list.triggered.connect(self.show_lanelet_list)
        tb2.addAction(intersection_list)
        intersection_list.triggered.connect(self.show_intersection_list)

        tb3 = self.addToolBar("Animation Play")
        self.button_play_pause = QAction(QIcon(":/icons/play.png"),
                                   "Play the animation", self)
        self.button_play_pause.triggered.connect(self.play_pause_animation)
        tb3.addAction(self.button_play_pause)
        #self.button_pause = QAction(QIcon(":/icons/pause.png"),
        #                            "Pause the animation", self)
        #self.button_pause.triggered.connect(self.pause_animation)
        #tb3.addAction(self.button_pause)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMaximumWidth(300)
        self.slider.setValue(0)
        self.slider.setMinimum(0)
        self.slider.setMaximum(99)
        # self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(1)
        self.slider.setToolTip(
            "Show corresponding Scenario at selected timestep")
        self.slider.valueChanged.connect(self.timestep_change)
        self.slider.sliderPressed.connect(self.detect_slider_clicked)
        self.slider.sliderReleased.connect(self.detect_slider_release)
        self.crviewer.timestep.subscribe(self.slider.setValue)
        tb3.addWidget(self.slider)

        self.label1 = QLabel('  Frame: 0', self)
        tb3.addWidget(self.label1)

        self.label2 = QLabel(' / 0', self)
        tb3.addWidget(self.label2)

    def update_max_step(self, value: int = -1):
        logging.info('update_max_step')
        value = value if value > -1 else self.crviewer.max_timestep
        self.label2.setText(' / ' + str(value))
        self.slider.setMaximum(value)

    def create_import_actions(self):
        """Function to create the import action in the menu bar."""
        self.importfromOpendrive = self.create_action(
            "From OpenDrive",
            icon="",
            checkable=False,
            slot=self.od_2_cr,
            tip="Convert from OpenDrive to CommonRoad",
            shortcut=None)
        self.importfromOSM = self.create_action(
            "From OSM",
            icon="",
            checkable=False,
            slot=self.osm_2_cr,
            tip="Convert from OSM to CommonRoad",
            shortcut=None)

    def cr_2_osm(self):
        osm_interface = OSMInterface(self)
        osm_interface.start_export()

    def osm_2_cr(self):
        osm_interface = OSMInterface(self)
        osm_interface.start_import()

    def od_2_cr(self):
        opendrive_interface = OpenDRIVEInterface(self)
        opendrive_interface.start_import()

    def cr_2_od(self):
        opendrive_interface = OpenDRIVEInterface(self)
        opendrive_interface.start_import()

    def create_export_actions(self):
        """Function to create the export action in the menu bar."""
        self.exportAsCommonRoad = self.create_action(
            "As CommonRoad",
            icon="",
            checkable=False,
            slot=self.file_save,
            tip="Save as CommonRoad File (the same function as Save)",
            shortcut=None)

        self.exportAsOpendrive = self.create_action(
            "As Opendrive",
            icon="",
            checkable=False,
            slot=None,
            tip="Save as Opendrive File",
            shortcut=None)

    def create_setting_actions(self):
        """Function to create the export action in the menu bar."""
        self.osm_settings = self.create_action(
            "OSM Settings",
            icon="",
            checkable=False,
            slot=self.show_osm_settings,
            tip="Show settings for osm converter",
            shortcut=None)
        self.opendrive_settings = self.create_action(
            "OpenDRIVE Settings",
            icon="",
            checkable=False,
            slot=self.show_opendrive_settings,
            tip="Show settings for OpenDRIVE converter",
            shortcut=None)
        self.gui_settings = self.create_action(
            "GUI Settings",
            icon="",
            checkable=False,
            slot=self.show_gui_settings,
            tip="Show settings for the CR Scenario Designer",
            shortcut=None)
        if SUMO_AVAILABLE:
            self.sumo_settings = self.create_action(
                "SUMO Settings",
                icon="",
                checkable=False,
                slot=self.show_sumo_settings,
                tip="Show settings for the SUMO interface",
                shortcut=None)

    def create_help_actions(self):
        """Function to create the help action in the menu bar."""
        self.open_web = self.create_action("Open CR Web",
                                           icon="",
                                           checkable=False,
                                           slot=self.open_cr_web,
                                           tip="Open CommonRoad Web",
                                           shortcut=None)

    def create_viewer_dock(self):
        self.viewer_dock = QWidget(self)
        toolbar = NavigationToolbar(self.crviewer.dynamic, self.viewer_dock)
        layout = QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.crviewer.dynamic)
        self.viewer_dock.setLayout(layout)
        self.setCentralWidget(self.viewer_dock)

    def center(self):
        """Function that makes sure the main window is in the center of screen."""
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)

    def create_file_actions(self):
        """Function to create the file action in the menu bar."""
        self.fileNewAction = self.create_action(
            "New",
            icon=QIcon(":/icons/new_file.png"),
            checkable=False,
            slot=self.file_new,
            tip="New Commonroad File",
            shortcut=QKeySequence.New)
        self.fileOpenAction = self.create_action(
            "Open",
            icon=QIcon(":/icons/open_file.png"),
            checkable=False,
            slot=self.open_commonroad_file,
            tip="Open Commonroad File",
            shortcut=QKeySequence.Open)
        self.separator = QAction(self)
        self.separator.setSeparator(True)

        self.fileSaveAction = self.create_action(
            "Save",
            icon=QIcon(":/icons/save_file.png"),
            checkable=False,
            slot=self.file_save,
            tip="Save Commonroad File",
            shortcut=QKeySequence.Save)
        self.separator.setSeparator(True)
        self.exitAction = self.create_action("Quit",
                                             icon=QIcon(":/icons/close.png"),
                                             checkable=False,
                                             slot=self.closeWindow,
                                             tip="Quit",
                                             shortcut=QKeySequence.Close)

    def create_action(self,
                      text,
                      icon=None,
                      checkable=False,
                      slot=None,
                      tip=None,
                      shortcut=None):
        """Function to create the action in the menu bar."""
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(icon))
        if checkable:
            # toggle, True means on/off state, False means simply executed
            action.setCheckable(True)
            if slot is not None:
                action.toggled.connect(slot)
        else:
            if slot is not None:
                action.triggered.connect(slot)
        if tip is not None:
            action.setToolTip(tip)  # toolbar tip
            action.setStatusTip(tip)  # statusbar tip
        if shortcut is not None:
            action.setShortcut(shortcut)  # shortcut
        return action

    def open_cr_web(self):
        """Function to open the webseite of CommonRoad."""
        QDesktopServices.openUrl(QUrl("https://commonroad.in.tum.de/"))

    def file_new(self):
        """Function to create the action in the menu bar."""
        scenario = Scenario(0.1, 'new scenario')
        net = LaneletNetwork()
        scenario.lanelet_network = net
        self.crviewer.current_scenario = scenario
        self.open_scenario(scenario)
#        self.restore_parameters()

    def open_commonroad_file(self):
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
        self.open_path(path)

    def open_path(self, path):
        """ """
        try:
            commonroad_reader = CommonRoadFileReader(path)
            scenario, _ = commonroad_reader.open()
        except Exception as e:
            QMessageBox.warning(
                self,
                "CommonRoad XML error",
                "There was an error during the loading of the selected CommonRoad file.\n\n"
                + "Syntax Error: {}".format(e),
                QMessageBox.Ok,
            )
            return

        filename = os.path.splitext(os.path.basename(path))[0]
        self.open_scenario(scenario, filename)

    def open_scenario(self, new_scenario, filename="new_scenario"):
        """  """
        if self.check_scenario(new_scenario) >= 2:
            self.textBrowser.append("loading aborted")
            return
        self.filename = filename
        if SUMO_AVAILABLE:
            self.crviewer.open_scenario(new_scenario, self.sumobox.config)
            self.sumobox.scenario = self.crviewer.current_scenario
        else:
            self.crviewer.open_scenario(new_scenario)
        self.lanelet_list = LaneletList(self.update_view, self)
        self.intersection_list = IntersectionList(self.update_view, self)
        self.update_view()
        self.update_to_new_scenario()
       # self.restore_parameters()

    def update_to_new_scenario(self):
        """  """
        self.update_max_step()
        self.viewer_dock.setWindowIcon(QIcon(":/icons/cr1.ico"))
        if self.crviewer.current_scenario is not None:
            self.create_lanelet_list()
            self.create_intersection_list()
            self.setWindowTitle(self.filename)
            self.textBrowser.append("loading " + self.filename)
        else:
            self.lanelet_list_dock.close()
            self.intersection_list_dock.close()

    def check_scenario(self, scenario) -> int:
        """ 
        Check the scenario to validity and calculate a quality score.
        The higher the score the higher the data faults.

        :return: score
        """

        WARNING = 1
        FATAL_ERROR = 2
        verbose = True

        error_score = 0

        # handle fatal errors
        found_ids = util.find_invalid_ref_of_traffic_lights(scenario)
        if found_ids and verbose:
            error_score = max(error_score, FATAL_ERROR)
            self.textBrowser.append("invalid traffic light refs: " +
                                    str(found_ids))
            QMessageBox.critical(
                self,
                "CommonRoad XML error",
                "Scenario contains invalid traffic light refenence(s): " +
                str(found_ids),
                QMessageBox.Ok,
            )

        found_ids = util.find_invalid_ref_of_traffic_signs(scenario)
        if found_ids and verbose:
            error_score = max(error_score, FATAL_ERROR)
            self.textBrowser.append("invalid traffic sign refs: " +
                                    str(found_ids))
            QMessageBox.critical(
                self,
                "CommonRoad XML error",
                "Scenario contains invalid traffic sign refenence(s): " +
                str(found_ids),
                QMessageBox.Ok,
            )

        if error_score >= FATAL_ERROR:
            return error_score

        # handle warnings
        found_ids = util.find_invalid_lanelet_polygons(scenario)
        if found_ids and verbose:
            error_score = max(error_score, WARNING)
            self.textBrowser.append(
                "Warning: Lanelet(s) with invalid polygon:" + str(found_ids))
            QMessageBox.warning(
                self,
                "CommonRoad XML error",
                "Scenario contains lanelet(s) with invalid polygon: " +
                str(found_ids),
                QMessageBox.Ok,
            )

        return error_score

    def file_save(self):
        """Function to save a CR .xml file."""

        if self.crviewer.current_scenario is None:
            messbox = QMessageBox()
            messbox.warning(self, "Warning", "There is no file to save!",
                            QMessageBox.Ok, QMessageBox.Ok)
            messbox.close()
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Select file to save scenario",
            self.filename + ".xml",
            "CommonRoad files *.xml (*.xml)",
            options=QFileDialog.Options(),
        )
        if not file_path:
            return

        try:
            fd = open(file_path, "w")
            fd.close()
            writer = CommonRoadFileWriter(
                scenario=self.crviewer.current_scenario,
                planning_problem_set=None,
                author="",
                affiliation="",
                source="",
                tags="",
            )
            writer.write_scenario_to_file(file_path,
                                          OverwriteExistingFile.ALWAYS)
        except IOError as e:
            QMessageBox.critical(
                self,
                "CommonRoad file not created!",
                "The CommonRoad file was not saved due to an error.\n\n" +
                "{}".format(e),
                QMessageBox.Ok,
            )

    def processtrigger(self, q):
        self.status.showMessage(q.text() + ' is triggered')

    def closeWindow(self):
        reply = QMessageBox.warning(self, "Warning",
                                    "Do you really want to quit?",
                                    QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            qApp.quit()

    def closeEvent(self, event):
        event.ignore()
        self.closeWindow()

    def road_network_toolbox_show(self):
        self.road_network_toolbox_widget.show()

    def obstacle_toolbox_show(self):
        self.obstacle_toolbox_widget.show()

    def update_view(self, caller=None, focus_on_network=None):
        """ update all compoments. triggered by the component caller"""

        # reset selection of all other selectable elements
        if caller is not None:
            if caller is not self.intersection_list:
                self.intersection_list.reset_selection()
            if caller is not self.lanelet_list:
                self.lanelet_list.reset_selection()

        self.lanelet_list.update(self.crviewer.current_scenario)
        self.intersection_list.update(self.crviewer.current_scenario)

        if self.crviewer.current_scenario is None:
            return
        if self.intersection_list.selected_id is not None:
            selected_intersection = find_intersection_by_id(
                self.crviewer.current_scenario,
                self.intersection_list.selected_id)
        else:
            selected_intersection = None
        if self.lanelet_list.selected_id is not None:
            selected_lanelet = self.crviewer.current_scenario.lanelet_network.find_lanelet_by_id(
                self.lanelet_list.selected_id)
        else:
            selected_lanelet = None
        if focus_on_network is None:
            focus_on_network = config.AUTOFOCUS
        self.crviewer.update_plot(sel_lanelet=selected_lanelet,
                                  sel_intersection=selected_intersection,
                                  focus_on_network=focus_on_network)

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


def main():
    parser = ArgumentParser()
    parser.add_argument("--input_file",
                        "-i",
                        default=None,
                        help="load this file after startup")
    args = parser.parse_args()

    # application
    app = QApplication(sys.argv)
    if args.input_file:
        w = MWindow(args.input_file)
    else:
        w = MWindow()
    w.showMaximized()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
