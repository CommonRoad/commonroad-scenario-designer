import logging
import os
import pathlib
import sys
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import copy
from typing import Union

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.scenario.lanelet import LaneletNetwork, Lanelet
from commonroad.scenario.scenario import Scenario
from commonroad.scenario.obstacle import Obstacle

from crdesigner.input_output.gui.gui_src import CR_Scenario_Designer  # do not remove!!!
from crdesigner.input_output.gui.converter_modules.opendrive_interface import OpenDRIVEInterface
from crdesigner.input_output.gui.converter_modules.osm_interface import OSMInterface
from crdesigner.input_output.gui.misc.gui_settings import GUISettings
from crdesigner.input_output.gui.misc.commonroad_viewer import AnimatedViewer
from crdesigner.input_output.gui.gui_resources.MainWindow import Ui_mainWindow
from crdesigner.input_output.gui.toolboxes.road_network_toolbox import RoadNetworkToolbox
from crdesigner.input_output.gui.toolboxes.obstacle_toolbox import ObstacleToolbox
from crdesigner.input_output.gui.toolboxes.map_converter_toolbox import MapConversionToolbox
from crdesigner.input_output.gui.gui_resources.scenario_saving_dialog import ScenarioDialog
from crdesigner.input_output.gui.settings import config
from crdesigner.input_output.gui.misc import util

from crdesigner.input_output.gui.toolboxes.gui_sumo_simulation import SUMO_AVAILABLE
if SUMO_AVAILABLE:
    from crdesigner.input_output.gui.settings.sumo_settings import SUMOSettings


class MWindow(QMainWindow, Ui_mainWindow):
    """The Main window of the CR Scenario Designer."""

    def __init__(self, path=None):
        super().__init__()
        self.tmp_folder = "/tmp/cr_designer/"
        pathlib.Path(self.tmp_folder).mkdir(parents=True, exist_ok=True)

        self.setupUi(self)
        self.setWindowIcon(QIcon(':/icons/cr.ico'))
        self.setWindowTitle("CommonRoad Scenario Designer")
        self.centralwidget.setStyleSheet('background-color:rgb(150,150,150)')
        self.setWindowFlag(Qt.Window)

        # attributes
        self.filename = None
        self.slider_clicked = False

        # Scenario + Lanelet variables
        self.scenarios = []
        self.current_scenario_index = -1

        # GUI attributes
        self.road_network_toolbox = None
        self.obstacle_toolbox = None
        self.map_converter_toolbox = None

        self.console = None
        self.play_activated = False
        self.text_browser = None

        self.viewer_dock = None
        self.sumo_settings = None
        self.gui_settings = None

        self.scenario_saving_dialog = ScenarioDialog()

        self.cr_viewer = AnimatedViewer(self, self.viewer_callback)

        self.create_file_actions()
        self.create_setting_actions()
        self.create_help_actions()
        self.create_viewer_dock()
        self.create_toolbar()
        self.create_console()

        self.create_road_network_toolbox()
        self.create_obstacle_toolbox()
        self.create_converter_toolbox()

        # came until here...
        self.status = self.statusbar
        self.status.showMessage("Welcome to CR Scenario Designer")

        menu_bar = self.menuBar()  # instant of menu
        menu_file = menu_bar.addMenu('File')  # add menu 'file'
        menu_file.addAction(self.fileNewAction)
        menu_file.addAction(self.fileOpenAction)
        menu_file.addAction(self.fileSaveAction)
        menu_file.addAction(self.separator)
        menu_file.addAction(self.exitAction)

        menu_setting = menu_bar.addMenu('Setting')  # add menu 'Setting'
        menu_setting.addAction(self.gui_settings)
        menu_setting.addAction(self.sumo_settings)
        menu_setting.addAction(self.osm_settings)

        menu_help = menu_bar.addMenu('Help')  # add menu 'Help'
        menu_help.addAction(self.open_web)
        menu_help.addAction(self.open_forum)

        self.center()

        if path:
            self.open_path(path)

    # moved to create_road_network_toolbox.py
    def create_road_network_toolbox(self):
        """ Create the Road network toolbar."""
        self.road_network_toolbox = RoadNetworkToolbox(current_scenario=self.cr_viewer.current_scenario,
                                                       text_browser=self.text_browser,
                                                       callback=self.toolbox_callback,
                                                       tmp_folder=self.tmp_folder,
                                                       selection_changed_callback=self.cr_viewer.update_plot)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.road_network_toolbox)

    def create_converter_toolbox(self):
        """ Create the map converter toolbar."""
        self.map_converter_toolbox = MapConversionToolbox(self.cr_viewer.current_scenario,
                                                          self.toolbox_callback, self.text_browser,
                                                          self.obstacle_toolbox.sumo_simulation)
        self.addDockWidget(Qt.RightDockWidgetArea, self.map_converter_toolbox)

    # already moved to create_obstacle_toolbox.py
    def create_obstacle_toolbox(self):
        """ Create the obstacle toolbar."""
        self.obstacle_toolbox = ObstacleToolbox(self.cr_viewer.current_scenario, self.toolbox_callback, self.tmp_folder)
        self.addDockWidget(Qt.RightDockWidgetArea, self.obstacle_toolbox)

    # Already moved to general_services.py
    def viewer_callback(self, selected_object: Union[Lanelet, Obstacle], output: str):
        if isinstance(selected_object, Lanelet):
            self.road_network_toolbox.road_network_toolbox.selected_lanelet_two.setCurrentText(
                self.road_network_toolbox.road_network_toolbox.selected_lanelet_one.currentText())
            self.road_network_toolbox.road_network_toolbox.selected_lanelet_one.setCurrentText(
                str(selected_object.lanelet_id))
            self.road_network_toolbox.road_network_toolbox.selected_lanelet_update.setCurrentText(
                str(selected_object.lanelet_id))
        elif isinstance(selected_object, Obstacle):
            self.obstacle_toolbox.obstacle_toolbox.selected_obstacle.setCurrentText(str(selected_object.obstacle_id))
        if output != "":
            self.text_browser.append(output)

    # already moved to mwindow.py
    def toolbox_callback(self, scenario):
        if scenario is not None:
            self.cr_viewer.open_scenario(scenario)
            self.update_view(focus_on_network=True)
            self.update_max_step()
            self.store_scenario()

    # Already moved to setting_actions.py
    def show_osm_settings(self):
        osm_interface = OSMInterface(self)
        osm_interface.show_settings()

    # Already moved at setting_actions.py
    def show_opendrive_settings(self):
        opendrive_interface = OpenDRIVEInterface(self)
        opendrive_interface.show_settings()

    # Already moved at setting_actions.py
    def show_gui_settings(self):
        self.gui_settings = GUISettings(self)

    def initialize_toolboxes(self):
        self.road_network_toolbox.initialize_toolbox()
        self.obstacle_toolbox.initialize_toolbox()

    # Already moved to setting_actions.py
    def show_sumo_settings(self):
        self.sumo_settings = SUMOSettings(self, config=self.obstacle_toolbox.sumo_simulation.config)

    # already moved to toolbar.py
    def detect_slider_clicked(self):
        self.slider_clicked = True
        self.cr_viewer.pause()
        self.cr_viewer.dynamic.update_plot()

    # already moved to toolbar.py
    def detect_slider_release(self):
        self.slider_clicked = False
        self.cr_viewer.pause()

    # already moved to toolbar.py
    def time_step_change(self, value):
        if self.cr_viewer.current_scenario:
            self.cr_viewer.set_timestep(value)
            self.label1.setText('  Time Stamp: ' + str(value))
            self.cr_viewer.animation.event_source.start()

    # already moved to toolbar.py
    def play_pause_animation(self):
        """Function connected with the play button in the sumo-toolbar."""
        if not self.cr_viewer.current_scenario:
            messbox = QMessageBox()
            reply = messbox.warning(
                self, "Warning",
                "Please load or create a CommonRoad scenario before attempting to play",
                QMessageBox.Ok | QMessageBox.No, QMessageBox.Ok)
            if (reply == QMessageBox.Ok):
                self.open_commonroad_file()
            return
        if not self.play_activated:
            self.cr_viewer.play()
            self.text_browser.append("Playing the animation")
            self.button_play_pause.setIcon(QIcon(":/icons/pause.png"))
            self.play_activated = True
        else:
            self.cr_viewer.pause()
            self.text_browser.append("Pause the animation")
            self.button_play_pause.setIcon(QIcon(":/icons/play.png"))
            self.play_activated = False

    # already moved to toolbar.py
    def save_video(self):
        """Function connected with the save button in the Toolbar."""
        if not self.cr_viewer.current_scenario:
            messbox = QMessageBox()
            reply = messbox.warning(self, "Warning",
                                    "Please load or create a CommonRoad scenario before saving a video",
                                    QMessageBox.Ok | QMessageBox.No,
                                    QMessageBox.Ok)
            if (reply == QMessageBox.Ok):
                self.open_commonroad_file()
            else:
                messbox.close()
        else:
            self.text_browser.append("Save video for scenario with ID " +
                                     str(self.cr_viewer.current_scenario.scenario_id))
            self.cr_viewer.save_animation()
            self.text_browser.append("Saving the video finished.")

    # already moved to console.py
    def create_console(self):
        """Function to create the console."""
        self.console = QDockWidget(self)
        self.console.setTitleBarWidget(QWidget(
            self.console))  # no title of Dock
        self.text_browser = QTextBrowser()
        self.text_browser.setMaximumHeight(80)
        self.text_browser.setObjectName("textBrowser")
        self.console.setWidget(self.text_browser)
        self.console.setFloating(False)  # set if console can float
        self.console.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.console)

    # already moved to toolbar.py
    def create_toolbar(self):
        """Function to create toolbar of the main Window."""
        tb1 = self.addToolBar("File")
        action_new = QAction(QIcon(":/icons/new_file.png"), "new CR File", self)
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

        tb1.addSeparator()
        tb2 = self.addToolBar("Toolboxes")
        action_road_network_toolbox = QAction(QIcon(":/icons/road_network_toolbox.png"), "Open Road Network Toolbox",
                                              self)
        tb2.addAction(action_road_network_toolbox)
        action_road_network_toolbox.triggered.connect(self.road_network_toolbox_show)
        action_obstacle_toolbox = QAction(QIcon(":/icons/obstacle_toolbox.png"), "Open Obstacle Toolbox", self)
        tb2.addAction(action_obstacle_toolbox)
        action_obstacle_toolbox.triggered.connect(self.obstacle_toolbox_show)
        action_converter_toolbox = QAction(QIcon(":/icons/tools.ico"), "Open Map Converter Toolbox", self)
        tb2.addAction(action_converter_toolbox)
        action_converter_toolbox.triggered.connect(self.map_converter_toolbox_show)
        tb2.addSeparator()

        tb3 = self.addToolBar("Undo/Redo")

        action_undo = QAction(QIcon(":/icons/button_undo.png"), "undo last action", self)
        tb3.addAction(action_undo)
        action_undo.triggered.connect(self.undo_action)

        action_redo = QAction(QIcon(":/icons/button_redo.png"), "redo last action", self)
        tb3.addAction(action_redo)
        action_redo.triggered.connect(self.redo_action)

        tb3.addSeparator()

        tb4 = self.addToolBar("Animation Play")
        self.button_play_pause = QAction(QIcon(":/icons/play.png"), "Play the animation", self)
        self.button_play_pause.triggered.connect(self.play_pause_animation)
        tb4.addAction(self.button_play_pause)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMaximumWidth(300)
        self.slider.setValue(0)
        self.slider.setMinimum(0)
        self.slider.setMaximum(99)
        # self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(1)
        self.slider.setToolTip("Show corresponding Scenario at selected timestep")
        self.slider.valueChanged.connect(self.time_step_change)
        self.slider.sliderPressed.connect(self.detect_slider_clicked)
        self.slider.sliderReleased.connect(self.detect_slider_release)
        self.cr_viewer.time_step.subscribe(self.slider.setValue)
        tb4.addWidget(self.slider)

        self.label1 = QLabel('  Time Stamp: 0', self)
        tb4.addWidget(self.label1)

        self.label2 = QLabel(' / 0', self)
        tb4.addWidget(self.label2)

        action_save_video = QAction(QIcon(":/icons/save_video.png"), "Save Video", self)
        tb4.addAction(action_save_video)
        action_save_video.triggered.connect(self.save_video)

    def update_max_step(self, value: int = -1):
        logging.info('update_max_step')
        value = value if value > -1 else self.cr_viewer.max_timestep
        self.label2.setText(' / ' + str(value))
        self.slider.setMaximum(value)

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

    # Already moved to hrlp_actions
    def create_help_actions(self):
        """Function to create the help action in the menu bar."""
        self.open_web = self.create_action("Open CR Web",
                                           icon="",
                                           checkable=False,
                                           slot=self.open_cr_web,
                                           tip="Open CommonRoad Website",
                                           shortcut=None)
        self.open_forum = self.create_action("Open Forum",
                                             icon="",
                                             checkable=False,
                                             slot=self.open_cr_forum,
                                             tip="Open CommonRoad Forum",
                                             shortcut=None)
    # Already moved to general_services.py
    def create_viewer_dock(self):
        self.viewer_dock = QWidget(self)
        toolbar = NavigationToolbar(self.cr_viewer.dynamic, self.viewer_dock)
        layout = QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.cr_viewer.dynamic)
        self.viewer_dock.setLayout(layout)
        self.setCentralWidget(self.viewer_dock)

    # already moved to mwindow.py
    def center(self):
        """Function that makes sure the main window is in the center of screen."""
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)

    # TODO already moved to mwindow_controller
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
                                             slot=self.close_window,
                                             tip="Quit",
                                             shortcut=QKeySequence.Close)

    # TODO already moved to mwindow_controller
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

    # Already moved to help_actions.py
    def open_cr_web(self):
        """Function to open the CommonRoad website."""
        QDesktopServices.openUrl(QUrl("https://commonroad.in.tum.de/"))

    # Already moved to help_actions.py
    def open_cr_forum(self):
        """Function to open the CommonRoad Forum."""
        QDesktopServices.openUrl(QUrl("https://commonroad.in.tum.de/forum/c/map-tool/11"))

    # TODO already moved to mwindow_controller
    def file_new(self):
        """Function to create the action in the menu bar."""

        scenario = Scenario(0.1, affiliation="Technical University of Munich", source="CommonRoad Scenario Designer")
        net = LaneletNetwork()
        scenario.lanelet_network = net
        self.cr_viewer.current_scenario = scenario
        self.cr_viewer.current_pps = None
        self.open_scenario(scenario)
#        self.restore_parameters()

    # TODO already moved to mwindow.py
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

    # TODO already moved to mwindow_controller.py
    def open_path(self, path):
        """ """
        try:
            commonroad_reader = CommonRoadFileReader(path)
            scenario, pps = commonroad_reader.open()
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
        self.open_scenario(scenario, filename, pps)

    # moved to mwindow.py
    def update_toolbox_scenarios(self):
        scenario = self.cr_viewer.current_scenario
        self.road_network_toolbox.refresh_toolbox(scenario)
        self.obstacle_toolbox.refresh_toolbox(scenario)
        self.map_converter_toolbox.refresh_toolbox(scenario)
        if SUMO_AVAILABLE:
            self.obstacle_toolbox.sumo_simulation.scenario = scenario
            self.map_converter_toolbox.sumo_simulation.scenario = scenario

    # TODO already moved to mwindow_controller.py
    def open_scenario(self, new_scenario, filename="new_scenario", pps=None):
        """  """
        if self.check_scenario(new_scenario) >= 2:
            self.text_browser.append("loading aborted")
            return
        self.filename = filename
        if SUMO_AVAILABLE:
            self.cr_viewer.open_scenario(new_scenario, self.obstacle_toolbox.sumo_simulation.config,
                                         planning_problem_set=pps)
            self.obstacle_toolbox.sumo_simulation.scenario = self.cr_viewer.current_scenario
        else:
            self.cr_viewer.open_scenario(new_scenario, planning_problem_set=pps)
        self.update_view(focus_on_network=True)
        self.store_scenario()
        self.update_toolbox_scenarios()
        self.update_to_new_scenario()

    def update_to_new_scenario(self):
        """  """
        self.update_max_step()
        self.initialize_toolboxes()
        self.viewer_dock.setWindowIcon(QIcon(":/icons/cr1.ico"))
        if self.cr_viewer.current_scenario is not None:
            self.text_browser.append("Loading " + self.filename)

    def check_scenario(self, scenario) -> int:
        """
        Check the scenario to validity and calculate a quality score.
        The higher the score the higher the data faults.

        :return: score
        """

        warning = 1
        fatal_error = 2
        verbose = True

        error_score = 0

        # handle fatal errors
        found_ids = util.find_invalid_ref_of_traffic_lights(scenario)
        if found_ids and verbose:
            error_score = max(error_score, fatal_error)
            self.text_browser.append("invalid traffic light refs: " +
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
            error_score = max(error_score, fatal_error)
            self.text_browser.append("invalid traffic sign refs: " +
                                     str(found_ids))
            QMessageBox.critical(
                self,
                "CommonRoad XML error",
                "Scenario contains invalid traffic sign refenence(s): " +
                str(found_ids),
                QMessageBox.Ok,
            )

        if error_score >= fatal_error:
            return error_score

        # handle warnings
        found_ids = util.find_invalid_lanelet_polygons(scenario)
        if found_ids and verbose:
            error_score = max(error_score, warning)
            self.text_browser.append(
                "Warning: Lanelet(s) with invalid polygon:" + str(found_ids))
            QMessageBox.warning(
                self,
                "CommonRoad XML error",
                "Scenario contains lanelet(s) with invalid polygon: " +
                str(found_ids),
                QMessageBox.Ok,
            )

        return error_score

    # TODO already moved to file_actions.py
    def file_save(self):
        """Function to save a CR .xml file."""

        if self.cr_viewer.current_scenario is None:
            messbox = QMessageBox()
            messbox.warning(self, "Warning", "There is no file to save!",
                            QMessageBox.Ok, QMessageBox.Ok)
            messbox.close()
            return

        self.scenario_saving_dialog.show(self.cr_viewer.current_scenario, self.cr_viewer.current_pps)

    def process_trigger(self, q):
        self.status.showMessage(q.text() + ' is triggered')

    # TODO already moved to file_action.py
    def close_window(self):
        reply = QMessageBox.warning(self, "Warning",
                                    "Do you really want to quit?",
                                    QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            qApp.quit()

    def closeEvent(self, event):
        event.ignore()
        self.close_window()

    # already moved to toolbar.py
    def road_network_toolbox_show(self):
        self.road_network_toolbox.show()

    # already moved to toolbar.py
    def obstacle_toolbox_show(self):
        self.obstacle_toolbox.show()

    # already moved to toolbar.py
    def map_converter_toolbox_show(self):
        self.map_converter_toolbox.show()

    # already moved to mwindow.py
    def update_view(self, focus_on_network=None):
        """ update all components."""

        # reset selection of all other selectable elements
        if self.cr_viewer.current_scenario is None:
            return
        if focus_on_network is None:
            focus_on_network = config.AUTOFOCUS
        self.cr_viewer.update_plot(focus_on_network=focus_on_network)

    # moved to mwindow.py
    def store_scenario(self):
        self.scenarios.append(copy.deepcopy(self.cr_viewer.current_scenario))
        self.current_scenario_index += 1
        self.update_toolbox_scenarios()

    # already moved to toolbar.py
    def undo_action(self):
        if self.current_scenario_index >= 0:
            self.current_scenario_index -= 1
        else:
            return
        self.cr_viewer.current_scenario = self.scenarios[self.current_scenario_index]
        self.update_view(focus_on_network=True)
        self.update_toolbox_scenarios()

    # already moved to toolbar.py
    def redo_action(self):
        if self.current_scenario_index < len(self.scenarios) - 1:
            self.current_scenario_index += 1
        else:
            return
        self.cr_viewer.current_scenario = self.scenarios[self.current_scenario_index]
        self.update_view(focus_on_network=True)
        self.update_toolbox_scenarios()


def start_gui(input_file: str = None):
    # application
    app = QApplication(sys.argv)
    if input_file:
        w = MWindow(input_file)
    else:
        w = MWindow()
    w.showMaximized()
    sys.exit(app.exec_())


if __name__ == '__main__':
    start_gui()
