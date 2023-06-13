from PyQt5.QtGui import *
from PyQt5.QtCore import *
from crdesigner.ui.gui.mwindow.toolboxes.converter_toolbox.map_converter_toolbox import MapConversionToolbox
from crdesigner.ui.gui.mwindow.toolboxes.service_layer.general_services import toolbox_callback


def create_converter_toolbox(mwindow):
    """ Create the map converter toolbar_wrapper."""
    mwindow.map_converter_toolbox = MapConversionToolbox(mwindow.animated_viewer_wrapper.cr_viewer.current_scenario,
                                                         lambda scenario: toolbox_callback(mwindow, scenario, True),
                                                         mwindow.crdesigner_console_wrapper.text_browser,
                                                         mwindow.obstacle_toolbox.sumo_simulation, mwindow)
    mwindow.addDockWidget(Qt.RightDockWidgetArea, mwindow.map_converter_toolbox)
    return mwindow.map_converter_toolbox  # for visibility
