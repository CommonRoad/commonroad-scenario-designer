import math

import numpy as np
from commonroad.scenario.traffic_light import (
    TrafficLight,
    TrafficLightCycle,
    TrafficLightCycleElement,
    TrafficLightDirection,
    TrafficLightState,
)

from crdesigner.common.logging import logger
from crdesigner.common.sumo_available import SUMO_AVAILABLE
from crdesigner.ui.gui.model.scenario_model import ScenarioModel
from crdesigner.ui.gui.view.toolboxes.road_network_toolbox.road_network_toolbox_ui.road_network_toolbox_ui import (
    RoadNetworkToolboxUI,
)
from crdesigner.ui.gui.view.toolboxes.road_network_toolbox.traffic_lights_ui import (
    AddTrafficLightsUI,
)

if SUMO_AVAILABLE:
    from crdesigner.map_conversion.map_conversion_interface import SumoConfig
    from crdesigner.map_conversion.sumo_map.cr2sumo.converter import CR2SumoMapConverter


class AddTrafficLightsController:
    def __init__(
        self,
        road_network_controller,
        scenario_model: ScenarioModel,
        road_network_toolbox_ui: RoadNetworkToolboxUI,
    ):
        self.scenario_model = scenario_model
        self.road_network_toolbox_ui = road_network_toolbox_ui
        self.road_network_controller = road_network_controller
        self.traffic_lights_ui = AddTrafficLightsUI(
            self.scenario_model, self.road_network_toolbox_ui
        )

    def connect_gui_traffic_lights(self):
        self.road_network_toolbox_ui.button_add_traffic_light.clicked.connect(
            lambda: self.add_traffic_light()
        )
        self.road_network_toolbox_ui.button_update_traffic_light.clicked.connect(
            lambda: self.update_traffic_light()
        )
        self.road_network_toolbox_ui.button_remove_traffic_light.clicked.connect(
            lambda: self.remove_traffic_light()
        )
        self.road_network_toolbox_ui.button_create_traffic_lights.clicked.connect(
            lambda: self.create_traffic_light_for_referenced_lanelets()
        )
        self.road_network_toolbox_ui.selected_traffic_light.currentTextChanged.connect(
            lambda: self.traffic_lights_ui.update_traffic_light_information()
        )

    @logger.log
    def add_traffic_light(self, traffic_light_id: int = None):
        """
        Adds a new traffic light to the scenario based on the user selection.

        @param traffic_light_id: Id which the new traffic sign should have.
        """
        if self.road_network_controller.mwindow.play_activated:
            self.road_network_controller.text_browser.append("Please stop the animation first.")
            return

        if not self.scenario_model.scenario_created():
            self.road_network_controller.text_browser.append("_Warning:_ Create a new file")
            return

        if (
            len(self.road_network_toolbox_ui.referenced_lanelets_traffic_light.get_checked_items())
            == 0
        ):
            self.road_network_controller.text_browser.append("_Warning:_ Add Referenced Lanelets")
            return
        # Check if only 'None' is selected - if yes -> Warning
        if (
            "None"
            in self.road_network_toolbox_ui.referenced_lanelets_traffic_light.get_checked_items()
            and len(
                self.road_network_toolbox_ui.referenced_lanelets_traffic_light.get_checked_items()
            )
            == 1
        ):
            self.road_network_controller.text_browser.append("_Warning:_ Add Referenced Lanelets")
            return
        # Check if 'None' is and other items are selected -> Uncheck 'None'
        elif (
            "None"
            in self.road_network_toolbox_ui.referenced_lanelets_traffic_light.get_checked_items()
        ):
            self.road_network_toolbox_ui.referenced_lanelets_traffic_light.uncheck_items("None")
        referenced_lanelets = {
            int(la)
            for la in self.road_network_toolbox_ui.referenced_lanelets_traffic_light.get_checked_items()
        }
        if self.road_network_toolbox_ui.x_position_traffic_light.text():
            x_position = self.road_network_controller.get_float(
                self.road_network_toolbox_ui.x_position_traffic_light
            )
        else:
            x_position = 0
        if self.road_network_toolbox_ui.y_position_traffic_light.text():
            y_position = self.road_network_controller.get_float(
                self.road_network_toolbox_ui.y_position_traffic_light
            )
        else:
            y_position = 0

        traffic_light_direction = TrafficLightDirection(
            self.road_network_toolbox_ui.traffic_light_directions.currentText()
        )
        time_offset = int(self.road_network_toolbox_ui.time_offset.text())
        time_red = int(self.road_network_toolbox_ui.time_red.text())
        time_green = int(self.road_network_toolbox_ui.time_green.text())
        time_yellow = int(self.road_network_toolbox_ui.time_yellow.text())
        time_red_yellow = int(self.road_network_toolbox_ui.time_red_yellow.text())
        time_inactive = int(self.road_network_toolbox_ui.time_inactive.text())
        traffic_light_active = self.road_network_toolbox_ui.traffic_light_active.isChecked()
        traffic_light_cycle_order = (
            self.road_network_toolbox_ui.traffic_light_cycle_order.currentText().split("-")
        )

        traffic_light_cycle = []
        for elem in traffic_light_cycle_order:
            if elem == "r" and time_red > 0:
                traffic_light_cycle.append(
                    TrafficLightCycleElement(TrafficLightState.RED, time_red)
                )
            elif elem == "g" and time_green > 0:
                traffic_light_cycle.append(
                    TrafficLightCycleElement(TrafficLightState.GREEN, time_green)
                )
            elif elem == "ry" and time_red_yellow > 0:
                traffic_light_cycle.append(
                    TrafficLightCycleElement(TrafficLightState.RED_YELLOW, time_red_yellow)
                )
            elif elem == "y" and time_yellow > 0:
                traffic_light_cycle.append(
                    TrafficLightCycleElement(TrafficLightState.YELLOW, time_yellow)
                )
            elif elem == "in" and time_inactive > 0:
                traffic_light_cycle.append(
                    TrafficLightCycleElement(TrafficLightState.INACTIVE, time_inactive)
                )

        if traffic_light_id is None:
            traffic_light_id = self.scenario_model.generate_object_id()

        new_traffic_light = TrafficLight(
            traffic_light_id,
            np.array([x_position, y_position]),
            TrafficLightCycle(
                traffic_light_cycle, time_offset=time_offset, active=traffic_light_active
            ),
            direction=traffic_light_direction,
            active=traffic_light_active,
        )

        self.scenario_model.add_traffic_light(new_traffic_light, referenced_lanelets)
        self.road_network_controller.set_default_road_network_list_information()

    @logger.log
    def update_traffic_light(self):
        """
        Updates a traffic light from the scenario based on the user selection.
        """
        if self.road_network_controller.mwindow.play_activated:
            self.road_network_controller.text_browser.append("Please stop the animation first.")
            return

        if not self.scenario_model.scenario_created():
            self.road_network_controller.text_browser.append("_Warning:_ Create a new file")
            return
        if (
            len(self.road_network_toolbox_ui.referenced_lanelets_traffic_light.get_checked_items())
            == 0
        ):
            self.road_network_controller.text_browser.append("_Warning:_ Add Referenced Lanelets")
            return
        # Check if only 'None' is selected - if yes -> Warning
        if (
            "None"
            in self.road_network_toolbox_ui.referenced_lanelets_traffic_light.get_checked_items()
            and len(
                self.road_network_toolbox_ui.referenced_lanelets_traffic_light.get_checked_items()
            )
            == 1
        ):
            self.road_network_controller.text_browser.append("_Warning:_ Add Referenced Lanelets")
            return  # Check if 'None' is and other items are selected -> Uncheck 'None'
        elif (
            "None"
            in self.road_network_toolbox_ui.referenced_lanelets_traffic_light.get_checked_items()
        ):
            self.road_network_toolbox_ui.referenced_lanelets_traffic_light.uncheck_items("None")
        if self.road_network_toolbox_ui.selected_traffic_light.currentText() not in ["", "None"]:
            selected_traffic_light_id = int(
                self.road_network_toolbox_ui.selected_traffic_light.currentText()
            )
        else:
            return

        self.scenario_model.update_traffic_light(selected_traffic_light_id)
        self.add_traffic_light(selected_traffic_light_id)

    @logger.log
    def remove_traffic_light(self):
        """
        Removes a traffic light from the scenario.
        """
        if self.road_network_controller.mwindow.play_activated:
            self.road_network_controller.text_browser.append("Please stop the animation first.")
            return

        if not self.scenario_model.scenario_created():
            self.road_network_controller.text_browser.append("_Warning:_ Create a new file")
            return
        if self.road_network_toolbox_ui.selected_traffic_light.currentText() not in ["", "None"]:
            selected_traffic_light_id = int(
                self.road_network_toolbox_ui.selected_traffic_light.currentText()
            )
        else:
            return

        self.scenario_model.remove_traffic_light(selected_traffic_light_id)
        self.road_network_controller.set_default_road_network_list_information()

    @logger.log
    def create_traffic_light_for_referenced_lanelets(self):
        if self.road_network_controller.mwindow.play_activated:
            self.road_network_controller.text_browser.append("Please stop the animation first.")
            return

        if not SUMO_AVAILABLE:
            self.road_network_controller.text_browser.append("SUMO is not installed correctly!")
            return
        lanelet_ids = [
            int(lanelet_id)
            for lanelet_id in self.road_network_toolbox_ui.referenced_lanelets_traffic_light.get_checked_items()
        ]
        if not lanelet_ids:
            return
        self.road_network_toolbox_ui.referenced_lanelets_traffic_light.clear()
        converter = CR2SumoMapConverter(
            self.scenario_model.get_current_scenario(),
            SumoConfig.from_scenario(self.scenario_model.get_current_scenario()),
        )
        converter.create_sumo_files(self.road_network_controller.tmp_folder)
        oks = []
        dt = self.scenario_model.get_current_scenario().dt
        offset = int(self.road_network_toolbox_ui.time_offset.text())
        red = int(self.road_network_toolbox_ui.time_red.text())
        red_yellow = int(self.road_network_toolbox_ui.time_red_yellow.text())
        green = int(self.road_network_toolbox_ui.time_green.text())
        yellow = int(self.road_network_toolbox_ui.time_yellow.text())
        total = red + red_yellow + green + yellow

        for lanelet_id in lanelet_ids:
            try:
                ok = converter.auto_generate_traffic_light_system(
                    lanelet_id,
                    green_time=int(green * dt),
                    yellow_time=int(yellow * dt),
                    all_red_time=0,
                    left_green_time=math.ceil(0.06 * total * dt),
                    crossing_min_time=math.ceil(0.1 * total * dt),
                    crossing_clearance_time=math.ceil(0.15 * total * dt),
                    time_offset=int(offset * dt),
                )
            except Exception:
                ok = False
            oks.append(ok)
            self.road_network_controller.text_browser.append(
                ("Created" if ok else "ERROR: Could not create")
                + f" traffic light system for lanelet {lanelet_id}"
            )

        if any(oks):
            self.scenario_model.create_traffic_lights_for_referenced_lanelets(
                converter.lanelet_network
            )
