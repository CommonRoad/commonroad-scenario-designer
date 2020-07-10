import signal
import sys
import os
from lxml import etree
import numpy as np

from crmapconverter.io.V3_0.GUI_resources.MainWindow import Ui_mainWindow
from crmapconverter.io.V3_0.gui_toolbox import UpperToolbox, SumoTool
from crmapconverter.io.V3_0.gui_cr_viewer import CrViewer
from crmapconverter.io.V3_0.gui_opendrive2cr import OD2CR
from crmapconverter.io.V3_0.gui_osm2cr import OSM2CR
from crmapconverter.io.V3_0.gui_setting_interface import Setting
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from commonroad.common.file_writer import CommonRoadFileWriter
from crmapconverter.osm.lanelet2osm import L2OSMConverter


from crmapconverter.io.V3_0.GUI_src import CR_Scenario_Designer


class MWindow(QMainWindow, Ui_mainWindow):
    """The Mainwindow of CR Scenario Designer."""

    def __init__(self):
        super(MWindow, self).__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon(':/icons/cr.ico'))
        self.centralwidget.setStyleSheet('background-color:rgb(150,150,150)')
        self.setWindowFlag(True)

        self.count = 0
        self.tool1 = None
        self.tool2 = None
        self.toolBox = None
        self.console = None
        self.textBrowser = None
        self.sumobox = None
        self.crviewer = CrViewer()
        self.lanelets_List = None
        self.intersection_List = None
        self.timer = None
        self.ani_path = None
        self.od2cr = None

        self.current_scenario = None
        self.commoroad_filename = None
        self.selected_lanelet_id = None
        self.slider_clicked = False

        self.create_file_actions()
        self.create_import_actions()
        self.create_export_actions()
        self.create_setting_actions()
        self.create_help_actions()
        self.create_toolbar()
        self.create_console()
        self.create_toolbox()

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
        menu_export.addAction(self.exportAsOSM)
        # menu_export.addAction(self.export2SUMO)

        menu_setting = menuBar.addMenu('Setting')  # add menu 'Setting'
        menu_setting.addAction(self.setting)

        menu_help = menuBar.addMenu('Help')  # add menu 'Help'
        menu_help.addAction(self.open_web)

        self.center()

    def setting_interface(self):
        self.set = Setting()

    def create_toolbox(self):
        """ Create the Upper toolbox."""
        self.uppertoolBox = UpperToolbox()

        self.tool1 = QDockWidget("ToolBox")
        self.tool1.setFloating(True)
        self.tool1.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.tool1.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.tool1.setWidget(self.uppertoolBox)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tool1)
        self.create_sumobox()
        self.uppertoolBox.button_sumo_simulation.clicked.connect(
            self.tool_box2_show)
        self.uppertoolBox.button_lanlist.clicked.connect(
            self.show_laneletslist)
        self.uppertoolBox.button_intersection_list.clicked.connect(
            self.show_intersection_list)
        self.uppertoolBox.button_save.clicked.connect(
            self.save_animation)

    def create_laneletslist(self, object):
        """Create the Laneletslist and put it into right Dockwidget area."""
        if self.lanelets_List is not None:
            self.lanelets_List.close()
            self.lanelets_List = None
        self.lanelets_List = QDockWidget("Lanelets list " +
                                         self.crviewer.filename)
        self.lanelets_List.setFloating(True)
        self.lanelets_List.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.lanelets_List.setAllowedAreas(Qt.RightDockWidgetArea)
        self.lanelets_List.setWidget(object.laneletsList)
        self.addDockWidget(Qt.RightDockWidgetArea, self.lanelets_List)

    def show_laneletslist(self):
        """Function connected with button 'Lanelets List' to show the lanelets list."""
        if self.lanelets_List is None:
            if self.od2cr is None:
                messbox = QMessageBox()
                reply = messbox.question(
                    self, "Warning",
                    "Please load or convert a CR Scenario or first",
                    QtWidgets.QMessageBox.Ok)
                if (reply == QtWidgets.QMessageBox.Ok):
                    messbox.close()
                else:
                    messbox.close()
            else:
                self.lanelets_List.show()
        else:
            self.lanelets_List.show()

    def create_intersection_list(self, object):
        """Create the Laneletslist and put it into right Dockwidget area."""
        if self.intersection_List is not None:
            self.intersection_List.close()
            self.intersection_List = None
        self.intersection_List = QDockWidget("Intersection list " +
                                             self.crviewer.filename)
        self.intersection_List.setFloating(True)
        self.intersection_List.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.intersection_List.setAllowedAreas(Qt.RightDockWidgetArea)
        self.intersection_List.setWidget(object.intersection_List)
        self.addDockWidget(Qt.RightDockWidgetArea, self.intersection_List)
        self.intersection_List.close()

    def show_intersection_list(self):
        """Function connected with button 'Lanelets List' to show the lanelets list."""
        if self.intersection_List is None:
            if self.od2cr is None:
                messbox = QMessageBox()
                reply = messbox.question(
                    self, "Warning",
                    "Please load or convert a CR Scenario or first",
                    QtWidgets.QMessageBox.Ok)
                if (reply == QtWidgets.QMessageBox.Ok):
                    messbox.close()
                else:
                    messbox.close()
            else:
                self.intersection_List.show()
        else:
            self.intersection_List.show()

    def create_sumobox(self):
        """Function to create the sumo toolbox(bottom toolbox)."""
        self.sumobox = SumoTool()
        self.tool2 = QDockWidget("Sumo Simulation", self)
        self.tool2.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.tool2.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.tool2.setWidget(self.sumobox)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tool2)
        self.tool2.setMinimumHeight(200)

    def detect_slider_clicked(self):
        self.slider_clicked = True
        print(self.slider_clicked)
        self.crviewer.pause()
        self.crviewer.canvas.update_plot()

    def detect_slider_release(self):
        self.slider_clicked = False
        print(self.slider_clicked)
        self.crviewer.pause()

    def timestep_change(self, value):
        self.crviewer.set_time_step(value)
        self.label1.setText('Timestep: ' + str(value))
        self.crviewer.animation.event_source.start()

    def play_animation(self):
        """Function connected with the play button in the sumo-toolbox."""
        if self.crviewer.current_scenario is None:
            messbox = QMessageBox()
            reply = messbox.question(
                self,
                "Warning",
                "You should firstly load a scenario",
                QMessageBox.Ok | QMessageBox.No,
                QMessageBox.Ok)
            if (reply == QtWidgets.QMessageBox.Ok):
                self.file_open()
        else:
            self.crviewer.play()

    def pause_animation(self):
        """Function connected with the pause button in Toolbar."""
        self.crviewer.pause()

    def save_animation(self):
        """Function connected with the save button in the Toolbar."""
        if self.crviewer is None:
            messbox = QMessageBox()
            reply = messbox.question(self, "Warning",
                                     "You should firstly load an animation",
                                     QMessageBox.Ok | QMessageBox.No,
                                     QMessageBox.Ok)
            if (reply == QtWidgets.QMessageBox.Ok):
                self.file_open()
            else:
                messbox.close()
        else:
            self.crviewer.save_animation(
                self.uppertoolBox.save_menu.currentText())

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
        new = QAction(QIcon(":/icons/new_file.png"), "new CR File", self)
        tb1.addAction(new)
        new.triggered.connect(self.file_new)
        open = QAction(QIcon(":/icons/open_file.png"), "open CR File", self)
        tb1.addAction(open)
        open.triggered.connect(self.file_open)
        save = QAction(QIcon(":/icons/save_file.png"), "save CR File", self)
        tb1.addAction(save)
        save.triggered.connect(self.file_save)
        tb1.addSeparator()
        tb2 = self.addToolBar("ToolBox")
        toolbox = QAction(QIcon(":/icons/tools.ico"),
                          "show Toolbox for CR Scenario", self)
        tb2.addAction(toolbox)
        toolbox.triggered.connect(self.tool_box1_show)
        tb2.addSeparator()
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
        self.crviewer.timestep.subscribe(
            lambda timestep: self.slider.setValue(timestep))
        tb3.addWidget(self.slider)

        self.label1 = QLabel('  Step: 0', self)
        tb3.addWidget(self.label1)

        self.label2 = QLabel('      Total Step:', self)
        tb3.addWidget(self.label2)

    def update_max_step(self):
        self.label2.setText('      Total Step: ' + str(self.crviewer.max_step))
        self.slider.setMaximum(self.crviewer.max_step)

    def create_import_actions(self):
        """Function to create the import action in the menu bar."""
        self.importfromOpendrive = self.create_action(
            "From OpenDrive",
            icon="",
            checkable=False,
            slot=self.opendrive_2_cr,
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
        if self.crviewer.current_scenario is not None:
            proj_string, ok = QInputDialog.getText(
                self, 'Export as OSM', 'Enter Proj-string:')
            if ok:
                path, _ = QFileDialog.getSaveFileName(
                    self,
                    "QFileDialog.getSaveFileName()",
                    ".osm",
                    "OSM files (*.osm)",
                    options=QFileDialog.Options(),
                )

                if not path:
                    return

                l2osm = L2OSMConverter(proj_string=proj_string)
                osm = l2osm(self.crviewer.current_scenario)
                with open(f"{path}", "wb") as file_out:
                    file_out.write(
                        etree.tostring(
                            osm,
                            xml_declaration=True,
                            encoding="UTF-8",
                            pretty_print=True))

    def opendrive_2_cr(self):
        """Function to realize converter OD2CR and show the result."""
        self.od2cr = OD2CR()
        self.od2cr.setWindowIcon(QIcon(":/icons/Groupe_3.ico"))
        if self.od2cr.filename is not None:
            self.setCentralWidget(self.od2cr)  # setup mdi of CR File
            self.setWindowTitle(self.od2cr.filename)  # set up the title
            self.create_laneletslist(self.od2cr)
            self.create_intersection_list(self.od2cr)
            self.textBrowser.append("Converted from " + self.od2cr.filename)
            self.textBrowser.append(self.od2cr.statsText)
            self.textBrowser.setMaximumHeight(800)
            self.current_scenario = self.od2cr.current_scenario
            self.commoroad_filename = self.od2cr.filename

        else:
            self.textBrowser.append(
                "Terminated because no OpenDrive file selected")

    def osm_2_cr(self):
        """Function to realize converter OSM2CR and show the result."""
        osm2cr = OSM2CR()

    def create_export_actions(self):
        """Function to create the export action in the menu bar."""
        self.exportAsCommonRoad = self.create_action(
            "As CommonRoad",
            icon="",
            checkable=False,
            slot=self.file_save,
            tip="Save as CommonRoad File (the same function as Save)",
            shortcut=None)
        self.exportAsOSM = self.create_action(
            "As OSM",
            icon="",
            checkable=False,
            slot=self.cr_2_osm,
            tip="Convert from OSM to CommonRoad",
            shortcut=None)

    def create_setting_actions(self):
        """Function to create the export action in the menu bar."""
        self.setting = self.create_action("Settings",
                                          icon="",
                                          checkable=False,
                                          slot=self.setting_interface,
                                          tip="Show settings for converters",
                                          shortcut=None)

    def create_help_actions(self):
        """Function to create the help action in the menu bar."""
        self.open_web = self.create_action("Open CR Web",
                                          icon="",
                                          checkable=False,
                                          slot=self.open_cr_web,
                                          tip="Open CommonRoad Web",
                                          shortcut=None)

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
            slot=self.file_open,
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
        """Not Finished---"""
        #new = QTextEdit()
        # new.setWindowTitle("New")
        # new.setWindowIcon(QIcon(":/icons/cr.ico"))
        # self.setCentralWidget(QTextEdit())  # setup new scenario file
        #self.textBrowser.append("add new file")
        # show message in statusbar
        #self.status.showMessage("Creating New File")

    def file_open(self):
        """Function to open a CR .xml file."""
        self.crviewer = CrViewer()
        self.crviewer.open_commonroad_file()
        self.update_max_step()
        self.crviewer.setWindowIcon(QIcon(":/icons/cr1.ico"))
        if self.crviewer.filename is not None:
            self.create_laneletslist(self.crviewer)
            self.create_intersection_list(self.crviewer)
            # window.setWindowTitle(self.crviewer.filename)  # set
            # up the title
            self.textBrowser.append("loading " +
                                    self.crviewer.filename)
            # self.status.showMessage("Opening " + crviewer.filename)
            self.setCentralWidget(self.crviewer)
            self.commoroad_filename = self.crviewer.filename
            self.current_scenario = self.crviewer.current_scenario
        else:
            self.textBrowser.append(
                "Terminated because no CommonRoad file selected")

    def file_save(self):
        """Function to save a CR .xml file."""
        fileEdit = self.centralWidget()
        if self.current_scenario is None:
            messbox = QMessageBox()
            reply = messbox.warning(self, "Warning",
                                    "There is no file to save!",
                                    QMessageBox.Ok, QMessageBox.Ok)

            if reply == QMessageBox.Ok:
                messbox.close()
            else:
                messbox.close()

        else:
            path, _ = QFileDialog.getSaveFileName(
                self,
                "QFileDialog.getSaveFileName()",
                ".xml",
                "CommonRoad files *.xml (*.xml)",
                options=QFileDialog.Options(),
            )

            if not path:
                self.no_file_named()
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
                    "The CommonRoad file was not saved due to an error.\n\n{}".
                    format(e),
                    QMessageBox.Ok,
                )
                return

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
        result = QtWidgets.QMessageBox.question(
            self, "Warning", "Do you want to exit?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if (result == QtWidgets.QMessageBox.Yes):
            event.accept()
        else:
            event.ignore()

    def tool_box1_show(self):
        self.tool1.show()

    def tool_box2_show(self):
        self.tool2.show()

    def no_file_named(self):
        messbox = QMessageBox()
        reply = messbox.warning(self, "Warning", "You should name the file!",
                                QMessageBox.Ok | QMessageBox.No,
                                QMessageBox.Ok)

        if reply == QMessageBox.Ok:
            self.file_save()
        else:
            messbox.close()


if __name__ == '__main__':
    # application
    app = QApplication(sys.argv)
    w = MWindow()
    w.show()
    sys.exit(app.exec_())
