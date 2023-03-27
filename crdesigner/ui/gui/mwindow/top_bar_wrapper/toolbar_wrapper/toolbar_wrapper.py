import math
import sys

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from crdesigner.ui.gui.mwindow.service_layer import config
from crdesigner.ui.gui.mwindow.service_layer.gui_src import CR_Scenario_Designer


# of the icons


class ToolBarWrapper:
    """
    Wrapper class for the toolbar_wrapper.
    """

    def __init__(self, mwindow, file_new, open_commonroad_file, file_save):
        self.mwindow = mwindow  # reference to the main window
        self.tb1 = mwindow.addToolBar("File")
        self.action_new = QAction(QIcon(":/icons/new_file.png"), "new CR File", mwindow)
        self.tb1.addAction(self.action_new)
        self.action_new.triggered.connect(lambda: file_new(mwindow))
        self.action_open = QAction(QIcon(":/icons/open_file.png"), "open CR File", mwindow)
        self.tb1.addAction(self.action_open)
        self.action_open.triggered.connect(lambda: open_commonroad_file(mwindow))
        self.action_save = QAction(QIcon(":/icons/save_file.png"), "save CR File", mwindow)
        self.tb1.addAction(self.action_save)
        self.action_save.triggered.connect(lambda: file_save(mwindow))

        self.tb1.addSeparator()
        self.tb2 = mwindow.addToolBar("Toolboxes")
        self.action_road_network_toolbox = QAction(QIcon(":/icons/road_network_toolbox.png"),
                                                   "Open Road Network Toolbox", mwindow)
        self.tb2.addAction(self.action_road_network_toolbox)
        self.action_road_network_toolbox.triggered.connect(lambda: _road_network_toolbox_show(mwindow))
        self.action_obstacle_toolbox = QAction(QIcon(":/icons/obstacle_toolbox.png"), "Open Obstacle Toolbox", mwindow)
        self.tb2.addAction(self.action_obstacle_toolbox)
        self.action_obstacle_toolbox.triggered.connect(lambda: _obstacle_toolbox_show(mwindow))
        self.action_converter_toolbox = QAction(QIcon(":/icons/tools.ico"), "Open Map Converter Toolbox", mwindow)
        self.tb2.addAction(self.action_converter_toolbox)
        self.action_converter_toolbox.triggered.connect(lambda: _map_converter_toolbox_show(mwindow))
        self.tb2.addSeparator()

        self.tb3 = mwindow.addToolBar("Undo/Redo")

        self.action_undo = QAction(QIcon(":/icons/button_undo.png"), "undo last action", mwindow)
        self.tb3.addAction(self.action_undo)
        self.action_undo.triggered.connect(lambda: _undo_action(mwindow))

        self.action_redo = QAction(QIcon(":/icons/button_redo.png"), "redo last action", mwindow)
        self.tb3.addAction(self.action_redo)
        self.action_redo.triggered.connect(lambda: _redo_action(mwindow))

        self.tb3.addSeparator()

        self.tb4 = mwindow.addToolBar("Animation Play")
        self.button_play_pause = QAction(QIcon(":/icons/play.png"), "Play the animation", mwindow)
        self.button_play_pause.triggered.connect(
            lambda: play_pause_animation(mwindow=mwindow, open_commonroad_file=(lambda mw: open_commonroad_file(mw))))
        self.tb4.addAction(self.button_play_pause)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMaximumWidth(300)
        self.slider.setValue(0)
        self.slider.setMinimum(0)
        self.slider.setMaximum(99)
        # self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(1)
        self.slider.setToolTip("Show corresponding Scenario at selected timestep")
        self.slider.valueChanged.connect(lambda value, ov=mwindow: _time_step_change(value=value, mwindow=ov))
        self.slider.sliderPressed.connect(lambda: _detect_slider_clicked(mwindow))
        self.slider.sliderReleased.connect(lambda: _detect_slider_release(mwindow))
        mwindow.animated_viewer_wrapper.cr_viewer.time_step.subscribe(self.slider.setValue)
        self.tb4.addWidget(self.slider)

        self.label1 = QLabel('  Time Stamp:', mwindow)
        self.tb4.addWidget(self.label1)

        self.edit = QLineEdit()
        validator = QIntValidator()
        validator.setBottom(0)
        self.edit.setValidator(validator)
        self.edit.setText('0')
        self.edit.setAlignment(Qt.AlignRight)
        self.edit.textChanged.connect(lambda: _time_step_set(mwindow))
        self.edit.setMaximumWidth(40)
        self.tb4.addWidget(self.edit)

        self.label2 = QLabel(' / 0', mwindow)
        self.tb4.addWidget(self.label2)

        self.action_save_video = QAction(QIcon(":/icons/save_video.png"), "Save Video", mwindow)
        self.tb4.addAction(self.action_save_video)
        self.action_save_video.triggered.connect(lambda: _save_video(mwindow, open_commonroad_file))

        self.tb4.addSeparator()

        self.tb5 = mwindow.addToolBar("Lanelet Operations")

        self.drawing_mode = QAction(QIcon(":/icons/drawing_mode.png"), "draw lanes", mwindow)
        self.drawing_mode.setCheckable(True)
        self.tb5.addAction(self.drawing_mode)
        self.drawing_mode.triggered.connect(lambda: _drawing_mode(mwindow, self.drawing_mode.isChecked()))

        self.add_adjacent_left = QAction(QIcon(":/icons/add_adjacent_left.png"), "add adjacent left", mwindow)
        self.tb5.addAction(self.add_adjacent_left)
        self.add_adjacent_left.setDisabled(True)
        self.add_adjacent_left.triggered.connect(lambda: _add_adj_left(mwindow))

        self.add_adjacent_right = QAction(QIcon(":/icons/add_adjacent_right.png"), "add adjacent right", mwindow)
        self.tb5.addAction(self.add_adjacent_right)
        self.add_adjacent_right.setDisabled(True)
        self.add_adjacent_right.triggered.connect(lambda: _add_adj_right(mwindow))

        self.split_lanelet = QAction(QIcon(":/icons/split_lanelet.png"), "split lane", mwindow)
        self.split_lanelet.setCheckable(True)
        self.tb5.addAction(self.split_lanelet)
        self.split_lanelet.triggered.connect(lambda: _split_lanelet(mwindow, self.split_lanelet.isChecked()))
        self.split_lanelet.setDisabled(True)

        self.merge_lanelet = QAction(QIcon(":/icons/merge_lanelet.png"), "merge lanes", mwindow)
        self.tb5.addAction(self.merge_lanelet)
        self.merge_lanelet.triggered.connect(lambda: _merge_lanelets(mwindow))
        self.merge_lanelet.setDisabled(True)

    def reset_toolbar(self):
        if self.split_lanelet.isChecked():
            self.split_lanelet.trigger()
        if self.drawing_mode.isChecked():
            self.drawing_mode.trigger()

    def enable_toolbar(self, number_of_selected_lanelets):
        self.split_lanelet.setDisabled(True)
        self.add_adjacent_left.setDisabled(True)
        self.add_adjacent_right.setDisabled(True)
        self.merge_lanelet.setDisabled(True)
        if number_of_selected_lanelets == 1:
            self.split_lanelet.setDisabled(False)
        if number_of_selected_lanelets >= 1:
            self.add_adjacent_right.setDisabled(False)
            self.add_adjacent_left.setDisabled(False)
        if number_of_selected_lanelets >= 2:
            self.merge_lanelet.setDisabled(False)


# functions which are passed as arguments to elements of the gui


def _road_network_toolbox_show(mwindow):
    """
        Show the network Toolbox.
    """
    mwindow.road_network_toolbox.show()


def _obstacle_toolbox_show(mwindow):
    """
        Show the obstacle Toolbox.
    """
    mwindow.obstacle_toolbox.show()


def _map_converter_toolbox_show(mwindow):
    """
        Show the Map converter Toolbox.
    """
    mwindow.map_converter_toolbox.show()


def _undo_action(mwindow):
    """
        Undo any action.
    """
    if mwindow.current_scenario_index >= 0:
        mwindow.current_scenario_index -= 1
    else:
        return
    mwindow.animated_viewer_wrapper.cr_viewer.current_scenario = mwindow.scenarios[mwindow.current_scenario_index]
    mwindow.animated_viewer_wrapper.cr_viewer.original_lanelet_network = mwindow.scenarios[
        mwindow.current_scenario_index].lanelet_network
    mwindow.animated_viewer_wrapper.update_view(focus_on_network=True)
    mwindow.update_toolbox_scenarios()


def _redo_action(mwindow):
    """
        Redo any action.
    """
    if mwindow.current_scenario_index < len(mwindow.scenarios) - 1:
        mwindow.current_scenario_index += 1
    else:
        return
    mwindow.animated_viewer_wrapper.cr_viewer.current_scenario = mwindow.scenarios[mwindow.current_scenario_index]
    mwindow.animated_viewer_wrapper.cr_viewer.original_lanelet_network = mwindow.scenarios[
        mwindow.current_scenario_index].lanelet_network
    mwindow.animated_viewer_wrapper.update_view(focus_on_network=True)
    mwindow.update_toolbox_scenarios()


def play_pause_animation(mwindow, open_commonroad_file):
    """Function connected with the play button in the sumo-toolbar_wrapper."""
    if not mwindow.animated_viewer_wrapper.cr_viewer.current_scenario:
        messbox = QMessageBox()
        reply = messbox.warning(mwindow, "Warning",
                                "Please load or create a CommonRoad scenario before attempting to play",
                                QMessageBox.Ok | QMessageBox.No, QMessageBox.Ok)
        if reply == QMessageBox.Ok:
            open_commonroad_file(mwindow)
        return
    if not mwindow.play_activated:
        mwindow.animated_viewer_wrapper.cr_viewer.play()
        mwindow.crdesigner_console_wrapper.text_browser.append("Playing the animation")
        if config.DARKMODE:
            mwindow.top_bar_wrapper.toolbar_wrapper.button_play_pause.setIcon(QIcon(":/icons/pause_darkmode.png"))
        else:
            mwindow.top_bar_wrapper.toolbar_wrapper.button_play_pause.setIcon(QIcon(":/icons/pause.png"))
        mwindow.play_activated = True
    else:
        mwindow.animated_viewer_wrapper.cr_viewer.pause()
        mwindow.crdesigner_console_wrapper.text_browser.append("Pause the animation")
        mwindow.top_bar_wrapper.toolbar_wrapper.button_play_pause.setIcon(QIcon(":/icons/play.png"))
        mwindow.play_activated = False


def _time_step_change(mwindow, value):
    if mwindow.animated_viewer_wrapper.cr_viewer.current_scenario:
        mwindow.animated_viewer_wrapper.cr_viewer.set_timestep(value)
        mwindow.top_bar_wrapper.toolbar_wrapper.edit.setText(str(value))
        mwindow.animated_viewer_wrapper.cr_viewer.animation.event_source.start()


def _time_step_set(mwindow):
    if mwindow.top_bar_wrapper.toolbar_wrapper.edit.text() == "":
        return
    if mwindow.animated_viewer_wrapper.cr_viewer.current_scenario:
        mwindow.top_bar_wrapper.toolbar_wrapper.slider.setValue(
                int(float(mwindow.top_bar_wrapper.toolbar_wrapper.edit.text())))
        mwindow.animated_viewer_wrapper.cr_viewer.pause()
        mwindow.animated_viewer_wrapper.cr_viewer.dynamic.draw_idle()
        mwindow.animated_viewer_wrapper.update_view()


def _detect_slider_clicked(mwindow):
    mwindow.slider_clicked = True
    mwindow.animated_viewer_wrapper.cr_viewer.pause()
    mwindow.animated_viewer_wrapper.cr_viewer.dynamic.draw_idle()


def _detect_slider_release(mwindow):
    mwindow.slider_clicked = False
    mwindow.animated_viewer_wrapper.cr_viewer.pause()


def _save_video(mwindow, open_commonroad_file):
    """Function connected with the save button in the Toolbar."""
    if not mwindow.animated_viewer_wrapper.cr_viewer.current_scenario:
        messbox = QMessageBox()
        reply = messbox.warning(mwindow, "Warning", "Please load or create a CommonRoad scenario before saving a video",
                                QMessageBox.Ok | QMessageBox.No, QMessageBox.Ok)
        if reply == QMessageBox.Ok:
            open_commonroad_file(mwindow)
        else:
            messbox.close()
    else:
        mwindow.crdesigner_console_wrapper.text_browser.append("Save video for scenario with ID " + str(
                mwindow.animated_viewer_wrapper.cr_viewer.current_scenario.scenario_id))
        mwindow.animated_viewer_wrapper.cr_viewer.save_animation()
        mwindow.crdesigner_console_wrapper.text_browser.append("Saving the video finished.")


def _split_lanelet(mwindow, is_checked):
    mwindow.animated_viewer_wrapper.cr_viewer.dynamic.activate_split_lanelet(is_checked)


def _drawing_mode(mwindow, is_checked):
    mwindow.animated_viewer_wrapper.cr_viewer.dynamic.activate_drawing_mode(is_checked)


def _add_adj_left(mwindow):
    mwindow.animated_viewer_wrapper.cr_viewer.dynamic.add_adjacent(True)


def _add_adj_right(mwindow):
    mwindow.animated_viewer_wrapper.cr_viewer.dynamic.add_adjacent(False)


def _merge_lanelets(mwindow):
    mwindow.animated_viewer_wrapper.cr_viewer.dynamic.merge_lanelets()
