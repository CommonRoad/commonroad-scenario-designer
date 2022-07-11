from crdesigner.ui.gui.mwindow.toolboxes.road_network_toolbox.road_network_toolbox import RoadNetworkToolbox
from crdesigner.ui.gui.mwindow.toolboxes.service_layer.general_services import toolbox_callback
from PyQt5.QtGui import *
from PyQt5.QtCore import *


def create_road_network_toolbox(mwindow):
    """ Create the Road network toolbar_wrapper."""
    mwindow.road_network_toolbox = RoadNetworkToolbox(
            current_scenario=mwindow.animated_viewer_wrapper.cr_viewer.current_scenario,
            text_browser=mwindow.crdesigner_console_wrapper.text_browser,
            callback=lambda scenario: toolbox_callback(mwindow, scenario), tmp_folder=mwindow.tmp_folder,
            selection_changed_callback=mwindow.animated_viewer_wrapper.cr_viewer.update_plot, mwindow=mwindow)
    mwindow.addDockWidget(Qt.LeftDockWidgetArea, mwindow.road_network_toolbox)
    return mwindow.road_network_toolbox  # for visibility
