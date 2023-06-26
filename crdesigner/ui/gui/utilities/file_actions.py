from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import os
import logging

from commonroad.scenario.scenario import Scenario
from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.common.file_reader import CommonRoadFileReader, FileFormat
from crdesigner.ui.gui.utilities.gui_sumo_simulation import SUMO_AVAILABLE

if SUMO_AVAILABLE:
    pass


def file_new(mwindow):
    """
    Function passed to the fileNewAction to create the action in the menu bar.
    """
    scenario = Scenario(0.1, affiliation="Technical University of Munich", source="CommonRoad Scenario Designer")
    net = LaneletNetwork()
    scenario.replace_lanelet_network(net)
    mwindow.scenario_model.set_scenario(scenario)

    mwindow.animated_viewer_wrapper.cr_viewer.current_pps = None
    _open_scenario(mwindow=mwindow, new_scenario=scenario)
    mwindow.animated_viewer_wrapper.cr_viewer.dynamic.draw_temporary_points = {}



def open_commonroad_file(mwindow):
    """ """
    path, _ = QFileDialog.getOpenFileName(mwindow.mwindow_ui, "Open a CommonRoad scenario", "",
                                          "CommonRoad scenario *.xml file (*.xml);; "
                                          "CommonRoad scenario *.pb file (*.pb)", options=QFileDialog.Options(), )
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
    mwindow.scenario_model.set_scenario(scenario)
    _open_scenario(mwindow, scenario, filename, pps)


def _open_scenario(mwindow, new_scenario, filename="new_scenario", pps=None):
    if mwindow.check_scenario(new_scenario) >= 2:
        mwindow.crdesigner_console_wrapper.text_browser.append("loading aborted")
        return
    mwindow.filename = filename
    if SUMO_AVAILABLE:
        mwindow.animated_viewer_wrapper.cr_viewer.open_scenario(mwindow.obstacle_toolbox.sumo_simulation.config,
                                                                planning_problem_set=pps, new_file_added=True)
        mwindow.obstacle_toolbox.sumo_simulation.scenario = mwindow.scenario_model.get_current_scenario()
    else:
        mwindow.animated_viewer_wrapper.cr_viewer.open_scenario(planning_problem_set=pps,
                                                                new_file_added=True)
    mwindow.animated_viewer_wrapper.update_view(new_file_added=True)
    update_to_new_scenario(mwindow)


def update_to_new_scenario(mwindow):
    """"""
    update_max_step(mwindow)
    mwindow.mwindow_ui.initialize_toolboxes()
    mwindow.animated_viewer_wrapper.viewer_dock.setWindowIcon(QIcon(":/icons/cr1.ico"))
    if not mwindow.animated_viewer_wrapper.cr_viewer.scenario_model.scenario_created():
        mwindow.crdesigner_console_wrapper.text_browser.append("Loading " + mwindow.filename)


def file_save(mwindow):
    """Function to save a CR .xml file."""
    if not mwindow.scenario_model.scenario_created():
        messbox = QMessageBox()
        messbox.warning(mwindow.mwindow_ui, "Warning", "There is no file to save!", QMessageBox.Ok, QMessageBox.Ok)
        messbox.close()
        return

    mwindow.scenario_saving_dialog.show(mwindow.scenario_model,
                                        mwindow.animated_viewer_wrapper.cr_viewer.current_pps)


def update_max_step(mwindow, value: int = -1):
    logging.info('update_max_step')
    value = value if value > -1 else mwindow.animated_viewer_wrapper.cr_viewer.max_timestep
    mwindow.mwindow_ui.top_bar.toolbar_wrapper.tool_bar_ui.label2.setText(' / ' + str(value))
    mwindow.mwindow_ui.top_bar.toolbar_wrapper.tool_bar_ui.slider.setMaximum(value)


def close_window(mwindow):
    """
        For closing the window.
    """
    reply = QMessageBox.warning(mwindow, "Warning", "Do you really want to quit?", QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.Yes)
    if reply == QMessageBox.Yes:
        qApp.quit()