""" """
from PyQt5.QtWidgets import QMainWindow

from crmapconverter.io.V3_0.GUI_resources.gui_settings_ui import Ui_MainWindow


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
        sets the values of the settings window to the current values of config.py

        :return: None
        """
        # example code:
        # window.le_benchmark_id.setText(config.BENCHMARK_ID)
        # window.sb_compression_threshold.setValue(config.COMPRESSION_THRESHOLD)
        # window.chk_delete_short_edges.setChecked(config.DELETE_SHORT_EDGES)
        return

    def save_to_config(self) -> bool:
        """
        saves the values in the settings window to config.py
        """
        # example code:
        # config.BENCHMARK_ID = window.le_benchmark_id.text()
        # config.AERIAL_IMAGES = swindow.chb_aerial.isChecked()
        # config.DOWNLOAD_EDGE_LENGTH = window.sb_donwload_radius.value()
        return True

    
    def has_valid_entries(self) -> bool:
        return True

    def apply_close(self) -> None:
        """
        closes settings if settings could be saved to config
        """
        if self.save_to_config():
            self.settings_window.close()