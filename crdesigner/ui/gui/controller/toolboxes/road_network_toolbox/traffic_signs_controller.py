import numpy as np
from commonroad.scenario.traffic_sign import (
    TrafficSign,
    TrafficSignElement,
    TrafficSignIDCountries,
)

from crdesigner.common.logging import logger
from crdesigner.ui.gui.model.scenario_model import ScenarioModel
from crdesigner.ui.gui.view.toolboxes.road_network_toolbox.road_network_toolbox_ui.road_network_toolbox_ui import (
    RoadNetworkToolboxUI,
)
from crdesigner.ui.gui.view.toolboxes.road_network_toolbox.traffic_signs_ui import (
    AddTrafficSignUI,
)


class AddTrafficSignController:
    def __init__(
        self,
        road_network_controller,
        scenario_model: ScenarioModel,
        road_network_toolbox_ui: RoadNetworkToolboxUI,
    ):
        self.scenario_model = scenario_model
        self.road_network_toolbox_ui = road_network_toolbox_ui
        self.road_network_controller = road_network_controller
        self.traffic_sign_ui = AddTrafficSignUI(self.scenario_model, self.road_network_toolbox_ui)

    def connect_gui_traffic_signs(self):
        self.road_network_toolbox_ui.button_add_traffic_sign_element.clicked.connect(
            lambda: self.traffic_sign_ui.add_traffic_sign_element(
                self.road_network_controller.text_browser
            )
        )
        self.road_network_toolbox_ui.button_remove_traffic_sign_element.clicked.connect(
            lambda: self.remove_traffic_sign_element()
        )
        self.road_network_toolbox_ui.button_add_traffic_sign.clicked.connect(
            lambda: self.add_traffic_sign()
        )
        self.road_network_toolbox_ui.button_remove_traffic_sign.clicked.connect(
            lambda: self.remove_traffic_sign()
        )
        self.road_network_toolbox_ui.button_update_traffic_sign.clicked.connect(
            lambda: self.update_traffic_sign()
        )
        self.road_network_toolbox_ui.selected_traffic_sign.currentTextChanged.connect(
            lambda: self.traffic_sign_ui.update_traffic_sign_information(
                self.road_network_controller.text_browser
            )
        )

    @logger.log
    def remove_traffic_sign_element(self):
        """
        Removes last entry in traffic sign element table of a traffic sign.
        """
        if self.road_network_controller.mwindow.play_activated:
            self.road_network_controller.text_browser.append("Please stop the animation first.")
            return

        num_rows = self.road_network_toolbox_ui.traffic_sign_element_table.rowCount()
        self.road_network_toolbox_ui.traffic_sign_element_table.removeRow(num_rows - 1)

    @logger.log
    def add_traffic_sign(self, traffic_sign_id: int = None):
        """
        Adds a traffic sign to a CommonRoad scenario.

        @param traffic_sign_id: Id which the new traffic sign should have.
        """
        if self.road_network_controller.mwindow.play_activated:
            self.road_network_controller.text_browser.append("Please stop the animation first.")
            return

        if not self.scenario_model.scenario_created():
            self.road_network_controller.text_browser.append("_Warning:_ Create a new file")
            return  # Check if list is empty -> Warning
        if (
            len(self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.get_checked_items())
            == 0
        ):
            self.road_network_controller.text_browser.append("_Warning:_ Add Referenced Lanelets")
            return
        # Check if only 'None' is selected - if yes -> Warning
        if (
            "None"
            in self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.get_checked_items()
            and len(
                self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.get_checked_items()
            )
            == 1
        ):
            self.road_network_controller.text_browser.append("_Warning:_ Add Referenced Lanelets")
            return
        # Check if 'None' is and other items are selected -> Uncheck 'None'
        elif (
            "None"
            in self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.get_checked_items()
        ):
            self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.uncheck_items("None")

        traffic_sign_elements = []
        referenced_lanelets = {
            int(la)
            for la in self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.get_checked_items()
        }
        first_occurrence = set()  # TODO compute first occurrence
        virtual = self.road_network_toolbox_ui.traffic_sign_virtual_selection.isChecked()
        if self.road_network_toolbox_ui.x_position_traffic_sign.text():
            x_position = self.road_network_controller.get_float(
                self.road_network_toolbox_ui.x_position_traffic_sign
            )
        else:
            x_position = 0
        if self.road_network_toolbox_ui.y_position_traffic_sign.text():
            y_position = self.road_network_controller.get_float(
                self.road_network_toolbox_ui.y_position_traffic_sign
            )
        else:
            y_position = 0
        for row in range(self.road_network_toolbox_ui.traffic_sign_element_table.rowCount()):
            sign_id = self.road_network_toolbox_ui.traffic_sign_element_table.cellWidget(
                row, 0
            ).currentText()
            if self.road_network_toolbox_ui.traffic_sign_element_table.item(row, 1) is None:
                additional_value = []
            else:
                additional_value = [
                    self.road_network_toolbox_ui.traffic_sign_element_table.item(row, 1).text()
                ]
            traffic_sign_elements.append(
                TrafficSignElement(
                    TrafficSignIDCountries[self.scenario_model.get_country_id()][sign_id],
                    additional_value,
                )
            )

        if len(traffic_sign_elements) == 0:
            self.road_network_controller.text_browser.append(
                "_Warning:_ No traffic sign element added."
            )
            return
        traffic_sign_id = (
            traffic_sign_id
            if traffic_sign_id is not None
            else self.scenario_model.generate_object_id()
        )
        new_sign = TrafficSign(
            traffic_sign_id,
            traffic_sign_elements,
            first_occurrence,
            np.array([x_position, y_position]),
            virtual,
        )

        self.scenario_model.add_traffic_sign(new_sign, referenced_lanelets)
        self.road_network_controller.set_default_road_network_list_information()

    @logger.log
    def remove_traffic_sign(self):
        """
        Removes selected traffic sign from scenario.
        """
        if self.road_network_controller.mwindow.play_activated:
            self.road_network_controller.text_browser.append("Please stop the animation first.")
            return

        if not self.scenario_model.scenario_created():
            self.road_network_controller.text_browser.append("_Warning:_ Create a new file")
            return
        if self.road_network_toolbox_ui.selected_traffic_sign.currentText() not in ["", "None"]:
            selected_traffic_sign_id = int(
                self.road_network_toolbox_ui.selected_traffic_sign.currentText()
            )
        else:
            return

        self.scenario_model.remove_traffic_sign(selected_traffic_sign_id)
        self.road_network_controller.set_default_road_network_list_information()

    @logger.log
    def update_traffic_sign(self):
        """
        Updates information of selected traffic sign.
        """
        if self.road_network_controller.mwindow.play_activated:
            self.road_network_controller.text_browser.append("Please stop the animation first.")
            return

        if not self.scenario_model.scenario_created():
            self.road_network_controller.text_browser.append("_Warning:_ Create a new file")
            return
        if (
            len(self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.get_checked_items())
            == 0
        ):
            self.road_network_controller.text_browser.append("_Warning:_ Add Referenced Lanelets")
            return
        # Check if only 'None' is selected - if yes -> Warning
        if (
            "None"
            in self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.get_checked_items()
            and len(
                self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.get_checked_items()
            )
            == 1
        ):
            self.road_network_controller.text_browser.append("_Warning:_ Add Referenced Lanelets")
            return
        # Check if 'None' is and other items are selected -> Uncheck 'None'
        elif (
            "None"
            in self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.get_checked_items()
        ):
            self.road_network_toolbox_ui.referenced_lanelets_traffic_sign.uncheck_items("None")
        if self.road_network_toolbox_ui.selected_traffic_sign.currentText() not in ["", "None"]:
            selected_traffic_sign_id = int(
                self.road_network_toolbox_ui.selected_traffic_sign.currentText()
            )
        else:
            return

        self.scenario_model.update_traffic_sign(selected_traffic_sign_id)
        self.add_traffic_sign(selected_traffic_sign_id)
