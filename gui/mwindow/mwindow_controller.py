import pathlib
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from commonroad.scenario.scenario import Scenario
from commonroad.scenario.lanelet import LaneletNetwork, Lanelet



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


def create_file_actions(mwindow, open_commonroad_file, file_save, close_window):
    """
        Function to create the file actions in the menu bar.
    """
    fileNewAction = _create_action("New", icon=QIcon(":/icons/new_file.png"), checkable=False,
            slot=_file_new, tip="New Commonroad File", shortcut=QKeySequence.New)
    fileOpenAction = _create_action("Open", icon=QIcon(":/icons/open_file.png"), checkable=False,
            slot=open_commonroad_file, tip="Open Commonroad File", shortcut=QKeySequence.Open)
    separator = QAction(mwindow)
    separator.setSeparator(True)

    fileSaveAction = _create_action("Save", icon=QIcon(":/icons/save_file.png"), checkable=False,
            slot=file_save, tip="Save Commonroad File", shortcut=QKeySequence.Save)
    separator.setSeparator(True)
    exitAction = _create_action("Quit", icon=QIcon(":/icons/close.png"), checkable=False,
                                         slot=close_window, tip="Quit", shortcut=QKeySequence.Close)
    return fileNewAction, fileOpenAction, separator, fileSaveAction, exitAction


def _create_action(self, text, icon=None, checkable=False, slot=None, tip=None, shortcut=None):
    """
        Generic function used to create actions for the menu bar.
    """
    action = QAction(text, self)
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


def _file_new(mwindow):
    """
        Function passed to the fileNewAction to create the action in the menu bar.
    """
    scenario = Scenario(0.1, affiliation="Technical University of Munich", source="CommonRoad Scenario Designer")
    net = LaneletNetwork()
    scenario.lanelet_network = net
    mwindow.cr_viewer.current_scenario = scenario
    mwindow.cr_viewer.current_pps = None
    mwindow.open_scenario(scenario)
