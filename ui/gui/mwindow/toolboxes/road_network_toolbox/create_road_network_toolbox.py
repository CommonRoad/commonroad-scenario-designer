from crdesigner.input_output.gui.toolboxes.road_network_toolbox import RoadNetworkToolbox
from PyQt5.QtGui import *
from PyQt5.QtCore import *


def create_road_network_toolbox(mwindow):
    """ Create the Road network toolbar_wrapper."""
    mwindow.road_network_toolbox = RoadNetworkToolbox(current_scenario=mwindow.cr_viewer.current_scenario,
                                                   text_browser=mwindow.text_browser, callback=mwindow.toolbox_callback,
                                                   tmp_folder=mwindow.tmp_folder,
                                                   selection_changed_callback=mwindow.cr_viewer.update_plot)
    mwindow.addDockWidget(Qt.LeftDockWidgetArea, mwindow.road_network_toolbox)
    return mwindow.road_network_toolbox  # for visibility
