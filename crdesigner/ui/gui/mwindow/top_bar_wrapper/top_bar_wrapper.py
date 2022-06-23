from crdesigner.ui.gui.mwindow.top_bar_wrapper.menu_bar_wrapper.menu_bar_wrapper import MenuBarWrapper
from crdesigner.ui.gui.mwindow.top_bar_wrapper.toolbar_wrapper.toolbar_wrapper import ToolBarWrapper
# service layer imports
from crdesigner.ui.gui.mwindow.top_bar_wrapper.service_layer import *


class TopBarWrapper:
    """
    Generic wrapper for the top bar - contains the file actions which are used in the toolbar and the menu_bar.
    """

    def __init__(self, mwindow):
        self.mwindow = mwindow  # reference back
        # now actually create the menu_bar_wrapper
        self.menu_bar_wrapper = MenuBarWrapper(mwindow=self.mwindow, file_new=file_new,
                                               open_commonroad_file=open_commonroad_file,
                                               close_window=close_window, show_settings=show_settings,
                                               open_cr_web=open_cr_web, open_cr_forum=open_cr_forum,
                                               file_save=file_save)
        self.toolbar_wrapper = ToolBarWrapper(mwindow=self.mwindow, file_new=file_new,
                                              open_commonroad_file=open_commonroad_file, file_save=file_save)
