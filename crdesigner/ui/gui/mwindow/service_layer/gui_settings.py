""" window with settings for the Scenario Designer """

import yaml

from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.commonroad_viewer.service_layer.draw_params_updater import \
    set_draw_params
from crdesigner.ui.gui.mwindow.service_layer import config
import os
from crdesigner.configurations.definition import ROOT_DIR

from crdesigner.ui.gui.mwindow.service_layer import transfer
from crdesigner.ui.gui.mwindow.service_layer.aerial_data import validate_bing_key, validate_ldbv_credentials
from PyQt5.QtWidgets import *
class GUISettings:

    def __init__(self, parent):
        self.darkmode = config.DARKMODE
        self.parent = parent
        self.window = self.parent.window.gui_settings

    def connect_events(self):
        """ connect buttons to callables """
        self.window.chk_darkmode.stateChanged.connect(self.update_window)

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
        self.window.cmb_axis_visible.setCurrentText(config.AXIS_VISIBLE)
        self.window.chk_darkmode.setChecked(config.DARKMODE)
        self.window.chk_legend.setChecked(config.LEGEND)
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
        config.AXIS_VISIBLE = str(self.window.cmb_axis_visible.currentText())
        config.DARKMODE = self.window.chk_darkmode.isChecked()
        config.LEGEND = self.window.chk_legend.isChecked()
        config.BING_MAPS_KEY = self.window.lineed_bing_maps_key.text()
        if config.BING_MAPS_KEY != "":
            check = validate_bing_key()
            if not check:
                print("_Warning__: Specified Bing Maps key is wrong.")
                warning_dialog = QMessageBox()
                warning_dialog.warning(None, "Warning",
                                       "Specified Bing Maps key is wrong.",
                                       QMessageBox.Ok, QMessageBox.Ok)
                warning_dialog.close()
                config.BING_MAPS_KEY = ""

        config.LDBV_USERNAME = self.window.lineed_ldbv_username.text()
        config.LDBV_PASSWORD = self.window.lineed_ldbv_password.text()
        if config.LDBV_USERNAME != "" or config.LDBV_PASSWORD != "":
            check = validate_ldbv_credentials()
            if not check:
                print("_Warning__: Specified LDBV username or password is wrong.")
                warning_dialog = QMessageBox()
                warning_dialog.warning(None, "Warning", "Specified LDBV username or password is wrong.", QMessageBox.Ok,
                                       QMessageBox.Ok)
                warning_dialog.close()
                config.LDBV_USERNAME = ""
                config.LDBV_PASSWORD = ""


    def has_valid_entries(self) -> bool:
        """
        Check if the user input is valid. Otherwise warn the user.

        :return: bool wether the input is valid
        """
        # use if settings get extended
        return True

    def set_draw_params_gui(self):
        set_draw_params(trajectory=config.DRAW_TRAJECTORY, intersection=config.DRAW_INTERSECTIONS,
                        obstacle_label=config.DRAW_OBSTACLE_LABELS, obstacle_icon=config.DRAW_OBSTACLE_ICONS,
                        obstacle_direction=config.DRAW_OBSTACLE_DIRECTION, obstacle_signal=config.DRAW_OBSTACLE_SIGNALS,
                        occupancy=config.DRAW_OCCUPANCY, traffic_signs=config.DRAW_TRAFFIC_SIGNS,
                        traffic_lights=config.DRAW_TRAFFIC_LIGHTS, incoming_lanelets=config.DRAW_INCOMING_LANELETS,
                        successors=config.DRAW_SUCCESSORS, intersection_labels=config.DRAW_INTERSECTION_LABELS,
                        colorscheme=self.parent.cr_designer.colorscheme(), )

    def apply_close(self) -> None:
        """
        closes settings if settings could be saved to config
        """
        if self.has_valid_entries():
            self.save_to_config()
            self.darkmode = config.DARKMODE

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
                            colorscheme=self.parent.cr_designer.colorscheme(), )
            # to save the changed settings into custom_settings.yaml file
            self.save_config_to_custom_settings()
        else:
            print("invalid settings")

    def update_window(self):
        config.DARKMODE = self.window.chk_darkmode.isChecked()
        self.set_draw_params_gui()
        if self.parent.cr_designer.animated_viewer_wrapper.cr_viewer.current_scenario != None:
            self.parent.cr_designer.animated_viewer_wrapper.cr_viewer.update_plot()
        self.parent.cr_designer.update_window()
        self.parent.window.update_window()

    def close(self):
        config.DARKMODE = self.darkmode
        self.set_draw_params_gui()
        self.parent.canvas.update_obstacle_trajectory_params()
        if self.parent.cr_designer.animated_viewer_wrapper.cr_viewer.current_scenario != None:
            self.parent.cr_designer.animated_viewer_wrapper.cr_viewer.update_plot()
        self.parent.cr_designer.update_window()
        self.parent.window.update_window()

    def apply_set_to_default(self):
        '''
        the variables in config.py will be changed back to the default values, not the file itself
        '''
        path_to_default_settings = os.path.join(ROOT_DIR, 'default_settings.yaml')
        transfer.transfer_yaml_to_config(path_to_default_settings, config)
        with open(path_to_default_settings) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
        self.set_draw_params_gui()

        path_to_custom_settings = os.path.join(ROOT_DIR, 'custom_settings.yaml')
        with open(path_to_custom_settings, 'w') as yaml_file:
            yaml_file.write(yaml.dump(data, default_flow_style=False))
        self.parent.canvas.update_obstacle_trajectory_params()
        if self.parent.cr_designer.animated_viewer_wrapper.cr_viewer.current_scenario != None:
            self.parent.cr_designer.animated_viewer_wrapper.cr_viewer.update_plot()
        self.parent.cr_designer.update_window()
        self.parent.window.update_window()

    def save_config_to_custom_settings(self):
        '''
        when clicking on ok button the changed settings will be written into the custom_settings.yaml file
        '''
        path_to_custom_settings = os.path.join(ROOT_DIR, 'custom_settings.yaml')
        with open(path_to_custom_settings) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
        for key in dir(config):
            yaml_key = key.lower()
            if yaml_key in data:
                data[yaml_key] = getattr(config, key)
        with open(path_to_custom_settings, 'w') as yaml_file:
            yaml_file.write(yaml.dump(data, default_flow_style=False))
