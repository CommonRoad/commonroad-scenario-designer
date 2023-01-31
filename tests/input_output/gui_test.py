from crdesigner.ui.gui.mwindow.mwindow import MWindow
import sys
from PyQt5.QtWidgets import *

# HOW TO ADD TESTS ?
# 1. all tests need to be in the test_pyqt_framework method. Otherwise, the construction / destruction causes segfaults.
# 2. Always add the area which is tested (e.g. -- TOOLBAR)
# 3. write the testing between # ----- PERFORM TESTS ------ # and # -- FINISH
# 4. write the asserts after -- FINISH
# 5. app and window are used as the handles to the app


def test_pyqt_framework(qtbot):
    """
    Test the correct link between functionality and GUI - this does NOT test the functionality!
    """
    # init the app and the qtbot
    app = QApplication(sys.argv)
    window = MWindow()
    qtbot.addWidget(window)

    # ----- PERFORM TESTS ------ #
    # -- TOOLBAR
    execute_toolbar_test(window)
    # -- MENUBAR
    execute_menubar_test(window)

    # -- FINISH
    app.closeAllWindows()
    app.quit()


def execute_menubar_test(window):
    # test the file_new
    file_new_success = False
    try:
        window.top_bar_wrapper.menu_bar_wrapper.action_new.trigger()
        file_new_success = True
    except Exception as e:
        print("file_new failed with exception: " + str(e))
    # skip file open and file safe due to IO
    # test the 'setting' tab
    menubar_wrapper_setting_successful = False
    try:
        window.top_bar_wrapper.menu_bar_wrapper.settings_action.trigger()
        menubar_wrapper_setting_successful = True
    except Exception as e:
        print("menubar_wrapper_setting failed with exception: " + str(e))
    # test the sumo setting tab

    """
    menubar_wrapper_gui_setting_sumo_successful = False
    if SUMO_AVAILABLE:
        try:
            window.top_bar_wrapper.menu_bar_wrapper.sumo_settings_action.trigger()
            menubar_wrapper_gui_setting_sumo_successful = True
        except Exception as e:
            print("menubar_wrapper_gui_setting_sumo failed with exception: " + str(e))
    else:
        menubar_wrapper_gui_setting_sumo_successful = True
    """
    # skip the web calls due to we do not want to produce IO

    assert file_new_success
    assert menubar_wrapper_setting_successful
    #assert menubar_wrapper_gui_setting_sumo_successful


def execute_toolbar_test(window):
    # action_new
    toolbar_wrapper_action_new_successful = False
    try:
        window.top_bar_wrapper.toolbar_wrapper.action_new.trigger()
        toolbar_wrapper_action_new_successful = True
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
    # the play button is skipped since we do not test playing videos

    assert map_converter_toolbox_success
    assert road_network_toolbox_success
    assert obstacle_toolbox_success
    assert redo_action_success
    assert undo_action_success
    assert toolbar_wrapper_action_new_successful
