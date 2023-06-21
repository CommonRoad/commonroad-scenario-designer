from PyQt5.QtWidgets import QMessageBox

from crdesigner.ui.gui.model.settings.gui_settings_model import gui_settings
from crdesigner.ui.gui.utilities.aerial_data import validate_bing_key, validate_ldbv_credentials
from crdesigner.ui.gui.utilities.draw_params_updater import set_draw_params
from crdesigner.ui.gui.view.settings.gui_settings_ui import GUISettingsUI
from crdesigner.ui.gui.view.settings.settings_ui import HEIGHT, COLUMNS, WIDTHF, WIDTHM, FACTOR


class GUISettingController:

    def __init__(self, parent):
        self.darkmode = gui_settings.DARKMODE
        self.parent = parent

        # Set up the UI and add it to the settings tab
        self.gui_settings_ui = GUISettingsUI(h=HEIGHT, c=COLUMNS, wf=WIDTHF, wm=WIDTHM, f=FACTOR)
        self.gui_settings_ui.setupUi(self.parent.settings_ui.tabWidget)
        self.parent.settings_ui.tabWidget.addTab(self.gui_settings_ui.scrollArea, "GUI")

    def connect_events(self):
        """ connect buttons to callables """
        self.gui_settings_ui.chk_darkmode.stateChanged.connect(self.update_window)

    def update_ui_values(self):
        """
        sets the values of the settings window to the current values of config
        """
        self.gui_settings_ui.chk_autofocus.setChecked(gui_settings.AUTOFOCUS)
        self.gui_settings_ui.chk_draw_trajectory.setChecked(gui_settings.DRAW_TRAJECTORY)
        self.gui_settings_ui.chk_draw_intersection.setChecked(gui_settings.DRAW_INTERSECTIONS)
        self.gui_settings_ui.chk_draw_label.setChecked(gui_settings.DRAW_OBSTACLE_LABELS)
        self.gui_settings_ui.chk_draw_obstacle_icon.setChecked(gui_settings.DRAW_OBSTACLE_ICONS)
        self.gui_settings_ui.chk_draw_obstacle_direction.setChecked(gui_settings.DRAW_OBSTACLE_DIRECTION)
        self.gui_settings_ui.chk_draw_obstacle_signal.setChecked(gui_settings.DRAW_OBSTACLE_SIGNALS)
        self.gui_settings_ui.chk_draw_occupancy.setChecked(gui_settings.DRAW_OCCUPANCY)
        self.gui_settings_ui.chk_draw_traffic_sign.setChecked(gui_settings.DRAW_TRAFFIC_SIGNS)
        self.gui_settings_ui.chk_draw_traffic_light.setChecked(gui_settings.DRAW_TRAFFIC_LIGHTS)
        self.gui_settings_ui.chk_draw_incoming_lanelet.setChecked(gui_settings.DRAW_INCOMING_LANELETS)
        self.gui_settings_ui.chk_draw_successors.setChecked(gui_settings.DRAW_SUCCESSORS)
        self.gui_settings_ui.chk_draw_intersection_label.setChecked(gui_settings.DRAW_INTERSECTION_LABELS)
        self.gui_settings_ui.cmb_axis_visible.setCurrentText(gui_settings.AXIS_VISIBLE)
        self.gui_settings_ui.chk_darkmode.setChecked(gui_settings.DARKMODE)
        self.gui_settings_ui.chk_legend.setChecked(gui_settings.LEGEND)
        return

    def save_to_config(self):
        """
        saves the values in the settings window to config.py
        """
        gui_settings.AUTOFOCUS = self.gui_settings_ui.chk_autofocus.isChecked()
        gui_settings.DRAW_TRAJECTORY = self.gui_settings_ui.chk_draw_trajectory.isChecked()
        gui_settings.DRAW_INTERSECTIONS = self.gui_settings_ui.chk_draw_intersection.isChecked()
        gui_settings.DRAW_OBSTACLE_LABELS = self.gui_settings_ui.chk_draw_label.isChecked()
        gui_settings.DRAW_OBSTACLE_ICONS = self.gui_settings_ui.chk_draw_obstacle_icon.isChecked()
        gui_settings.DRAW_OBSTACLE_DIRECTION = self.gui_settings_ui.chk_draw_obstacle_direction.isChecked()
        gui_settings.DRAW_OBSTACLE_SIGNALS = self.gui_settings_ui.chk_draw_obstacle_signal.isChecked()
        gui_settings.DRAW_OCCUPANCY = self.gui_settings_ui.chk_draw_occupancy.isChecked()
        gui_settings.DRAW_TRAFFIC_SIGNS = self.gui_settings_ui.chk_draw_traffic_sign.isChecked()
        gui_settings.DRAW_TRAFFIC_LIGHTS = self.gui_settings_ui.chk_draw_traffic_light.isChecked()
        gui_settings.DRAW_INCOMING_LANELETS = self.gui_settings_ui.chk_draw_incoming_lanelet.isChecked()
        gui_settings.DRAW_SUCCESSORS = self.gui_settings_ui.chk_draw_successors.isChecked()
        gui_settings.DRAW_INTERSECTION_LABELS = self.gui_settings_ui.chk_draw_intersection_label.isChecked()
        gui_settings.AXIS_VISIBLE = str(self.gui_settings_ui.cmb_axis_visible.currentText())
        gui_settings.DARKMODE = self.gui_settings_ui.chk_darkmode.isChecked()
        gui_settings.LEGEND = self.gui_settings_ui.chk_legend.isChecked()
        gui_settings.BING_MAPS_KEY = self.gui_settings_ui.lineed_bing_maps_key.text()
        if gui_settings.BING_MAPS_KEY != "":
            check = validate_bing_key()
            if not check:
                print("_Warning__: Specified Bing Maps key is wrong.")
                warning_dialog = QMessageBox()
                warning_dialog.warning(None, "Warning", "Specified Bing Maps key is wrong.", QMessageBox.Ok,
                                       QMessageBox.Ok)
                warning_dialog.close()
                gui_settings.BING_MAPS_KEY = ""

        gui_settings.LDBV_USERNAME = self.gui_settings_ui.lineed_ldbv_username.text()
        gui_settings.LDBV_PASSWORD = self.gui_settings_ui.lineed_ldbv_password.text()
        if gui_settings.LDBV_USERNAME != "" or gui_settings.LDBV_PASSWORD != "":
            check = validate_ldbv_credentials()
            if not check:
                print("_Warning__: Specified LDBV username or password is wrong.")
                warning_dialog = QMessageBox()
                warning_dialog.warning(None, "Warning", "Specified LDBV username or password is wrong.", QMessageBox.Ok,
                                       QMessageBox.Ok)
                warning_dialog.close()
                gui_settings.LDBV_USERNAME = ""
                gui_settings.LDBV_PASSWORD = ""

    def has_valid_entries(self) -> bool:
        """
        Check if the user input is valid. Otherwise, warn the user.

        :return: bool wether the input is valid
        """
        # use if settings get extended
        return True

    def set_draw_params_gui(self):
        set_draw_params(trajectory=gui_settings.DRAW_TRAJECTORY, intersection=gui_settings.DRAW_INTERSECTIONS,
                        obstacle_label=gui_settings.DRAW_OBSTACLE_LABELS,
                        obstacle_icon=gui_settings.DRAW_OBSTACLE_ICONS,
                        obstacle_direction=gui_settings.DRAW_OBSTACLE_DIRECTION,
                        obstacle_signal=gui_settings.DRAW_OBSTACLE_SIGNALS, occupancy=gui_settings.DRAW_OCCUPANCY,
                        traffic_signs=gui_settings.DRAW_TRAFFIC_SIGNS, traffic_lights=gui_settings.DRAW_TRAFFIC_LIGHTS,
                        incoming_lanelets=gui_settings.DRAW_INCOMING_LANELETS, successors=gui_settings.DRAW_SUCCESSORS,
                        intersection_labels=gui_settings.DRAW_INTERSECTION_LABELS,
                        colorscheme=self.parent.cr_designer.colorscheme(), )

    def apply_close(self) -> None:
        """
        closes settings if settings could be saved to config
        """
        if self.has_valid_entries():
            self.save_to_config()
            self.darkmode = gui_settings.DARKMODE

            self.set_draw_params_gui()
            # to save the changed settings into custom_settings.yaml file
            gui_settings.save_config_to_custom_settings()
        else:
            print("invalid settings")

    def update_window(self):
        gui_settings.DARKMODE = self.gui_settings_ui.chk_darkmode.isChecked()
        self.set_draw_params_gui()
        self._update_connected()

    def close(self):
        gui_settings.DARKMODE = self.darkmode
        self.set_draw_params_gui()
        self.parent.canvas.update_obstacle_trajectory_params()
        self._update_connected()

    def _update_connected(self):
        if self.parent.scenario_model.scenario_created():
            self.parent.cr_designer.animated_viewer_wrapper.cr_viewer.update_plot()
        self.parent.cr_designer.update_window()
        self.parent.settings_ui.update_window()
