#from crmapconverter.io.V2_0.gui_2_0 import OSM2CRActivity1, initialise
from tkinter import *
from PIL import Image, ImageTk

try:
    from crmapconverter.io.gui import opendrive_gui as gui_od2cr
    from crmapconverter.osm2cr.converter_modules.gui_modules.gui_embedding import StartMenu, MainApp
    from commonroad.common.file_writer import CommonRoadFileWriter
    from commonroad.common.file_reader import CommonRoadFileReader

    from crmapconverter.osm.osm2lanelet import OSM2LConverter
    from crmapconverter.osm.parser import OSMParser
    from crmapconverter.osm.lanelet2osm import L2OSMConverter

    from crmapconverter.opendriveparser.parser import parse_opendrive
    from crmapconverter.opendriveconversion.network import Network
    from crmapconverter.io.viewer import MainWindow as ViewerWidget
    import crmapconverter.io.viewer as CRViewerQT
except:
    print("You need to install manually commonroad")

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

def openDRIVE2CR():
    """Converter OpenDRIVE2Lanelet intial function (V1.0)"""
    gui_od2cr()

def default():
    print("coming soon")

