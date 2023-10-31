from crdesigner.ui.gui.view.top_bar.menu_bar_ui import MenuBarUI


class MenuBarController:

    def __init__(self, mwindow: 'MWindowController'):
        self.mwindow = mwindow
        self.menubar_ui = MenuBarUI(self.mwindow)
