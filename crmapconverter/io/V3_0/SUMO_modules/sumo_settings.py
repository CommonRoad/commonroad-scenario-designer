import sys
from crmapconverter.io.V3_0.GUI_resources.sumo_settings_ui import Ui_MainWindow
from crmapconverter.sumo_map.config import SumoConfig as config

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
        # self.window.le_ego_ids.setText(config.ego_ids) # List but why?
        # self.window.lineEdit_departure_interval_vehicles.setText(
        #     config.departure_interval_vehicles ) # Intervall
            
        # spin boxes
        # self.window.spinBox.setValue(config.
        self.window.sb_random_seed.setValue(config.random_seed)
        # self.window.sb_2.setValue(config.
        self.window.sb_ego_start_time.setValue(config.ego_start_time)
        self.window.sb_num_ego_vehicles.setValue(config.n_ego_vehicles) # rename
        self.window.sb_overwrite_speed_limit.setValue(
            config.overwrite_speed_limit)
        self.window.sb_lanelet_check_time_window.setValue(
            config.lanelet_check_time_window)
        self.window.sb_unrestricted_max_speed_default.setValue(
            config.unrestricted_max_speed_default)
        self.window.sb_delta_steps.setValue(config.delta_steps)
        self.window.sb_n_vehicles_max.setValue(config.n_vehicles_max)
        self.window.sb_consistency_window.setValue(config.consistency_window)
        self.window.sb_max_veh_per_km.setValue(config.max_veh_per_km)
        self.window.sb_veh_per_second.setValue(config.veh_per_second)
        self.window.sb_unrestricted_speed_limit_default.setValue(
            config.unrestricted_speed_limit_default)
        self.window.sb_fringe_factor.setValue(config.fringe_factor)
        self.window.sb_wait_pos_internal_junctions.setValue(
            config.wait_pos_internal_junctions)
        self.window.sb_ego_veh_width.setValue(config.ego_veh_width)
        self.window.sb_protection_margin.setValue(config.protection_margin)
        self.window.sb_lane_change_tol.setValue(config.lane_change_tol)
        self.window.sb_vehicle_length_interval.setValue(
            config.vehicle_length_interval)
        self.window.sb_ego_veh_length.setValue(config.ego_veh_length)
        self.window.sb_vehicle_width_interval.setValue(
            config.vehicle_width_interval)
        # TODO veh dist to extra window
        self.window.sb_passenger.setValue(config.veh_distribution['passenger'])
        self.window.sb_truck.setValue(config.veh_distribution['truck'])
        self.window.sb_bus.setValue(config.veh_distribution['bus'])
        self.window.sb_bicycle.setValue(config.veh_distribution['bicycle'])
        self.window.sb_pedestrian.setValue(
            config.veh_distribution['pedestrian'])
            
        # combo boxes
        # comboBox_lane_change_window.
        # comboBox_compute_orientation

    def save_to_config(self) -> None:
        """
        saves the values in the settings window to config.py

        :return: None
        """
        # config.ego_ids = le_ego_ids.text()
        # config.departure_interval_vehicles = lineEdit_departure_interval_vehicles.text()
        # spin boxes
        # config. = sb.value() # ?
        config.random_seed = sb_random_seed.value()
        # config. = sb_2.value() # ?
        config.ego_start_time = sb_ego_start_time.value()
        configsb_n_ego_vehicles. = sb_num_ego_vehicles.value()
        config.overwrite_speed_limit = sb_overwrite_speed_limit.value()
        config.lanelet_check_time_window = sb_lanelet_check_time_window.value()
        config.unrestricted_max_speed_default = sb_unrestricted_max_speed_default.value()
        config.delta_steps = sb_delta_steps.value()
        config.n_vehicles_max = sb_n_vehicles_max.value()
        config.consistency_window = sb_consistency_window.value()
        config.max_veh_per_km = sb_max_veh_per_km.value()
        config.veh_per_second = sb_veh_per_second.value()
        config.unrestricted_speed_limit_default = sb_unrestricted_speed_limit_default.value()
        config.fringe_factor = sb_fringe_factor.value()
        config.wait_pos_internal_junctions = sb_wait_pos_internal_junctions.value()
        config.ego_veh_width = sb_ego_veh_width.value()
        config.protection_margin = sb_protection_margin.value()
        config.lane_change_tol = sb_lane_change_tol.value()
        config.vehicle_length_interval = sb_vehicle_length_interval.value()
        config.ego_veh_length = sb_ego_veh_length.value()
        config.vehicle_width_interval = sb_vehicle_width_interval.value()
        # TODO to extra window
        config.passenger = sb_passenger.value()
        config.truck = sb_truck.value()
        config.bus = sb_bus.value()
        config.bicycle = sb_bicycle.value()
        config.pedestrian = sb_pedestrian.value()
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
        # for var_name in dir(config_default):
        #     if not var_name.startswith('__'):
        #         setattr(config, var_name, getattr(config_default, var_name))
