
from argparse import ArgumentParser
import os
import sys
import logging
import numpy as np

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QMainWindow, QDockWidget, QMessageBox, QAction,
                             QLabel, QFileDialog, QDesktopWidget, QVBoxLayout,
                             QSlider, QWidget, QApplication, qApp, QLineEdit, QFormLayout, QPushButton, QDialog, QRadioButton)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QIcon, QKeySequence, QDesktopServices, QIntValidator
from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT as
                                                NavigationToolbar)

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.file_writer import (CommonRoadFileWriter,
                                           OverwriteExistingFile)
from commonroad.scenario.scenario import Scenario, LaneletNetwork, Lanelet

from crmapconverter.io.scenario_designer.gui_resources.MainWindow import Ui_mainWindow
from crmapconverter.io.scenario_designer.gui_toolbox import UpperToolbox
from crmapconverter.io.scenario_designer.converter_modules.osm_interface import OSMInterface
from crmapconverter.io.scenario_designer.converter_modules.opendrive_interface import (
    OpenDRIVEInterface)
from crmapconverter.io.scenario_designer.gui_settings import GUISettings
from crmapconverter.io.scenario_designer.sumo_gui_modules.sumo_settings import SUMOSettings
from crmapconverter.io.scenario_designer.sumo_gui_modules.gui_sumo_simulation import SUMOSimulation
from crmapconverter.io.scenario_designer.sumo_gui_modules.gui_sumo_simulation import SUMO_AVAILABLE
from crmapconverter.io.scenario_designer.gui_viewer import (
    LaneletList, IntersectionList, find_intersection_by_id, AnimatedViewer)
from crmapconverter.io.scenario_designer import config
from crmapconverter.io.scenario_designer import util

from commonroad.scenario.lanelet import Lanelet
from commonroad.scenario.lanelet import LaneletType
class LaneletSettings(QDialog):
    def __init__(self):
        super().__init__()
        self.lanelet_length = 50
        self.lanelet_width = 20
        self.setadjacent = False
        self.setPredecessor = False
        self.setWindowTitle("Lanelet settings")
        self.setGeometry(100, 100, 500, 300)

        self.length = QLineEdit()
        self.length.setValidator(QIntValidator())
        self.length.setMaxLength(4)
        self.length.setAlignment(Qt.AlignRight)

        self.width = QLineEdit()
        self.width.setValidator(QIntValidator())
        self.width.setMaxLength(4)
        self.width.setAlignment(Qt.AlignRight)

        self.adjacentLanelet = QRadioButton()
        self.adjacentLanelet.setText("set ajacent lanelet")
        self.adjacentLanelet.toggled.connect(self.adjacent_button)

        self.Predecessor = QRadioButton()
        self.Predecessor.setText("set predecessor automatically")
        self.Predecessor.toggled.connect(self.predecessor_button)


        self.apply_button = QPushButton()
        self.apply_button.setText("apply")
        self.apply_button.clicked.connect(self.apply_button_click)

        self.set_default = QPushButton()
        self.set_default.setText("set default")
        self.set_default.clicked.connect(self.set_default_click)

        layout = QFormLayout()
        layout.addRow("Lanelet length", self.length)
        layout.addRow("Lanelet width ", self.width)
        layout.addWidget(self.adjacentLanelet)
        layout.addWidget(self.Predecessor)
        layout.addWidget(self.apply_button)
        layout.addWidget(self.set_default)

        self.setLayout(layout)

    def predecessor_button(self):
        self.setPredecessor = self.Predecessor.isChecked()

    def adjacent_button(self):
        if self.adjacentLanelet.isChecked() == True:
            self.setadjacent = True
        else:
            self.setadjacent = False

    def apply_button_click(self):
        if self.length.text():
            self.lanelet_length = int(self.length.text())
        else:
            self.lanelet_length = 50
        if self.width.text():
            self.lanelet_width = int(self.width.text())
        else:
            self.lanelet_width = 12
        print(self.lanelet_length)
        print(self.lanelet_width)
        self.close()

    def set_default_click(self):
        self.length.clear()
        self.width.clear()
        self.length.insert("50")
        self.width.insert("20")
        self.setadjacent = False
        self.adjacentLanelet.setChecked(False)
        self.Predecessor.setChecked(True)
        self.setPredecessor = True

    def showsettings(self):
        self.show()

    def getLanletLength(self):
        return self.lanelet_length

    def getLaneletWidth(self):
        return self.lanelet_width

    def getAdjacentLanelet(self):
        return self.setadjacent

    def getPredecessor(self):
        return self.setPredecessor
