import math
import os
import numpy as np

from commonroad.common.common_lanelet import LineMarking
from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.scenario.obstacle import StaticObstacle, ObstacleType
from commonroad.scenario.scenario import Scenario
from commonroad.geometry.shape import Rectangle
from commonroad.scenario.state import InitialState

from crdesigner.ui.gui.autosaves.autosaves_setup import DIR_AUTOSAVE
from crdesigner.ui.gui.controller.mwindow_controller import MWindowController
from crdesigner.ui.gui.utilities.file_actions import open_commonroad_file
from crdesigner.ui.gui.utilities.map_creator import MapCreator


def test_pyqt_framework(qtbot):
    """
    Test the correct link between functionality and GUI - this does NOT test the functionality!
    """

    # do not create an QApplication() here: https://github.com/pytest-dev/pytest-qt/issues/504

    path_autosave = DIR_AUTOSAVE + "/autosave" + ".xml"
    if os.path.exists(path_autosave):
        os.remove(path_autosave)

    window = MWindowController(test=True)
    qtbot.addWidget(window.mwindow_ui)

    # ----- PERFORM TESTS ------ #
    # -- TOOLBAR
    execute_toolbar_test(window)
    # -- Scenario
    execute_scenario_tests(window)
    # -- Obstacle Test
    execute_add_obstacle_test(window)
    # -- MENUBAR
    execute_menubar_test(window)
    # -- Load Scenario
    execute_load_scenario_test(window)

    if os.path.exists(path_autosave):
        os.remove(path_autosave)


def execute_menubar_test(window):
    # test the file_new
    file_new_success = False
    try:
        window.mwindow_ui.top_bar.menu_bar.menubar_ui.action_new.trigger()
        file_new_success = True
    except Exception as e:
        print("file_new failed with exception: " + str(e))
    # skip file open and file safe due to IO
    # test the 'setting' tab
    menubar_wrapper_setting_successful = False
    try:
        window.mwindow_ui.top_bar.menu_bar.menubar_ui.settings_action.trigger()
        menubar_wrapper_setting_successful = True
    except Exception as e:
        print("menubar_wrapper_setting failed with exception: " + str(e))
    # test the sumo setting tab

    """
    menubar_wrapper_gui_setting_sumo_successful = False
    if SUMO_AVAILABLE:
        try:
            window.top_bar.menu_bar.menubar_ui.sumo_settings_action.trigger()
            menubar_wrapper_gui_setting_sumo_successful = True
        except Exception as e:
            print("menubar_wrapper_gui_setting_sumo failed with exception: " + str(e))
    else:
        menubar_wrapper_gui_setting_sumo_successful = True
    """
    # skip the web calls due to we do not want to produce IO

    assert file_new_success
    assert menubar_wrapper_setting_successful
    # assert menubar_wrapper_gui_setting_sumo_successful


def execute_toolbar_test(window):
    # action_new
    toolbar_wrapper_action_new_successful = False
    scenario = Scenario(0.1, affiliation="Technical University of Munich", source="CommonRoad Scenario Designer")
    net = LaneletNetwork()
    scenario.replace_lanelet_network(net)
    scenario_in_app = None
    try:
        window.mwindow_ui.top_bar.toolbar_wrapper.tool_bar_ui.action_new.trigger()
        toolbar_wrapper_action_new_successful = True
        scenario_in_app = window.scenario_model.get_current_scenario()
    except Exception as e:
        print("toolbar_wrapper_action_new failed with exception: " + str(e))
    # action_open is left out due to compatibility with os
    # action_safe is left out due to compatibility with os
    # now the toolboxes
    road_network_toolbox_success = False
    try:
        window.mwindow_ui.top_bar.toolbar_wrapper.tool_bar_ui.action_road_network_toolbox.trigger()
        road_network_toolbox_success = True
    except Exception as e:
        print("road_network_toolbox failed with exception: " + str(e))
    scenario_toolbox_success = False
    try:
        window.mwindow_ui.top_bar.toolbar_wrapper.tool_bar_ui.action_scenario_toolbox.trigger()
        scenario_toolbox_success = True
    except Exception as e:
        print("road_network_toolbox failed with exception: " + str(e))
    obstacle_toolbox_success = False
    try:
        window.mwindow_ui.top_bar.toolbar_wrapper.tool_bar_ui.action_obstacle_toolbox.trigger()
        obstacle_toolbox_success = True
    except Exception as e:
        print("obstacle_toolbox failed with exception: " + str(e))
    map_converter_toolbox_success = False
    try:
        window.mwindow_ui.top_bar.toolbar_wrapper.tool_bar_ui.action_converter_toolbox.trigger()
        map_converter_toolbox_success = True
    except Exception as e:
        print("action_converter_toolbox failed with exception: " + str(e))
    # the redo and undo actions
    redo_action_success = False
    try:
        window.mwindow_ui.top_bar.toolbar_wrapper.tool_bar_ui.action_redo.trigger()
        redo_action_success = True
    except Exception as e:
        print("redo_action failed with exception: " + str(e))
    undo_action_success = False
    try:
        window.mwindow_ui.top_bar.toolbar_wrapper.tool_bar_ui.action_undo.trigger()
        undo_action_success = True
    except Exception as e:
        print("undo_action failed with exception: " + str(e))
    # the play button is skipped since we do not test playing videos

    assert map_converter_toolbox_success
    assert road_network_toolbox_success
    assert scenario == scenario_in_app
    assert scenario_toolbox_success
    assert obstacle_toolbox_success
    assert redo_action_success
    assert undo_action_success
    assert toolbar_wrapper_action_new_successful


def execute_scenario_tests(window):
    # Tests for adding a Lanelet to a Scenario
    scenario = Scenario(0.1, affiliation="Technical University of Munich", source="CommonRoad Scenario Designer")
    net = LaneletNetwork()
    scenario.replace_lanelet_network(net)
    lanelet_start_pos_x = 0.0
    lanelet_start_pos_y = 0.0
    lanelet_width = 3.0
    lanelet_length = 10.0
    num_vertices = 20
    lanelet_id = 1
    lanelet_type = set()
    predecessors = []
    successors = []
    adjacent_left = None
    adjacent_right = None
    adjacent_left_same_direction = True
    adjacent_right_same_direction = True
    user_one_way = set()
    user_bidirectional = set()
    line_marking_left = LineMarking.UNKNOWN
    line_marking_right = LineMarking.UNKNOWN
    stop_line = None
    traffic_signs = set()
    traffic_lights = set()
    stop_line_at_end = False
    stop_line_at_beginning = False
    lanelet = MapCreator.create_straight(lanelet_width, lanelet_length, num_vertices, lanelet_id, lanelet_type,
                                         predecessors, successors, adjacent_left, adjacent_right,
                                         adjacent_left_same_direction, adjacent_right_same_direction, user_one_way,
                                         user_bidirectional, line_marking_left, line_marking_right, stop_line,
                                         traffic_signs, traffic_lights, stop_line_at_end, stop_line_at_beginning)

    lanelet.translate_rotate(np.array([lanelet_start_pos_x, lanelet_start_pos_y]), 0)
    scenario.add_objects(lanelet)
    scenario_in_app = None
    try:
        window.road_network_toolbox.road_network_toolbox_ui.place_at_position.click()
        window.road_network_toolbox.road_network_toolbox_ui.button_add_lanelet.click()
        scenario_in_app = window.scenario_model.get_current_scenario()
    except Exception as e:
        print("Add_lanelet failed with exception: " + str(e))

    scenario_count_actual = len(window.scenario_model.scenarios())

    # Tests for updating a lanelet
    selected_lanelet_length = 10.0
    actual_selected_lanelet_length = 0
    should_be_length_of_changed_lanelet = '20.0'
    changed_lanelet_length_after_update = 0

    try:
        window.road_network_toolbox.road_network_toolbox_ui.selected_lanelet_update.setCurrentIndex(1)
        actual_selected_lanelet_length = window.road_network_toolbox.get_float(
                window.road_network_toolbox.road_network_toolbox_ui.selected_lanelet_length)
        window.road_network_toolbox.road_network_toolbox_ui.selected_lanelet_length.setText("20.0")
        window.road_network_toolbox.road_network_toolbox_ui.button_update_lanelet.click()
        changed_lanelet_length_after_update = window.road_network_toolbox.lanelet_controller.lanelet_ui.get_length(
                window.scenario_model.find_lanelet_by_id(1))

    except Exception as e:
        print("Select_lanelet failed with exception: " + str(e))

    assert actual_selected_lanelet_length == selected_lanelet_length
    assert should_be_length_of_changed_lanelet == changed_lanelet_length_after_update

    assert 2 == scenario_count_actual
    assert scenario == scenario_in_app


def execute_add_obstacle_test(window):
    expected_obstacle = StaticObstacle(obstacle_id=2,
                                       obstacle_type=ObstacleType("unknown"),
                                       obstacle_shape=Rectangle(length=5.0, width=5.0),
                                       initial_state=InitialState(**{'position': np.array(
                                                 [0.0, 0.0]), 'orientation': math.radians(0.0), 'time_step': 1}))

    actual_obstacle = None

    try:
        window.obstacle_toolbox.obstacle_toolbox_ui.obstacle_length.setText("5")
        window.obstacle_toolbox.obstacle_toolbox_ui.obstacle_width .setText("5")
        window.obstacle_toolbox.obstacle_toolbox_ui.obstacle_orientation.setText("0")
        window.obstacle_toolbox.obstacle_toolbox_ui.obstacle_x_Position.setText("0")
        window.obstacle_toolbox.obstacle_toolbox_ui.obstacle_y_Position.setText("0")
        window.obstacle_toolbox.obstacle_toolbox_ui.button_add_static_obstacle.click()
        actual_obstacle = window.scenario_model.find_obstacle_by_id(2)

    except Exception as e:
        print(f"Add Obstacle failed with exception: {str(e)}.")

    assert expected_obstacle == actual_obstacle

    
def execute_load_scenario_test(window):
    parent_directory = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
    path_to_test = parent_directory + "/map_conversion/test_maps/sumo/ARG_Carcarana-10_2_T-1.xml"
    expected_count_lanelets = 94
    expected_count_traffic_signs = 8
    actual_count_lanelets = 0
    actual_count_traffic_signs = 0

    try:
        open_commonroad_file(window, path_to_test)
        actual_count_lanelets = len(window.scenario_model.get_lanelets())
        actual_count_traffic_signs = len(window.scenario_model.get_traffic_signs())
    except Exception as e:
        print(f"Opening a file failed with exception {str(e)}")

    assert expected_count_lanelets == actual_count_lanelets
    assert expected_count_traffic_signs == actual_count_traffic_signs
