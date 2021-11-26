from crdesigner.input_output.gui.commonroad_scenario_designer_gui import start_gui as start_gui_old_entry
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from ui.gui.mwindow.mwindow import MWindow


def start_gui_old():
    """
    The main entry point to the gui. For now this is more of an adapter to redirect to the implementation.
    """
    start_gui_old_entry()


def start_gui_new(input_file: str = None):
    """
    Redirect to the
    """
    # application
    app = QApplication(sys.argv)
    if input_file:
        w = MWindow(input_file)
    else:
        w = MWindow()
    w.showMaximized()
    sys.exit(app.exec_())


if __name__ == '__main__':
    start_gui_new()
