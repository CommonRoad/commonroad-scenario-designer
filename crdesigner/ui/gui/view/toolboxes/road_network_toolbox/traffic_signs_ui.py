from commonroad.scenario.traffic_sign import (
    SupportedTrafficSignCountry,
    TrafficSignIDCountries,
)
from PyQt6.QtWidgets import QComboBox, QTableWidgetItem

from crdesigner.common.logging import logger
from crdesigner.ui.gui.model.scenario_model import ScenarioModel
from crdesigner.ui.gui.view.toolboxes.road_network_toolbox.road_network_toolbox_ui.road_network_toolbox_ui import (
    RoadNetworkToolboxUI,
)


class AddTrafficSignUI:
    def __init__(
        self, scenario_model: ScenarioModel, road_network_toolbox_ui: RoadNetworkToolboxUI
    ):
        self.road_network_toolbox_ui = road_network_toolbox_ui
        self.scenario_model = scenario_model

    @logger.log
    def update_traffic_sign_information(self, text_browser):
        """
        Updates information of traffic sign widget based on traffic sign ID selected by the user.
        """
        if self.road_network_toolbox_ui.selected_traffic_sign.currentText() not in ["", "None"]:
            country_signs = globals()[
                "TrafficSignID"
                + SupportedTrafficSignCountry(
                    self.scenario_model.get_country_id()
                ).name.capitalize()
            ]
            selected_traffic_sign_id = int(
                self.road_network_toolbox_ui.selected_traffic_sign.currentText()
            )
            traffic_sign = self.scenario_model.find_traffic_sign_by_id(selected_traffic_sign_id)
            referenced_lanelets = [
                str(la.lanelet_id)
                for la in self.scenario_model.get_lanelets()
                if selected_traffic_sign_id in la.traffic_signs
            ]
            self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.set_checked_items(
                referenced_lanelets
            )

            self.road_network_toolbox_ui.traffic_sign_virtual_selection.setChecked(
                traffic_sign.virtual
            )
            self.road_network_toolbox_ui.x_position_traffic_sign.setText(
                str(traffic_sign.position[0])
            )
            self.road_network_toolbox_ui.y_position_traffic_sign.setText(
                str(traffic_sign.position[1])
            )
            self.road_network_toolbox_ui.traffic_sign_element_table.setRowCount(0)
            for elem in traffic_sign.traffic_sign_elements:
                self.add_traffic_sign_element(text_browser)
                num_rows = self.road_network_toolbox_ui.traffic_sign_element_table.rowCount()
                self.road_network_toolbox_ui.traffic_sign_element_table.cellWidget(
                    num_rows - 1, 0
                ).setCurrentText(country_signs(elem.traffic_sign_element_id).name)
                if len(elem.additional_values) > 0:
                    self.road_network_toolbox_ui.traffic_sign_element_table.setItem(
                        num_rows - 1, 1, QTableWidgetItem(str(elem.additional_values[0]))
                    )
                else:
                    self.road_network_toolbox_ui.traffic_sign_element_table.setItem(
                        num_rows - 1, 1, QTableWidgetItem("")
                    )
        else:
            self.road_network_toolbox_ui.traffic_sign_virtual_selection.setChecked(False)
            self.road_network_toolbox_ui.x_position_traffic_sign.setText("0.0")
            self.road_network_toolbox_ui.y_position_traffic_sign.setText("0.0")
            self.road_network_toolbox_ui.traffic_sign_element_table.setRowCount(0)

    def set_default_traffic_sign_information(self):
        self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.clear()
        self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.addItems(
            ["None"] + [str(item) for item in self.scenario_model.collect_lanelet_ids()]
        )
        self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.setCurrentIndex(0)

        self.road_network_toolbox_ui.selected_traffic_sign.clear()
        self.road_network_toolbox_ui.selected_traffic_sign.addItems(
            ["None"] + [str(item) for item in self.scenario_model.collect_traffic_sign_ids()]
        )
        self.road_network_toolbox_ui.selected_traffic_sign.setCurrentIndex(0)

    def initialize_traffic_sign_information(self):
        """
        Initializes traffic sign GUI elements with traffic sign information.
        """
        self.road_network_toolbox_ui.x_position_traffic_sign.setText("0.0")
        self.road_network_toolbox_ui.y_position_traffic_sign.setText("0.0")

    @logger.log
    def add_traffic_sign_element(self, text_browser):
        """
        Adds traffic sign element to traffic sign.
        Only a default entry is created the user has to specify the traffic sign ID manually afterward.
        """
        if not self.scenario_model.scenario_created():
            text_browser.append("_Warning:_ Create a new file")
            return
        num_rows = self.road_network_toolbox_ui.traffic_sign_element_table.rowCount()
        self.road_network_toolbox_ui.traffic_sign_element_table.insertRow(num_rows)
        combo_box = QComboBox()
        combo_box.addItems(
            [elem.name for elem in TrafficSignIDCountries[self.scenario_model.get_country_id()]]
        )
        self.road_network_toolbox_ui.traffic_sign_element_table.setCellWidget(
            num_rows, 0, combo_box
        )
