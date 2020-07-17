import sys
from crmapconverter.io.V3_0.GUI_resources.sumo_settings_ui import Ui_MainWindow
from crmapconverter.sumo_map import config

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class SUMOSettings:

    def __init__(self, parent):

        self.cr_designer = parent
        self.window = Ui_MainWindow()
        self.window.setupUi(self.window)
        
        # connect events
        self.window.botton_restore_defaults.clicked(self.restore_defaults)
        self.window.botton_close.clicked(self.close_button)

        self.update_ui_values()

        self.window.show()

    def update_ui_values(self) -> None:
        """
        sets the values of the settings window to the current values of config.py

        :return: None
        """
        # line edits
        self.window.le_ego_ids.setText(config.
        self.window.lineEdit_departure_interval_vehicles.setText(config.
        # spin boxes
        self.window.spinBox.setValue(config.
        self.window.sb_random_seed.setValue(config.
        self.window.sb_2.setValue(config.
        self.window.sb_ego_start_time.setValue(config.
        self.window.sb_num_ego_vehicles.setValue(config.
        self.window.sb_overwrite_speed_limit.setValue(config.
        self.window.sb_lanelet_check_time_window.setValue(config.
        self.window.sb_unrestricted_max_speed_default.setValue(config.
        self.window.sb_delta_steps.setValue(config.
        self.window.sb_n_vehicles_max.setValue(config.
        self.window.sb_consistency_window.setValue(config.
        self.window.sb_max_veh_per_km.setValue(config.
        self.window.sb_veh_per_second.setValue(config.
        self.window.sb_unrestricted_speed_limit_default.setValue(config.
        self.window.sb_fringe_factor.setValue(config.
        self.window.sb_wait_pos_internal_junctions.setValue(config.
        self.window.sb_ego_veh_width.setValue(config.
        self.window.sb_protection_margin.setValue(config.
        self.window.sb_lane_change_tol.setValue(config.
        self.window.sb_vehicle_length_interval.setValue(config.
        self.window.sb_ego_veh_length.setValue(config.
        self.window.sb_vehicle_width_interval.setValue(config.
        self.window.sb_passenger.setValue(config.
        self.window.sb_truck.setValue(config.
        self.window.sb_bus.setValue(config.
        self.window.sb_bicycle.setValue(config.
        self.window.sb_pedestrian.setValue(config.
        # combo boxes
        # comboBox_lane_change_window.
        # comboBox_compute_orientation

    def save_to_config(self) -> None:
        """
        saves the values in the settings window to config.py

        :return: None
        """
        config. = le_ego_ids.text()
        config. = lineEdit_departure_interval_vehicles.text()
        # spin boxes
        config. = sb.value()
        config. = sb_random_seed.value()
        config. = sb_2.value()
        config. = sb_ego_start_time.value()
        config. = sb_num_ego_vehicles.value()
        config. = sb_overwrite_speed_limit.value()
        config. = sb_lanelet_check_time_window.value()
        config. = sb_unrestricted_max_speed_default.value()
        config. = sb_delta_steps.value()
        config. = sb_n_vehicles_max.value()
        config. = sb_consistency_window.value()
        config. = sb_max_veh_per_km.value()
        config. = sb_veh_per_second.value()
        config. = sb_unrestricted_speed_limit_default.value()
        config. = sb_fringe_factor.value()
        config. = sb_wait_pos_internal_junctions.value()
        config. = sb_ego_veh_width.value()
        config. = sb_protection_margin.value()
        config. = sb_lane_change_tol.value()
        config. = sb_vehicle_length_interval.value()
        config. = sb_ego_veh_length.value()
        config. = sb_vehicle_width_interval.value()
        config. = sb_passenger.value()
        config. = sb_truck.value()
        config. = sb_bus.value()
        config. = sb_bicycle.value()
        config. = sb_pedestrian.value()
        # combo boxes
        # config. = comboBox_lane_change_window
        # config. = comboBox_compute_orientation

    def close_button(self) -> None:
        """
        closes settings without saving

        :return: None
        """
        self.save_to_config()
        self.window.close()

    def restore_defaults(self):
        """
        sets the values of config to defaults

        :return: None
        """
        for var_name in dir(config_default):
            if not var_name.startswith('__'):
                setattr(config, var_name, getattr(config_default, var_name))
