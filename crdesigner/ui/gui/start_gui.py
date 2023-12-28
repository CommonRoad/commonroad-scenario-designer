import sys
from typing import Optional

from PyQt6.QtWidgets import QApplication

from crdesigner.ui.gui.controller.mwindow_controller import MWindowController
from crdesigner.ui.gui.utilities.file_actions import open_path


def start_gui(input_file: Optional[str] = None):
    """
    Redirect to the main window start.

    @param input_file: CommonRoad scenario which should be loaded at startup.
    """
    app = QApplication(sys.argv)
    w = MWindowController()
    if input_file:
        open_path(mwindow=w, path=input_file)
    w.mwindow_ui.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    start_gui()
