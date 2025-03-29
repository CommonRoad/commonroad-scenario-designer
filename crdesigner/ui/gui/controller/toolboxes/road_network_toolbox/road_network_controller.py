from typing import Union

from commonroad.scenario.lanelet import Lanelet
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import QDockWidget

from crdesigner.common.config.osm_config import osm_config as config
from crdesigner.ui.gui.controller.toolboxes.road_network_toolbox.aerial_image_controller import (
    AddAerialImageController,
)
from crdesigner.ui.gui.controller.toolboxes.road_network_toolbox.intersections_controller import (
    AddIntersectionController,
)
from crdesigner.ui.gui.controller.toolboxes.road_network_toolbox.lanelet_controller import (
    AddLaneletController,
)
from crdesigner.ui.gui.controller.toolboxes.road_network_toolbox.traffic_lights_controller import (
    AddTrafficLightsController,
)
from crdesigner.ui.gui.controller.toolboxes.road_network_toolbox.traffic_signs_controller import (
    AddTrafficSignController,
)
from crdesigner.ui.gui.model.scenario_model import ScenarioModel
from crdesigner.ui.gui.utilities.waitingspinnerwidget import QtWaitingSpinner
from crdesigner.ui.gui.view.toolboxes.road_network_toolbox.road_network_toolbox_ui.road_network_toolbox_ui import (
    RoadNetworkToolboxUI,
)


class RoadNetworkController(
    QDockWidget,
):
    def __init__(self, mwindow):
        super().__init__("Road Network Toolbox")
        self.scenario_model = mwindow.scenario_model
        self.road_network_toolbox_ui = RoadNetworkToolboxUI(mwindow)
        self.adjust_ui()
        self.mwindow = mwindow
        self.text_browser = mwindow.crdesigner_console_wrapper.text_browser
        self.last_added_lanelet_id = None
        self.tmp_folder = mwindow.tmp_folder
        self.selection_changed_callback = mwindow.animated_viewer_wrapper.cr_viewer.update_plot
        self.initialized = False
        self.update = False
        self.updated_lanelet = False
        self.aerial_map_threshold = config.AERIAL_IMAGE_THRESHOLD

        self.lanelet_controller = AddLaneletController(
            self, self.scenario_model, self.road_network_toolbox_ui
        )
        self.traffic_sign_controller = AddTrafficSignController(
            self, self.scenario_model, self.road_network_toolbox_ui
        )
        self.traffic_lights_controller = AddTrafficLightsController(
            self, self.scenario_model, self.road_network_toolbox_ui
        )
        self.intersection_controller = AddIntersectionController(
            self, self.scenario_model, self.road_network_toolbox_ui
        )
        self.aerial_image_controller = AddAerialImageController(
            self, self.scenario_model, self.road_network_toolbox_ui
        )

        self.traffic_sign_controller.traffic_sign_ui.initialize_traffic_sign_information()
        self.traffic_lights_controller.traffic_lights_ui.initialize_traffic_light_information()
        self.intersection_controller.intersection_ui.initialize_intersection_information()
        self.set_default_road_network_list_information()

        self.connect_gui_elements()

    def adjust_ui(self):
        """Updates GUI properties like width, etc."""
        self.setFloating(True)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setWidget(self.road_network_toolbox_ui)
        self.road_network_toolbox_ui.setMinimumWidth(375)

    def connect_gui_elements(self):
        self.initialized = False
        self.lanelet_controller.connect_gui_lanelet()
        self.traffic_sign_controller.connect_gui_traffic_signs()
        self.traffic_lights_controller.connect_gui_traffic_lights()
        self.intersection_controller.connect_gui_intersection()
        self.aerial_image_controller.connect_gui_aerial_image()

    def refresh_toolbox(self, model: ScenarioModel):
        self.scenario_model = model
        self.set_default_road_network_list_information()

    def set_default_road_network_list_information(self):
        self.update = True

        self.lanelet_controller.lanelet_ui.set_default_lanelet_information()
        self.traffic_sign_controller.traffic_sign_ui.set_default_traffic_sign_information()
        self.traffic_lights_controller.traffic_lights_ui.set_default_traffic_lights_information()
        self.intersection_controller.intersection_ui.set_default_intersection_information()

        self.update = False

    def initialize_road_network_toolbox(self):
        self.traffic_sign_controller.traffic_sign_ui.initialize_traffic_sign_information()
        self.traffic_lights_controller.traffic_lights_ui.initialize_traffic_light_information()
        self.intersection_controller.intersection_ui.initialize_intersection_information()
        self.set_default_road_network_list_information()
        self.initialized = True

    def get_float(self, str) -> float:
        """
        Validates number and replace , with . to be able to insert german floats

        @return: string argument as valid float if not empty or not - else standard value 5
        """
        if str.text() == "-":
            self.text_browser.append(
                "Inserted value of invalid. Standard value 5 will be used instead."
            )
        if str.text() and str.text() != "-":
            return float(str.text().replace(",", "."))
        else:
            return 5

    def selected_lanelet(self) -> Union[Lanelet, None]:
        return self.lanelet_controller.selected_lanelet()

    def disable_show_of_curved_lanelet(self, button_title: str = "") -> None:
        """
        If a section of the road network toolbox is pressed it is checked if the curved_lanelet should be shown

        :param button_title: Title of the section to differentiate which button is clicked
        """
        if (
            self.road_network_toolbox_ui.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.current_edited_lanelet_scenario
            is None
        ):
            return

        place_at_position = self.road_network_toolbox_ui.place_at_position.isChecked()
        connect_to_last_selection = (
            self.road_network_toolbox_ui.connect_to_previous_selection.isChecked()
        )
        connect_to_predecessors_selection = (
            self.road_network_toolbox_ui.connect_to_predecessors_selection.isChecked()
        )
        connect_to_successors_selection = (
            self.road_network_toolbox_ui.connect_to_successors_selection.isChecked()
        )
        if button_title == "Add Lanelet" and (
            place_at_position
            or connect_to_last_selection
            or connect_to_predecessors_selection
            or connect_to_successors_selection
        ):
            if self.road_network_toolbox_ui.curved_check_button is not None:
                self.road_network_toolbox_ui.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.display_curved_lanelet(
                    self.road_network_toolbox_ui.curved_check_button.button.isChecked(), True
                )

        elif (
            button_title == "Lanelet Attributes"
            and self.road_network_toolbox_ui.selected_curved_checkbox.button.isChecked()
            and self.road_network_toolbox_ui.selected_curved_checkbox.button.isEnabled()
        ):
            self.road_network_toolbox_ui.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.display_curved_lanelet(
                self.road_network_toolbox_ui.selected_curved_checkbox.button.isChecked(), False
            )

        elif (
            place_at_position
            or connect_to_last_selection
            or connect_to_predecessors_selection
            or connect_to_successors_selection
        ):
            if self.road_network_toolbox_ui.curved_check_button is not None:
                self.road_network_toolbox_ui.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.display_curved_lanelet(
                    False
                )
                self.road_network_toolbox_ui.curved_check_button.setChecked(False)
        else:
            self.road_network_toolbox_ui.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.display_curved_lanelet(
                False
            )
            self.road_network_toolbox_ui.selected_curved_checkbox.setChecked(False)

    @pyqtSlot(str)
    def stopSpinner(self, data):
        self.scenario_model.notify_all()
        self.road_network_toolbox_ui.Spinner.stop()

    def startSpinner(self, spinner: QtWaitingSpinner):
        if spinner.is_spinning():
            spinner.stop()
        spinner.start()
