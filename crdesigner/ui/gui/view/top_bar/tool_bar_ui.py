from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon, QIntValidator
from PyQt6.QtWidgets import QLabel, QLineEdit, QSlider

from crdesigner.ui.gui.resources.icons import CR_Scenario_Designer

# Otherwise the import seems unused
CR_Scenario_Designer.qInitResources()


class ToolBarUI:
    def __init__(self, mwindow_ui):
        self.mwindow_ui = mwindow_ui

        # File actions
        self.tb1 = mwindow_ui.addToolBar("File")
        self.action_new = QAction(QIcon(":/icons/new_file.png"), "new CR File", mwindow_ui)
        self.tb1.addAction(self.action_new)

        self.action_open = QAction(QIcon(":/icons/open_file.png"), "open CR File", mwindow_ui)
        self.tb1.addAction(self.action_open)

        self.action_save = QAction(QIcon(":/icons/save_file.png"), "save CR File", mwindow_ui)
        self.tb1.addAction(self.action_save)

        # Toolboxes
        self.tb1.addSeparator()
        self.tb2 = mwindow_ui.addToolBar("Toolboxes")

        self.action_road_network_toolbox = QAction(
            QIcon(":/icons/road_network_toolbox.png"), "Open Road Network Toolbox", mwindow_ui
        )
        self.tb2.addAction(self.action_road_network_toolbox)

        self.action_obstacle_toolbox = QAction(
            QIcon(":/icons/obstacle_toolbox.png"), "Open Obstacle Toolbox", mwindow_ui
        )
        self.tb2.addAction(self.action_obstacle_toolbox)

        self.action_converter_toolbox = QAction(
            QIcon(":/icons/tools.ico"), "Open Map Converter Toolbox", mwindow_ui
        )
        self.tb2.addAction(self.action_converter_toolbox)

        self.action_scenario_toolbox = QAction(
            QIcon(":/icons/scenario_toolbox.png"), "Open Scenario Toolbox", mwindow_ui
        )
        self.tb2.addAction(self.action_scenario_toolbox)

        # Undo / Redo
        self.tb2.addSeparator()
        self.tb3 = self.mwindow_ui.addToolBar("Undo/Redo")

        self.action_undo = QAction(QIcon(":/icons/button_undo.png"), "undo last action", mwindow_ui)
        self.tb3.addAction(self.action_undo)

        self.action_redo = QAction(QIcon(":/icons/button_redo.png"), "redo last action", mwindow_ui)
        self.tb3.addAction(self.action_redo)

        # Animation Player
        self.tb3.addSeparator()

        self.tb4 = mwindow_ui.addToolBar("Animation Play")
        self.button_play_pause = QAction(
            QIcon(":/icons/play.png"), "Play the animation", mwindow_ui
        )
        self.tb4.addAction(self.button_play_pause)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMaximumWidth(300)
        self.slider.setValue(0)
        self.slider.setMinimum(0)
        self.slider.setMaximum(99)
        self.slider.setTickInterval(1)
        self.tb4.addWidget(self.slider)

        self.label1 = QLabel("  Time Stamp:", mwindow_ui)
        self.tb4.addWidget(self.label1)

        self.edit = QLineEdit()
        validator = QIntValidator()
        validator.setBottom(0)
        self.edit.setValidator(validator)
        self.edit.setText("0")
        self.edit.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.edit.setMaximumWidth(40)
        self.tb4.addWidget(self.edit)

        self.label2 = QLabel(" / 0", mwindow_ui)
        self.tb4.addWidget(self.label2)

        self.action_save_video = QAction(QIcon(":/icons/save_video.png"), "Save Video", mwindow_ui)
        self.tb4.addAction(self.action_save_video)

        # Lanelet Operations
        self.tb4.addSeparator()
        self.tb5 = mwindow_ui.addToolBar("Lanelet Operations")

        self.drawing_mode = QAction(QIcon(":/icons/drawing_mode.png"), "draw lanes", mwindow_ui)
        self.drawing_mode.setCheckable(True)
        self.tb5.addAction(self.drawing_mode)

        self.add_adjacent_left = QAction(
            QIcon(":/icons/add_adjacent_left.png"), "add adjacent left", mwindow_ui
        )
        self.tb5.addAction(self.add_adjacent_left)
        self.add_adjacent_left.setDisabled(True)

        self.add_adjacent_right = QAction(
            QIcon(":/icons/add_adjacent_right.png"), "add adjacent right", mwindow_ui
        )
        self.tb5.addAction(self.add_adjacent_right)
        self.add_adjacent_right.setDisabled(True)

        self.split_lanelet = QAction(QIcon(":/icons/split_lanelet.png"), "split lane", mwindow_ui)
        self.split_lanelet.setCheckable(True)
        self.tb5.addAction(self.split_lanelet)
        self.split_lanelet.setDisabled(True)

        self.merge_lanelet = QAction(QIcon(":/icons/merge_lanelet.png"), "merge lanes", mwindow_ui)
        self.tb5.addAction(self.merge_lanelet)
        self.merge_lanelet.setDisabled(True)

        self.crop_map = QAction(QIcon(":/icons/crop_map.png"), "crop map", mwindow_ui)
        self.tb5.addAction(self.crop_map)
        self.crop_map.setCheckable(True)

        self.cancel_edit_vertices = QAction(
            QIcon(":/icons/close.png"), "Stop editing vertices", mwindow_ui
        )
        self.tb5.addAction(self.cancel_edit_vertices)
        self.cancel_edit_vertices.setVisible(False)

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
