"""
    The main entrance to the toolbar.
"""

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


def create_toolbar(mwindow, file_new, open_commonroad_file, file_save):
    """Function to create toolbar of the main Window."""
    tb1 = mwindow.addToolBar("File")
    action_new = QAction(QIcon(":/icons/new_file.png"), "new CR File", mwindow)
    tb1.addAction(action_new)
    action_new.triggered.connect(file_new)
    action_open = QAction(QIcon(":/icons/open_file.png"), "open CR File", mwindow)
    tb1.addAction(action_open)
    action_open.triggered.connect(open_commonroad_file)
    action_save = QAction(QIcon(":/icons/save_file.png"), "save CR File", mwindow)
    tb1.addAction(action_save)
    action_save.triggered.connect(file_save)

    tb1.addSeparator()
    tb2 = mwindow.addToolBar("Toolboxes")
    action_road_network_toolbox = QAction(QIcon(":/icons/road_network_toolbox.png"), "Open Road Network Toolbox", mwindow)
    tb2.addAction(action_road_network_toolbox)
    action_road_network_toolbox.triggered.connect(_road_network_toolbox_show)
    action_obstacle_toolbox = QAction(QIcon(":/icons/obstacle_toolbox.png"), "Open Obstacle Toolbox", mwindow)
    tb2.addAction(action_obstacle_toolbox)
    action_obstacle_toolbox.triggered.connect(_obstacle_toolbox_show)
    action_converter_toolbox = QAction(QIcon(":/icons/tools.ico"), "Open Map Converter Toolbox", mwindow)
    tb2.addAction(action_converter_toolbox)
    action_converter_toolbox.triggered.connect(_map_converter_toolbox_show)
    tb2.addSeparator()

    tb3 = mwindow.addToolBar("Undo/Redo")

    action_undo = QAction(QIcon(":/icons/button_undo.png"), "undo last action", mwindow)
    tb3.addAction(action_undo)
    action_undo.triggered.connect(_undo_action)

    action_redo = QAction(QIcon(":/icons/button_redo.png"), "redo last action", mwindow)
    tb3.addAction(action_redo)
    action_redo.triggered.connect(_redo_action)

    tb3.addSeparator()

    tb4 = mwindow.addToolBar("Animation Play")
    mwindow.button_play_pause = QAction(QIcon(":/icons/play.png"), "Play the animation", mwindow)
    mwindow.button_play_pause.button_play_pause.triggered.connect(play_pause_animation)
    tb4.addAction(mwindow.button_play_pause)

    mwindow.slider = QSlider(Qt.Horizontal)
    mwindow.slider.setMaximumWidth(300)
    mwindow.slider.setValue(0)
    mwindow.slider.setMinimum(0)
    mwindow.slider.setMaximum(99)
    # self.slider.setTickPosition(QSlider.TicksBelow)
    mwindow.slider.setTickInterval(1)
    mwindow.slider.setToolTip("Show corresponding Scenario at selected timestep")
    mwindow.slider.valueChanged.connect(_time_step_change)
    mwindow.slider.sliderPressed.connect(_detect_slider_clicked)
    mwindow.slider.sliderReleased.connect(_detect_slider_release)
    mwindow.cr_viewer.time_step.subscribe(mwindow.slider.setValue)
    tb4.addWidget(mwindow.slider)

    mwindow.label1 = QLabel('  Time Stamp: 0', mwindow)
    tb4.addWidget(mwindow.label1)

    mwindow.label2 = QLabel(' / 0', mwindow)
    tb4.addWidget(mwindow.label2)

    action_save_video = QAction(QIcon(":/icons/save_video.png"), "Save Video", mwindow)
    tb4.addAction(action_save_video)
    action_save_video.triggered.connect(_save_video)

    return mwindow.button_play_pause, mwindow.label1, mwindow.label2  # return for the sake of consistency


def _road_network_toolbox_show(mwindow):
    """
        Show the network Toolbox.
    """
    mwindow.road_network_toolbox.show()


def _obstacle_toolbox_show(self):
    """
        Show the obstacle Toolbox.
    """
    self.obstacle_toolbox.show()


def _map_converter_toolbox_show(self):
    """
        Show the Map converter Toolbox.
    """
    self.map_converter_toolbox.show()


def _undo_action(mwindow):
    """
        Undo any action.
    """
    if mwindow.current_scenario_index >= 0:
        mwindow.current_scenario_index -= 1
    else:
        return
    mwindow.cr_viewer.current_scenario = mwindow.scenarios[mwindow.current_scenario_index]
    mwindow.update_view(focus_on_network=True)
    mwindow.update_toolbox_scenarios()


def _redo_action(mwindow):
    """
        Redo any action.
    """
    if mwindow.current_scenario_index < len(mwindow.scenarios) - 1:
        mwindow.current_scenario_index += 1
    else:
        return
    mwindow.cr_viewer.current_scenario = mwindow.scenarios[mwindow.current_scenario_index]
    mwindow.update_view(focus_on_network=True)
    mwindow.update_toolbox_scenarios()


def play_pause_animation(mwindow, open_commonroad_file):
    """Function connected with the play button in the sumo-toolbar."""
    if not mwindow.cr_viewer.current_scenario:
        messbox = QMessageBox()
        reply = messbox.warning(
            mwindow, "Warning",
            "Please load or create a CommonRoad scenario before attempting to play",
            QMessageBox.Ok | QMessageBox.No, QMessageBox.Ok)
        if (reply == QMessageBox.Ok):
            open_commonroad_file()
        return
    if not mwindow.play_activated:
        mwindow.cr_viewer.play()
        mwindow.text_browser.append("Playing the animation")
        mwindow.button_play_pause.setIcon(QIcon(":/icons/pause.png"))
        mwindow.play_activated = True
    else:
        mwindow.cr_viewer.pause()
        mwindow.text_browser.append("Pause the animation")
        mwindow.button_play_pause.setIcon(QIcon(":/icons/play.png"))
        mwindow.play_activated = False


def _time_step_change(mwindow, value):
    if mwindow.cr_viewer.current_scenario:
        mwindow.cr_viewer.set_timestep(value)
        mwindow.label1.setText('  Time Stamp: ' + str(value))
        mwindow.cr_viewer.animation.event_source.start()


def _detect_slider_clicked(mwindow):
    mwindow.slider_clicked = True
    mwindow.cr_viewer.pause()
    mwindow.cr_viewer.dynamic.update_plot()


def _detect_slider_release(mwindow):
    mwindow.slider_clicked = False
    mwindow.cr_viewer.pause()


def _save_video(mwindow, open_commonroad_file):
    """Function connected with the save button in the Toolbar."""
    if not mwindow.cr_viewer.current_scenario:
        messbox = QMessageBox()
        reply = messbox.warning(mwindow, "Warning",
                                "Please load or create a CommonRoad scenario before saving a video",
                                QMessageBox.Ok | QMessageBox.No,
                                QMessageBox.Ok)
        if (reply == QMessageBox.Ok):
            open_commonroad_file()
        else:
            messbox.close()
    else:
        mwindow.text_browser.append("Save video for scenario with ID " +
                                 str(mwindow.cr_viewer.current_scenario.scenario_id))
        mwindow.cr_viewer.save_animation()
        mwindow.text_browser.append("Saving the video finished.")
