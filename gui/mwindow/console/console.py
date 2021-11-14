from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


def create_console(mwindow) -> (any, any):
    """Function to create the console."""
    mwindow.console = QDockWidget(mwindow)
    mwindow.console.setTitleBarWidget(QWidget(mwindow.console))  # no title of Dock
    mwindow.text_browser = QTextBrowser()
    mwindow.text_browser.setMaximumHeight(80)
    mwindow.text_browser.setObjectName("textBrowser")
    mwindow.console.setWidget(mwindow.text_browser)
    mwindow.console.setFloating(False)  # set if console can float
    mwindow.console.setFeatures(QDockWidget.NoDockWidgetFeatures)
    mwindow.addDockWidget(Qt.BottomDockWidgetArea, mwindow.console)
    return mwindow.console, mwindow.text_browser  # return here for visibility
