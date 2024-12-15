from typing import List, Union

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QMainWindow

from crdesigner.common.config.config_base import Attribute
from crdesigner.common.config.settings_config import settings
from crdesigner.ui.gui.view.settings.settings_tab_ui import SettingsTabUI

HEIGHT = 25
WIDTHF = 280
WIDTHM = 390
FACTOR = 0.9
FONT_SIZE = 9


class SettingsUI:
    """
    This class creates the settings window and handles the saving and loading of the settings.
    """

    def __init__(self, mwindow):
        """Initialize the settings window and all tabs."""
        # create settings window
        self.mwindow = mwindow
        self.settings = QMainWindow()
        self.settings.setObjectName("Settings")
        self.settings.resize(int(1820 * FACTOR), int(1400 * FACTOR))

        # Define a stylesheet with the desired font size and apply it to the settings window
        stylesheet = "QWidget { font-size: %dpt; }" % FONT_SIZE
        self.settings.setStyleSheet(stylesheet)

        # create central widget
        self.central_widget = QtWidgets.QWidget(self.settings)
        self.central_widget.setObjectName("centralwidget")
        self.centralLayout = QtWidgets.QVBoxLayout(self.central_widget)
        self.centralLayout.setContentsMargins(0, 0, 0, 0)  # No margins
        self.central_widget.setObjectName("centralLayout")

        # create tab widget
        self.tabWidget = QtWidgets.QTabWidget(self.central_widget)
        self.centralLayout.addWidget(self.tabWidget)
        self.tabBar = QtWidgets.QTabBar()
        self.tabWidget.setTabBar(self.tabBar)

        # create tab gui
        self.frame = QtWidgets.QFrame(self.central_widget)
        self.frameLayout = QtWidgets.QHBoxLayout(self.frame)
        self.frameLayout.setContentsMargins(0, 0, 0, 0)  # No margins
        self.frame.setLayout(self.frameLayout)
        self.frame.setMinimumSize(int(1700 * FACTOR), 43)

        # button cancel
        self.button_cancel = QtWidgets.QPushButton(self.frame)
        self.button_cancel.setObjectName("button_cancel")
        self.button_cancel.setMinimumSize(150, 40)
        self.button_cancel.setMaximumSize(150, 40)

        # button ok
        self.button_ok = QtWidgets.QPushButton(self.frame)
        self.button_ok.setObjectName("button_ok")
        self.button_ok.setMinimumSize(150, 40)
        self.button_ok.setMaximumSize(150, 40)

        # button set to default
        self.button_set_to_default = QtWidgets.QPushButton(self.frame)
        self.button_set_to_default.setObjectName("button_set_to_default")
        self.button_set_to_default.setMinimumSize(150, 40)
        self.button_set_to_default.setMaximumSize(150, 40)

        # spacer
        spacer_fixed = QtWidgets.QSpacerItem(
            20, 1, QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
        )
        spacer_expanding = QtWidgets.QSpacerItem(
            1, 1, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed
        )

        # button select directory
        self.button_select_directory = QtWidgets.QPushButton(self.frame)
        self.button_select_directory.setObjectName("button_select_directory")
        self.button_select_directory.setText("Select Directory")
        self.button_select_directory.setMinimumSize(180, 40)
        self.button_select_directory.setMaximumSize(180, 40)

        # label settings directory
        self.label_settings_directory = QtWidgets.QLabel(self.frame)
        self.label_settings_directory.setObjectName("label_settings_directory")
        self.label_settings_directory.setText(settings.CUSTOM_SETTINGS_DIR)
        self.label_settings_directory.setMinimumSize(500, 40)
        settings.get_attribute("CUSTOM_SETTINGS_DIR").subscribe(
            self.label_settings_directory.setText
        )

        # create directory selection layout
        self.frameLayout.addItem(spacer_fixed)
        self.frameLayout.addWidget(self.button_select_directory)
        self.frameLayout.addWidget(self.label_settings_directory)

        # create expanding spacer
        self.frameLayout.addItem(spacer_expanding)

        # add buttons
        self.frameLayout.addWidget(self.button_cancel)
        self.frameLayout.addWidget(self.button_ok)
        self.frameLayout.addWidget(self.button_set_to_default)

        # add frame
        self.centralLayout.addWidget(self.frame)

        # tab gui
        self.settings.setCentralWidget(self.central_widget)
        self.menubar = QtWidgets.QMenuBar(self.settings)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 990, 23))
        self.menubar.setObjectName("menubar")
        self.settings.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(self.settings)
        self.statusbar.setObjectName("statusbar")
        self.settings.setStatusBar(self.statusbar)

    def _retranslate_ui(self, mwindow):
        _translate = QtCore.QCoreApplication.translate

        mwindow.setWindowTitle(_translate("MainWindow", "Settings"))
        self.button_ok.setText(_translate("MainWindow", "Ok"))
        self.button_cancel.setText(_translate("MainWindow", "Cancel"))
        self.button_set_to_default.setText(_translate("MainWindow", "Set to default"))

    def update_window(self):
        """This function updates the settings window by setting all necessary colors."""
        # get colorscheme
        p = QtGui.QPalette()

        # set colors for settings window
        p.setColor(
            QtGui.QPalette.ColorRole.Window, QtGui.QColor(self.mwindow.colorscheme().background)
        )
        p.setColor(
            QtGui.QPalette.ColorRole.Base,
            QtGui.QColor(self.mwindow.colorscheme().second_background),
        )
        p.setColor(
            QtGui.QPalette.ColorRole.Button, QtGui.QColor(self.mwindow.colorscheme().background)
        )
        p.setColor(
            QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor(self.mwindow.colorscheme().color)
        )
        p.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor(self.mwindow.colorscheme().color))
        p.setColor(
            QtGui.QPalette.ColorRole.WindowText, QtGui.QColor(self.mwindow.colorscheme().color)
        )
        p.setColor(
            QtGui.QPalette.ColorRole.Link, QtGui.QColor(self.mwindow.colorscheme().background)
        )

        # set colors for tab bar
        self.settings.setPalette(p)

        # set colors for elements
        p.setColor(
            QtGui.QPalette.ColorRole.Button, QtGui.QColor(self.mwindow.colorscheme().highlight)
        )
        # TODO Find solution in pyqt6
        p.setColor(
            QtGui.QPalette.ColorRole.Window, QtGui.QColor(self.mwindow.colorscheme().highlight_text)
        )
        p.setColor(
            QtGui.QPalette.ColorRole.ButtonText,
            QtGui.QColor(self.mwindow.colorscheme().highlight_text),
        )

        # set colors for buttons
        self.tabBar.setPalette(p)
        self.button_ok.setPalette(p)
        self.button_cancel.setPalette(p)
        self.button_set_to_default.setPalette(p)

    def _add_tab(self, name: str, layout: List[List[Union[Attribute, str]]]):
        tab = SettingsTabUI(layout, self, FACTOR, WIDTHF, WIDTHM, HEIGHT, FONT_SIZE)
        self.tabWidget.addTab(tab.scrollArea, name)
