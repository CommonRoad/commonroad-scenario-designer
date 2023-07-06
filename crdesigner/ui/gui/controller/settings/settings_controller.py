from PyQt5 import QtCore, QtWidgets

from crdesigner.config.gui_config import gui_config as gui_settings_model
from crdesigner.config.settings_config import settings as settings_model, CONFIGS_TO_RENDER
from crdesigner.ui.gui.utilities.draw_params_updater import set_draw_params
from crdesigner.ui.gui.view.settings.settings_ui import SettingsUI


class SettingsController:
    """
    Controller for the settings window. Mainly provides the logic for the buttons. And
    connects the settings window to the settings models. Also sets up the UI.
    """

    def __init__(self, parent):
        """
        Initialize the settings controller. As well as the settings UI.
        """
        self.cr_designer = parent.mwindow_ui
        self.scenario_model = parent.scenario_model
        self.canvas = parent.animated_viewer_wrapper.cr_viewer.dynamic

        self.settings_ui = SettingsUI(self.cr_designer)

        for config in CONFIGS_TO_RENDER:
            tab_name = config.__class__.__name__.replace("Config", "").upper()
            self.settings_ui._add_tab(tab_name, config.LAYOUT)

        self.settings_ui.update_window()
        self.settings_ui._retranslate_ui(self.settings_ui.settings)
        QtCore.QMetaObject.connectSlotsByName(self.settings_ui.settings)

        self.connect_events()

    def connect_events(self):
        """
        Connect buttons to callables.
        """
        self.settings_ui.button_select_directory.clicked.connect(_select_directory)
        self.settings_ui.button_ok.clicked.connect(self.apply_close)
        self.settings_ui.button_cancel.clicked.connect(self.close)
        self.settings_ui.button_set_to_default.clicked.connect(_set_default)

    def close(self):
        """
        Reset the settings to their previous values and close the settings window.
        """
        _restore_all_settings()

        self._hide_and_update()

    def apply_close(self):
        """
        Save the settings to their respective files and close the settings window.
        """
        if not _validate_all():
            return
        _save_all_to_yaml()
        self._hide_and_update()

    def show(self):
        """
        Backup the current settings and show the settings window.
        """
        _backup_settings()
        self.settings_ui.settings.show()

    def _hide_and_update(self):
        self._update_all_dependents()
        self.settings_ui.settings.hide()

    def _update_all_dependents(self):
        # GUI updates
        set_draw_params(trajectory=gui_settings_model.DRAW_TRAJECTORY,
                        intersection=gui_settings_model.DRAW_INTERSECTIONS,
                        obstacle_label=gui_settings_model.DRAW_OBSTACLE_LABELS,
                        obstacle_icon=gui_settings_model.DRAW_OBSTACLE_ICONS,
                        obstacle_direction=gui_settings_model.DRAW_OBSTACLE_DIRECTION,
                        obstacle_signal=gui_settings_model.DRAW_OBSTACLE_SIGNALS,
                        occupancy=gui_settings_model.DRAW_OCCUPANCY,
                        traffic_signs=gui_settings_model.DRAW_TRAFFIC_SIGNS,
                        traffic_lights=gui_settings_model.DRAW_TRAFFIC_LIGHTS,
                        incoming_lanelets=gui_settings_model.DRAW_INCOMING_LANELETS,
                        successors=gui_settings_model.DRAW_SUCCESSORS,
                        intersection_labels=gui_settings_model.DRAW_INTERSECTION_LABELS,
                        colorscheme=self.cr_designer.colorscheme())


def _set_default():
    """
    Sets the default settings for all settings models.
    """
    for config in CONFIGS_TO_RENDER:
        config.reset_settings()


def _select_directory():
    """
    Opens a file dialog to select a directory. If a directory is selected, the
    CUSTOM_SETTINGS_DIR attribute of the settings model is set to the selected directory.
    (This triggers the _load_custom_settings function in the settings model.)
    """
    directory = QtWidgets.QFileDialog.getExistingDirectory(caption="Select Directory")
    if directory:
        settings_model.CUSTOM_SETTINGS_DIR = directory
        settings_model.notify_all()


def _validate_all() -> bool:
    valid = True
    for config in CONFIGS_TO_RENDER:
        if not config.validate_all_settings():
            valid = False
    return valid


def _backup_settings():
    for config in CONFIGS_TO_RENDER:
        config.backup_settings()


def _save_all_to_yaml():
    for config in CONFIGS_TO_RENDER:
        config.save_to_yaml_file()
    settings_model.save_to_yaml_file()


def _restore_all_settings():
    for config in CONFIGS_TO_RENDER:
        config.restore_settings()
        config.notify_all()
