import unittest
import pytest
import time

from crdesigner.ui.gui.mwindow.mwindow import MWindow
import sys
from PyQt5.QtWidgets import *
from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.gui_sumo_simulation import SUMO_AVAILABLE


def test_toolbar_wrapper(qtbot):
    """
    Test the correct link between functionality and GUI - this does NOT test the functionality!
    """
    print("Started test_top_bar - "
          " WARNING: this tests the link between the functionality and the GUI, NOT the functionality per se."
          " NOTE: use QT_QPA_PLATFORM = 'offscreen' as variable when using it in the pipeline - "
          " by this the window is supressed.")
    # init the app and the qtbot
    app = QApplication(sys.argv)
    window = MWindow()
    qtbot.addWidget(window)
    window.showMaximized()
    # perform the test
    # action_new
    toolbar_wrapper_action_new_successfull = False
    try:
        window.top_bar_wrapper.toolbar_wrapper.action_new.trigger()
        toolbar_wrapper_action_new_successfull = True
    except Exception as e:
        print("toolbar_wrapper_action_new failed with exception: " + str(e))

    # action_open is left out due to compatibility with os

    # action_safe is left out due to compatibility with os

    # now the toolboxes
    road_network_toolbox_success = False
    try:
        window.top_bar_wrapper.toolbar_wrapper.action_road_network_toolbox.trigger()
        road_network_toolbox_success = True
    except Exception as e:
        print("road_network_toolbox failed with exception: " + str(e))

    obstacle_toolbox_success = False
    try:
        window.top_bar_wrapper.toolbar_wrapper.action_obstacle_toolbox.trigger()
        obstacle_toolbox_success = True
    except Exception as e:
        print("obstacle_toolbox failed with exception: " + str(e))
    map_converter_toolbox_success = False
    try:
        window.top_bar_wrapper.toolbar_wrapper.action_converter_toolbox.trigger()
        map_converter_toolbox_success = True
    except Exception as e:
        print("action_converter_toolbox failed with exception: " + str(e))

    # the redo and undo actions
    redo_action_success = False
    try:
        window.top_bar_wrapper.toolbar_wrapper.action_redo.trigger()
        redo_action_success = True
    except Exception as e:
        print("redo_action failed with exception: " + str(e))

    undo_action_success = False
    try:
        window.top_bar_wrapper.toolbar_wrapper.action_undo.trigger()
        undo_action_success = True
    except Exception as e:
        print("undo_action failed with exception: " + str(e))

    # the play button is skipped due we dont test paying vids.

    # finish all of and assert the results
    app.quit()
    assert toolbar_wrapper_action_new_successfull
    assert road_network_toolbox_success
    assert obstacle_toolbox_success
    assert map_converter_toolbox_success
    assert redo_action_success
    assert undo_action_success


def test_menu_bar(qtbot):
    """
        Test the correct link between functionality and GUI - this does NOT test the functionality!
        """
    print("Started test_menu_bar - "
          " WARNING: this tests the link between the functionality and the GUI, NOT the functionality per se."
          " NOTE: use QT_QPA_PLATFORM = 'offscreen' as variable when using it in the pipeline - "
          " by this the window is supressed.")
    # init the app and the qtbot
    app = QApplication(sys.argv)
    window = MWindow()
    qtbot.addWidget(window)
    window.showMaximized()
    # test the file_new
    file_new_success = False
    try:
        window.top_bar_wrapper.menu_bar_wrapper.action_new.trigger()
        file_new_success = True
    except Exception as e:
        print("file_new failed with exception: " + str(e))

    # skip file open and file safe due to IO

    # test the 'setting' tab
    menubar_wrapper_gui_setting_successfull = False
    try:
        window.top_bar_wrapper.menu_bar_wrapper.gui_settings_action.trigger()
        menubar_wrapper_gui_setting_successfull = True
    except Exception as e:
        print("menubar_wrapper_gui_setting failed with exception: " + str(e))

    # test the sumo setting tab
    menubar_wrapper_gui_setting_sumo_successfull = False
    if SUMO_AVAILABLE:
        try:
            window.top_bar_wrapper.menu_bar_wrapper.sumo_settings_action.trigger()
            menubar_wrapper_gui_setting_sumo_successfull = True
        except Exception as e:
            print("menubar_wrapper_gui_setting_sumo failed with exception: " + str(e))
    else:
        menubar_wrapper_gui_setting_sumo_successfull = True

    # skip the web calls due to we dont want to produce IO
    # assert and finish
    app.quit()
    assert file_new_success
    assert menubar_wrapper_gui_setting_successfull
    assert menubar_wrapper_gui_setting_sumo_successfull
