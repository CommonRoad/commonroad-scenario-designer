from commonroad.common.util import Interval
from commonroad.scenario.obstacle import ObstacleType

try:
    # required for Ubuntu 20.04 since there a system library is too old for pyqt6 and the import fails
    # when not importing this, one can still use the map conversion
    from PyQt6.QtWidgets import QMessageBox

    pyqt_available = True
except (ImportError, RuntimeError):
    pyqt_available = False

from crdesigner.map_conversion.sumo_map.config import SumoConfig
from crdesigner.ui.gui.utilities.util import Observable


class SUMOSettings:
    def __init__(self, parent, config: Observable = None):
        self.parent = parent
        self.window = self.parent.window.sumo_config
        self.config = config

        def on_config_change(config):
            self._config = config
            self.update_ui_values()

        self.config.subscribe(on_config_change)

        self._config = SumoConfig.from_scenario_name("new_scenario") if not config else config.value

    def connect_events(self):
        """connect buttons to callables"""
        pass

    def update_ui_values(self):
        """
        sets the values of the settings window to the current values of config

        :return: None
        """
        # line edits
        self.window.le_ego_ids.setText(",".join([str(e) for e in self._config.ego_ids]))
        interv = self._config.departure_interval_vehicles
        self.window.le_departure_interval_vehicles.setText(
            str(interv.start) + "," + str(interv.end)
        )

        # spin boxes
        self.window.sb_departure_time_ego.setValue(int(self._config.departure_time_ego))

        self.window.sb_random_seed.setValue(int(self._config.random_seed))
        self.window.sb_lateral_resolution.setValue(int(self._config.lateral_resolution))
        self.window.sb_ego_start_time.setValue(self._config.ego_start_time)
        self.window.sb_n_ego_vehicles.setValue(self._config.n_ego_vehicles)  # rename
        self.window.sb_overwrite_speed_limit.setValue(int(self._config.overwrite_speed_limit))
        self.window.sb_lanelet_check_time_window.setValue(
            int(self._config.lanelet_check_time_window)
        )
        self.window.sb_unrestricted_max_speed_default.setValue(
            int(self._config.unrestricted_max_speed_default)
        )
        self.window.sb_delta_steps.setValue(int(self._config.delta_steps))
        self.window.sb_n_vehicles_max.setValue(int(self._config.n_vehicles_max))
        self.window.sb_consistency_window.setValue(int(self._config.consistency_window))
        self.window.sb_max_veh_per_km.setValue(int(self._config.max_veh_per_km))
        self.window.sb_veh_per_second.setValue(int(self._config.veh_per_second))
        self.window.sb_unrestricted_speed_limit_default.setValue(
            int(self._config.unrestricted_speed_limit_default)
        )
        self.window.sb_fringe_factor.setValue(int(self._config.fringe_factor))
        self.window.sb_wait_pos_internal_junctions.setValue(
            self._config.wait_pos_internal_junctions
        )
        self.window.sb_ego_veh_width.setValue(self._config.ego_veh_width)
        self.window.sb_protection_margin.setValue(self._config.protection_margin)
        self.window.sb_lane_change_tol.setValue(self._config.lane_change_tol)
        self.window.sb_vehicle_length_interval.setValue(self._config.vehicle_length_interval)
        self.window.sb_ego_veh_length.setValue(self._config.ego_veh_length)
        self.window.sb_vehicle_width_interval.setValue(self._config.vehicle_width_interval)
        self.window.sb_passenger.setValue(self._config.veh_distribution[ObstacleType.CAR])
        self.window.sb_truck.setValue(self._config.veh_distribution[ObstacleType.TRUCK])
        self.window.sb_bus.setValue(self._config.veh_distribution[ObstacleType.BUS])
        self.window.sb_bicycle.setValue(self._config.veh_distribution[ObstacleType.PEDESTRIAN])
        self.window.sb_pedestrian.setValue(self._config.veh_distribution[ObstacleType.PEDESTRIAN])

        # check boxes
        self.window.chk_lane_change_sync.setChecked(self._config.lane_change_sync)
        self.window.chk_compute_orientation.setChecked(self._config.compute_orientation)

    def save_to_config(self):
        """
        saves the values in the settings window to config
        """

        window = self.window

        # line edits
        ego_ids_str = window.le_ego_ids.text()
        if ego_ids_str:
            self._config.ego_ids = [int(e) for e in ego_ids_str.split(",")]
        interv_str = window.le_departure_interval_vehicles.text().split(",")
        self._config.departure_interval_vehicles = Interval(
            float(interv_str[0]), float(interv_str[1])
        )

        # spin boxes
        self._config.departure_time_ego = window.sb_departure_time_ego.value()
        self._config.random_seed = window.sb_random_seed.value()
        self._config.lateral_resolution = window.sb_lateral_resolution.value()
        self._config.ego_start_time = window.sb_ego_start_time.value()
        self._config.n_ego_vehicles = window.sb_n_ego_vehicles.value()
        self._config.overwrite_speed_limit = window.sb_overwrite_speed_limit.value()
        self._config.lanelet_check_time_window = window.sb_lanelet_check_time_window.value()
        self._config.unrestricted_max_speed_default = (
            window.sb_unrestricted_max_speed_default.value()
        )
        self._config.delta_steps = window.sb_delta_steps.value()
        self._config.n_vehicles_max = window.sb_n_vehicles_max.value()
        self._config.consistency_window = window.sb_consistency_window.value()
        self._config.max_veh_per_km = window.sb_max_veh_per_km.value()
        self._config.veh_per_second = window.sb_veh_per_second.value()
        self._config.unrestricted_speed_limit_default = (
            window.sb_unrestricted_speed_limit_default.value()
        )
        self._config.fringe_factor = window.sb_fringe_factor.value()
        self._config.wait_pos_internal_junctions = window.sb_wait_pos_internal_junctions.value()
        self._config.ego_veh_width = window.sb_ego_veh_width.value()
        self._config.protection_margin = window.sb_protection_margin.value()
        self._config.lane_change_tol = window.sb_lane_change_tol.value()
        self._config.vehicle_length_interval = window.sb_vehicle_length_interval.value()
        self._config.ego_veh_length = window.sb_ego_veh_length.value()
        self._config.vehicle_width_interval = window.sb_vehicle_width_interval.value()
        self._config.passenger = window.sb_passenger.value()
        self._config.truck = window.sb_truck.value()
        self._config.bus = window.sb_bus.value()
        self._config.bicycle = window.sb_bicycle.value()
        self._config.pedestrian = window.sb_pedestrian.value()

        # combo boxes
        self._config.lane_change_sync = window.chk_lane_change_sync.isChecked()
        self._config.compute_orientation = window.chk_compute_orientation.isChecked()

        self.config.value = self._config

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

    def apply_close(self) -> None:
        """
        closes settings if settings could be saved to config
        """
        if self.has_valid_entries():
            self.save_to_config()
        else:
            print("invalid settings")

    def restore_defaults(self):
        """
        sets the values of config to defaults

        :return: None
        """
        self._config = SumoConfig.from_scenario_name(self._config.scenario_name)
        self.update_ui_values()

    def warn(self, msg):
        if pyqt_available:
            messbox = QMessageBox()
            messbox.warning(
                None, "Warning", msg, QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Ok
            )
