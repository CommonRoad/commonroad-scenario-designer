import pathlib

from PyQt5 import QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import logging

from crdesigner.ui.gui.mwindow.service_layer.util import *
import copy
from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.gui_sumo_simulation import SUMO_AVAILABLE

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


def center(mwindow):
    """Function that makes sure the main window is in the center of screen."""
    screen = QDesktopWidget().screenGeometry()
    size = mwindow.geometry()
    mwindow.move(int((screen.width() - size.width()) / 2), int((screen.height() - size.height()) / 2))


def update_max_step_service_layer(mwindow, value):
    logging.info('update_max_step')
    value = value if value > -1 else mwindow.animated_viewer_wrapper.cr_viewer.max_timestep
    mwindow.top_bar_wrapper.toolbar_wrapper.label2.setText(' / ' + str(value))
    mwindow.top_bar_wrapper.toolbar_wrapper.slider.setMaximum(value)


def store_scenario_service_layer(mwindow):
    mwindow.scenarios.append(copy.deepcopy(mwindow.animated_viewer_wrapper.cr_viewer.current_scenario))
    mwindow.current_scenario_index += 1
    mwindow.update_toolbox_scenarios()


def update_toolbox_scenarios_service_layer(mwindow):
    scenario = mwindow.animated_viewer_wrapper.cr_viewer.current_scenario
    mwindow.road_network_toolbox.refresh_toolbox(scenario)
    mwindow.obstacle_toolbox.refresh_toolbox(scenario)
    mwindow.map_converter_toolbox.refresh_toolbox(scenario)
    if SUMO_AVAILABLE:
        mwindow.obstacle_toolbox.sumo_simulation.scenario = scenario
        mwindow.map_converter_toolbox.sumo_simulation.scenario = scenario


def check_scenario_service_layer(mwindow, scenario) -> int:
    """
    Check the scenario to validity and calculate a quality score.
    The higher the score the higher the data faults.

    :return: score
    """

    warning = 1
    fatal_error = 2
    verbose = True

    error_score = 0

    # handle fatal errors
    found_ids = find_invalid_ref_of_traffic_lights(scenario)
    if found_ids and verbose:
        error_score = max(error_score, fatal_error)
        mwindow.crdesigner_console_wrapper.text_browser.append("invalid traffic light refs: " + str(found_ids))
        QMessageBox.critical(
            mwindow,
            "CommonRoad XML error",
            "Scenario contains invalid traffic light refenence(s): " +
            str(found_ids),
            QMessageBox.Ok,
        )

    found_ids = find_invalid_ref_of_traffic_signs(scenario)
    if found_ids and verbose:
        error_score = max(error_score, fatal_error)
        mwindow.crdesigner_console_wrapper.text_browser.append("invalid traffic sign refs: " + str(found_ids))
        QMessageBox.critical(
            mwindow,
            "CommonRoad XML error",
            "Scenario contains invalid traffic sign refenence(s): " +
            str(found_ids),
            QMessageBox.Ok,
        )

    if error_score >= fatal_error:
        return error_score

    # handle warnings
    found_ids = find_invalid_lanelet_polygons(scenario)
    if found_ids and verbose:
        error_score = max(error_score, warning)
        mwindow.crdesigner_console_wrapper.text_browser.append(
            "Warning: Lanelet(s) with invalid polygon:" + str(found_ids))
        QMessageBox.warning(
            mwindow,
            "CommonRoad XML error",
            "Scenario contains lanelet(s) with invalid polygon: " +
            str(found_ids),
            QMessageBox.Ok,
        )

    return error_score


def close_window(mwindow):
    """
        For closing the window.
    """
    messageBox = QMessageBox(QMessageBox.Warning,  "Warning", "Do you really want to quit?", buttons=QMessageBox.Yes | QMessageBox.No, parent=mwindow)

    p = QtGui.QPalette()
    p.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(mwindow.colorscheme().background))
    p.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(mwindow.colorscheme().second_background))
    p.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor(mwindow.colorscheme().highlight))
    p.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor(mwindow.colorscheme().highlight_text))
    p.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor(mwindow.colorscheme().color))
    p.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor(mwindow.colorscheme().color))
    messageBox.setPalette(p)

    messageBox.exec_()
    reply = messageBox.standardButton(messageBox.clickedButton())

    if reply == messageBox.Yes:
        qApp.quit()
