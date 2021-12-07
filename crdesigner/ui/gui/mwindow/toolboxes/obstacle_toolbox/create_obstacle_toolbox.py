from crdesigner.ui.gui.mwindow.toolboxes.obstacle_toolbox.obstacle_toolbox import ObstacleToolbox
from crdesigner.ui.gui.mwindow.toolboxes.service_layer.general_services import toolbox_callback
from PyQt5.QtGui import *
from PyQt5.QtCore import *


def create_obstacle_toolbox(mwindow):
    """ Create the obstacle toolbar_wrapper."""
    mwindow.obstacle_toolbox = ObstacleToolbox(mwindow.animated_viewer_wrapper.cr_viewer.current_scenario, lambda scenario: toolbox_callback(mwindow, scenario), mwindow.tmp_folder)
    mwindow.addDockWidget(Qt.RightDockWidgetArea, mwindow.obstacle_toolbox)
    return mwindow.obstacle_toolbox
