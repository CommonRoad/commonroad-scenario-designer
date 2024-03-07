from typing import List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QComboBox, QTableWidgetItem

from crdesigner.common.logging import logger
from crdesigner.ui.gui.model.scenario_model import ScenarioModel
from crdesigner.ui.gui.utilities.toolbox_ui import CheckableComboBox
from crdesigner.ui.gui.view.toolboxes.road_network_toolbox.road_network_toolbox_ui.road_network_toolbox_ui import (
    RoadNetworkToolboxUI,
)


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
            int(self.road_network_toolbox_ui.selected_intersection.currentText())
        )
        for inc in selected_intersection.incomings:
            self.road_network_toolbox_ui.intersection_incomings_table.setItem(0, 0, inc.incoming_id)

    @logger.log
    def remove_incoming(self):
        """
        Removes a row from the intersection incoming table.
        """
        num_rows = self.road_network_toolbox_ui.intersection_incomings_table.rowCount()
        self.road_network_toolbox_ui.intersection_incomings_table.removeRow(num_rows - 1)
        self.update_left_of_combobox()

    @logger.log
    def remove_outgoing(self):
        """
        Removes a row from the intersection outgoing table.
        """
        num_rows = self.road_network_toolbox_ui.intersection_outgoings_table.rowCount()
        self.road_network_toolbox_ui.intersection_outgoings_table.removeRow(num_rows - 1)

    @logger.log
    def remove_crossing(self):
        """
        Removes a row from the intersection crossing table.
        """
        num_rows = self.road_network_toolbox_ui.intersection_crossings_table.rowCount()
        self.road_network_toolbox_ui.intersection_crossings_table.removeRow(num_rows - 1)

    def update_left_of_combobox(self, incoming_ids: List[str] = None):
        """
        Collects all incoming IDs in incoming table and updates left of combobox

        @param incoming_ids: List of available incoming IDs.
        """
        if incoming_ids is None:
            incoming_ids = [
                self.road_network_toolbox_ui.intersection_incomings_table.item(row, 0).text()
                for row in range(self.road_network_toolbox_ui.intersection_incomings_table.rowCount())
            ]
        for row in range(self.road_network_toolbox_ui.intersection_incomings_table.rowCount()):
            combo_box_left_of = QComboBox()
            combo_box_left_of.addItems(incoming_ids)
            if row != self.road_network_toolbox_ui.intersection_incomings_table.rowCount() - 1:
                index = self.road_network_toolbox_ui.intersection_incomings_table.cellWidget(row, 5).findText(
                    self.road_network_toolbox_ui.intersection_incomings_table.cellWidget(row, 5).currentText(),
                    Qt.MatchFlag.MatchFixedString,
                )
            else:
                index = -1
            self.road_network_toolbox_ui.intersection_incomings_table.setCellWidget(row, 5, combo_box_left_of)
            if index >= 0:
                self.road_network_toolbox_ui.intersection_incomings_table.cellWidget(row, 5).setCurrentIndex(index)

    def set_default_intersection_information(self):
        self.road_network_toolbox_ui.selected_intersection.clear()
        self.road_network_toolbox_ui.selected_intersection.addItems(
            ["None"] + [str(item) for item in self.scenario_model.collect_intersection_ids()]
        )
        self.road_network_toolbox_ui.selected_intersection.setCurrentIndex(0)

        self.road_network_toolbox_ui.intersection_lanelet_to_fit.clear()
        self.road_network_toolbox_ui.intersection_lanelet_to_fit.addItems(
            ["None"]
            + [
                str(item)
                for item in self.scenario_model.collect_incoming_lanelet_ids_from_intersection(
                    self.road_network_toolbox_ui.selected_intersection.currentText()
                )
            ]
        )
        self.road_network_toolbox_ui.intersection_lanelet_to_fit.setCurrentIndex(0)

        self.road_network_toolbox_ui.other_lanelet_to_fit.clear()
        self.road_network_toolbox_ui.other_lanelet_to_fit.addItems(
            ["None"] + [str(item) for item in self.scenario_model.collect_lanelet_ids()]
        )
        self.road_network_toolbox_ui.other_lanelet_to_fit.setCurrentIndex(0)

        self.road_network_toolbox_ui.intersection_incomings_table.setRowCount(0)
        self.road_network_toolbox_ui.intersection_outgoings_table.setRowCount(0)
        self.road_network_toolbox_ui.intersection_crossings_table.setRowCount(0)

    def update_intersection_information(self):
        """
        Updates information of intersection widget based on intersection ID selected by the user.
        """
        if self.road_network_toolbox_ui.selected_intersection.currentText() not in ["", "None"]:
            selected_intersection_id = int(self.road_network_toolbox_ui.selected_intersection.currentText())
            intersection = self.scenario_model.find_intersection_by_id(selected_intersection_id)
            self.road_network_toolbox_ui.intersection_incomings_table.setRowCount(0)

            for incoming in intersection.incomings:
                self.add_incoming_to_table(False)
                num_rows = self.road_network_toolbox_ui.intersection_incomings_table.rowCount()
                self.road_network_toolbox_ui.intersection_incomings_table.setItem(
                    num_rows - 1, 0, QTableWidgetItem(str(incoming.incoming_id))
                )
                self.road_network_toolbox_ui.intersection_incomings_table.cellWidget(num_rows - 1, 1).set_checked_items(
                    [str(la_id) for la_id in incoming.incoming_lanelets]
                )
                self.road_network_toolbox_ui.intersection_incomings_table.cellWidget(num_rows - 1, 2).set_checked_items(
                    [str(la_id) for la_id in incoming.outgoing_left]
                )
                self.road_network_toolbox_ui.intersection_incomings_table.cellWidget(num_rows - 1, 3).set_checked_items(
                    [str(la_id) for la_id in incoming.outgoing_straight]
                )
                self.road_network_toolbox_ui.intersection_incomings_table.cellWidget(num_rows - 1, 4).set_checked_items(
                    [str(la_id) for la_id in incoming.outgoing_right]
                )

            for outgoing in intersection.outgoings:
                self.add_outgoing_to_table(False)
                num_rows = self.road_network_toolbox_ui.intersection_outgoings_table.rowCount()
                self.road_network_toolbox_ui.intersection_outgoings_table.setItem(
                    num_rows - 1, 0, QTableWidgetItem(str(outgoing.outgoing_id))
                )
                self.road_network_toolbox_ui.intersection_outgoings_table.cellWidget(num_rows - 1, 1).set_checked_items(
                    [str(la_id) for la_id in outgoing.outgoing_lanelets]
                )
                self.road_network_toolbox_ui.intersection_outgoings_table.cellWidget(num_rows - 1, 2).set_checked_items(
                    str(outgoing.incoming_group_id)
                )

            for crossing in intersection.crossings:
                self.add_crossing_to_table(False)
                num_rows = self.road_network_toolbox_ui.intersection_crossings_table.rowCount()
                self.road_network_toolbox_ui.intersection_crossings_table.setItem(
                    num_rows - 1, 0, QTableWidgetItem(str(crossing.crossing_id))
                )
                self.road_network_toolbox_ui.intersection_crossings_table.cellWidget(num_rows - 1, 1).set_checked_items(
                    [str(la_id) for la_id in crossing.crossing_lanelets]
                )
                self.road_network_toolbox_ui.intersection_crossings_table.cellWidget(num_rows - 1, 2).set_checked_items(
                    [str(inc_id) for inc_id in crossing.incoming_group_id]
                )
                self.road_network_toolbox_ui.intersection_crossings_table.cellWidget(num_rows - 1, 3).set_checked_items(
                    [str(inc_id) for inc_id in crossing.outgoing_group_id]
                )

            self.road_network_toolbox_ui.intersection_lanelet_to_fit.clear()
            current_text = self.road_network_toolbox_ui.selected_intersection.currentText()
            self.road_network_toolbox_ui.intersection_lanelet_to_fit.addItems(
                ["None"]
                + [
                    str(item)
                    for item in self.scenario_model.collect_incoming_lanelet_ids_from_intersection(current_text)
                ]
            )
            self.road_network_toolbox_ui.intersection_lanelet_to_fit.setCurrentIndex(0)

    @logger.log
    def add_incoming_to_table(self, new_incoming: bool = True):
        """
        Adds a row to the intersection incoming table.
        Only a default entry is created the user has to specify the incoming afterward manually.

        @param new_incoming: Boolean indicating whether this will be a new incoming or from a new intersection
        @param incoming_ids: List of available incoming IDs.
        """
        if not self.scenario_model.scenario_created():
            self.road_network_toolbox_ui.mwindow.text_browser.append("_Warning:_ Create a new file")
            return

        num_rows = self.road_network_toolbox_ui.intersection_incomings_table.rowCount()
        self.road_network_toolbox_ui.intersection_incomings_table.insertRow(num_rows)
        lanelet_ids = [str(la_id) for la_id in self.scenario_model.collect_lanelet_ids()]
        if new_incoming:
            self.road_network_toolbox_ui.intersection_incomings_table.setItem(
                num_rows, 0, QTableWidgetItem(str(self.scenario_model.generate_object_id()))
            )
        combo_box_lanelets = CheckableComboBox()
        combo_box_lanelets.addItems(lanelet_ids)
        self.road_network_toolbox_ui.intersection_incomings_table.setCellWidget(num_rows, 1, combo_box_lanelets)
        combo_box_successors_left = CheckableComboBox()
        combo_box_successors_left.addItems(lanelet_ids)
        self.road_network_toolbox_ui.intersection_incomings_table.setCellWidget(num_rows, 2, combo_box_successors_left)
        combo_box_successors_straight = CheckableComboBox()
        combo_box_successors_straight.addItems(lanelet_ids)
        self.road_network_toolbox_ui.intersection_incomings_table.setCellWidget(
            num_rows, 3, combo_box_successors_straight
        )
        combo_box_successors_right = CheckableComboBox()
        combo_box_successors_right.addItems(lanelet_ids)
        self.road_network_toolbox_ui.intersection_incomings_table.setCellWidget(num_rows, 4, combo_box_successors_right)

    @logger.log
    def add_outgoing_to_table(self, new_outgoing: bool = True):
        if not self.scenario_model.scenario_created():
            self.road_network_toolbox_ui.mwindow.text_browser.append("_Warning:_ Create a new file")
            return

        selected_intersection_id = int(self.road_network_toolbox_ui.selected_intersection.currentText())
        selected_intersection = self.scenario_model.find_intersection_by_id(selected_intersection_id)
        incoming_groups = selected_intersection.incomings
        incoming_group_ids = [str(incoming.incoming_id) for incoming in incoming_groups]
        num_rows = self.road_network_toolbox_ui.intersection_outgoings_table.rowCount()
        self.road_network_toolbox_ui.intersection_outgoings_table.insertRow(num_rows)
        lanelet_ids = [str(la_id) for la_id in self.scenario_model.collect_lanelet_ids()]
        if new_outgoing:
            self.road_network_toolbox_ui.intersection_outgoings_table.setItem(
                num_rows, 0, QTableWidgetItem(str(self.scenario_model.generate_object_id()))
            )

        combo_box_lanelets = CheckableComboBox()
        combo_box_lanelets.addItems(lanelet_ids)
        self.road_network_toolbox_ui.intersection_outgoings_table.setCellWidget(num_rows, 1, combo_box_lanelets)

        combo_box_incoming_group = CheckableComboBox()
        combo_box_incoming_group.addItems(incoming_group_ids)
        self.road_network_toolbox_ui.intersection_outgoings_table.setCellWidget(num_rows, 2, combo_box_incoming_group)

    @logger.log
    def add_crossing_to_table(self, new_crossing: bool = True):
        if not self.scenario_model.scenario_created():
            self.road_network_toolbox_ui.mwindow.text_browser.append("_Warning:_ Create a new file")
            return

        num_rows = self.road_network_toolbox_ui.intersection_crossings_table.rowCount()
        self.road_network_toolbox_ui.intersection_crossings_table.insertRow(num_rows)
        lanelet_ids = [str(la_id) for la_id in self.scenario_model.collect_lanelet_ids()]
        if new_crossing:
            self.road_network_toolbox_ui.intersection_crossings_table.setItem(
                num_rows, 0, QTableWidgetItem(str(self.scenario_model.generate_object_id()))
            )

        combo_box_lanelets = CheckableComboBox()
        combo_box_lanelets.addItems(lanelet_ids)
        self.road_network_toolbox_ui.intersection_crossings_table.setCellWidget(num_rows, 1, combo_box_lanelets)

        combo_box_incoming_group = CheckableComboBox()
        combo_box_incoming_group.addItems(lanelet_ids)
        self.road_network_toolbox_ui.intersection_crossings_table.setCellWidget(num_rows, 2, combo_box_incoming_group)

        combo_box_outgoing_group = CheckableComboBox()
        combo_box_outgoing_group.addItems(lanelet_ids)
        self.road_network_toolbox_ui.intersection_crossings_table.setCellWidget(num_rows, 3, combo_box_outgoing_group)

    def initialize_intersection_information(self):
        """
        Initializes GUI elements with intersection information.
        """
        self.road_network_toolbox_ui.intersection_diameter.setText("10")
        self.road_network_toolbox_ui.intersection_lanelet_width.setText("3.0")
        self.road_network_toolbox_ui.intersection_incoming_length.setText("20")
