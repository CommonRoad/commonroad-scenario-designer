"""Wrapper for the middle visualization."""

from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.commonroad_viewer import AnimatedViewer
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from typing import Union
from commonroad.scenario.lanelet import Lanelet
from commonroad.scenario.obstacle import Obstacle
from crdesigner.ui.gui.mwindow.toolboxes.toolbox_ui import PosB
from PyQt5.QtWidgets import *


class AnimatedViewerWrapper:

    def __init__(self, mwindow):
        self.cr_viewer = AnimatedViewer(mwindow, self.viewer_callback)

        # handle to the toolboxes and the console for the viewer callback
        self.viewer_dock = None
        self.mwindow = mwindow  # handle back to the main window

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

    def viewer_callback(self, selected_object: Union[Lanelet, Obstacle], output: str, temporary_positions = None):
        """
        Callback when the user clicks a lanelet, an obstacle or a position inside the scenario visualization.
        @return: returns draw_temporary_position which indicates whether temporary position should be drawn afterwards
        """
        draw_temporary_position = False
        if isinstance(selected_object, Lanelet):
            self.mwindow.road_network_toolbox.road_network_toolbox_ui.selected_lanelet_two.setCurrentText(
                    self.mwindow.road_network_toolbox.road_network_toolbox_ui.selected_lanelet_one.currentText())
            self.mwindow.road_network_toolbox.road_network_toolbox_ui.selected_lanelet_one.setCurrentText(
                    str(selected_object.lanelet_id))
            self.mwindow.road_network_toolbox.road_network_toolbox_ui.selected_lanelet_update.setCurrentText(
                    str(selected_object.lanelet_id))
        elif isinstance(selected_object, Obstacle):
            self.mwindow.obstacle_toolbox.obstacle_toolbox_ui.selected_obstacle.setCurrentText(
                    str(selected_object.obstacle_id))
        elif isinstance(selected_object, PosB):
            for button in self.mwindow.road_network_toolbox.road_network_toolbox_ui.position_buttons:
                if button.button_pressed:
                    temporary_positions[id(button)] = (float(selected_object.x_position),
                                                       float(selected_object.y_position))
                    button.button_release()
                    button.x_position.setText(selected_object.x_position)
                    button.y_position.setText(selected_object.y_position)
                    draw_temporary_position = True
            for button in self.mwindow.obstacle_toolbox.obstacle_toolbox_ui.position_buttons:
                if button.button_pressed:
                    temporary_positions[str(id(button))] = (float(selected_object.x_position),
                                                            float(selected_object.y_position))
                    button.button_release()
                    button.x_position.setText(selected_object.x_position)
                    button.y_position.setText(selected_object.y_position)
                    draw_temporary_position = True

        if output != "":
            self.mwindow.crdesigner_console_wrapper.text_browser.append(output)

        return draw_temporary_position

    def update_view(self, new_file_added: bool = None, focus_on_network=None):
        """
        Update all components.  
        :param new_file_added: if a new cr file was created or added
        """
        # reset selection of all other selectable elements
        if self.cr_viewer.current_scenario is None:
            return
        self.cr_viewer.update_plot(new_file_added=new_file_added)

    def update_window(self):
        self.toolbar.setStyleSheet('background-color:' + self.mwindow.colorscheme().background +
                                   '; color:' + self.mwindow.colorscheme().color + '; font-size:' +
                                   self.mwindow.colorscheme().font_size)
        self.cr_viewer.update_window()


