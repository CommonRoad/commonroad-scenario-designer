import sys
from lxml import etree
from crmapconverter.osm.lanelet2osm import L2OSMConverter
from crmapconverter.osm2cr.converter_modules.gui_modules.gui_embedding import MainApp
from PyQt5.QtWidgets import *




class OSM2CR(QDialog):
    """Call OSM converter GUI"""

    def __init__(self, parent=None):
        super(OSM2CR, self).__init__(parent)
        self.start()

    def start(self):
        self.osm = MainApp()
        self.osm.start()

