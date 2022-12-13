from PyQt5.QtWidgets import QMainWindow

from crdesigner.ui.gui.mwindow.service_layer.gui_resources.settings_ui import Ui_Settings
from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.commonroad_viewer.dynamic_canvas import DynamicCanvas
import crdesigner.ui.gui.mwindow.service_layer.gui_settings as gui
import crdesigner.ui.gui.mwindow.service_layer.sumo_settings as sumo
import crdesigner.ui.gui.mwindow.service_layer.osm_settings as osm
from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.gui_sumo_simulation import SUMO_AVAILABLE
import json

class Settings:

    def __init__(self, parent):
        self.cr_designer = parent
        self.settings_window = QMainWindow()
        self.window = Ui_Settings()

        self.window.setupUi(self.settings_window, self.cr_designer)
        self.gui_settings = gui.GUISettings(self)
        if SUMO_AVAILABLE:
            self.sumo_settings = sumo.SUMOSettings(self, config=parent.obstacle_toolbox.sumo_simulation.config)
        self.osm_settings = osm.OSMSettings(self, None)
        self.connect_events()
        self.update_ui_values()
        self.settings_window.show()
        self.canvas = DynamicCanvas()

    def connect_events(self):
        """ connect buttons to callables """
        #self.window.btn_restore_defaults.clicked.connect(self.restore_default_button)
        self.window.button_ok.clicked.connect(self.apply_close)
        self.window.button_cancel.clicked.connect(self.close)
        self.window.button_settodefault.clicked.connect(self.clicked)
        self.osm_settings.connect_events(self.window.osm_settings)
        self.gui_settings.connect_events()
        if SUMO_AVAILABLE:
            self.sumo_settings.connect_events()

    def close(self):
        self.settings_window.close()
        self.gui_settings.close()

    def update_ui_values(self):
        """
        sets the values of the settings window to the current values of config
        """
        self.gui_settings.update_ui_values()
        if SUMO_AVAILABLE:
            self.sumo_settings.update_ui_values()
        self.osm_settings.update_ui_values()
        self.cr_designer.update_window()

    def save_to_config(self):
        """
        saves the values in the settings window to config.py
        """
        self.gui_settings.save_to_config()
        self.sumo_settings.save_to_config()
        self.osm_settings.save_to_config()

    def has_valid_entries(self) -> bool:
        """
        Check if the user input is valid. Otherwise, warn the user.

        :return: bool whether the input is valid
        """
        # use if settings get extended
        return True

    def apply_close(self) -> None:
        """
        closes settings if settings could be saved to config
        """

        if self.has_valid_entries():
            self.gui_settings.apply_close()
            if SUMO_AVAILABLE:
                self.sumo_settings.apply_close()
            self.osm_settings.apply_close()
            self.settings_window.close()
            self.cr_designer.crdesigner_console_wrapper.text_browser.append("settings saved")
            self.canvas.update_obstacle_trajectory_params()
            if self.cr_designer.animated_viewer_wrapper.cr_viewer.current_scenario != None:
                self.cr_designer.animated_viewer_wrapper.cr_viewer.update_plot()
            self.cr_designer.update_window()

        else:
            print("invalid settings")

    def clicked(self):

        self.gui_settings.apply_set_to_default()
        self.osm_settings.apply_set_to_default()
        if SUMO_AVAILABLE:
            self.sumo_settings.restore_defaults()
        self.settings_window.close()
        self.cr_designer.crdesigner_console_wrapper.text_browser.append("default settings")
        if self.cr_designer.animated_viewer_wrapper.cr_viewer.current_scenario != None:
            self.cr_designer.animated_viewer_wrapper.cr_viewer.update_plot()
        self.cr_designer.update_window()
