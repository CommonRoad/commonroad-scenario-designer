from crdesigner.input_output.gui.gui_resources.MainWindow import Ui_mainWindow
from crdesigner.input_output.gui.gui_resources.scenario_saving_dialog import ScenarioDialog
from crdesigner.input_output.gui.misc.commonroad_viewer import AnimatedViewer
from meta.CONSTANTS import *
from gui.mwindow.service_layer.general_services import setup_tmp
from gui.mwindow.service_layer.general_services import setup_mwindow
from gui.mwindow.service_layer.file_actions import create_file_actions
from gui.mwindow.service_layer.setting_actions import create_setting_actions
from gui.mwindow.service_layer.help_actions import create_help_actions
from gui.mwindow.service_layer.general_services import create_viewer_dock
from gui.mwindow.service_layer.general_services import viewer_callback

from crdesigner.input_output.gui.gui_src import CR_Scenario_Designer  # do not remove!!!

from PyQt5.QtWidgets import *


class MWindow(QMainWindow, Ui_mainWindow):
    """The Main window of the CR Scenario Designer."""

    def __init__(self, path=None):
        super().__init__()
        # init or set all attributes here
        self.tmp_folder = MWINDOW_TMP_FOLDER_PATH
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

        # init any objects here
        self.scenario_saving_dialog = ScenarioDialog()
        self.cr_viewer = AnimatedViewer(self, viewer_callback)

        # call the setup methods in the service layer
        setup_tmp(tmp_folder_path=self.tmp_folder)
        setup_mwindow(self)
        self.fileNewAction, self.fileOpenAction, self.separator, self.fileSaveAction, self.exitAction = create_file_actions(mwindow=self)
        self.osm_settings, self.opendrive_settings, self.gui_settings, self.sumo_settings = create_setting_actions()
        self.open_web, self.open_forum = create_help_actions()
        self.viewer_dock = create_viewer_dock(mwindow=self)
