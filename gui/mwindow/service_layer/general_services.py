import pathlib
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from typing import Union
from commonroad.scenario.lanelet import Lanelet
from commonroad.scenario.obstacle import Obstacle

from crdesigner.input_output.gui.toolboxes.gui_sumo_simulation import SUMO_AVAILABLE
if SUMO_AVAILABLE:
    from crdesigner.input_output.gui.settings.sumo_settings import SUMOSettings

"""
    This file is a general collection of smaller functions which are used in the mwindow 
    or by two or more components from the service_layer.
"""


def setup_tmp(tmp_folder_path: str):
    """
        Setup the tmp folder of the MWindow at the given Path.
    """
    pathlib.Path(tmp_folder_path).mkdir(parents=True, exist_ok=True)


def setup_mwindow(mwindow):
    """
        Calling the methods for setting up the main window.
    """
    mwindow.setupUi(mwindow)
    mwindow.setWindowIcon(QIcon(':/icons/cr.ico'))
    mwindow.setWindowTitle("CommonRoad Scenario Designer")
    mwindow.centralwidget.setStyleSheet('background-color:rgb(150,150,150)')
    mwindow.setWindowFlag(Qt.Window)


def create_action(mwindow, text, icon=None, checkable=False, slot=None, tip=None, shortcut=None):
    """
        Generic function used to create actions for the settings or the menu bar.
    """
    action = QAction(text, mwindow)
    if icon is not None:
        action.setIcon(QIcon(icon))
    if checkable:
        # toggle, True means on/off state, False means simply executed
        action.setCheckable(True)
        if slot is not None:
            action.toggled.connect(slot)
    else:
        if slot is not None:
            action.triggered.connect(slot)
    if tip is not None:
        action.setToolTip(tip)  # toolbar tip
        action.setStatusTip(tip)  # statusbar tip
    if shortcut is not None:
        action.setShortcut(shortcut)  # shortcut
    return action


def create_viewer_dock(mwindow) -> any:  # returning here just for the sake of consistency
    """Create the viewer dock."""
    mwindow.viewer_dock = QWidget(mwindow)
    toolbar = NavigationToolbar(mwindow.cr_viewer.dynamic, mwindow.viewer_dock)
    layout = QVBoxLayout()
    layout.addWidget(toolbar)
    layout.addWidget(mwindow.cr_viewer.dynamic)
    mwindow.viewer_dock.setLayout(layout)
    mwindow.setCentralWidget(mwindow.viewer_dock)
    return mwindow.viewer_dock


def viewer_callback(mwindow, selected_object: Union[Lanelet, Obstacle], output: str):
    """
        TODO find out what this method does.
    """
    if isinstance(selected_object, Lanelet):
        mwindow.road_network_toolbox.road_network_toolbox.selected_lanelet_two.setCurrentText(
            mwindow.road_network_toolbox.road_network_toolbox.selected_lanelet_one.currentText())
        mwindow.road_network_toolbox.road_network_toolbox.selected_lanelet_one.setCurrentText(
            str(selected_object.lanelet_id))
        mwindow.road_network_toolbox.road_network_toolbox.selected_lanelet_update.setCurrentText(
            str(selected_object.lanelet_id))
    elif isinstance(selected_object, Obstacle):
        mwindow.obstacle_toolbox.obstacle_toolbox.selected_obstacle.setCurrentText(str(selected_object.obstacle_id))
    if output != "":
        mwindow.text_browser.append(output)
