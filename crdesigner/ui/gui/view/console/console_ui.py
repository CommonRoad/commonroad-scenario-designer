from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDockWidget, QTextBrowser, QWidget


class ConsoleUI:
    """
    Wrapper class for the crdesigner_console_wrapper.
    """

    def __init__(self, mwindow):
        self.mwindow = mwindow  # reference to the main window
        self.console = QDockWidget(mwindow.mwindow_ui)
        self.console.setTitleBarWidget(QWidget(self.console))  # no title of Dock
        self.text_browser = QTextBrowser()
        self.text_browser.setMaximumHeight(80)
        self.text_browser.setObjectName("textBrowser")
        self.console.setWidget(self.text_browser)
        self.console.setFloating(False)  # set if crdesigner_console_wrapper can float
        self.console.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        mwindow.mwindow_ui.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.console)
