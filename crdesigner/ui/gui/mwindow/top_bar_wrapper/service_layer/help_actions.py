from crdesigner.ui.gui.mwindow.top_bar_wrapper.service_layer.general_services import create_action
from PyQt5.QtGui import *
from PyQt5.QtCore import *


def open_cr_web():
    """Function to open the CommonRoad website."""
    QDesktopServices.openUrl(QUrl("https://commonroad.in.tum.de/"))


def open_cr_forum():
    """Function to open the CommonRoad Forum."""
    QDesktopServices.openUrl(QUrl("https://commonroad.in.tum.de/forum/c/map-tool/11"))
