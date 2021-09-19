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
from crdesigner.input_output.gui.osm_gui_modules import gui_embedding, settings, gui
from crdesigner.input_output.gui.osm_gui_modules.GUI_resources.start_window import Ui_MainWindow as startWindow
from crdesigner.input_output.gui.converter_modules.converter_interface import ConverterInterface


class OSMInterface(ConverterInterface):
    """
    Import interface GUI for the osm converter.
    """

    def __init__(self, parent):
        self.cr_designer = parent
        self.main_window = QMainWindow(parent)
        self.start_menu = StartMenu(self)
        self.edge_edit_window: Optional[EdgeEdit] = None
        self.lane_link_window: Optional[LaneLinkEdit] = None
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
            self.edge_edit_window = EdgeEdit(self, graph, None)
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
            self.lane_link_window = LaneLinkEdit(self, graph, None)
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
        self.start_menu = StartMenu(self)

    def show_settings(self):
        self.settings = settings.SettingsMenu(self, self.main_window.close)


class StartMenu(gui_embedding.StartMenu):
    """
    Menu to start GUI
    Links to menus and functions via buttons
    """

    def bind_start_window_events(self, window: startWindow) -> None:
        """
        binds methods to button clicks and other user inputs

        :param window: start window object
        :return: None
        """
        # connect to all buttons of the start window
        window.b_start.clicked.connect(self.start_conversion)
        window.b_load_file.clicked.connect(self.select_file)
        window.b_load_state.clicked.connect(self.load_edit_state)
        window.b_download.clicked.connect(self.download_map)
        window.b_settings.clicked.connect(self.show_settings)

        # connect all other listeners
        window.coordinate_input.textChanged.connect(self.verify_coordinate_input)
        window.rb_load_file.clicked.connect(self.load_file_clicked)
        window.input_bench_id.textChanged.connect(self.bench_id_set)
        window.rb_download_map.clicked.connect(self.download_map_clicked)


class EdgeEdit(gui_embedding.EdgeEdit):
    """
    Embedding for edge edit GUI,
    Also embeds an Attribute editor
    """

    def __init__(
        self, app: OSMInterface, graph: Optional[rg.Graph], ee_gui: Optional[gui.EdgeEditGUI]
    ):
        """

        :param app: main pyqt5 app
        :param graph: the graph to edit
        :param ee_gui: the gui to embed, a new will be created if None
        """
        super().__init__(app, graph, ee_gui)
        self.embedding.pushButton.setStyleSheet("background-color: rgb(0, 255, 127);")
        self.embedding.pushButton.setIcon(QIcon(":/icons/next_step.png"))
        self.embedding.pushButton_2.setIcon(QIcon(":/icons/next_step.png"))
        self.embedding.pushButton_3.setIcon(QIcon(":/icons/next_step.png"))


class LaneLinkEdit(gui_embedding.LaneLinkEdit):
    """
    Embedding for lane link GUI
    """

    def __init__(
        self, app: OSMInterface, graph: Optional[rg.Graph], ll_gui: Optional[gui.LaneLinkGUI]
    ):
        """

        :param app: main pyqt5 app
        :param graph: the graph to edit
        :param ll_gui: the embedded gui object
        """
        super().__init__(app, graph, ll_gui)
        self.embedding.pushButton_2.setStyleSheet("background-color: rgb(0, 255, 127);")
        self.embedding.pushButton.setStyleSheet("background-color: rgb(0, 255, 127);")
        self.embedding.pushButton.setIcon(QIcon(":/icons/next_step.png"))
        self.embedding.pushButton_2.setIcon(QIcon(":/icons/next_step.png"))
        self.embedding.pushButton_3.setIcon(QIcon(":/icons/next_step.png"))