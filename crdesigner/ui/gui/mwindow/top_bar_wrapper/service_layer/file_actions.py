from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import os
import logging

from commonroad.scenario.scenario import Scenario
from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.common.file_reader import CommonRoadFileReader, FileFormat
from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.gui_sumo_simulation import SUMO_AVAILABLE

if SUMO_AVAILABLE:
    pass


def file_new(mwindow):
    """
        Function passed to the fileNewAction to create the action in the menu bar.
    """
    scenario = Scenario(0.1, affiliation="Technical University of Munich", source="CommonRoad Scenario Designer")
    net = LaneletNetwork()
    scenario.replace_lanelet_network(net)
    mwindow.animated_viewer_wrapper.cr_viewer.current_scenario = scenario
    mwindow.animated_viewer_wrapper.cr_viewer.current_pps = None
    _open_scenario(mwindow=mwindow, new_scenario=scenario)
    mwindow.animated_viewer_wrapper.cr_viewer.dynamic.draw_temporary_points = {}


def open_commonroad_file(mwindow):
    """ """
    path, _ = QFileDialog.getOpenFileName(mwindow, "Open a CommonRoad scenario", "",
                                          "CommonRoad scenario *.xml file (*.xml);; "
                                          "CommonRoad scenario *.pb file (*.pb)",
                                          options=QFileDialog.Options(), )
    if not path:
        return
    _open_path(mwindow=mwindow, path=path)


def _open_path(mwindow, path):
    """ """
    try:
        if ".pb" in path:
            commonroad_reader = CommonRoadFileReader(path, file_format=FileFormat.PROTOBUF)
        else:
            commonroad_reader = CommonRoadFileReader(path, file_format=FileFormat.XML)
        scenario, pps = commonroad_reader.open()
    except Exception as e:
        QMessageBox.warning(mwindow, "CommonRoad XML error",
                            "There was an error during the loading of the selected CommonRoad file.\n\n" +
                            "Syntax Error: {}".format(e), QMessageBox.Ok, )
        return

    filename = os.path.splitext(os.path.basename(path))[0]
    _open_scenario(mwindow, scenario, filename, pps)


def _open_scenario(mwindow, new_scenario, filename="new_scenario", pps=None):
    if mwindow.check_scenario(new_scenario) >= 2:
        mwindow.crdesigner_console_wrapper.text_browser.append("loading aborted")
        return
    mwindow.filename = filename
    if SUMO_AVAILABLE:
        mwindow.animated_viewer_wrapper.cr_viewer.open_scenario(new_scenario,
                                                                mwindow.obstacle_toolbox.sumo_simulation.config,
                                                                planning_problem_set=pps, new_file_added=True)
        mwindow.obstacle_toolbox.sumo_simulation.scenario = mwindow.animated_viewer_wrapper.cr_viewer.current_scenario
    else:
        mwindow.animated_viewer_wrapper.cr_viewer.open_scenario(new_scenario, planning_problem_set=pps,
                                                                new_file_added=True)
    mwindow.store_scenario()
    mwindow.update_toolbox_scenarios()
    update_to_new_scenario(mwindow)


def update_to_new_scenario(mwindow):
    """"""
    update_max_step(mwindow)
    mwindow.initialize_toolboxes()
    mwindow.animated_viewer_wrapper.viewer_dock.setWindowIcon(QIcon(":/icons/cr1.ico"))
    if mwindow.animated_viewer_wrapper.cr_viewer.current_scenario is not None:
        mwindow.crdesigner_console_wrapper.text_browser.append("Loading " + mwindow.filename)


def file_save(mwindow):
    """Function to save a CR .xml file."""
    if mwindow.animated_viewer_wrapper.cr_viewer.current_scenario is None:
        messbox = QMessageBox()
        messbox.warning(mwindow, "Warning", "There is no file to save!", QMessageBox.Ok, QMessageBox.Ok)
        messbox.close()
        return

    mwindow.scenario_saving_dialog.show(mwindow.animated_viewer_wrapper.cr_viewer.current_scenario,
                                        mwindow.animated_viewer_wrapper.cr_viewer.current_pps)


def update_max_step(mwindow, value: int = -1):
    logging.info('update_max_step')
    value = value if value > -1 else mwindow.animated_viewer_wrapper.cr_viewer.max_timestep
    mwindow.top_bar_wrapper.toolbar_wrapper.label2.setText(' / ' + str(value))
    mwindow.top_bar_wrapper.toolbar_wrapper.slider.setMaximum(value)


def close_window(mwindow):
    """
        For closing the window.
    """
    reply = QMessageBox.warning(mwindow, "Warning", "Do you really want to quit?", QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.Yes)
    if reply == QMessageBox.Yes:
        qApp.quit()
