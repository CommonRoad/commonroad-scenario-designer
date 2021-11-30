from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from ui.gui.mwindow.service_layer.gui_src import CR_Scenario_Designer # do not remove! This is for the correct paths
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
        self.action_road_network_toolbox = QAction(QIcon(":/icons/road_network_toolbox.png"), "Open Road Network Toolbox", mwindow)
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
        self.button_play_pause.triggered.connect(lambda: play_pause_animation(mwindow=mwindow, open_commonroad_file=(lambda: open_commonroad_file(mwindow))))
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
        mwindow.cr_viewer.time_step.subscribe(self.slider.setValue)
        self.tb4.addWidget(self.slider)

        self.label1 = QLabel('  Time Stamp: 0', mwindow)
        self.tb4.addWidget(self.label1)

        self.label2 = QLabel(' / 0', mwindow)
        self.tb4.addWidget(self.label2)

        self.action_save_video = QAction(QIcon(":/icons/save_video.png"), "Save Video", mwindow)
        self.tb4.addAction(self.action_save_video)
        self.action_save_video.triggered.connect(_save_video)


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
    """Function connected with the play button in the sumo-toolbar_wrapper."""
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
        mwindow.console_wrapper.text_browser.append("Playing the animation")
        mwindow.toolbar_wrapper.button_play_pause.setIcon(QIcon(":/icons/pause.png"))
        mwindow.play_activated = True
    else:
        mwindow.cr_viewer.pause()
        mwindow.console.text_browser.append("Pause the animation")
        mwindow.toolbar_wrapper.button_play_pause.setIcon(QIcon(":/icons/play.png"))
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
