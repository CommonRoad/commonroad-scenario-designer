""" main window of the GUI Scenario Designer """

from argparse import ArgumentParser
import os
import sys
import logging
import numpy as np
import time


from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QMainWindow, QDockWidget, QMessageBox, QAction,
                             QLabel, QFileDialog, QDesktopWidget, QVBoxLayout,
                             QSlider, QWidget, QApplication, qApp, QLineEdit, QFormLayout, QPushButton, QDialog)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QIcon, QKeySequence, QDesktopServices, QIntValidator
from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT as
                                                NavigationToolbar)

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.file_writer import (CommonRoadFileWriter,
                                           OverwriteExistingFile)
from commonroad.scenario.scenario import Scenario, LaneletNetwork, Lanelet

from crmapconverter.io.scenario_designer.gui_resources.MainWindow import Ui_mainWindow
from crmapconverter.io.scenario_designer.gui_toolbox import UpperToolbox, LaneletInformationToolbox
from crmapconverter.io.scenario_designer.converter_modules.osm_interface import OSMInterface
from crmapconverter.io.scenario_designer.converter_modules.opendrive_interface import (
    OpenDRIVEInterface)
from crmapconverter.io.scenario_designer.gui_settings import GUISettings
from crmapconverter.io.scenario_designer.sumo_gui_modules.gui_sumo_simulation import SUMO_AVAILABLE
if SUMO_AVAILABLE:
    from crmapconverter.io.scenario_designer.sumo_gui_modules.sumo_settings import SUMOSettings
    from crmapconverter.io.scenario_designer.sumo_gui_modules.gui_sumo_simulation import SUMOSimulation
from crmapconverter.io.scenario_designer.gui_viewer import (
    LaneletList, IntersectionList, find_intersection_by_id, AnimatedViewer)
from crmapconverter.io.scenario_designer import config
from crmapconverter.io.scenario_designer import util
from crmapconverter.io.scenario_designer.lanelet_settings import LaneletSettings
from crmapconverter.io.scenario_designer.curve_settings import CurveSettings
from crmapconverter.io.scenario_designer.traffic_signs_settings import TrafficSignsSettings, TrafficSignsSelection, TrafficLightSelection, DeleteTrafficElement

from crmapconverter.io.scenario_designer.adjecent_settings import AdjecentSettings, ConnectSettings, FitSettings, RemoveSettings
from crmapconverter.io.scenario_designer.intersection_settings import *

from commonroad.scenario.lanelet import Lanelet, LaneletType, LaneletNetwork
from commonroad.scenario.traffic_sign import *
from commonroad.scenario.traffic_sign_interpreter import TrafficSigInterpreter

from crmapconverter.io.scenario_designer.map_creator import mapcreator

class MWindow(QMainWindow, Ui_mainWindow):
    """The Mainwindow of CR Scenario Designer."""
    def __init__(self, path=None):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon(':/icons/cr.ico'))
        self.centralwidget.setStyleSheet('background-color:rgb(150,150,150)')
        self.setWindowFlag(True)

        # attributes
        self.mapcreator = mapcreator()
        self.filename = None
        self.crviewer = AnimatedViewer(self)
        self.lanelet_list = None
        self.intersection_list = None
        self.count = 0
        self.timer = None
        self.ani_path = None
        self.slider_clicked = False

        #Senario + Lanelet variables
        self.scenario = None
        self.latestid = None
        self.traffic_signs_id = 200
        self.traffic_light_id = 300
        self.selected_lanelet = None
        self.selected_predecessor = None
        self.selected_successor = None

        self.pred = False
        self.rot_angle_straight = 0
        self.rot_angle_curve = 0

        self.lenfor = 50
        self.widfor = 20
        self.vertfor = 20
        self.adjfor = None
        self.lanelettype = set()
        self.roaduser ="vehicle"
        self.linemarkingleft = "no_marking"
        self.linemarkingright = "no_marking"
        self.lanelet_pos_x = 0
        self.lanelet_pos_y = 0
        self.backwards = False
        self.roaduser_oneway = set()
        self.roaduser_bidirectional = set()

        self.radcurve = 50
        self.widcurve = 20
        self.numcurve = 30
        self.anglcurve = np.pi/2
        self.adjcurve = None
        self.curvetype = "urban"
        self.roaduser_curve = "vehicle"
        self.linemarkingright_curve = "no_marking"
        self.linemarkingleft_curve = "no_marking"
        self.curve_pos_x = 0
        self.curve_pos_y = 0
        self.curve_direction = False

        # GUI attributes
        self.tool1 = None
        self.tool2 = None
        self.toolBox = None
        self.console = None
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
        self.create_toolbox()
        self.create_laneletinformation()
        #self.create_laneletsettings()

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

    def show_sumo_settings(self):
        self.sumo_settings = SUMOSettings(self, config=self.sumobox.config)


    # Toolbox functionality
    def click_straight(self, posX, posY):
        if self.scenario == None:
            self.textBrowser.append("create a new file")
            return
        lanelet = self.mapcreator.create_straight(self.widfor, self.lenfor, self.vertfor,
                                             self.scenario.lanelet_network, self.scenario, self.pred, self.lanelettype,
                                             self.roaduser_oneway, self.roaduser_bidirectional, self.linemarkingleft,
                                             self.linemarkingright, backwards=self.backwards)
        lanelet.translate_rotate(np.array([posX, posY]), self.rot_angle_straight)

        self.update_view(focus_on_network=True)

    def click_curve(self, turnright=True, curve_posX=0, curve_posY=0):
        if self.scenario == None:
            self.textBrowser.append("create a new file")
            return
        if turnright:
            lanelet = self.mapcreator.create_curve(self.widcurve, self.radcurve, self.anglcurve,self.numcurve,
                                              self.scenario.lanelet_network, self.scenario, self.pred, self.curvetype,
                                              self.roaduser_curve, self.linemarkingleft_curve, self.linemarkingright_curve)

            #lanelet.translate_rotate(np.array([curve_posX, curve_posY]), -np.pi/2)

        else:
            lanelet = self.mapcreator.create_curve(self.widcurve, self.radcurve, -self.anglcurve, self.numcurve,
                                              self.scenario.lanelet_network, self.scenario, self.pred, self.curvetype,
                                             self.roaduser_curve, self.linemarkingleft_curve, self.linemarkingright_curve)
            #lanelet.translate_rotate(np.array([curve_posX, curve_posY]), np.pi/2)
        lanelet.translate_rotate(np.array([curve_posX, curve_posY]), self.rot_angle_curve)

        self.update_view(focus_on_network=True)

    def fit_func(self):
        if self.scenario == None:
            self.textBrowser.append("create a new file")
            return
        self.FIT = FitSettings()
        self.FIT.exec()
        pred = self.FIT.getPredecessor()
        succ = self.FIT.getSuccessor()
        pred_lanelet = self.scenario.lanelet_network.find_lanelet_by_id(pred)
        succ_lanelet = self.scenario.lanelet_network.find_lanelet_by_id(succ)
        if pred_lanelet == None or succ_lanelet == None:
            self.textBrowser.append("select valid lanelet IDs")
            return
        else:
            self.mapcreator.fit_to_predecessor( pred_lanelet, succ_lanelet)
            self.update_view(focus_on_network=True)

    def create_laneletsettings(self):
        self.lanelet_settings = LaneletSettings()

    def forwards(self):
        self.LL = LaneletSettings()
        self.LL.exec()
        self.lenfor = self.LL.getLanletLength()
        self.widfor = self.LL.getLaneletWidth()
        self.pred = self.LL.getPredecessor()
        self.adjfor = self.LL.getAdjacentLanelet()
        indexlist = self.LL.getLaneletType()
        self.lanelettype = set()
        for i in range(0, len(indexlist)):
            lt = LaneletType(indexlist[i])
            self.lanelettype.add(LaneletType(indexlist[i]))

        #Roaduser one-way:
        indexlist2 = self.LL.getOnewayRoadUser()
        self.roaduser_oneway = set()
        for i in range(0, len(indexlist2)):
            ro = RoadUser(indexlist2[i])
            self.roaduser_oneway.add(RoadUser(indexlist2[i]))

        #Roaduser bidirectional:
        indexlist3 = self.LL.getBidirectionalRoadUser()
        self.roaduser_bidirectional = set()
        for i in range(0, len(indexlist3)):
            ro = RoadUser(indexlist3[i])
            self.roaduser_bidirectional.add(RoadUser(indexlist3[i]))

        self.linemarkingright = self.LL.getLineMarkingRight()
        self.linemarkingleft = self.LL.getLineMarkingLeft()
        self.lanelet_pos_x = self.LL.getPosX()
        self.lanelet_pos_y = self.LL.getPosY()
        self.backwards = self.LL.getDirection()
        self.vertfor = self.LL.getNumVertices()


    def curve(self):
        self.CU = CurveSettings()
        self.CU.exec()
        self.radcurve = self.CU.getCurveRadius()
        self.widcurve = self.CU.getCurveWidth()
        self.numcurve = self.CU.getNumberVertices()
        self.anglcurve = self.CU.getAngle()
        self.pred = self.CU.getPredecessor()
        self.curvetype = self.CU.getLaneletType()
        self.roaduser_curve = self.CU.getRoadUser()
        self.linemarkingright_curve = self.CU.getLineMarkingRight()
        self.linemarkingleft_curve = self.CU.getLineMarkingLeft()
        self.curve_pos_x = self.CU.getPosX()
        self.curve_pos_y = self.CU.getPosY()
        self.curve_direction = self.CU.getCurveDirection()

    def adjacent(self):
        if self.scenario == None:
            self.textBrowser.append("create a new file")
            return

        self.ADJ = AdjecentSettings()
        self.ADJ.exec()
        id = self.ADJ.getLaneletId()
        forwards = self.ADJ.isForwards()
        left = self.ADJ.isAdjacentSideLeft()
        lanelet = self.scenario.lanelet_network.find_lanelet_by_id(id)
        if lanelet == None:
            self.textBrowser.append("select a valid lanelet id")
            return
        if left:
            adjacent_lanelet = self.mapcreator.adjacent_lanelet_left(lanelet, self.scenario.lanelet_network,
                                                                self.scenario, same_direction=forwards)
        else:
            adjacent_lanelet = self.mapcreator.adjacent_lanelet_right(lanelet, self.scenario.lanelet_network,
                                                                self.scenario, same_direction=forwards)
        self.update_view(focus_on_network=True)

    def select_predecessor(self):
        self.selected_predecessor = self.crviewer.selected_lanelet_use[0]

    def select_successor(self):
        self.selected_successor = self.crviewer.selected_lanelet_use[0]

    def connect_lanelets(self):
        if self.scenario == None:
            self.textBrowser.append("create a new file")
            return

        self.CONNECT = ConnectSettings()
        self.CONNECT.exec()
        pred = self.CONNECT.getPredecessor()
        succ = self.CONNECT.getSuccessor()
        pred_lanelet = self.scenario.lanelet_network.find_lanelet_by_id(pred)
        succ_lanelet = self.scenario.lanelet_network.find_lanelet_by_id(succ)
        if pred_lanelet == None or succ_lanelet == None:
            self.textBrowser.append("select valid lanelet IDs")
            return
        else:
            connecting_lanelet = self.mapcreator.connect_lanelets4(pred_lanelet, succ_lanelet,
                                                             self.scenario.lanelet_network, self.scenario)
            self.update_view(focus_on_network=True)

    def remove_lanelet(self):
        if self.scenario == None:
            self.textBrowser.append("create a new file")
            return
        self.REMOVE = RemoveSettings()
        self.REMOVE.exec()
        id = self.REMOVE.getLaneletId()
        lanelet = self.scenario.lanelet_network.find_lanelet_by_id(id)
        if lanelet == None:
            self.textBrowser.append("select valid lanelet ID")
            return

        self.mapcreator.remove_lanelet(lanelet, self.scenario.lanelet_network, self.scenario)
        self.update_view(focus_on_network=True)

    def traffic_signs(self):
        self.showTS = TrafficSignsSelection()
        self.showTS.exec()
        sig = self.showTS.getSign()
        vals = self.showTS.getAdditionalValues()
        x = self.showTS.getPosX()
        y = self.showTS.getPosY()


        if self.showTS.getLaneletID():
            lanelet_id = int(self.showTS.getLaneletID())
        else:
            return

        self.traffic1 = TrafficSign(self.traffic_signs_id, [TrafficSignElement(TrafficSignIDGermany(sig), [vals])], {lanelet_id},
                                    np.array([x, y]))
        self.scenario.lanelet_network.add_traffic_sign(self.traffic1, {lanelet_id})
        if lanelet_id:
            lanelet = self.scenario.lanelet_network.find_lanelet_by_id(lanelet_id)
            lanelet.add_traffic_sign_to_lanelet(self.traffic_signs_id)
        self.update_view(focus_on_network=True)

        self.traffic_signs_id = self.traffic_signs_id + 1

    def traffic_light(self):
        self.showTL = TrafficLightSelection()
        self.showTL.exec()
        if self.showTL.getLaneletID():
            lanelet_id = int(self.showTL.getLaneletID())
        else:
            return
        direction = self.showTL.getDirection()
        isactive = self.showTL.get_isactive()
        x = self.showTL.getPosX()
        y = self.showTL.getPosY()
        time_offset = self.showTL.getTimeOffset()
        red = self.showTL.getRed()
        red_yellow = self.showTL.getRed_Yellow()
        green = self.showTL.getGreen()
        yellow = self.showTL.getYellow()
        cycle = [(TrafficLightState.RED, red),
                 (TrafficLightState.RED_YELLOW, red_yellow),
                 (TrafficLightState.GREEN, green),
                 (TrafficLightState.YELLOW, yellow)]
        cycle_element_list = [TrafficLightCycleElement(state[0], state[1]) for state in cycle]
        tl = TrafficLight(traffic_light_id=self.traffic_light_id, cycle=cycle_element_list, position=np.array([x,y]),
                          direction=direction, time_offset=time_offset, active=isactive)

        if lanelet_id:
            lanelet = self.scenario.lanelet_network.find_lanelet_by_id(lanelet_id)
            self.scenario.lanelet_network.add_traffic_light(tl, [lanelet_id])
        self.traffic_light_id = self.traffic_light_id + 1
        self.update_view(focus_on_network=True)

        return

    def traffic_light_exec(self):
        x = 0
        y = 0
        id = 1
        tl = TrafficLight(traffic_light_id=id, cycle=[], position=np.array([x, y]), direction=TrafficLightDirection.ALL)
        lanelet = self.scenario.lanelet_network.find_lanelet_by_id(1)
        #lanelet.add_traffic_light_to_lanelet(id)
        self.scenario.lanelet_network.add_traffic_light(tl, [1,2])
        id = id + 1
        x = 10
        y = 10
        tl2 = TrafficLight(traffic_light_id=id, cycle=[], position=np.array([x, y]), direction=TrafficLightDirection.ALL)
        self.scenario.lanelet_network.add_traffic_light(tl2, [2])


        self.update_view(focus_on_network=True)

    def create_traffic_signs_settings(self):
        self.TS = TrafficSignsSettings()
        self.TS.exec()
        self.country = self.TS.getCountry()
        self.traffic_signs_settings = 0

    def delete_traffic_element(self):
        self.DL = DeleteTrafficElement()
        self.DL.exec()
        element_id = self.DL.getTrafficElement()
        if self.DL.getLaneletId() != None:
            laneletid = self.DL.getLaneletId()
        else:
            laneletid = self.crviewer.selected_lanelet_use[0]._lanelet_id

        lanelet = self.scenario.lanelet_network.find_lanelet_by_id(laneletid)
        trafficelementset = lanelet._traffic_signs
        trafficlightset = lanelet._traffic_lights
        if element_id in trafficelementset:
            trafficelementset.remove(element_id)
            del self.scenario.lanelet_network._traffic_signs[element_id]

        if element_id in trafficlightset:
            trafficlightset.remove(element_id)
            del self.scenario.lanelet_network._traffic_lights[element_id]

        self.scenario.lanelet_network.cleanup_lanelet_references()
        self.update_view(focus_on_network=True)





    def click_x_crossing(self):
        XC = XCrossing()
        XC.exec()
        width = 20
        diameter = 80
        width = XC.getWidth()
        diameter = XC.getDiameter()
        self.mapcreator.x_crossing(width, diameter, self.crviewer.current_scenario.lanelet_network,
                                                self.crviewer.current_scenario)
        # lanelet.translate_rotate(np.array([0, 0]), self.rot_angle_curve)
        self.update_view(focus_on_network=True)


    def click_t_crossing(self):
        TC = TCrossing()
        TC.exec()
        width = 20
        diameter = 80
        width = TC.getWidth()
        diameter = TC.getDiameter()
        self.mapcreator.t_crossing(width, diameter, self.crviewer.current_scenario.lanelet_network,
                                                self.crviewer.current_scenario)
        self.update_view(focus_on_network=True)


    def fit_intersection(self):
        if self.selected_predecessor and self.selected_successor and self.selected_intersection:
            for l in self.crviewer.current_scenario.lanelet_network.lanelets:
                if self.selected_successor.lanelet_id in l.successor:
                    l._successor.remove(self.selected_successor.lanelet_id)
            self.mapcreator.fit_intersection_to_predecessor(
            self.selected_predecessor, self.selected_successor, self.selected_intersection,
            self.crviewer.current_scenario.lanelet_network, self.crviewer.current_scenario)
            self.update_view(focus_on_network=True)

    def create_toolbox(self):
        """ Create the Upper toolbox."""
        self.uppertoolBox = UpperToolbox()

        self.tool1 = QDockWidget("ToolBox")
        self.tool1.setFloating(True)
        self.tool1.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.tool1.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.tool1.setWidget(self.uppertoolBox)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tool1)

        self.uppertoolBox.button_traffic_signs_settings.clicked.connect(lambda: self.create_traffic_signs_settings())
        self.uppertoolBox.button_traffic_signs.clicked.connect(lambda: self.traffic_signs())
        self.uppertoolBox.button_traffic_light.clicked.connect(lambda: self.traffic_light())
        self.uppertoolBox.delete_traffic_sign.clicked.connect(lambda: self.delete_traffic_element())

        self.uppertoolBox.button_forwards.clicked.connect(lambda: self.click_straight(self.lanelet_pos_x, self.lanelet_pos_y))
        self.uppertoolBox.button_lanelet_settings.clicked.connect(lambda: self.forwards())
        self.uppertoolBox.button_turn_right.clicked.connect(lambda: self.click_curve(self.curve_direction, self.curve_pos_x, self.curve_pos_y))
        self.uppertoolBox.button_curve_settings.clicked.connect(self.curve)

        self.uppertoolBox.button_fit_to_predecessor.clicked.connect(lambda: self.fit_func())
        self.uppertoolBox.button_adjacent.clicked.connect(lambda: self.adjacent())
        self.uppertoolBox.button_connect_lanelets.clicked.connect(lambda: self.connect_lanelets())
        self.uppertoolBox.button_remove_lanelet.clicked.connect(lambda: self.remove_lanelet())

        self.uppertoolBox.button_X.clicked.connect(lambda: self.click_x_crossing())
        self.uppertoolBox.button_T.clicked.connect(lambda: self.click_t_crossing())

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

        self.tool2 = QDockWidget("Lanelet Information")
        self.tool2.setFloating(True)
        self.tool2.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.tool2.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.tool2.setWidget(self.lowertoolBox)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tool2)
        self.lowertoolBox.refresh_button.clicked.connect(lambda: self.refresh_information())
        self.tool2.setMaximumHeight(400)
        self.lowertoolBox.edit_button.clicked.connect(lambda: self.edit_lanelet())

#        if self.crviewer.selected_lanelet_use[0]:
 #           self.selected_lanelet = self.crviewer.selected_lanelet_use[0]


        #selected_lanelet = self.crviewer.current_scenario.lanelet_network.find_lanelet_by_id(
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
            if self.crviewer.selected_lanelet_use[0] != None:
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
                angle = self.mapcreator.calc_angle_between2(self.selected_lanelet)
                angle = (angle/np.pi) * 180
                self.lowertoolBox.radius.clear()
                rad = self.mapcreator.calc_radius(self.selected_lanelet)
                self.lowertoolBox.traffic_sign_ids.clear()
                traffic_ids = self.selected_lanelet.traffic_signs
                for t in traffic_ids:
                    t = str(t)
                    self.lowertoolBox.traffic_sign_ids.insert(t)
                    self.lowertoolBox.traffic_sign_ids.insert(", ")
                print(traffic_ids)
                if int(angle) != 0:
                    self.lowertoolBox.angle.clear()
                    self.lowertoolBox.angle.insert(str(int(angle)))
                    self.lowertoolBox.length.clear()
                    self.lowertoolBox.radius.clear()
                    self.lowertoolBox.radius.insert(str(int(rad)))


    def edit_lanelet(self):
        posX = 0
        posY = 0
        if self.scenario == None:
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

        if int((self.selected_angle)) == 0:
            self.roaduser_oneway = set()
            lanelet = self.mapcreator.edit_straight(self.selected_id, self.selected_width, self.selected_length, self.selected_vertices,
                                             self.scenario.lanelet_network, self.scenario, self.pred, self.lanelettype,
                                             self.roaduser_oneway, self.linemarkingleft, self.linemarkingright, backwards=self.backwards)
            lanelet.translate_rotate(np.array([posX, posY]), self.rot_angle_straight)
        else:
            curve = self.mapcreator.edit_curve(self.selected_id, self.selected_width, self.selected_radius, np.deg2rad(self.selected_angle), self.selected_vertices,
                                             self.scenario.lanelet_network, self.scenario, self.pred, self.lanelettype,
                                             self.roaduser, self.linemarkingleft, self.linemarkingright)

        self.update_view(focus_on_network=True)



    def create_sumobox(self):
        """Function to create the sumo toolbox(bottom toolbox)."""
        """self.tool2 = QDockWidget("Sumo Simulation", self)
        self.tool2.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.tool2.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.tool2.setWidget(self.sumobox)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tool2)
        self.tool2.setMaximumHeight(400)"""

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

    def play_animation(self):
        """Function connected with the play button in the sumo-toolbox."""
        if not self.crviewer.current_scenario:
            messbox = QMessageBox()
            reply = messbox.warning(
                self, "Warning",
                "Please load an animation before attempting to play",
                QMessageBox.Ok | QMessageBox.No, QMessageBox.Ok)
            if (reply == QtWidgets.QMessageBox.Ok):
                self.open_commonroad_file()
        else:
            self.crviewer.play()
            self.textBrowser.append("Playing the animation")

    def pause_animation(self):
        """Function connected with the pause button in Toolbar."""
        self.crviewer.pause()
        self.textBrowser.append("Pause the animation")

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
                                    self.uppertoolBox.save_menu.currentText() +
                                    " ...")
            self.crviewer.save_animation(
                self.uppertoolBox.save_menu.currentText())
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

        #TODO: undo button
        """action_undo = QAction(QIcon(":/icons/save_file.png"), "undo last action", self)
        tb1.addAction(action_undo)"""

        tb1.addSeparator()
        tb2 = self.addToolBar("ToolBox")
        toolbox = QAction(QIcon(":/icons/tools.ico"),
                          "show Toolbox for CR Scenario", self)
        tb2.addAction(toolbox)
        toolbox.triggered.connect(self.tool_box1_show)
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
        self.button_play = QAction(QIcon(":/icons/play.png"),
                                   "Play the animation", self)
        self.button_play.triggered.connect(self.play_animation)
        tb3.addAction(self.button_play)
        self.button_pause = QAction(QIcon(":/icons/pause.png"),
                                    "Pause the animation", self)
        self.button_pause.triggered.connect(self.pause_animation)
        tb3.addAction(self.button_pause)

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
        self.scenario = scenario
        self.open_scenario(scenario)

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

    def tool_box1_show(self):
        self.tool1.show()

    def tool_box2_show(self):
        self.tool2.show()

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
