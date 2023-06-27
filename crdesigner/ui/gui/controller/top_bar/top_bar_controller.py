from __future__ import annotations

from crdesigner.ui.gui.controller.top_bar.menu_bar_controller import MenuBarController
from crdesigner.ui.gui.controller.top_bar.tool_bar_controller import ToolBarController


class TopBarController:

    def __init__(self, mwindow: 'MWindowController'):
        self.menu_bar = MenuBarController(mwindow)
        self.toolbar_wrapper = ToolBarController(mwindow)
