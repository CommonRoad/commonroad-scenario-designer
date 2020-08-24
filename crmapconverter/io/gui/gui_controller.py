"""This module provides the controller functions of the GUI"""

__author__ = "Rayane Zaibet"

from tkinter import *
from PIL import Image, ImageTk
try:
    from PyQt5 import QtGui, QtCore, QtWidgets
    from PyQt5.QtWidgets import QFileDialog, QWidget, QApplication, QMainWindow
except:
    print("You need manually to install your Qt distribution")


try:
    from commonroad.common.file_writer import CommonRoadFileWriter
    from commonroad.common.file_reader import CommonRoadFileReader
except:
    print("You need first to install commonroad")

try:
    import crmapconverter.io.gui as G
    from crmapconverter.osm2cr.converter_modules.gui_modules.gui_embedding import StartMenu, MainApp
    from crmapconverter.osm.osm2lanelet import OSM2LConverter
    from crmapconverter.osm.parser import OSMParser
    from crmapconverter.osm.lanelet2osm import L2OSMConverter
    from crmapconverter.opendrive.opendriveparser.parser import parse_opendrive
    from crmapconverter.opendrive.opendriveconversion.network import Network
    from crmapconverter.io.viewer import MainWindow as ViewerWidget
    import crmapconverter.io.viewer as CRViewerQT
except:
    print("You need first to install crmapconverter")
try:
    from crmapconverter.osm2cr.main import start_gui as gui_osm2cr
except ModuleNotFoundError as module_err:
    print(module_err)
    print("It seems like you did not install the dependencies for osm2cr.")
except:
    print("You need to install manually commonroad")


#GLOBAL FUNCTIONS
def image_encoding(path):
    """Loads an image in the right format to inster it in the Tkinter File System"""

    return ImageTk.PhotoImage(Image.open(path))

class CRViewerQt(QWidget):
    """Class used to provied the existant viewer deveopped in PyQt5"""

    def __init__(self, path=None):
        self.path = path
        super().__init__()

    def commonroad_visualization_menu(self):
        """Open the simple color-supported visualization of a CommonRoad file."""
        viewer = QMainWindow(self)
        commonroad_viewer_widget = ViewerWidget(self, path=self.path)
        viewer.setCentralWidget(commonroad_viewer_widget)
        viewer.show()



def CRviewer_run(path=None):
    app = QtWidgets.QApplication(sys.argv)
    ui = CRViewerQt(path)
    ui.commonroad_visualization_menu()
    app.exec_()

def default():
    print("coming soon")

