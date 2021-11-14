from PyQt5.QtGui import *
from PyQt5.QtCore import *
from crdesigner.input_output.gui.toolboxes.map_converter_toolbox import MapConversionToolbox


def create_converter_toolbox(mwindow):
    """ Create the map converter toolbar."""
    mwindow.map_converter_toolbox = MapConversionToolbox(mwindow.cr_viewer.current_scenario, mwindow.toolbox_callback,
                                                      mwindow.text_browser, mwindow.obstacle_toolbox.sumo_simulation)
    mwindow.addDockWidget(Qt.RightDockWidgetArea, mwindow.map_converter_toolbox)
    return mwindow.map_converter_toolbox  # for visibility
