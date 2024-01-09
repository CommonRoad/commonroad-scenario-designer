from __future__ import annotations

from typing import TYPE_CHECKING

from crdesigner.ui.gui.view.top_bar.menu_bar_ui import MenuBarUI

if TYPE_CHECKING:
    from crdesigner.ui.gui.controller.mwindow_controller import MWindowController


class MenuBarController:
    def __init__(self, mwindow: MWindowController):
        self.mwindow = mwindow
        self.menubar_ui = MenuBarUI(self.mwindow)
