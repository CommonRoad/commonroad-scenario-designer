from commonroad.scenario.traffic_light import TrafficLightState

from crdesigner.common.logging import logger
from crdesigner.ui.gui.model.scenario_model import ScenarioModel
from crdesigner.ui.gui.view.toolboxes.road_network_toolbox.road_network_toolbox_ui.road_network_toolbox_ui import (
    RoadNetworkToolboxUI,
)


class AddTrafficLightsUI:
    def __init__(
        self, scenario_model: ScenarioModel, road_network_toolbox_ui: RoadNetworkToolboxUI
    ):
        self.road_network_toolbox_ui = road_network_toolbox_ui
        self.scenario_model = scenario_model

    @logger.log
    def update_traffic_light_information(self):
        """
        Updates information of traffic light widget based on traffic light ID selected by the user.
        """
        if self.road_network_toolbox_ui.selected_traffic_light.currentText() not in ["", "None"]:
            selected_traffic_light_id = int(
                self.road_network_toolbox_ui.selected_traffic_light.currentText()
            )
            traffic_light = self.scenario_model.find_traffic_light_by_id(selected_traffic_light_id)

            self.road_network_toolbox_ui.x_position_traffic_light.setText(
                str(traffic_light.position[0])
            )
            self.road_network_toolbox_ui.y_position_traffic_light.setText(
                str(traffic_light.position[1])
            )
            self.road_network_toolbox_ui.time_offset.setText(
                str(traffic_light.traffic_light_cycle.time_offset)
            )
            self.road_network_toolbox_ui.traffic_light_active.setChecked(True)

            cycle_order = ""
            for elem in traffic_light.traffic_light_cycle.cycle_elements:
                if elem.state is TrafficLightState.RED:
                    cycle_order += "r-"
                    self.road_network_toolbox_ui.time_red.setText(str(elem.duration))
                if elem.state is TrafficLightState.GREEN:
                    cycle_order += "g-"
                    self.road_network_toolbox_ui.time_green.setText(str(elem.duration))
                if elem.state is TrafficLightState.YELLOW:
                    cycle_order += "y-"
                    self.road_network_toolbox_ui.time_yellow.setText(str(elem.duration))
                if elem.state is TrafficLightState.RED_YELLOW:
                    cycle_order += "ry-"
                    self.road_network_toolbox_ui.time_red_yellow.setText(str(elem.duration))
                if elem.state is TrafficLightState.INACTIVE:
                    cycle_order += "in-"
                    self.road_network_toolbox_ui.time_inactive.setText(str(elem.duration))
            cycle_order = cycle_order[:-1]
            self.road_network_toolbox_ui.traffic_light_cycle_order.setCurrentText(cycle_order)

            self.road_network_toolbox_ui.traffic_light_directions.setCurrentText(
                str(traffic_light.direction.value)
            )

            referenced_lanelets = [
                str(la.lanelet_id)
                for la in self.scenario_model.get_lanelets()
                if selected_traffic_light_id in la.traffic_lights
            ]
            self.road_network_toolbox_ui.referenced_lanelets_traffic_light.set_checked_items(
                referenced_lanelets
            )

    def set_default_traffic_lights_information(self):
        self.road_network_toolbox_ui.referenced_lanelets_traffic_light.clear()
        self.road_network_toolbox_ui.referenced_lanelets_traffic_light.addItems(
            ["None"] + [str(item) for item in self.scenario_model.collect_lanelet_ids()]
        )
        self.road_network_toolbox_ui.referenced_lanelets_traffic_light.setCurrentIndex(0)

        self.road_network_toolbox_ui.selected_traffic_light.clear()
        self.road_network_toolbox_ui.selected_traffic_light.addItems(
            ["None"] + [str(item) for item in self.scenario_model.collect_traffic_light_ids()]
        )
        self.road_network_toolbox_ui.selected_traffic_light.setCurrentIndex(0)

    def initialize_traffic_light_information(self):
        """
        Initializes traffic light GUI elements with traffic light information.
        """
        self.road_network_toolbox_ui.x_position_traffic_light.setText("0.0")
        self.road_network_toolbox_ui.y_position_traffic_light.setText("0.0")
        self.road_network_toolbox_ui.time_offset.setText("0")
        self.road_network_toolbox_ui.time_red.setText("120")
        self.road_network_toolbox_ui.time_red_yellow.setText("15")
        self.road_network_toolbox_ui.time_yellow.setText("70")
        self.road_network_toolbox_ui.time_green.setText("380")
        self.road_network_toolbox_ui.time_inactive.setText("0")
        self.road_network_toolbox_ui.traffic_light_active.setChecked(True)
