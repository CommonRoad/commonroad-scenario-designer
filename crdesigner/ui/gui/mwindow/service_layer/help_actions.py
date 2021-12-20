from crdesigner.ui.gui.mwindow.service_layer.general_services import create_action
from PyQt5.QtGui import *
from PyQt5.QtCore import *


def create_help_actions(mwindow) -> (any, any):
    """Function to create the help action in the menu bar."""
    open_web = create_action(mwindow=mwindow, text="Open CR Web", icon="", checkable=False, slot=_open_cr_web,
                             tip="Open CommonRoad Website", shortcut=None)
    open_forum = create_action(mwindow=mwindow, text="Open Forum", icon="", checkable=False, slot=_open_cr_forum,
                               tip="Open CommonRoad Forum", shortcut=None)
    return open_web, open_forum


def _open_cr_web():
    """Function to open the CommonRoad website."""
    QDesktopServices.openUrl(QUrl("https://commonroad.in.tum.de/"))


def _open_cr_forum():
    """Function to open the CommonRoad Forum."""
    QDesktopServices.openUrl(QUrl("https://commonroad.in.tum.de/forum/c/map-tool/11"))
