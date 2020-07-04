import signal
import sys
import os
from lxml import etree
import numpy as np
import matplotlib.pyplot as plt
import time

from crmapconverter.io.V3_0.GUI_resources.MainWindow import Ui_mainWindow
from crmapconverter.io.V3_0.gui_toolbox import UpperToolbox, Sumo_simulation_tool
from crmapconverter.io.V3_0.gui_sumo_simulation import Sumo_simulation_play, Sumo_simulation_step_play
from crmapconverter.io.V3_0.gui_cr_viewer import Crviewer
from crmapconverter.io.V3_0.gui_opendrive2cr import OD2CR
from crmapconverter.io.V3_0.gui_osm2cr import OSM2CR
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


from commonroad.common.file_writer import CommonRoadFileWriter

from crmapconverter.io.V3_0.GUI_src import CR_Scenario_Designer


class MWindow(QMainWindow, Ui_mainWindow):
    """The Mainwindow of CR Scenario Designer."""

    count = 0
    tool1 = None
    tool2 = None
    toolBox = None
    console = None
    textBrowser = None
    sumobox = None
    play = None
    crviewer = None
    lanelets_List = None
    play_step = None
    timer = None
    ani_path = None

    def __init__(self):
        super(MWindow, self).__init__()
        # self.center()
        self.setupUi(self)
        self.setWindowIcon(QIcon(':/icons/cr.ico'))
        self.centralwidget.setStyleSheet('background-color:rgb(150,150,150)')
        self.setWindowFlag(True)

        self.current_scenario = None
        self.commoroad_filename = None
        self.selected_lanelet_id = None

        self.createFileActions()
        self.createImportActions()
        self.createExportActions()
        self.createtoolbar()
        self.createconsole()
        self.createtoolbox()

        self.status = self.statusbar
        self.status.showMessage("Welcome to CR Scenario Designer")

        menuBar = self.menuBar()  # instant of menu
        file = menuBar.addMenu('File')  # add menu 'file'

        file.addAction(self.fileNewAction)
        file.addAction(self.fileOpenAction)
        file.addAction(self.fileSaveAction)
        file.addAction(self.separator)
        file.addAction(self.exitAction)

        menu_import = menuBar.addMenu('Import')  # add menu 'Import'
        menu_import.addAction(self.importfromOpendrive)
        menu_import.addAction(self.importfromOSM)
        # menu_import.addAction(self.importfromSUMO)

        menu_export = menuBar.addMenu('Export')  # add menu 'Export'
        menu_export.addAction(self.exportAsCommonRoad)
        # menu_export.addAction(self.exportAsOSM)
        # menu_export.addAction(self.export2SUMO)

        self.center()

    def createtoolbox(self):
        """ Create the Upper toolbox."""
        self.uppertoolBox = UpperToolbox()

        self.tool1 = QDockWidget("ToolBox")
        self.tool1.setFloating(True)
        self.tool1.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.tool1.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.tool1.setWidget(self.uppertoolBox)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tool1)
        self.createsumobox()
        self.uppertoolBox.button_sumo_simulation.clicked.connect(
            self.ToolBox2_show)
        self.uppertoolBox.button_lanlist.clicked.connect(self.showlaneletslist)

    def createlaneletslist(self):
        """Create the Laneletslist and put it into right Dockwidget area."""
        if self.lanelets_List is not None:
            self.lanelets_List.close()
            self.lanelets_List = None
        self.lanelets_List = QDockWidget(
            "Lanelets list " + self.crviewer.commonroad_filename)
        self.lanelets_List.setFloating(True)
        self.lanelets_List.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.lanelets_List.setAllowedAreas(Qt.RightDockWidgetArea)
        self.lanelets_List.setWidget(self.crviewer.laneletsList)
        self.addDockWidget(Qt.RightDockWidgetArea, self.lanelets_List)

    def showlaneletslist(self):
        """Function connected with button 'Lanelets List' to show the lanelets list."""
        if self.crviewer is None:
            messbox = QMessageBox()
            reply = messbox.question(
                self,
                "Warning",
                "Please load a CR Scenario first",
                QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.No)
            if (reply == QtWidgets.QMessageBox.Ok):
                self.fileOpen()
            else:
                messbox.close()
        else:
            self.lanelets_List.show()

    def createsumobox(self):
        """Function to create the sumo toolbox(bottom toolbox)."""
        self.sumobox = Sumo_simulation_tool()
        self.tool2 = QDockWidget("Sumo Simulation", self)
        self.tool2.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.tool2.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.tool2.setWidget(self.sumobox)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tool2)
        self.tool2.setMinimumHeight(400)
        self.sumobox.button_import.clicked.connect(lambda:self.importsumoanimation(None))
        self.sumobox.button_save.clicked.connect(self.savesumoanimation)
        self.sumobox.button_pause.clicked.connect(self.pausesumoanimation)
        self.sumobox.button_play.clicked.connect(self.playsumoanimation)

        """for sumo frame by frame play"""
        self.sumobox.slider.valueChanged[int].connect(self.timestepchange)

    def activate_sumoanimation_step(self):
        if self.lanelets_List is not None:
            self.lanelets_List.close()
            self.lanelets_List = None
        if self.play is not None:
            self.play.ani.event_source.stop()
        if self.ani_path != None:
            self.textBrowser.append("Showing Simulation frame by frame")
            self.play_step = Sumo_simulation_step_play(self.ani_path)
        if self.play_step.commonroad_filename is not None:
            # play.current_scenario = scenario_editing.current_scenario
            self.play_step.setWindowIcon(QIcon(":/icons/cr1.ico"))
            self.setCentralWidget(self.play_step)
            self.commoroad_filename = self.play_step.commonroad_filename
            self.play_step.play_timesteps(self.play_step.current_scenario, 0)
            self.textBrowser.append("Ready")

    def timestepchange(self, value):
        if self.play is not None:
            if self.play_step is None:
                self.activate_sumoanimation_step()
            if self.sumobox.radioButton.isChecked():
                # self.sumobox.slider.setValue(value)
                self.sumobox.label.setText('Timestep: ' + str(value))
                self.play_step.play_timesteps(
                    self.play_step.current_scenario, value)

    def playsumoanimation(self):
        """Function connected with the play button in the sumo-toolbox."""
        if self.play is not None:
            if self.play_step is not None:
                self.sumobox.radioButton.setChecked(False)
                self.importsumoanimation(self.ani_path)
                self.play.ani.event_source.start()
                self.play_step = None
            else:
                self.play.ani.event_source.start()
        else:
            messbox = QMessageBox()
            reply = messbox.question(
                self,
                "Warning",
                "You should firstly load an animation",
                QMessageBox.Ok | QMessageBox.No,
                QMessageBox.Ok)
            if (reply == QtWidgets.QMessageBox.Ok):
                self.playsumoanimation()
            else:
                messbox.close()

    def pausesumoanimation(self):
        """Function connected with the pause button in the sumo-toolbox."""
        if self.play is not None:
            self.play.ani.event_source.stop()
        else:
            messbox = QMessageBox()
            reply = messbox.question(
                self,
                "Warning",
                "You should firstly load an animation",
                QMessageBox.Ok | QMessageBox.No,
                QMessageBox.Ok)
            if (reply == QtWidgets.QMessageBox.Ok):
                self.playsumoanimation()
            else:
                messbox.close()

    def importsumoanimation(self, path):
        """Function connected with the pause button in the sumo-toolbox."""
        if self.lanelets_List is not None:
            self.lanelets_List.close()
            self.lanelets_List = None

        self.textBrowser.append("Opening the CR Scenario Simulation")
        self.play = Sumo_simulation_play(path)
        if self.play.commonroad_filename is not None:
            # play.current_scenario = scenario_editing.current_scenario
            self.ani_path = self.play.path
            self.play.setWindowIcon(QIcon(":/icons/cr1.ico"))
            self.setCentralWidget(self.play)
            self.play.setWindowFlags(Qt.WindowCloseButtonHint)
            self.commoroad_filename = self.play.commonroad_filename
            # window.setWindowTitle(scenario_editing.commonroad_filename)  # set up
            # the title

    # self.textBrowser.append("loading Animation " + scenario_editing.commonroad_filename)
    # self.status.showMessage("Opening " + crviewer.commonroad_filename)

    def savesumoanimation(self):
        """Function connected with the save button in the sumo-toolbox."""
        if self.play is None:
            messbox = QMessageBox()
            reply = messbox.question(
                self,
                "Warning",
                "You should firstly load an animation",
                QMessageBox.Ok | QMessageBox.No,
                QMessageBox.Ok)
            if (reply == QtWidgets.QMessageBox.Ok):
                self.importsumoanimation()
            else:
                messbox.close()
        else:
            self.play.saveanimation(self.sumobox.save_menu.currentText())

    def createconsole(self):
        """Function to create the console."""
        self.console = QDockWidget(self)
        self.console.setTitleBarWidget(
            QWidget(self.console))  # no title of Dock
        self.textBrowser = QtWidgets.QTextBrowser()
        self.textBrowser.setMaximumHeight(80)
        self.textBrowser.setObjectName("textBrowser")
        self.console.setWidget(self.textBrowser)
        self.console.setFloating(False)  # set if console can float
        self.console.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.console)

    def createtoolbar(self):
        """Function to create toolbar of the main Window."""
        tb1 = self.addToolBar("File")
        new = QAction(QIcon(":/icons/new_file.png"), "new CR File", self)
        tb1.addAction(new)
        new.triggered.connect(self.fileNew)
        open = QAction(QIcon(":/icons/open_file.png"), "open CR File", self)
        tb1.addAction(open)
        open.triggered.connect(self.fileOpen)
        save = QAction(QIcon(":/icons/save_file.png"), "save CR File", self)
        tb1.addAction(save)
        save.triggered.connect(self.fileSave)
        tb1.addSeparator()
        tb2 = self.addToolBar("ToolBox")
        toolbox = QAction(
            QIcon(":/icons/tools.ico"),
            "show Toolbox for CR Scenario",
            self)
        tb2.addAction(toolbox)
        toolbox.triggered.connect(self.ToolBox1_show)

    def createImportActions(self):
        """Function to create the import action in the menu bar."""
        self.importfromOpendrive = self.createAction(
            "From OpenDrive",
            icon="",
            checkable=False,
            slot=self.opendrive2cr,
            tip="Convert from OpenDrive to CommonRoad",
            shortcut=None)
        self.importfromOSM = self.createAction(
            "From OSM",
            icon="",
            checkable=False,
            slot=self.osm2cr,
            tip="Convert from OSM to CommonRoad",
            shortcut=None)
        # self.importfromSUMO = self.createAction("From SUMO", icon="", checkable=False, slot=self.sumo2cr, tip="Convert from OSM to CommonRoad", shortcut=QKeySequence.Close)

    def opendrive2cr(self):
        """Function to realize converter OD2CR and show the result."""
        od2cr = OD2CR()
        od2cr.setWindowIcon(QIcon(":/icons/Groupe_3.ico"))
        if od2cr.input_filename is not None:
            self.setCentralWidget(od2cr)  # setup mdi of CR File
            self.setWindowTitle(od2cr.input_filename)  # set up the title
            self.textBrowser.append("Converted from " + od2cr.input_filename)
            self.textBrowser.append(od2cr.statsText)
            self.textBrowser.setMaximumHeight(800)

        else:
            self.textBrowser.append(
                "Terminated because no OpenDrive file selected")

    def osm2cr(self):
        """Function to realize converter OSM2CR and show the result."""
        # window = QMdiSubWindow()  #
        osm2cr = OSM2CR()

        # window.setWidget(osm2cr)  # setup mdi of CR File
        # window.setWindowTitle(osm2cr.input_filename)  # set up the title
        # self.textBrowser.append("Converted from " + osm2cr.input_filename)
        # self.textBrowser.append(osm2cr.statsText)
        # self.textBrowser.setMaximumHeight(800)
        # self.mdi.addSubWindow(window)
        # window.showMaximized()
        # window.show()

    def createExportActions(self):
        """Function to create the export action in the menu bar."""
        self.exportAsCommonRoad = self.createAction(
            "As CommonRoad",
            icon="",
            checkable=False,
            slot=self.fileSave,
            tip="Save as CommonRoad File (the same function as Save)",
            shortcut=None)
        self.exportAsOSM = self.createAction(
            "From OSM",
            icon="",
            checkable=False,
            slot=self.osm2cr,
            tip="Convert from OSM to CommonRoad",
            shortcut=None)
        # self.export2SUMO = self.createAction("From SUMO", icon="", checkable=False, slot=self.sumo2cr, tip="Convert from OSM to CommonRoad", shortcut=QKeySequence.Close)

    def center(self):
        """Function that makes sure the main window is in the center of screen."""
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)

    def createFileActions(self):
        """Function to create the file action in the menu bar."""
        self.fileNewAction = self.createAction(
            "New",
            icon=QIcon(":/icons/new_file.png"),
            checkable=False,
            slot=self.fileNew,
            tip="New Commonroad File",
            shortcut=QKeySequence.New)
        self.fileOpenAction = self.createAction(
            "Open",
            icon=QIcon(":/icons/open_file.png"),
            checkable=False,
            slot=self.fileOpen,
            tip="Open Commonroad File",
            shortcut=QKeySequence.Open)
        self.separator = QAction(self)
        self.separator.setSeparator(True)

        self.fileSaveAction = self.createAction(
            "Save",
            icon=QIcon(":/icons/save_file.png"),
            checkable=False,
            slot=self.fileSave,
            tip="Save Commonroad File",
            shortcut=QKeySequence.Save)
        self.separator.setSeparator(True)
        self.exitAction = self.createAction(
            "Quit",
            icon=QIcon(":/icons/close.png"),
            checkable=False,
            slot=self.closeWindow,
            tip="Quit",
            shortcut=QKeySequence.Close)

    def createAction(
            self,
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

    def fileNew(self):
        """Function to create the action in the menu bar."""
        """Not Finished---"""
        new = QTextEdit()
        new.setWindowTitle("New")
        new.setWindowIcon(QIcon(":/icons/cr.ico"))
        self.setCentralWidget(QTextEdit())  # setup new scenario file
        self.textBrowser.append("add new file")
        # show message in statusbar
        self.status.showMessage("Creating New File")

    def fileOpen(self):
        """Function to open a CR .xml file."""
        if self.play is not None:
            self.play.ani._stop()

        self.crviewer = Crviewer()
        self.crviewer.setWindowIcon(QIcon(":/icons/cr1.ico"))
        if self.crviewer.commonroad_filename is not None:
            self.createlaneletslist()
            # window.setWindowTitle(self.crviewer.commonroad_filename)  # set
            # up the title
            self.textBrowser.append(
                "loading " + self.crviewer.commonroad_filename)
            # self.status.showMessage("Opening " + crviewer.commonroad_filename)
            self.setCentralWidget(self.crviewer)
            self.commoroad_filename = self.crviewer.commonroad_filename
        else:
            self.textBrowser.append(
                "Terminated because no CommonRoad file selected")

    def fileSave(self):
        """Function to save a CR .xml file."""
        fileEdit = self.centralWidget()
        if fileEdit is None:
            messbox = QMessageBox()
            reply = messbox.warning(
                self,
                "Warning",
                "There is no file to save!",
                QMessageBox.Ok,
                QMessageBox.Ok)

            if reply == QMessageBox.Ok:
                messbox.close()
            else:
                messbox.close()

        else:
            # if self.commonroad_filename == "":

            if not fileEdit.current_scenario:
                return
            path, _ = QFileDialog.getSaveFileName(
                self,
                "QFileDialog.getSaveFileName()",
                ".xml",
                "CommonRoad files *.xml (*.xml)",
                options=QFileDialog.Options(),
            )

            if not path:
                self.NoFilenamed()
                return

            try:
                with open(path, "w") as fh:
                    writer = CommonRoadFileWriter(
                        scenario=fileEdit.current_scenario,
                        planning_problem_set=None,
                        author="",
                        affiliation="",
                        source="",
                        tags="",
                    )
                    writer.write_scenario_to_file(path)
            except (IOError) as e:
                QMessageBox.critical(
                    self,
                    "CommonRoad file not created!",
                    "The CommonRoad file was not saved due to an error.\n\n{}".format(e),
                    QMessageBox.Ok,
                )
                return

    def processtrigger(self, q):
        self.status.showMessage(q.text() + ' is triggered')

    def closeWindow(self):
        reply = QMessageBox.warning(
            self,
            "Warning",
            "Do you really want to quit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            qApp.quit()

    def closeEvent(self, event):
        result = QtWidgets.QMessageBox.question(
            self,
            "Warning",
            "Do you want to exit?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if (result == QtWidgets.QMessageBox.Yes):
            event.accept()
        else:
            event.ignore()

    def ToolBox1_show(self):
        self.tool1.show()

    def ToolBox2_show(self):
        self.tool2.show()

    def NoFilenamed(self):
        messbox = QMessageBox()
        reply = messbox.warning(
            self,
            "Warning",
            "You should name the file!",
            QMessageBox.Ok | QMessageBox.No,
            QMessageBox.Ok)

        if reply == QMessageBox.Ok:
            self.fileSave()
        else:
            messbox.close()


if __name__ == '__main__':
    # application
    app = QApplication(sys.argv)
    w = MWindow()
    w.show()
    sys.exit(app.exec_())
