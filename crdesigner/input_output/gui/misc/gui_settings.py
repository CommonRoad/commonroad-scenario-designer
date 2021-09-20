""" window with settings for the Scenario Designer """
from PyQt5.QtWidgets import QMainWindow

from crdesigner.input_output.gui.gui_resources.gui_settings_ui import Ui_MainWindow
from crdesigner.input_output.gui.settings import config


class GUISettings:
    
    def __init__(self, parent):
        self.cr_designer = parent
        self.settings_window = QMainWindow()
        self.window = Ui_MainWindow()
        self.window.setupUi(self.settings_window)
        self.connect_events()
        self.update_ui_values()
        self.settings_window.show()
    
    def connect_events(self):
        """ connect buttons to callables """
        # self.window.btn_restore_defaults.clicked.connect(self.restore_default_button)
        self.window.botton_close.clicked.connect(self.apply_close)

    def update_ui_values(self):
        """
        sets the values of the settings window to the current values of config
        """
        self.window.chk_autofocus.setChecked(config.AUTOFOCUS)
        return

    def save_to_config(self):
        """
        saves the values in the settings window to config.py
        """
        config.AUTOFOCUS = self.window.chk_autofocus.isChecked()

    
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
            self.save_to_config()
            self.settings_window.close()
            self.cr_designer.text_browser.append("settings saved")
        else:
            print("invalid settings")