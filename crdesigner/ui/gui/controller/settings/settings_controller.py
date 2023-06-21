from PyQt5 import QtCore
from PyQt5.QtWidgets import QMainWindow

import crdesigner.ui.gui.controller.settings.gui_settings_controller as gui
import crdesigner.ui.gui.controller.settings.osm_settings_controller as osm
import crdesigner.ui.gui.controller.settings.sumo_settings_controller as sumo
from crdesigner.ui.gui.model.settings.gui_settings_model import gui_settings as gui_settings_model
from crdesigner.ui.gui.utilities.gui_sumo_simulation import SUMO_AVAILABLE
from crdesigner.ui.gui.view.settings.settings_ui import SettingsUI


class SettingsController:

    def __init__(self, parent):

        self.cr_designer = parent.mwindow_ui
        self.scenario_model = parent.scenario_model
        self.canvas = parent.animated_viewer_wrapper.cr_viewer.dynamic
        self.settings_window = QMainWindow(None)

        self.settings_ui = SettingsUI()
        self.settings_ui.setupUi(self.settings_window, self.cr_designer)

        self.gui_settings = gui.GUISettingController(self)
        self.settings_ui.gui_settings = self.gui_settings.gui_settings_ui

        self.osm_settings = osm.OSMSettingsController(self, None)
        self.settings_ui.osm_settings = self.osm_settings.osm_settings_ui

        self.sumo_settings = sumo.SUMOSettingsController(self, None)
        self.settings_ui.sumo_settings = self.sumo_settings.sumo_settings_ui

        self.settings_ui.update_window()
        self.settings_ui.retranslateUi(self.settings_window)
        QtCore.QMetaObject.connectSlotsByName(self.settings_window)

        if SUMO_AVAILABLE:
            self.sumo_settings = sumo.SUMOSettingsController(self,
                                                             config=parent.obstacle_toolbox.sumo_simulation.config)

        self.connect_events()
        self.update_ui_values()
        self.settings_window.show()

    def connect_events(self):
        """ connect buttons to callables """
        # self.window.btn_restore_defaults.clicked.connect(self.restore_default_button)
        self.settings_ui.button_ok.clicked.connect(self.apply_close)
        self.settings_ui.button_cancel.clicked.connect(self.close)
        self.settings_ui.button_settodefault.clicked.connect(self.clicked)
        self.osm_settings.connect_events(self.settings_ui.osm_settings)
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
            if self.scenario_model.scenario_created():
                self.cr_designer.animated_viewer_wrapper.cr_viewer.update_plot()
            self.cr_designer.update_window()

        else:
            print("invalid settings")

    def clicked(self):
        gui_settings_model.apply_set_to_default()
        self.gui_settings.update_window()

        self.osm_settings.apply_set_to_default()
        if SUMO_AVAILABLE:
            self.sumo_settings.restore_defaults()
        self.settings_window.close()
        self.cr_designer.crdesigner_console_wrapper.text_browser.append("default settings")
        if self.scenario_model.scenario_created():
            self.cr_designer.animated_viewer_wrapper.cr_viewer.update_plot()
        self.cr_designer.update_window()
