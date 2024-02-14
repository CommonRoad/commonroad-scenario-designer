import math
import os

import numpy as np
from commonroad.common.common_lanelet import LineMarking
from commonroad.common.common_scenario import FileInformation, ScenarioID
from commonroad.geometry.shape import Rectangle
from commonroad.scenario.lanelet import Lanelet, LaneletNetwork
from commonroad.scenario.obstacle import ObstacleType, StaticObstacle
from commonroad.scenario.scenario import Scenario
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
    # -- Adding lanelets by connect to selected
    execute_add_lanelet_test(window)
    # -- Removing multiple lanelets at the once
    execute_remove_multiple_lanelet_test(window)
    # -- Rotating multiple lanelets at once
    execute_rotate_multiple_lanelet_test(window)
    # -- Translating multiple lanelets at once
    execute_translate_multiple_lanelet_test(window)
    # update multiple lanelets
    execute_update_multiple_lanelet_test(window)

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
    assert menubar_wrapper_setting_successful  # assert menubar_wrapper_gui_setting_sumo_successful


def execute_toolbar_test(window):
    # action_new
    toolbar_wrapper_action_new_successful = False
    scenario = Scenario(
        0.1,
        file_information=FileInformation(
            affiliation="Technical University of Munich", source="CommonRoad Scenario Designer"
        ),
    )
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
    scenario = Scenario(
        0.1,
        file_information=FileInformation(
            affiliation="Technical University of Munich", source="CommonRoad Scenario Designer"
        ),
    )
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
    lanelet = MapCreator.create_straight(
        lanelet_width,
        lanelet_length,
        num_vertices,
        lanelet_id,
        lanelet_type,
        predecessors,
        successors,
        adjacent_left,
        adjacent_right,
        adjacent_left_same_direction,
        adjacent_right_same_direction,
        user_one_way,
        user_bidirectional,
        line_marking_left,
        line_marking_right,
        stop_line,
        traffic_signs,
        traffic_lights,
        stop_line_at_end,
        stop_line_at_beginning,
    )

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
    should_be_length_of_changed_lanelet = "20.0"
    changed_lanelet_length_after_update = 0

    try:
        window.road_network_toolbox.road_network_toolbox_ui.selected_lanelet_update.setCurrentIndex(1)
        window.road_network_toolbox.road_network_toolbox_ui.selected_lanelet_update.set_checked_items(["1"])
        actual_selected_lanelet_length = window.road_network_toolbox.get_float(
            window.road_network_toolbox.road_network_toolbox_ui.selected_lanelet_length
        )
        window.road_network_toolbox.road_network_toolbox_ui.selected_lanelet_length.setText("20.0")
        window.road_network_toolbox.road_network_toolbox_ui.button_update_lanelet.click()
        changed_lanelet_length_after_update = window.road_network_toolbox.lanelet_controller.lanelet_ui.get_length(
            window.scenario_model.find_lanelet_by_id(1)
        )

    except Exception as e:
        print("Select_lanelet failed with exception: " + str(e))

    assert actual_selected_lanelet_length == selected_lanelet_length
    assert should_be_length_of_changed_lanelet == changed_lanelet_length_after_update

    assert 2 == scenario_count_actual
    assert scenario == scenario_in_app


def execute_add_obstacle_test(window):
    expected_obstacle = StaticObstacle(
        obstacle_id=2,
        obstacle_type=ObstacleType("unknown"),
        obstacle_shape=Rectangle(length=5.0, width=5.0),
        initial_state=InitialState(
            **{"position": np.array([0.0, 0.0]), "orientation": math.radians(0.0), "time_step": 1}
        ),
    )

    actual_obstacle = None

    try:
        window.obstacle_toolbox.obstacle_toolbox_ui.obstacle_length.setText("5")
        window.obstacle_toolbox.obstacle_toolbox_ui.obstacle_width.setText("5")
        window.obstacle_toolbox.obstacle_toolbox_ui.obstacle_orientation.setText("0")
        window.obstacle_toolbox.obstacle_toolbox_ui.obstacle_x_Position.setText("0")
        window.obstacle_toolbox.obstacle_toolbox_ui.obstacle_y_Position.setText("0")
        window.obstacle_toolbox.obstacle_toolbox_ui.button_add_static_obstacle.click()
        actual_obstacle = window.scenario_model.find_obstacle_by_id(2)

    except Exception as e:
        print(f"Add Obstacle failed with exception: {str(e)}.")

    assert expected_obstacle == actual_obstacle


def add_lanelets(window):
    # set a scenario in the window
    scenario = Scenario(0.1, ScenarioID())
    window.scenario_model.set_scenario(scenario=scenario)
    # simulate a clikc on the place_at_position button
    window.road_network_toolbox.road_network_toolbox_ui.place_at_position.click()
    # add a lanelet at default position
    window.road_network_toolbox.lanelet_controller.add_lanelet()
    first_l_id = window.road_network_toolbox.last_added_lanelet_id

    # add second lanelet as predecessor
    window.road_network_toolbox.road_network_toolbox_ui.connect_to_selected_selection.click()
    window.road_network_toolbox.road_network_toolbox_ui.as_predecessor.setChecked(True)
    window.road_network_toolbox.road_network_toolbox_ui.selected_lanelet_one.setCurrentText(str(first_l_id))
    window.road_network_toolbox.lanelet_controller.add_lanelet()
    predecessor_l_id = window.road_network_toolbox.last_added_lanelet_id

    # add third lanelet as successor
    window.road_network_toolbox.road_network_toolbox_ui.connect_to_selected_selection.click()
    window.road_network_toolbox.road_network_toolbox_ui.as_predecessor.setChecked(False)
    window.road_network_toolbox.road_network_toolbox_ui.as_successor.setChecked(True)
    window.road_network_toolbox.road_network_toolbox_ui.selected_lanelet_one.setCurrentText(str(first_l_id))
    window.road_network_toolbox.lanelet_controller.add_lanelet()
    successor_l_id = window.road_network_toolbox.last_added_lanelet_id
    # find all three created lanelets
    first_lanelet = window.scenario_model.find_lanelet_by_id(first_l_id)
    predecessor_lanelet = window.scenario_model.find_lanelet_by_id(predecessor_l_id)
    successor_lanelet = window.scenario_model.find_lanelet_by_id(successor_l_id)

    return first_lanelet, predecessor_lanelet, successor_lanelet


def execute_add_lanelet_test(window):
    first_lanelet, predecessor_lanelet, successor_lanelet = add_lanelets(window=window)

    # check if predecessor and successor relationship is correctly set
    assert successor_lanelet.lanelet_id in first_lanelet.successor
    assert predecessor_lanelet.lanelet_id in first_lanelet.predecessor


def execute_remove_multiple_lanelet_test(window):
    first_lanelet, predecessor_lanelet, successor_lanelet = add_lanelets(window=window)
    window.road_network_toolbox.road_network_toolbox_ui.selected_lanelet_update.set_checked_items(
        [str(first_lanelet.lanelet_id), str(predecessor_lanelet.lanelet_id), str(successor_lanelet.lanelet_id)]
    )
    window.road_network_toolbox.lanelet_controller.remove_lanelet()

    assert 0 == len(window.scenario_model.get_current_scenario().lanelet_network.lanelets)


def execute_update_multiple_lanelet_test(window):
    # create three connected lanelets in road network
    first_lanelet, predecessor_lanelet, successor_lanelet = add_lanelets(window=window)

    window.road_network_toolbox.road_network_toolbox_ui.selected_number_vertices.setText("20")
    # select all lanelets
    window.road_network_toolbox.road_network_toolbox_ui.selected_lanelet_update.set_checked_items(
        [str(first_lanelet.lanelet_id), str(predecessor_lanelet.lanelet_id), str(successor_lanelet.lanelet_id)]
    )
    window.road_network_toolbox.lanelet_controller.lanelet_ui.update_lanelet_information(first_lanelet)
    # set parameters for updating
    window.road_network_toolbox.road_network_toolbox_ui.selected_lanelet_start_position_x.setText("0")
    window.road_network_toolbox.road_network_toolbox_ui.selected_lanelet_start_position_y.setText("0")
    window.road_network_toolbox.road_network_toolbox_ui.selected_lanelet_end_position_x.setText("10")
    window.road_network_toolbox.road_network_toolbox_ui.selected_lanelet_end_position_y.setText("0")
    window.road_network_toolbox.road_network_toolbox_ui.selected_lanelet_length.setText("10")
    window.road_network_toolbox.road_network_toolbox_ui.selected_lanelet_width.setText("3")
    # update all lanelets
    window.road_network_toolbox.lanelet_controller.update_lanelet()

    # since all lanelets were updated to same position -> they all have the same left and right vertices
    left_vertices = window.scenario_model.get_lanelets()[0].left_vertices
    rights_vertices = window.scenario_model.get_lanelets()[0].right_vertices
    for lanelet in window.scenario_model.get_lanelets()[1:]:
        # compare left vertices
        assert len(lanelet.left_vertices) == len(left_vertices)
        for index, vertex in enumerate(lanelet.left_vertices):
            assert vertex[0] == left_vertices[index][0]
        # compare right vertices
        assert len(lanelet.right_vertices) == len(rights_vertices)
        for index, vertex in enumerate(lanelet.right_vertices):
            assert vertex[0] == rights_vertices[index][0]


def execute_translate_multiple_lanelet_test(window):
    # create three connected lanelets
    first_lanelet, predecessor_lanelet, successor_lanelet = add_lanelets(window=window)
    # add them to the selected lanelets combo box
    window.road_network_toolbox.road_network_toolbox_ui.selected_lanelet_one.set_checked_items(
        [str(first_lanelet.lanelet_id), str(predecessor_lanelet.lanelet_id), str(successor_lanelet.lanelet_id)]
    )

    window.road_network_toolbox.road_network_toolbox_ui.y_translation.setText("10")
    window.road_network_toolbox.road_network_toolbox_ui.x_translation.setText("10")
    # save the old left vertices of each lanelet
    first_lanelet_left_vertices_old = first_lanelet.left_vertices
    predecessor_lanelet_left_vertices_old = predecessor_lanelet.left_vertices
    successor_lanelet_left_vertices_old = successor_lanelet.left_vertices

    window.road_network_toolbox.lanelet_controller.translate_lanelet()
    # iterate through the left vertices and check if the new coordinates are correct
    for index, vertice in enumerate(first_lanelet.left_vertices):
        assert vertice[0] == first_lanelet_left_vertices_old[index][0] + 10
        assert vertice[1] == first_lanelet_left_vertices_old[index][1] + 10

    for index, vertice in enumerate(predecessor_lanelet.left_vertices):
        assert vertice[0] == predecessor_lanelet_left_vertices_old[index][0] + 10
        assert vertice[1] == predecessor_lanelet_left_vertices_old[index][1] + 10

    for index, vertice in enumerate(successor_lanelet.left_vertices):
        assert vertice[0] == successor_lanelet_left_vertices_old[index][0] + 10
        assert vertice[1] == successor_lanelet_left_vertices_old[index][1] + 10


def calculate_width(lanelet_1: Lanelet):
    return lanelet_1.left_vertices[0][1] - lanelet_1.right_vertices[0][1]


def execute_rotate_multiple_lanelet_test(window):
    # create three connected lanelets
    first_lanelet, predecessor_lanelet, successor_lanelet = add_lanelets(window=window)
    # add them to the selected lanelets combo box
    window.road_network_toolbox.road_network_toolbox_ui.selected_lanelet_one.set_checked_items(
        [str(first_lanelet.lanelet_id), str(predecessor_lanelet.lanelet_id), str(successor_lanelet.lanelet_id)]
    )

    window.road_network_toolbox.road_network_toolbox_ui.rotation_angle.setValue(90)

    window.road_network_toolbox.lanelet_controller.rotate_lanelet()
    # iterate through lanelets and compare with new lanelets
    for lanelet in [first_lanelet, predecessor_lanelet, successor_lanelet]:
        new_lanelet = [
            elem
            for elem in window.scenario_model.get_current_scenario().lanelet_network.lanelets
            if elem.lanelet_id == lanelet.lanelet_id
        ][0]
        assert (
            lanelet.left_vertices[-1][1] + 10 - (calculate_width(lanelet_1=first_lanelet) / 2)
            == new_lanelet.left_vertices[-1][1]
        )


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
