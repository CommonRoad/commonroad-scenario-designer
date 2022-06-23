from PyQt5.QtWidgets import QMainWindow

from crdesigner.ui.gui.mwindow.service_layer.gui_resources.settings_ui import Ui_Settings
from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.commonroad_viewer.dynamic_canvas import DynamicCanvas
import crdesigner.ui.gui.mwindow.service_layer.gui_settings as gui
import crdesigner.ui.gui.mwindow.service_layer.sumo_settings as sumo
import crdesigner.ui.gui.mwindow.service_layer.osm_settings as osm

class Settings:

    def __init__(self, parent):
        self.cr_designer = parent
        self.settings_window = QMainWindow()
        self.window = Ui_Settings()

        self.window.setupUi(self.settings_window)
        self.gui_settings = gui.GUISettings(self)
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
        self.osm_settings.connect_events(self.window.osm_settings)

    def close(self):
        self.settings_window.close()

    def update_ui_values(self):
        """
        sets the values of the settings window to the current values of config
        """
        self.gui_settings.update_ui_values()
        self.sumo_settings.update_ui_values()
        self.osm_settings.update_ui_values()

    def save_to_config(self):
        """
        saves the values in the settings window to config.py
        """
        self.gui_settings.save_to_config()
        self.sumo_settings.save_to_config()
        self.osm_settings.save_to_config()

    def has_valid_entries(self) -> bool:
        """
        Check if the user input is valid. Otherwise warn the user.

        :return: bool wether the input is valid
        """
        # use if settings get extended
        return True

    def apply_close(self) -> None:
        """
        closes settings if settings could be saved to config
        """

        if self.has_valid_entries():
            self.gui_settings.apply_close()
            self.sumo_settings.apply_close()
            self.osm_settings.apply_close()
            self.settings_window.close()
            self.cr_designer.crdesigner_console_wrapper.text_browser.append("settings saved")
            self.canvas.update_obstacle_trajectory_params()


        else:
            print("invalid settings")
