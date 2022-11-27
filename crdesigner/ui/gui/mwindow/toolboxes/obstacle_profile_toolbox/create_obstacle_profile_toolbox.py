from crdesigner.ui.gui.mwindow.toolboxes.obstacle_profile_toolbox.obstacle_profile_toolbox import ObstacleProfileToolbox
from crdesigner.ui.gui.mwindow.toolboxes.service_layer.general_services import toolbox_callback

from PyQt5.QtGui import *
from PyQt5.QtCore import *


def create_obstacle_profile_toolbox(mwindow):
    """ Create the obstacle profile toolbar_wrapper."""
    mwindow.obstacle_profile_toolbox = ObstacleProfileToolbox(
        current_scenario=mwindow.animated_viewer_wrapper.cr_viewer.current_scenario,
        callback=lambda scenario: toolbox_callback(mwindow, scenario), tmp_folder=mwindow.tmp_folder,
        text_browser=mwindow.crdesigner_console_wrapper.text_browser, mwindow=mwindow)
    mwindow.addDockWidget(Qt.RightDockWidgetArea, mwindow.obstacle_profile_toolbox)
    return mwindow.obstacle_profile_toolbox