"""Wrapper for the middle visualization."""
from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.commonroad_viewer import AnimatedViewer
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from typing import Union
from commonroad.scenario.lanelet import Lanelet
from commonroad.scenario.obstacle import Obstacle
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
        toolbar = NavigationToolbar(self.cr_viewer.dynamic, self.viewer_dock)
        layout = QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.cr_viewer.dynamic)
        self.viewer_dock.setLayout(layout)
        self.mwindow.setCentralWidget(self.viewer_dock)

    def viewer_callback(self, selected_object: Union[Lanelet, Obstacle], output: str):
        """Callback when the user clicks a lanelet inside the scenario visualization."""
        if isinstance(selected_object, Lanelet):
            self.mwindow.road_network_toolbox.road_network_toolbox.selected_lanelet_two.setCurrentText(
                    self.mwindow.road_network_toolbox.road_network_toolbox.selected_lanelet_one.currentText())
            self.mwindow.road_network_toolbox.road_network_toolbox.selected_lanelet_one.setCurrentText(
                    str(selected_object.lanelet_id))
            self.mwindow.road_network_toolbox.road_network_toolbox.selected_lanelet_update.setCurrentText(
                    str(selected_object.lanelet_id))
        elif isinstance(selected_object, Obstacle):
            self.mwindow.obstacle_toolbox.obstacle_toolbox.selected_obstacle.setCurrentText(str(selected_object.obstacle_id))
        if output != "":
            self.mwindow.crdesigner_console_wrapper.text_browser.append(output)

    def update_view(self, focus_on_network=None):
        """ Update all components. """
        # reset selection of all other selectable elements
        if self.cr_viewer.current_scenario is None:
            return
        if focus_on_network is None:
            focus_on_network = config.AUTOFOCUS
        self.cr_viewer.update_plot(focus_on_network=focus_on_network)
