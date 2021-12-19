from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class CRDesignerConsoleWrapper:
    """
    Wrapper class for the crdesigner_console_wrapper.
    """

    def __init__(self, mwindow):
        self.mwindow = mwindow  # reference to the main window
        self.console = QDockWidget(mwindow)
        self.console.setTitleBarWidget(QWidget(self.console))  # no title of Dock
        self.text_browser = QTextBrowser()
        self.text_browser.setMaximumHeight(80)
        self.text_browser.setObjectName("textBrowser")
        self.console.setWidget(self.text_browser)
        self.console.setFloating(False)  # set if crdesigner_console_wrapper can float
        self.console.setFeatures(QDockWidget.NoDockWidgetFeatures)
        mwindow.addDockWidget(Qt.BottomDockWidgetArea, self.console)
