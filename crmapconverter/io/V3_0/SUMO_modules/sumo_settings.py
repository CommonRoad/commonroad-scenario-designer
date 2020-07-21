""" """

from PyQt5.QtWidgets import QMessageBox, QMainWindow

from commonroad.common.util import Interval

from crmapconverter.io.V3_0.GUI_resources.sumo_settings_ui import Ui_MainWindow
from crmapconverter.sumo_map.config import SumoConfig as config


class SUMOSettings:

    def __init__(self, parent):

        self.parent = parent
        self.settings_window = QMainWindow()
        self.window = Ui_MainWindow()
        self.window.setupUi(self.settings_window)
        self.window.setupUi(self.settings_window)
        
        # connect events
        self.window.botton_restore_defaults.clicked.connect(self.restore_defaults)
        self.window.botton_close.clicked.connect(self.close_button)

        self.update_ui_values()
        self.settings_window.show()

    def update_ui_values(self) -> None:
        """
        sets the values of the settings window to the current values of config

        :return: None
        """
        # line edits
        self.window.le_ego_ids.setText(",".join([str(e) for e in config.ego_ids]))
        interv = config.departure_interval_vehicles
        self.window.le_departure_interval_vehicles.setText(
            str(interv.start) + "," + str(interv.end))            

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
        self.window.sb_passenger.setValue(config.veh_distribution['passenger'])
        self.window.sb_truck.setValue(config.veh_distribution['truck'])
        self.window.sb_bus.setValue(config.veh_distribution['bus'])
        self.window.sb_bicycle.setValue(config.veh_distribution['bicycle'])
        self.window.sb_pedestrian.setValue(
            config.veh_distribution['pedestrian'])
            
        # check boxes
        self.window.chk_lane_change_sync.setChecked(config.lane_change_sync)
        self.window.chk_compute_orientation.setChecked(config.compute_orientation)

    def save_to_config(self) -> None:
        """
        saves the values in the settings window to config 

        :return: None
        """

        window = self.window

        if not self.has_valid_entries():
            return

        # line edits
        ego_ids_str = window.le_ego_ids.text()
        if ego_ids_str:
            config.ego_ids = [int(e) for e in ego_ids_str.split(",")]
        interv_str = window.le_departure_interval_vehicles.text().split(",")
        config.departure_interval_vehicles = Interval(
            float(interv_str[0]), float(interv_str[1]))

        # spin boxes
        # config. =window.sb.value() # ?
        config.random_seed =window.sb_random_seed.value()
        # config. = window.sb_2.value() # ?
        config.ego_start_time = window.sb_ego_start_time.value()
        config.n_ego_vehicles = window.sb_num_ego_vehicles.value()
        config.overwrite_speed_limit = window.sb_overwrite_speed_limit.value()
        config.lanelet_check_time_window = (
            window.sb_lanelet_check_time_window.value()
        )
        config.unrestricted_max_speed_default = (
            window.sb_unrestricted_max_speed_default.value()
        )
        config.delta_steps = window.sb_delta_steps.value()
        config.n_vehicles_max = window.sb_n_vehicles_max.value()
        config.consistency_window = window.sb_consistency_window.value()
        config.max_veh_per_km = window.sb_max_veh_per_km.value()
        config.veh_per_second = window.sb_veh_per_second.value()
        config.unrestricted_speed_limit_default = (
            window.sb_unrestricted_speed_limit_default.value()
        )
        config.fringe_factor = window.sb_fringe_factor.value()
        config.wait_pos_internal_junctions = (
            window.sb_wait_pos_internal_junctions.value()
        )
        config.ego_veh_width = window.sb_ego_veh_width.value()
        config.protection_margin = window.sb_protection_margin.value()
        config.lane_change_tol = window.sb_lane_change_tol.value()
        config.vehicle_length_interval = window.sb_vehicle_length_interval.value()
        config.ego_veh_length = window.sb_ego_veh_length.value()
        config.vehicle_width_interval = window.sb_vehicle_width_interval.value()
        config.passenger = window.sb_passenger.value()
        config.truck = window.sb_truck.value()
        config.bus = window.sb_bus.value()
        config.bicycle = window.sb_bicycle.value()
        config.pedestrian = window.sb_pedestrian.value()
        # combo boxes
        config.lane_change_sync = window.chk_lane_change_sync.isChecked()
        config.compute_orientation = window.chk_compute_orientation.isChecked()

    def has_valid_entries(self) -> bool:
        """ 
        Check if the user input is valid. Otherwise warn the user.

        :return: bool weather the input is valid
        """
        window = self.window

        ego_ids_str = window.le_ego_ids.text()
        if ego_ids_str:
            try:
                [int(e) for e in ego_ids_str.split(",")]
            except ValueError:
                self.warn("invalid settings: ego_ids")
                return False

        interv_str = window.le_departure_interval_vehicles.text().split(",")
        try:
            Interval(float(interv_str[0]), float(interv_str[1]))
        except ValueError:
            self.warn("invalid settings: departure_interval_vehicles")
            return False
        
        return True

    def close_button(self) -> None:
        """
        closes settings without saving

        :return: None
        """
        if self.save_to_config():
            self.settings_window.close()

    def restore_defaults(self):
        """
        sets the values of config to defaults

        :return: None
        """
        # for var_name in dir(config_default):
        #     if not var_name.startswith('__'):
        #         setattr(config, var_name, getattr(config_default, var_name))

    def warn(self, msg):
        messbox = QMessageBox()
        messbox.warning(None, 
                        "Warning",
                        msg,
                        QMessageBox.Ok, QMessageBox.Ok)
