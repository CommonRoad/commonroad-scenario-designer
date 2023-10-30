import logging

from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import *

from crdesigner.config.gui_config import gui_config, ColorSchema
from crdesigner.ui.gui.resources.MainWindow import Ui_mainWindow
from crdesigner.ui.gui.utilities.gui_sumo_simulation import SUMO_AVAILABLE

if SUMO_AVAILABLE:
    pass


class MWindowUI(QMainWindow, Ui_mainWindow):
    """The Main window of the CR Scenario Designer."""

    def __init__(self, path=None):
        super().__init__()
        self.setup_mwindow()
        self.obstacle_toolbox = None
        self.road_network_toolbox = None
        self.map_converter_toolbox = None
        self.scenario_toolbox = None
        self.crdesigner_console_wrapper = None

        self.animated_viewer_wrapper = None

        # GUI attributes
        self.play_activated = False
        self.viewer_dock = None
        self.sumo_settings = None
        self.gui_settings = None

        # Sets stylesheet of the Application
        self.set_stylesheet(gui_config.get_stylesheet())

    def setup_mwindow(self):
        """
            Calling the methods for setting up the main window.
        """
        self.setupUi(self)
        self.setWindowIcon(QIcon(':/icons/cr.ico'))
        self.setWindowTitle("CommonRoad Scenario Designer")
        self.centralwidget.setStyleSheet('background-color:rgb(150,150,150)')
        self.setWindowFlag(Qt.Window)

    def update_max_step(self, value: int = -1):
        """ Redirect to the service layer. """
        logging.info('update_max_step')
        value = value if value > -1 else self.animated_viewer_wrapper.cr_viewer.max_timestep
        self.top_bar.toolbar_wrapper.tool_bar_ui.label2.setText(' / ' + str(value))
        self.top_bar.toolbar_wrapper.tool_bar_ui.slider.setMaximum(value)

    def update_toolbox_scenarios(self):
        """ Redirect to the service layer. """
        self.update_toolbox_scenarios_service_layer(mwindow=self)

    # here are some actual functionalities which are either too small for sourcing out or cant be due to dependencies

    def process_trigger(self, q):
        self.status.showMessage(q.text() + ' is triggered')

    def initialize_toolboxes(self):
        self.road_network_toolbox.initialize_road_network_toolbox()
        self.obstacle_toolbox.obstacle_toolbox_ui.initialize_obstacle_information()
        self.scenario_toolbox.initialize_toolbox()

    def colorscheme(self) -> ColorSchema:
        return gui_config.get_colorscheme()

    def update_window(self):
        p = QtGui.QPalette()
        p.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(self.colorscheme().background))
        p.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(self.colorscheme().second_background))
        p.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor(self.colorscheme().background))
        p.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor(self.colorscheme().color))
        p.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor(self.colorscheme().color))
        p.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor(self.colorscheme().color))
        p.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor(self.colorscheme().background))
        self.setPalette(p)

        self.road_network_toolbox.road_network_toolbox_ui.update_window()
        self.obstacle_toolbox.obstacle_toolbox_ui.update_window()
        self.map_converter_toolbox.converter_toolbox_ui.update_window()
        self.scenario_toolbox.scenario_toolbox_ui.update_window()
        self.animated_viewer_wrapper.update_window()
        self.menubar.setStyleSheet(
            'background-color: ' + self.colorscheme().second_background + '; color: ' + self.colorscheme().color)

    def close_window(self) -> bool:
        """
        For closing the window.
        """
        message_box = QMessageBox(QMessageBox.Warning, "Warning", "Do you really want to quit?",
                                  buttons=QMessageBox.Yes | QMessageBox.No, parent=self)

        p = QtGui.QPalette()
        p.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(self.colorscheme().background))
        p.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(self.colorscheme().second_background))
        p.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor(self.colorscheme().highlight))
        p.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor(self.colorscheme().highlight_text))
        p.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor(self.colorscheme().color))
        p.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor(self.colorscheme().color))
        message_box.setPalette(p)

        message_box.exec_()
        reply = message_box.standardButton(message_box.clickedButton())
        if reply == message_box.Yes:
            return True
        else:
            return False

    def ask_for_autosaved_file(self):
        """
        Asking if the user wants to restore the old scenario

        @return: Boolean with the answer of the user
        """
        message_box = QMessageBox(QMessageBox.Warning, "Warning", "Do you want to restore the last project?",
                                  buttons=QMessageBox.Yes | QMessageBox.No, parent=self)

        p = QtGui.QPalette()
        p.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(self.colorscheme().background))
        p.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(self.colorscheme().second_background))
        p.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor(self.colorscheme().highlight))
        p.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor(self.colorscheme().highlight_text))
        p.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor(self.colorscheme().color))
        p.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor(self.colorscheme().color))
        message_box.setPalette(p)

        message_box.exec_()
        reply = message_box.standardButton(message_box.clickedButton())

        if reply == message_box.Yes:
            return True
        else:
            return False

    def set_stylesheet(self, sheet: str):
        """
        Sets the stylesheet to a modern look or the old look

        @param sheet: new staylesheet which should be set
        """
        qApp.setStyleSheet(sheet)