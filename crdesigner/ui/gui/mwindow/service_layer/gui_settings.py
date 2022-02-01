""" window with settings for the Scenario Designer """
from PyQt5.QtWidgets import QMainWindow

from crdesigner.ui.gui.mwindow.service_layer.gui_resources.gui_settings_ui import Ui_MainWindow
from crdesigner.ui.gui.mwindow.service_layer import config
from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.commonroad_viewer.service_layer.draw_params_updater import set_draw_params
from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.commonroad_viewer.dynamic_canvas import DynamicCanvas


class GUISettings:
    
    def __init__(self, parent):
        self.cr_designer = parent
        self.settings_window = QMainWindow()
        self.window = Ui_MainWindow()
        self.window.setupUi(self.settings_window)
        self.connect_events()
        self.update_ui_values()
        self.settings_window.show()
        self.canvas = DynamicCanvas()
    
    def connect_events(self):
        """ connect buttons to callables """
        # self.window.btn_restore_defaults.clicked.connect(self.restore_default_button)
        self.window.botton_close.clicked.connect(self.apply_close)

    def update_ui_values(self):
        """
        sets the values of the settings window to the current values of config
        """
        self.window.chk_autofocus.setChecked(config.AUTOFOCUS)
        self.window.chk_draw_trajectory.setChecked(config.DRAW_TRAJECTORY)
        self.window.chk_draw_intersection.setChecked(config.DRAW_INTERSECTIONS)
        self.window.chk_draw_label.setChecked(config.DRAW_OBSTACLE_LABELS)
        self.window.chk_draw_obstacle_icon.setChecked(config.DRAW_OBSTACLE_ICONS)
        self.window.chk_draw_obstacle_direction.setChecked(config.DRAW_OBSTACLE_DIRECTION)
        self.window.chk_draw_obstacle_signal.setChecked(config.DRAW_OBSTACLE_SIGNALS)
        self.window.chk_draw_occupancy.setChecked(config.DRAW_OCCUPANCY)
        self.window.chk_draw_traffic_sign.setChecked(config.DRAW_TRAFFIC_SIGNS)
        self.window.chk_draw_traffic_light.setChecked(config.DRAW_TRAFFIC_LIGHTS)
        self.window.chk_draw_incoming_lanelet.setChecked(config.DRAW_INCOMING_LANELETS)
        self.window.chk_draw_successors.setChecked(config.DRAW_SUCCESSORS)
        self.window.chk_draw_intersection_label.setChecked(config.DRAW_INTERSECTION_LABELS)
        return

    def save_to_config(self):
        """
        saves the values in the settings window to config.py
        """
        config.AUTOFOCUS = self.window.chk_autofocus.isChecked()
        config.DRAW_TRAJECTORY = self.window.chk_draw_trajectory.isChecked()
        config.DRAW_INTERSECTIONS = self.window.chk_draw_intersection.isChecked()
        config.DRAW_OBSTACLE_LABELS = self.window.chk_draw_label.isChecked()
        config.DRAW_OBSTACLE_ICONS = self.window.chk_draw_obstacle_icon.isChecked()
        config.DRAW_OBSTACLE_DIRECTION = self.window.chk_draw_obstacle_direction.isChecked()
        config.DRAW_OBSTACLE_SIGNALS = self.window.chk_draw_obstacle_signal.isChecked()
        config.DRAW_OCCUPANCY = self.window.chk_draw_occupancy.isChecked()
        config.DRAW_TRAFFIC_SIGNS = self.window.chk_draw_traffic_sign.isChecked()
        config.DRAW_TRAFFIC_LIGHTS = self.window.chk_draw_traffic_light.isChecked()
        config.DRAW_INCOMING_LANELETS = self.window.chk_draw_incoming_lanelet.isChecked()
        config.DRAW_SUCCESSORS = self.window.chk_draw_successors.isChecked()
        config.DRAW_INTERSECTION_LABELS = self.window.chk_draw_intersection_label.isChecked()

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
            self.cr_designer.crdesigner_console_wrapper.text_browser.append("settings saved")
            self.canvas.update_obstacle_trajectory_params()

            set_draw_params(trajectory=self.window.chk_draw_trajectory.isChecked(),
                                            intersection=self.window.chk_draw_intersection.isChecked(),
                                            obstacle_label=self.window.chk_draw_label.isChecked(),
                                            obstacle_icon=self.window.chk_draw_obstacle_icon.isChecked(),
                                            obstacle_direction=self.window.chk_draw_obstacle_direction.isChecked(),
                                            obstacle_signal=self.window.chk_draw_obstacle_signal.isChecked(),
                                            occupancy=self.window.chk_draw_occupancy.isChecked(),
                                            traffic_signs=self.window.chk_draw_traffic_sign.isChecked(),
                                            traffic_lights=self.window.chk_draw_traffic_light.isChecked(),
                                            incoming_lanelets=self.window.chk_draw_incoming_lanelet.isChecked(),
                                            successors=self.window.chk_draw_successors.isChecked(),
                                            intersection_labels=self.window.chk_draw_intersection_label.isChecked(),
                                            )
        else:
            print("invalid settings")
