import sys

from PyQt5.QtWidgets import *
from crdesigner.ui.gui.controller.mwindow_controller import MWindowController


def start_gui_new(input_file: str = None):
    """
    Redirect to the main window start.
    """
    # application
    app = QApplication(sys.argv)
    if input_file:
        w = MWindowController(input_file)
    else:
        w = MWindowController()
    w.mwindow_ui.showMaximized()
    sys.exit(app.exec_())


if __name__ == '__main__':
    start_gui_new()
