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
        # init the actions and settings used in the toolbar and the menu_bar
        self.fileNewAction, self.fileOpenAction, self.separator, self.fileSaveAction, self.exitAction = \
            create_file_actions(mwindow=self.mwindow)
        self.osm_settings, self.opendrive_settings, self.gui_settings, self.sumo_settings = \
            create_setting_actions(mwindow=self.mwindow)
        self.open_web, self.open_forum = create_help_actions(mwindow=self.mwindow)
        # now actually create the menu_bar_wrapper
        self.menu_bar_wrapper = MenuBarWrapper(mwindow=self.mwindow, fileNewAction=self.fileNewAction,
                                               fileOpenAction=self.fileOpenAction, separator=self.separator,
                                               exitAction=self.exitAction, gui_settings=self.gui_settings,
                                               sumo_settings=self.sumo_settings, osm_settings=self.osm_settings,
                                               open_web=self.open_web, open_forum=self.open_forum,
                                               fileSaveAction=self.fileSaveAction)
        self.toolbar_wrapper = ToolBarWrapper(mwindow=self.mwindow, file_new=file_new,
                                              open_commonroad_file=open_commonroad_file, file_save=file_save)
