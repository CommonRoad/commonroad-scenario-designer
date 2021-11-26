import pathlib
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from crdesigner.input_output.gui.toolboxes.gui_sumo_simulation import SUMO_AVAILABLE
if SUMO_AVAILABLE:
    from crdesigner.input_output.gui.settings.sumo_settings import SUMOSettings

"""
    This file is a general collection of smaller functions which are used in the mwindow 
    or by two or more components from the mwindow_service_layer.
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
        action.setToolTip(tip)  # toolbar_wrapper tip
        action.setStatusTip(tip)  # statusbar tip
    if shortcut is not None:
        action.setShortcut(shortcut)  # shortcut
    return action


def center(mwindow):
    """Function that makes sure the main window is in the center of screen."""
    screen = QDesktopWidget().screenGeometry()
    size = mwindow.geometry()
    mwindow.move((screen.width() - size.width()) / 2,
              (screen.height() - size.height()) / 2)