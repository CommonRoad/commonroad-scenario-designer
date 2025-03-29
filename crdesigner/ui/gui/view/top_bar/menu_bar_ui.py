from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QAction, QDesktopServices, QIcon, QKeySequence

from crdesigner.ui.gui.utilities.file_actions import (
    file_new,
    file_save,
    open_commonroad_file,
)


def open_cr_web():
    """Function to open the CommonRoad website."""
    QDesktopServices.openUrl(QUrl("https://commonroad.in.tum.de/"))


def open_cr_forum():
    """Function to open the CommonRoad Forum."""
    QDesktopServices.openUrl(QUrl("https://commonroad.in.tum.de/forum/c/map-tool/11"))


class MenuBarUI:
    """
    Class to create the menu bar of the main window.
    """

    def __init__(self, mwindow):
        """
        Constructor of the menu bar.
        """
        self.mwindow_ui = mwindow.mwindow_ui
        self.mwindow = mwindow

        self.menu_bar = self.mwindow_ui.menuBar()  # instant of menu

        self.menu_file = self.menu_bar.addMenu("File")  # add menu 'file'
        # create new file
        self.action_new = self.create_action(
            text="New",
            icon=QIcon(":/icons/new_file.png"),
            checkable=False,
            slot=lambda: file_new(mwindow),
            tip="New CommonRoad File",
            shortcut=QKeySequence.StandardKey.New,
        )
        self.menu_file.addAction(self.action_new)
        # open a file
        self.action_open = self.create_action(
            text="Open",
            icon=QIcon(":/icons/open_file.png"),
            checkable=False,
            slot=lambda: open_commonroad_file(mwindow),
            tip="Open CommonRoad File",
            shortcut=QKeySequence.StandardKey.Open,
        )
        self.menu_file.addAction(self.action_open)
        # seperator
        self.separator = QAction(self.mwindow_ui)
        self.separator.setSeparator(True)
        # save a file
        self.action_save = self.create_action(
            text="Save",
            icon=QIcon(":/icons/save_file.png"),
            checkable=False,
            slot=lambda: file_save(mwindow),
            tip="Save CommonRoad File",
            shortcut=QKeySequence.StandardKey.Save,
        )
        self.menu_file.addAction(self.action_save)
        self.separator.setSeparator(True)

        # exit action
        self.exit_action = self.create_action(
            text="Quit",
            icon=QIcon(":/icons/close.png"),
            checkable=False,
            slot=lambda: mwindow.close_window(),
            tip="Quit",
            shortcut=QKeySequence.StandardKey.Close,
        )
        self.menu_file.addAction(self.exit_action)

        # add menu 'Setting'
        self.settings_action = self.create_action(
            text="Settings",
            icon="",
            checkable=False,
            slot=lambda: self.show_settings(),
            tip="Show settings for the CR Scenario Designer",
            shortcut=None,
        )
        self.menu_bar.addAction(self.settings_action)

        # add menu 'Help'
        self.menu_help = self.menu_bar.addMenu("Help")
        self.open_web_action = self.create_action(
            text="Open CR Web",
            icon="",
            checkable=False,
            slot=open_cr_web,
            tip="Open CommonRoad Website",
            shortcut=None,
        )
        self.menu_help.addAction(self.open_web_action)
        self.open_forum_action = self.create_action(
            text="Open Forum",
            icon="",
            checkable=False,
            slot=open_cr_forum,
            tip="Open CommonRoad Forum",
            shortcut=None,
        )
        self.menu_help.addAction(self.open_forum_action)

    def create_action(self, text, icon=None, checkable=False, slot=None, tip=None, shortcut=None):
        """
        Generic function used to create actions for the settings or the menu bar.
        """
        action = QAction(text, self.mwindow_ui)

        if icon is not None:
            action.setIcon(QIcon(icon))
        if checkable:
            # toggle, True means on/off state, False means simply executed
            action.setCheckable(True)
            if slot is not None:
                action.toggled.connect(slot)
        else:
            if slot is not None:
                action.triggered.connect(slot)
        if tip is not None:
            action.setToolTip(tip)  # toolbar_wrapper tip
            action.setStatusTip(tip)  # statusbar tip
        if shortcut is not None:
            action.setShortcut(shortcut)  # shortcut
        return action

    def show_settings(self):
        """
        Show the settings.
        """
        self.mwindow.settings.show()
