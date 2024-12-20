"""Wrapper for the middle visualization."""

from typing import Union

from commonroad.scenario.lanelet import Lanelet
from commonroad.scenario.obstacle import Obstacle
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from crdesigner.common.logging import logger
from crdesigner.ui.gui.controller.animated_viewer.animated_viewer_controller import (
    AnimatedViewerController,
)
from crdesigner.ui.gui.model.scenario_model import ScenarioModel
from crdesigner.ui.gui.utilities.toolbox_ui import PosB


class AnimatedViewerWrapperController:
    def __init__(self, mwindow, scenario_model: ScenarioModel, scenario_saving_dialog):
        self.scenario_model = scenario_model
        self.scenario_model.subscribe(self.update_scenario)
        self.pps_model = mwindow.pps_model
        self.pps_model.subscribe(self.update_scenario)

        self.cr_viewer = AnimatedViewerController(
            mwindow, self.viewer_callback, self.scenario_model
        )
        self.scenario_saving_dialog = scenario_saving_dialog

        # handle to the toolboxes and the console for the viewer callback
        self.viewer_dock = None
        self.mwindow = mwindow.mwindow_ui  # handle back to the main window

    def update_scenario(self):
        """
        Notifies the GUI that the sceanrio has changed.

        @param new_file_added: Indikator if the added file is a complete new scenario
        """

        self.cr_viewer.open_scenario(new_file_added=self.scenario_model.is_new_file_added())
        self.update_view()
        self.mwindow.update_max_step()
        # Autosave
        self.scenario_saving_dialog.autosave(self.scenario_model.get_current_scenario())

    def create_viewer_dock(self):
        """
        Create the viewer dock. (The matplotlib visualization in the middle).
        IMPORTANT: has to be called AFTER the toolboxes - otherwise the mwindow.setCentralWidget destroys the references
        """
        self.viewer_dock = QWidget(self.mwindow)
        self.toolbar = NavigationToolbar(self.cr_viewer.dynamic, self.viewer_dock)
        self.update_window()
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.cr_viewer.dynamic)

        self.viewer_dock.setLayout(layout)
        self.mwindow.setCentralWidget(self.viewer_dock)

    @logger.log
    def viewer_callback(
        self, selected_object: Union[Lanelet, Obstacle], output: str, temporary_positions=None
    ):
        """
        Callback when the user clicks a lanelet, an obstacle or a position inside the scenario visualization.
        @return: returns draw_temporary_position which indicates whether temporary position should be drawn afterwards
        """
        draw_temporary_position = False
        if isinstance(selected_object, Lanelet):
            self.mwindow.road_network_toolbox.road_network_toolbox_ui.selected_lanelet_two.setCurrentText(
                self.mwindow.road_network_toolbox.road_network_toolbox_ui.selected_lanelet_one.currentText()
            )
            self.mwindow.road_network_toolbox.road_network_toolbox_ui.selected_lanelet_one.setCurrentText(
                str(selected_object.lanelet_id)
            )
            self.mwindow.road_network_toolbox.road_network_toolbox_ui.selected_lanelet_update.setCurrentText(
                str(selected_object.lanelet_id)
            )
        elif isinstance(selected_object, Obstacle):
            self.mwindow.obstacle_toolbox.obstacle_toolbox_ui.selected_obstacle.setCurrentText(
                str(selected_object.obstacle_id)
            )
        elif isinstance(selected_object, PosB):
            for (
                button
            ) in self.mwindow.road_network_toolbox.road_network_toolbox_ui.position_buttons:
                if button.button_pressed:
                    temporary_positions[id(button)] = (
                        float(selected_object.x_position),
                        float(selected_object.y_position),
                    )
                    button.button_release()
                    button.x_position.setText(selected_object.x_position)
                    button.y_position.setText(selected_object.y_position)
                    draw_temporary_position = True
            for button in self.mwindow.obstacle_toolbox.obstacle_toolbox_ui.position_buttons:
                if button.button_pressed:
                    temporary_positions[str(id(button))] = (
                        float(selected_object.x_position),
                        float(selected_object.y_position),
                    )
                    button.button_release()
                    button.x_position.setText(selected_object.x_position)
                    button.y_position.setText(selected_object.y_position)
                    draw_temporary_position = True

        if output != "":
            self.mwindow.crdesigner_console_wrapper.text_browser.append(output)

        return draw_temporary_position

    def update_view(self):
        """
        Update all components.
        """
        # reset selection of all other selectable elements
        if not self.scenario_model.scenario_created():
            return
        self.cr_viewer.update_plot()

    def update_window(self):
        self.toolbar.setStyleSheet(
            "background-color:"
            + self.mwindow.colorscheme().background
            + "; color:"
            + self.mwindow.colorscheme().color
            + "; font-size:"
            + self.mwindow.colorscheme().font_size
        )
        self.cr_viewer.update_window()
