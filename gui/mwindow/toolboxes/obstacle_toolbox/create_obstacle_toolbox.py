from crdesigner.input_output.gui.toolboxes.obstacle_toolbox import ObstacleToolbox
from PyQt5.QtGui import *
from PyQt5.QtCore import *


def create_obstacle_toolbox(mwindow):
    """ Create the obstacle toolbar_wrapper."""
    mwindow.obstacle_toolbox = ObstacleToolbox(mwindow.cr_viewer.current_scenario, mwindow.toolbox_callback, mwindow.tmp_folder)
    mwindow.addDockWidget(Qt.RightDockWidgetArea, mwindow.obstacle_toolbox)
    return mwindow.obstacle_toolbox
