# from ? import Ui_SettingsWindow 
class GUISettings:
    
    def __init__(self, parent):
        self.cr_designer = parent
        self.window = Ui_SettingsWindow(cr_designer)
        self.window.setupUi(self.app.main_window)
        self.update_ui_values()
        self.connect_events()
        self.window.show()
    
    def connect_events(self) -> None:
        # window.btn_restore_defaults.clicked.connect(self.restore_default_button)
        # window.btn_close.clicked.connect(self.close_button)
        return

    def update_ui_values(self) -> None:
        """
        sets the values of the settings window to the current values of config.py

        :return: None
        """
        # example code:
        # window.le_benchmark_id.setText(config.BENCHMARK_ID)
        # window.sb_compression_threshold.setValue(config.COMPRESSION_THRESHOLD)
        # window.chk_delete_short_edges.setChecked(config.DELETE_SHORT_EDGES)
        return

    def save_to_config(self) -> None:
        """
        saves the values in the settings window to config.py

        :return: None
        """
        # example code:
        # config.BENCHMARK_ID = window.le_benchmark_id.text()
        # config.AERIAL_IMAGES = swindow.chb_aerial.isChecked()
        # config.DOWNLOAD_EDGE_LENGTH = window.sb_donwload_radius.value()
        return

    def close_button(self) -> None:
        """
        closes settings without saving

        :return: None
        """
        self.save_to_config()
        # and close