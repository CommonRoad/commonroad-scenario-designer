from PyQt5.QtWidgets import QMessageBox
from commonroad.common.util import Interval
from commonroad.scenario.obstacle import ObstacleType

from crdesigner.map_conversion.sumo_map.config import SumoConfig
from crdesigner.ui.gui.utilities.util import Observable
from crdesigner.ui.gui.view.settings.settings_ui import HEIGHT, COLUMNS, WIDTHF, WIDTHM, FACTOR
from crdesigner.ui.gui.view.settings.sumo_settings_ui import SUMOSettingsUI


class SUMOSettingsController:

    # TODO: CONTROLLER
    def __init__(self, parent, config: Observable = None):
        self.parent = parent

        # Set up the UI and add it to the settings tab
        self.sumo_settings_ui = SUMOSettingsUI(h=HEIGHT, c=COLUMNS, wf=WIDTHF, wm=WIDTHM, f=FACTOR)
        self.sumo_settings_ui.setupUi(self.parent.settings_ui.tabWidget)
        self.parent.settings_ui.tabWidget.addTab(self.sumo_settings_ui.scrollArea, "SUMO")

        self.config = config

        # def on_config_change(config):  #     self._config = config  #     self.update_ui_values()

        # TODO: fix  # self.config.subscribe(on_config_change)  # self._config = SumoConfig.from_scenario_name(  #
        #  'new_scenario') if not config else config.value

    # TODO: CONTROLLER
    def connect_events(self):
        """ connect buttons to callables """
        pass

    # TODO: CONTROLLER
    def update_ui_values(self):
        """
        sets the values of the settings window to the current values of config

        :return: None
        """
        # line edits
        self.sumo_settings_ui.le_ego_ids.setText(",".join([str(e) for e in self.config.ego_ids]))
        interv = self._config.departure_interval_vehicles
        self.sumo_settings_ui.le_departure_interval_vehicles.setText(str(interv.start) + "," + str(interv.end))

        # spin boxes
        self.sumo_settings_ui.sb_departure_time_ego.setValue(int(self._config.departure_time_ego))

        self.sumo_settings_ui.sb_random_seed.setValue(int(self._config.random_seed))
        self.sumo_settings_ui.sb_lateral_resolution.setValue(int(self._config.lateral_resolution))
        self.sumo_settings_ui.sb_ego_start_time.setValue(self._config.ego_start_time)
        self.sumo_settings_ui.sb_n_ego_vehicles.setValue(self._config.n_ego_vehicles)  # rename
        self.sumo_settings_ui.sb_overwrite_speed_limit.setValue(int(self._config.overwrite_speed_limit))
        self.sumo_settings_ui.sb_lanelet_check_time_window.setValue(int(self._config.lanelet_check_time_window))
        self.sumo_settings_ui.sb_unrestricted_max_speed_default.setValue(
                int(self._config.unrestricted_max_speed_default))
        self.sumo_settings_ui.sb_delta_steps.setValue(int(self._config.delta_steps))
        self.sumo_settings_ui.sb_n_vehicles_max.setValue(int(self._config.n_vehicles_max))
        self.sumo_settings_ui.sb_consistency_window.setValue(int(self._config.consistency_window))
        self.sumo_settings_ui.sb_max_veh_per_km.setValue(int(self._config.max_veh_per_km))
        self.sumo_settings_ui.sb_veh_per_second.setValue(int(self._config.veh_per_second))
        self.sumo_settings_ui.sb_unrestricted_speed_limit_default.setValue(
                int(self._config.unrestricted_speed_limit_default))
        self.sumo_settings_ui.sb_fringe_factor.setValue(int(self._config.fringe_factor))
        self.sumo_settings_ui.sb_wait_pos_internal_junctions.setValue(self._config.wait_pos_internal_junctions)
        self.sumo_settings_ui.sb_ego_veh_width.setValue(self._config.ego_veh_width)
        self.sumo_settings_ui.sb_protection_margin.setValue(self._config.protection_margin)
        self.sumo_settings_ui.sb_lane_change_tol.setValue(self._config.lane_change_tol)
        self.sumo_settings_ui.sb_vehicle_length_interval.setValue(self._config.vehicle_length_interval)
        self.sumo_settings_ui.sb_ego_veh_length.setValue(self._config.ego_veh_length)
        self.sumo_settings_ui.sb_vehicle_width_interval.setValue(self._config.vehicle_width_interval)
        self.sumo_settings_ui.sb_passenger.setValue(self._config.veh_distribution[ObstacleType.CAR])
        self.sumo_settings_ui.sb_truck.setValue(self._config.veh_distribution[ObstacleType.TRUCK])
        self.sumo_settings_ui.sb_bus.setValue(self._config.veh_distribution[ObstacleType.BUS])
        self.sumo_settings_ui.sb_bicycle.setValue(self._config.veh_distribution[ObstacleType.PEDESTRIAN])
        self.sumo_settings_ui.sb_pedestrian.setValue(self._config.veh_distribution[ObstacleType.PEDESTRIAN])

        # check boxes
        self.sumo_settings_ui.chk_lane_change_sync.setChecked(self._config.lane_change_sync)
        self.sumo_settings_ui.chk_compute_orientation.setChecked(self._config.compute_orientation)

    # TODO: CONTROLLER
    def save_to_config(self):
        """
        saves the values in the settings window to config
        """

        window = self.sumo_settings_ui

        # line edits
        ego_ids_str = window.le_ego_ids.text()
        if ego_ids_str:
            self._config.ego_ids = [int(e) for e in ego_ids_str.split(",")]
        interv_str = window.le_departure_interval_vehicles.text().split(",")
        self._config.departure_interval_vehicles = Interval(float(interv_str[0]), float(interv_str[1]))

        # spin boxes
        self._config.departure_time_ego = window.sb_departure_time_ego.value()
        self._config.random_seed = window.sb_random_seed.value()
        self._config.lateral_resolution = window.sb_lateral_resolution.value()
        self._config.ego_start_time = window.sb_ego_start_time.value()
        self._config.n_ego_vehicles = window.sb_n_ego_vehicles.value()
        self._config.overwrite_speed_limit = window.sb_overwrite_speed_limit.value()
        self._config.lanelet_check_time_window = (window.sb_lanelet_check_time_window.value())
        self._config.unrestricted_max_speed_default = (window.sb_unrestricted_max_speed_default.value())
        self._config.delta_steps = window.sb_delta_steps.value()
        self._config.n_vehicles_max = window.sb_n_vehicles_max.value()
        self._config.consistency_window = window.sb_consistency_window.value()
        self._config.max_veh_per_km = window.sb_max_veh_per_km.value()
        self._config.veh_per_second = window.sb_veh_per_second.value()
        self._config.unrestricted_speed_limit_default = (window.sb_unrestricted_speed_limit_default.value())
        self._config.fringe_factor = window.sb_fringe_factor.value()
        self._config.wait_pos_internal_junctions = (window.sb_wait_pos_internal_junctions.value())
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

    # TODO: CONTROLLER
    def has_valid_entries(self) -> bool:
        """
        Check if the user input is valid. Otherwise warn the user.

        :return: bool weather the input is valid
        """
        window = self.sumo_settings_ui

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

    # TODO: CONTROLLER
    def apply_close(self) -> None:
        """
        closes settings if settings could be saved to config
        """
        if self.has_valid_entries():
            self.save_to_config()
        else:
            print("invalid settings")

    # TODO: CONTROLLER
    def restore_defaults(self):
        """
        sets the values of config to defaults

        :return: None
        """
        self._config = SumoConfig.from_scenario_name(self._config.scenario_name)
        self.update_ui_values()

    # TODO: VIEW
    def warn(self, msg):
        messbox = QMessageBox()
        messbox.warning(None, "Warning", msg, QMessageBox.Ok, QMessageBox.Ok)
