from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMessageBox

from crdesigner.common.config.gui_config import gui_config
from crdesigner.common.config.gui_config import gui_config as config
from crdesigner.common.logging import logger
from crdesigner.ui.gui.utilities.file_actions import (
    file_new,
    file_save,
    open_commonroad_file,
)
from crdesigner.ui.gui.view.top_bar.tool_bar_ui import ToolBarUI


class ToolBarController:
    def __init__(self, mwindow):
        self.mwindow = mwindow
        self.mwindow_ui = mwindow.mwindow_ui
        self.tool_bar_ui = ToolBarUI(mwindow_ui=self.mwindow_ui)
        self._connect_gui_elements()

    def _connect_gui_elements(self):
        # File actions
        self.tool_bar_ui.action_new.triggered.connect(lambda: file_new(self.mwindow))
        self.tool_bar_ui.action_open.triggered.connect(lambda: open_commonroad_file(self.mwindow))
        self.tool_bar_ui.action_save.triggered.connect(lambda: file_save(self.mwindow))

        # Toolboxes
        self.tool_bar_ui.action_road_network_toolbox.triggered.connect(
            lambda: self._road_network_toolbox_show()
        )
        self.tool_bar_ui.action_obstacle_toolbox.triggered.connect(
            lambda: self._obstacle_toolbox_show()
        )
        self.tool_bar_ui.action_converter_toolbox.triggered.connect(
            lambda: self._map_converter_toolbox_show()
        )
        self.tool_bar_ui.action_scenario_toolbox.triggered.connect(
            lambda: self._scenario_toolbox_show()
        )

        # Undo / Redo
        self.tool_bar_ui.action_redo.triggered.connect(lambda: self.mwindow.scenario_model.redo())
        self.tool_bar_ui.action_undo.triggered.connect(lambda: self.mwindow.scenario_model.undo())

        # Animation Player
        self.tool_bar_ui.button_play_pause.triggered.connect(
            lambda: self.play_pause_animation(open_cr_file=(lambda mw: open_commonroad_file(mw)))
        )
        self.tool_bar_ui.slider.valueChanged.connect(
            lambda value: self._time_step_change(value=value)
        )
        self.tool_bar_ui.slider.sliderPressed.connect(lambda: self._detect_slider_clicked())
        self.tool_bar_ui.slider.sliderReleased.connect(lambda: self._detect_slider_release())

        self.mwindow.animated_viewer_wrapper.cr_viewer.time_step.subscribe(
            self.tool_bar_ui.slider.setValue
        )
        self.tool_bar_ui.edit.textChanged.connect(lambda: self._time_step_set())
        self.tool_bar_ui.action_save_video.triggered.connect(
            lambda: self._save_video(open_commonroad_file)
        )

        # Lanelet Operations
        self.tool_bar_ui.drawing_mode.triggered.connect(
            lambda: self._drawing_mode(self.tool_bar_ui.drawing_mode.isChecked())
        )
        self.tool_bar_ui.add_adjacent_left.triggered.connect(lambda: self._add_adj_left())
        self.tool_bar_ui.add_adjacent_right.triggered.connect(lambda: self._add_adj_right())
        self.tool_bar_ui.split_lanelet.triggered.connect(
            lambda: self._split_lanelet(self.tool_bar_ui.split_lanelet.isChecked())
        )
        self.tool_bar_ui.merge_lanelet.triggered.connect(lambda: self._merge_lanelets())

        # Cropp Map
        self.tool_bar_ui.crop_map.triggered.connect(
            lambda: self._crop_map(self.tool_bar_ui.crop_map.isChecked())
        )

        self.tool_bar_ui.cancel_edit_vertices.triggered.connect(
            lambda: self._cancel_edit_vertices()
        )

    def _road_network_toolbox_show(self):
        """
        Show the network Toolbox.
        """
        self.mwindow.road_network_toolbox.show()

    def _obstacle_toolbox_show(self):
        """
        Show the obstacle Toolbox.
        """
        self.mwindow_ui.obstacle_toolbox.show()

    def _map_converter_toolbox_show(self):
        """
        Show the Map converter Toolbox.
        """
        self.mwindow_ui.map_converter_toolbox.show()

    def _scenario_toolbox_show(self):
        """
        Show the Scenario Toolbox.
        """
        self.mwindow_ui.scenario_toolbox.show()

    @logger.log
    def play_pause_animation(self, open_cr_file):
        """Function connected with the play button in the sumo-toolbar_wrapper."""
        if not self.mwindow.scenario_model.scenario_created():
            messagebox = QMessageBox()
            reply = messagebox.warning(
                self.mwindow_ui,
                "Warning",
                "Please load or create a CommonRoad scenario before attempting to play",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Ok,
            )
            if reply == QMessageBox.StandardButton.Ok:
                open_cr_file(self.mwindow)
            return
        if not gui_config.show_dynamic_obstacles():
            messagebox = QMessageBox()
            messagebox.warning(
                self.mwindow_ui,
                "Warning",
                "Please enable the display of dynamic obstacles in the settings ",
                QMessageBox.StandardButton.Ok,
            )

            return
        if not self.mwindow.play_activated:
            self.mwindow.animated_viewer_wrapper.cr_viewer.play()
            self.mwindow.crdesigner_console_wrapper.text_browser.append("Playing the animation")
            if config.DARKMODE:
                self.mwindow_ui.top_bar.toolbar_wrapper.tool_bar_ui.button_play_pause.setIcon(
                    QIcon(":/icons/pause_darkmode.png")
                )
            else:
                self.mwindow_ui.top_bar.toolbar_wrapper.tool_bar_ui.button_play_pause.setIcon(
                    QIcon(":/icons/pause.png")
                )
            self.mwindow.play_activated = True
            self.mwindow_ui.play_activated = True
        else:
            self.mwindow.animated_viewer_wrapper.cr_viewer.pause()
            self.mwindow.crdesigner_console_wrapper.text_browser.append("Pause the animation")
            self.mwindow_ui.top_bar.toolbar_wrapper.tool_bar_ui.button_play_pause.setIcon(
                QIcon(":/icons/play.png")
            )
            self.mwindow.play_activated = False
            self.mwindow_ui.play_activated = False

    def _time_step_change(self, value):
        if self.mwindow.scenario_model.scenario_created():
            self.mwindow.animated_viewer_wrapper.cr_viewer.set_timestep(value)
            self.mwindow_ui.top_bar.toolbar_wrapper.tool_bar_ui.edit.setText(str(value))
            self.mwindow.animated_viewer_wrapper.cr_viewer.animation.event_source.start()

            self.mwindow_ui.obstacle_toolbox.animate_obstacle_profile_state(value)

    def _time_step_set(self):
        if self.mwindow_ui.top_bar.toolbar_wrapper.tool_bar_ui.edit.text() == "":
            return
        if self.mwindow.scenario_model.scenario_created():
            self.mwindow_ui.top_bar.toolbar_wrapper.tool_bar_ui.slider.setValue(
                int(float(self.mwindow_ui.top_bar.toolbar_wrapper.tool_bar_ui.edit.text()))
            )
            self.mwindow.animated_viewer_wrapper.cr_viewer.pause()
            self.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.draw_idle()

    def _detect_slider_clicked(self):
        self.mwindow.slider_clicked = True
        self.mwindow.animated_viewer_wrapper.cr_viewer.pause()
        self.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.draw_idle()

    def _detect_slider_release(self):
        self.mwindow.slider_clicked = False
        self.mwindow.animated_viewer_wrapper.cr_viewer.pause()

    def _save_video(self, open_cr_file):
        """Function connected with the save button in the Toolbar."""
        if not self.mwindow.scenario_model.scenario_created():
            messbox = QMessageBox()
            reply = messbox.warning(
                self.mwindow.mwindow_ui,
                "Warning",
                "Please load or create a CommonRoad scenario before saving a video",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Ok,
            )
            if reply == QMessageBox.StandardButton.Ok:
                open_cr_file(self.mwindow)
            else:
                messbox.close()
        else:
            self.mwindow.crdesigner_console_wrapper.text_browser.append(
                "Save video for scenario with ID "
                + str(self.mwindow.scenario_model.get_scenario_id())
            )
            self.mwindow.animated_viewer_wrapper.cr_viewer.save_animation()
            self.mwindow.crdesigner_console_wrapper.text_browser.append(
                "Saving the video finished."
            )

    @logger.log
    def _split_lanelet(self, is_checked):
        self.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.activate_split_lanelet(is_checked)

    @logger.log
    def _drawing_mode(self, is_checked):
        self.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.activate_drawing_mode(is_checked)

    @logger.log
    def _add_adj_left(self):
        self.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.add_adjacent(True)

    @logger.log
    def _add_adj_right(self):
        self.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.add_adjacent(False)

    @logger.log
    def _merge_lanelets(self):
        self.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.merge_lanelets()

    @logger.log
    def _crop_map(self, is_checked: bool) -> None:
        """
        Private function to call the activate_cropp_map function of the DynamicCanvasController

        :param is_checked: Boolean which states whether the button is clicked or not
        """
        self.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.activate_crop_map(is_checked)

    def _cancel_edit_vertices(self):
        """
        Cancels the display of the vertices
        """
        self.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.cancel_edit_vertices()
