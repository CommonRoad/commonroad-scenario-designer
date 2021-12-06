class MenuBarWrapper:
    """
    Wrapper class for the menu bar.
    """

    def __init__(self, mwindow, fileNewAction, fileOpenAction, fileSaveAction, separator, exitAction, gui_settings,
                 sumo_settings, osm_settings, open_web, open_forum):
        self.menu_bar = mwindow.menuBar()  # instant of menu

        self.menu_file = self.menu_bar.addMenu('File')  # add menu 'file'
        self.menu_file.addAction(fileNewAction)
        self.menu_file.addAction(fileOpenAction)
        self.menu_file.addAction(fileSaveAction)
        self.menu_file.addAction(separator)
        self.menu_file.addAction(exitAction)

        self.menu_setting = self.menu_bar.addMenu('Setting')  # add menu 'Setting'
        self.menu_setting.addAction(gui_settings)
        self.menu_setting.addAction(sumo_settings)
        self.menu_setting.addAction(osm_settings)

        self.menu_help = self.menu_bar.addMenu('Help')  # add menu 'Help'
        self.menu_help.addAction(open_web)
        self.menu_help.addAction(open_forum)
