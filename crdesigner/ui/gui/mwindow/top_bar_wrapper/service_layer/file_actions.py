from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import os
import logging

from commonroad.scenario.scenario import Scenario
from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.common.file_reader import CommonRoadFileReader
from crdesigner.ui.gui.mwindow.top_bar_wrapper.service_layer.general_services import create_action
from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.gui_sumo_simulation import SUMO_AVAILABLE

if SUMO_AVAILABLE:
    pass


def create_file_actions(mwindow):
    """
        Function to create the file actions in the menu bar.
    """
    fileNewAction = create_action(mwindow=mwindow, text="New", icon=QIcon(":/icons/new_file.png"), checkable=False,
                                  slot=file_new, tip="New Commonroad File", shortcut=QKeySequence.New)
    fileOpenAction = create_action(mwindow=mwindow, text="Open", icon=QIcon(":/icons/open_file.png"), checkable=False,
                                   slot=open_commonroad_file, tip="Open Commonroad File", shortcut=QKeySequence.Open)
    separator = QAction(mwindow)
    separator.setSeparator(True)

    fileSaveAction = create_action(mwindow=mwindow, text="Save", icon=QIcon(":/icons/save_file.png"), checkable=False,
                                   slot=file_save, tip="Save Commonroad File", shortcut=QKeySequence.Save)
    separator.setSeparator(True)
    exitAction = create_action(mwindow=mwindow, text="Quit", icon=QIcon(":/icons/close.png"), checkable=False,
                               slot=_close_window, tip="Quit", shortcut=QKeySequence.Close)
    return fileNewAction, fileOpenAction, separator, fileSaveAction, exitAction


# here are the internal used functions


def file_new(mwindow):
    """
        Function passed to the fileNewAction to create the action in the menu bar.
    """
    scenario = Scenario(0.1, affiliation="Technical University of Munich", source="CommonRoad Scenario Designer")
    net = LaneletNetwork()
    scenario.lanelet_network = net
    mwindow.cr_viewer.current_scenario = scenario
    mwindow.cr_viewer.current_pps = None
    _open_scenario(mwindow=mwindow, new_scenario=scenario)


def open_commonroad_file(mwindow):
    """ """
    path, _ = QFileDialog.getOpenFileName(mwindow, "Open a CommonRoad scenario", "",
                                          "CommonRoad scenario files *.xml (*.xml)", options=QFileDialog.Options(), )
    if not path:
        return
    _open_path(mwindow=mwindow, path=path)


def _open_path(mwindow, path):
    """ """
    try:
        commonroad_reader = CommonRoadFileReader(path)
        scenario, pps = commonroad_reader.open()
    except Exception as e:
        QMessageBox.warning(mwindow, "CommonRoad XML error",
                            "There was an error during the loading of the selected CommonRoad file.\n\n" + \
                            "Syntax Error: {}".format(e), QMessageBox.Ok, )
        return

    filename = os.path.splitext(os.path.basename(path))[0]
    _open_scenario(mwindow, scenario, filename, pps)


def _open_scenario(mwindow, new_scenario, filename="new_scenario", pps=None):
    if mwindow.check_scenario(new_scenario) >= 2:
        mwindow.text_browser.append("loading aborted")
        return
    mwindow.filename = filename
    if SUMO_AVAILABLE:
        mwindow.cr_viewer.open_scenario(new_scenario, mwindow.obstacle_toolbox.sumo_simulation.config,
                                        planning_problem_set=pps)
        mwindow.obstacle_toolbox.sumo_simulation.scenario = mwindow.cr_viewer.current_scenario
    else:
        mwindow.cr_viewer.open_scenario(new_scenario, planning_problem_set=pps)
    mwindow.update_view(focus_on_network=True)
    mwindow.store_scenario()
    mwindow.update_toolbox_scenarios()
    update_to_new_scenario(mwindow)


def update_to_new_scenario(mwindow):
    """"""
    update_max_step(mwindow)
    mwindow.initialize_toolboxes()
    mwindow.viewer_dock.setWindowIcon(QIcon(":/icons/cr1.ico"))
    if mwindow.cr_viewer.current_scenario is not None:
        mwindow.console_wrapper.text_browser.append("Loading " + mwindow.filename)


def file_save(mwindow):
    """Function to save a CR .xml file."""
    if mwindow.cr_viewer.current_scenario is None:
        messbox = QMessageBox()
        messbox.warning(mwindow, "Warning", "There is no file to save!", QMessageBox.Ok, QMessageBox.Ok)
        messbox.close()
        return

    mwindow.scenario_saving_dialog.show(mwindow.cr_viewer.current_scenario, mwindow.cr_viewer.current_pps)


def update_max_step(mwindow, value: int = -1):
    logging.info('update_max_step')
    value = value if value > -1 else mwindow.cr_viewer.max_timestep
    mwindow.top_bar_wrapper.toolbar_wrapper.label2.setText(' / ' + str(value))
    mwindow.top_bar_wrapper.toolbar_wrapper.slider.setMaximum(value)


def _close_window(mwindow):
    """
        For closing the window.
    """
    reply = QMessageBox.warning(mwindow, "Warning", "Do you really want to quit?", QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.Yes)
    if reply == QMessageBox.Yes:
        qApp.quit()
