from PyQt5 import Qt
from PyQt5.QtWidgets import QTableWidgetItem, QComboBox

from crdesigner.ui.gui.model.scenario_model import ScenarioModel
from crdesigner.ui.gui.view.toolboxes.road_network_toolbox.road_network_toolbox_ui.road_network_toolbox_ui import \
    RoadNetworkToolboxUI
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from commonroad.scenario.traffic_sign import *



class AddIntersectionUI:

    def __init__(self, scenario_model: ScenarioModel, road_network_toolbox_ui: RoadNetworkToolboxUI):
        self.road_network_toolbox_ui = road_network_toolbox_ui
        self.scenario_model = scenario_model

    # TODO: Nowhere used
    def update_incomings(self):
        """
        Updates incoming table information.
        """
        selected_intersection = self.scenario_model.find_intersection_by_id(
                int(self.road_network_toolbox_ui.selected_intersection.currentText()))
        for inc in selected_intersection.incomings:
            self.road_network_toolbox_ui.intersection_incomings_table.setItem(0, 0, inc.incoming_id)

    def remove_incoming(self):
        """
        Removes a row from the intersection incoming table.
        """
        num_rows = self.road_network_toolbox_ui.intersection_incomings_table.rowCount()
        self.road_network_toolbox_ui.intersection_incomings_table.removeRow(num_rows - 1)
        self.update_left_of_combobox()

    def update_left_of_combobox(self, incoming_ids: List[str] = None):
        """
        Collects all incoming IDs in incoming table and updates left of combobox

        @param incoming_ids: List of available incoming IDs.
        """
        if incoming_ids is None:
            incoming_ids = [self.road_network_toolbox_ui.intersection_incomings_table.item(row, 0).text() for row in
                            range(self.road_network_toolbox_ui.intersection_incomings_table.rowCount())]
        for row in range(self.road_network_toolbox_ui.intersection_incomings_table.rowCount()):
            combo_box_left_of = QComboBox()
            combo_box_left_of.addItems(incoming_ids)
            if row != self.road_network_toolbox_ui.intersection_incomings_table.rowCount() - 1:
                index = self.road_network_toolbox_ui.intersection_incomings_table.cellWidget(row, 5).findText(
                        self.road_network_toolbox_ui.intersection_incomings_table.cellWidget(row, 5).currentText(),
                        Qt.MatchFixedString)
            else:
                index = -1
            self.road_network_toolbox_ui.intersection_incomings_table.setCellWidget(row, 5, combo_box_left_of)
            if index >= 0:
                self.road_network_toolbox_ui.intersection_incomings_table.cellWidget(row, 5).setCurrentIndex(index)

    def set_default_intersection_information(self):
        self.road_network_toolbox_ui.selected_intersection.clear()
        self.road_network_toolbox_ui.selected_intersection.addItems(
                ["None"] + [str(item) for item in self.scenario_model.collect_intersection_ids()])
        self.road_network_toolbox_ui.selected_intersection.setCurrentIndex(0)

        self.road_network_toolbox_ui.intersection_crossings.clear()
        self.road_network_toolbox_ui.intersection_crossings.addItems(
                ["None"] + [str(item) for item in self.scenario_model.collect_lanelet_ids()])
        self.road_network_toolbox_ui.intersection_crossings.setCurrentIndex(0)

        self.road_network_toolbox_ui.intersection_lanelet_to_fit.clear()
        self.road_network_toolbox_ui.intersection_lanelet_to_fit.addItems(["None"] + [
            str(item) for item in self.scenario_model.collect_incoming_lanelet_ids_from_intersection(
                    self.road_network_toolbox_ui.selected_intersection.currentText())])
        self.road_network_toolbox_ui.intersection_lanelet_to_fit.setCurrentIndex(0)

        self.road_network_toolbox_ui.other_lanelet_to_fit.clear()
        self.road_network_toolbox_ui.other_lanelet_to_fit.addItems(
                ["None"] + [str(item) for item in self.scenario_model.collect_lanelet_ids()])
        self.road_network_toolbox_ui.other_lanelet_to_fit.setCurrentIndex(0)

        self.road_network_toolbox_ui.intersection_incomings_table.setRowCount(0)

    def initialize_intersection_information(self):
        """
        Initializes GUI elements with intersection information.
        """
        self.road_network_toolbox_ui.intersection_diameter.setText("10")
        self.road_network_toolbox_ui.intersection_lanelet_width.setText("3.0")
        self.road_network_toolbox_ui.intersection_incoming_length.setText("20")