"""
This module contains the GUI of the osm -> CR converter
"""


import os
from typing import Optional

from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtGui import QIcon
from matplotlib.pyplot import close

from crdesigner.map_conversion.osm2cr.converter_modules.cr_operations import export
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations import road_graph as rg
from crdesigner.ui.gui.mwindow.service_layer.converter_modules.converter_interface import ConverterInterface


class OSMInterface(ConverterInterface):
    """
    Import interface GUI for the osm converter.
    """

    def __init__(self, parent):
        self.cr_designer = parent
        self.main_window = QMainWindow(parent)
        self.path = None
        self.settings = None

    def start_import(self):
        self.main_window.show()

    def edge_edit_embedding(self, graph: rg.Graph):
        """
        sets edge edit embedding as main window

        :param graph: the graph to edit
        :return: None
        """
        if graph is not None:
            self.main_window.show()
        else:
            print("no graph loaded")

    def lane_link_embedding(self, graph: rg.Graph):
        """
        sets lane link embedding as main window

        :param graph: the graph to edit
        :return:
        """
        if graph is not None:
            self.main_window.show()

    def export(self, graph):
        """ converts a graph to a scenario and loads it into the CrSD """
        scenario = export.convert_to_scenario(graph)
        filename = os.path.basename("new_scenario")
        self.cr_designer.open_scenario(scenario, filename)
        self.main_window.close()

    def show_start_menu(self):
        """
        closes open figures and shows the start menu

        :return: None
        """
        if self.edge_edit_window is not None:
            close(self.edge_edit_window.gui_plot.fig)
        if self.lane_link_window is not None:
            close(self.lane_link_window.gui_plot.fig)
        self.edge_edit_window = None
        self.lane_link_window = None

    def show_settings(self):
        self.settings = settings.OSMSettings(self, self.main_window.close)
