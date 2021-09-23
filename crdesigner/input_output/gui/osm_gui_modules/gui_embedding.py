"""
This module allows to embed the GUIs defined in gui.py in a pyqt5 window.
It also provides a main window to start the conversion process, and the possibility to view CR scenarios
"""

from abc import ABC, abstractmethod
import pickle
import re
import sys
from typing import Optional, Union, Tuple


from crdesigner.map_conversion.osm2cr import config
from crdesigner.map_conversion.osm2cr.converter_modules import converter
from crdesigner.map_conversion.osm2cr.converter_modules.cr_operations import export as ex
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations import road_graph as rg
from crdesigner.input_output.gui.osm_gui_modules import gui, settings
from crdesigner.input_output.gui.osm_gui_modules.GUI_resources.edge_edit_embedding import Ui_EdgeEdit \
    as eeGUI_frame
from crdesigner.input_output.gui.osm_gui_modules.GUI_resources.lane_link_edit_embedding \
    import Ui_LaneLinkEdit as llGUI_frame
from crdesigner.input_output.gui.osm_gui_modules.GUI_resources.scenario_view \
    import Ui_MainWindow as scenarioView
from crdesigner.input_output.gui.osm_gui_modules.GUI_resources.start_window import Ui_MainWindow as startWindow
from crdesigner.map_conversion.osm2cr.converter_modules.osm_operations.downloader import download_around_map

from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QSpinBox,
    QCheckBox,
    QDoubleSpinBox,
    QComboBox,
    QFileDialog,
    QMessageBox)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.pyplot import close
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Qt5Agg')


class MainApp:
    """
    Main App to start the gui GUI
    """

    def __init__(self, parent=None):
        if not parent:
            self.app = QApplication(sys.argv)
            self.main_window = QMainWindow()
        else:
            self.main_window = QMainWindow(parent)
            self.app = None
        self.start_menu = StartMenu(self)
        self.edge_edit_window: Optional[EdgeEdit] = None
        self.lane_link_window: Optional[LaneLinkEdit] = None

    def start(self) -> None:
        """
        starts the graphical application

        :return: None
        """
        self.main_window.show()
        if self.app:
            self.app.exec_()

    def edge_edit_embedding(self, graph: rg.Graph) -> None:
        """
        sets edge edit embedding as main window

        :param graph: the graph to edit
        :return: None
        """
        if graph is not None:
            self.edge_edit_window = EdgeEdit(self, graph, None)
            self.main_window.show()
        else:
            QMessageBox.warning(
                self,
                "Warning",
                "No graph loaded.",
                QMessageBox.Ok)

    def lane_link_embedding(self, graph: rg.Graph) -> None:
        """
        sets lane link embedding as main window

        :param graph: the graph to edit
        :return:
        """
        if graph is not None:
            self.lane_link_window = LaneLinkEdit(self, graph, None)
            self.main_window.show()

    def export(self, graph: rg.Graph) -> None:
        """
        Asks a file path and exports the graph to a CR scenario.

        :param graph: the graph to export
        :return: None
        """
        if graph is not None:

            file, _ = QFileDialog.getSaveFileName(
                caption="Save map in Common Road Format",
                filter="Common Road file *.xml (*.xml)",
                options=QFileDialog.Options(),
            )
            if file == "":
                print("file not exported and not saved")
                return
            try:
                ex.export(graph, file)
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Internal Error",
                    "There was an error during the conversion to CR scenario.\n\n{}"
                    .format(e),
                    QMessageBox.Ok,
                )
        self.show_start_menu()

    def show_start_menu(self) -> None:
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


class StartMenu(QWidget):
    """
    Menu to start GUI
    Links to menus and functions via buttons
    """

    def __init__(self, app: MainApp):
        """

        :param app: the main pyqt5 app, in which the Start Menu is running
        """
        super().__init__(parent=None)
        self.app: MainApp = app
        self.embedding: startWindow = startWindow()
        self.embedding.setupUi(self.app.main_window)
        self.selected_file: Optional[str] = None
        self.graph: Optional[rg.Graph] = None
        self.lat: Optional[float] = None
        self.lon: Optional[float] = None
        # bind events
        self.bind_start_window_events(self.embedding)
        # init benchmark id
        config.BENCHMARK_ID = self.embedding.input_bench_id.text()
        # init user edit checkbox
        self.embedding.chk_user_edit.setChecked(config.USER_EDIT)

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
        # window.b_view_scenario.clicked.connect(self.view_scenario)
        window.b_download.clicked.connect(self.download_map)
        window.b_settings.clicked.connect(self.show_settings)

        # connect all other listeners
        window.coordinate_input.textChanged.connect(self.verify_coordinate_input)
        window.rb_load_file.clicked.connect(self.load_file_clicked)
        window.input_bench_id.textChanged.connect(self.bench_id_set)
        window.rb_download_map.clicked.connect(self.download_map_clicked)

    def show_settings(self) -> None:
        """
        displays settings window

        :return: None
        """
        self.settings_menu = settings.SettingsMenu(self.app,
            self.app.show_start_menu)

    def load_edit_state(self) -> None:
        """
        loads an edit state and opens it

        :return: None
        """
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select a edit state file",
            "",
            "edit save *.save (*.save)",
            options=QFileDialog.Options(),
        )
        if filename == "" or filename is None:
            print("no file picked")
        else:
            with open(filename, "rb") as fd:
                gui_state = pickle.load(fd)
            if isinstance(gui_state, gui.EdgeEditGUI):
                EdgeEdit(self.app, None, gui_state)
                self.app.main_window.show()
            elif isinstance(gui_state, gui.LaneLinkGUI):
                LaneLinkEdit(self.app, None, gui_state)
                self.app.main_window.show()
            else:
                QMessageBox.critical(
                    self,
                    "Warning",
                    "Invalid GUI state.",
                    QMessageBox.Ok)
                return
        
    def view_scenario(self) -> None:
        """
        allows to display a cr file

        :return: None
        """
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Select CommonRoad scenario",
            "",
            "CommonRoad file *.xml (*.xml)",
            options=QFileDialog.Options(),
        )
        if file == "":
            print("no file picked")
        else:
            window = scenarioView()
            window.setupUi(self.app.main_window)
            fig, ax = plt.subplots()
            fig.tight_layout()
            layout = window.plot_frame
            canvas = fig.canvas
            toolbar = NavigationToolbar(canvas, self.app.main_window)
            layout.addWidget(toolbar)
            layout.addWidget(canvas)
            ex.view_xml(file, ax)
            self.app.main_window.show()
            window.b_back.clicked.connect(self.app.show_start_menu)

    def bench_id_set(self) -> None:
        """
        sets the benchmark ID when a new id is set in window

        :return: None
        """
        name = self.embedding.input_bench_id.text()
        name = re.sub(r"[^a-zA-Z0-9._\-]", "", name)
        self.embedding.input_bench_id.setText(name)
        config.BENCHMARK_ID = name

    def load_file_clicked(self) -> None:
        """
        specifies behavior when radio button load file is clicked

        :return: None
        """
        if self.selected_file is not None:
            self.embedding.input_picked_output.setText("File picked")
        else:
            self.embedding.input_picked_output.setText("No file picked")

    def download_map_clicked(self) -> None:
        """
        specifies behavior when radio button download osm map is clicked

        :return: None
        """
        if self.verify_coordinate_input():
            self.embedding.input_picked_output.setText("Map will be downloaded")
        else:
            self.embedding.input_picked_output.setText(
                "Cannot download, invalid Coordinates"
            )

    def select_file(self) -> None:
        """
        allows to select a osm file to load

        :return: None
        """

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select OpenStreetMap map",
            "",
            "OpenStreetMap file *.osm (*.osm)",
            options=QFileDialog.Options(),
        )

        self.embedding.input_bench_id.setText(filename.split('/')[-1].split('.')[0])
        if filename != "":
            self.selected_file = filename
            self.embedding.l_selected_file.setText(filename)
            if self.embedding.rb_load_file.isChecked():
                self.embedding.input_picked_output.setText("File picked")

    def hidden_conversion(self, graph: rg.Graph) -> None:
        """
        performs the conversion without user edit

        :param graph: graph to convert
        :return: None
        """
        try:
            graph = converter.step_collection_2(graph)
            graph = converter.step_collection_3(graph)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Internal Error",
                "There was an error during the processing of the graph.\n\n{}"
                .format(e),
                QMessageBox.Ok,
            )
            return
        # name = config.BENCHMARK_ID
        self.app.export(graph)

    def start_conversion(self) -> None:
        """
        starts the conversion process by picking a file and showing the edge edit gui

        :return: None
        """
        try:
            if self.embedding.rb_load_file.isChecked():
                if self.selected_file is not None:
                    self.read_osm_file(self.selected_file)
                else:
                    QMessageBox.warning(
                        self,
                        "Warning",
                        "No file selected.",
                        QMessageBox.Ok)
                    return
            else:
                self.download_and_open_osm_file()
        except ValueError as e:
            QMessageBox.critical(
                self,
                "Warning",
                "Map unreadable: " + str(e),
                QMessageBox.Ok)
            return
        if self.embedding.chk_user_edit.isChecked():
            self.app.edge_edit_embedding(self.graph)
        else:
            self.hidden_conversion(self.graph)

    def verify_coordinate_input(self) -> bool:
        """
        check if user input of coordinates are in correct format and sane

        :return: True if coordinates are valid
        """
        coords = self.embedding.coordinate_input.text()
        try:
            lat, lon = coords.split(", ")
            self.lat, self.lon = float(lat), float(lon)
            if not (-90 <= self.lat <= 90 and -180 <= self.lon <= 180):
                raise ValueError
            self.embedding.l_region.setText("Coordinates Valid")
            if self.embedding.rb_download_map.isChecked():
                self.embedding.input_picked_output.setText("Map will be downloaded")
            return True
        except ValueError:
            self.embedding.l_region.setText("Coordinates Invalid")
            if self.embedding.rb_download_map.isChecked():
                self.embedding.input_picked_output.setText(
                    "Cannot download, invalid Coordinates"
                )
            return False

    def download_map(self) -> Optional[str]:
        """
        downloads map, but does not open it

        :return: the file name
        """
        # TODO maybe ask for filename
        name = config.BENCHMARK_ID + ".osm"
        if not self.verify_coordinate_input():
            QMessageBox.critical(
                self,
                "Warning",
                "cannot download, coordinates invalid",
                QMessageBox.Ok)
            return None
        else:
            download_around_map(
                name, self.lat, self.lon, self.embedding.range_input.value()
            )
            return name

    def download_and_open_osm_file(self) -> None:
        """
        downloads the specified region and reads the osm file

        :return: None
        """
        name = self.download_map()
        if name is not None:
            self.read_osm_file(config.SAVE_PATH + name)

    def read_osm_file(self, file: str) -> None:
        """
        loads an osm file and performs first steps to create the road graph

        :param file: file name
        :return: None
        """
        try:
            self.graph = converter.step_collection_1(file)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Internal Error",
                "There was an error during the loading of the selected osm file.\n\n{}"
                .format(e),
                QMessageBox.Ok,
            )


class MapEdit(ABC):
    """
    Abstract class for edit embeddings
    """

    def __init__(
        self,
        app: MainApp,
        graph: rg.Graph,
        gui_plot: gui.GUI,
        embedding: Union[eeGUI_frame, llGUI_frame],
    ):
        """

        :param app: main pyqt5 app
        :param graph: the graph to edit
        :param gui_plot: the embedded gui object
        :param embedding: the embedding window
        """
        self.app = app
        self.graph: rg.Graph = graph
        self.embedding = embedding
        self.gui_plot = gui_plot

        self.embedding.setupUi(self.app)
        self.canvas: FigureCanvas
        self.toolbar: NavigationToolbar
        self.canvas, self.toolbar = self.embed_plot_in_window(
            self.gui_plot, self.embedding
        )

        self.gui_plot.setup_event_listeners(self.canvas)
        self.bind_events()
        self.canvas.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.canvas.setFocus()

    @abstractmethod
    def bind_events(self):
        pass

    @abstractmethod
    def finalize(self):
        pass

    def embed_plot_in_window(
        self, plot: gui.GUI, window: Union[eeGUI_frame, llGUI_frame]
    ) -> Tuple[FigureCanvas, NavigationToolbar]:
        """
        embeds mpl plot in given window

        :param plot: the embedded gui
        :param window: the embedding window
        :return: Tuple of canvas and toolbar
        """
        layout = window.plot_frame
        canvas = plot.fig.canvas
        toolbar = NavigationToolbar(canvas, self.app)
        layout.addWidget(toolbar)
        layout.addWidget(canvas)
        return canvas, toolbar

    def reload_gui(self) -> None:
        """
        reloads the canvas after a different gui is loaded from disk,
        this method is passed as reloader to the gui

        :return: None
        """
        if self.gui_plot.restart:
            old_type = type(self.gui_plot)
            self.embedding.plot_frame.removeWidget(self.canvas)
            self.canvas.deleteLater()
            self.embedding.plot_frame.removeWidget(self.toolbar)
            self.toolbar.deleteLater()
            self.gui_plot = self.gui_plot.new_gui
            assert self.gui_plot is not None
            assert type(self.gui_plot) == old_type
            self.canvas, self.toolbar = self.embed_plot_in_window(
                self.gui_plot, self.embedding
            )
            self.gui_plot.setup_event_listeners(self.canvas)
            self.canvas.setFocusPolicy(QtCore.Qt.ClickFocus)
            self.canvas.setFocus()
            self.gui_plot.restart = False
            self.bind_events()
            self.graph = self.gui_plot.graph
        else:
            raise ValueError("restart should be true")


class EdgeEdit(MapEdit):
    """
    Embedding for edge edit GUI,
    Also embeds an Attribute editor
    """

    def __init__(
        self, app: MainApp, graph: Optional[rg.Graph], ee_gui: Optional[gui.EdgeEditGUI]
    ):
        """

        :param app: main pyqt5 app
        :param graph: the graph to edit
        :param ee_gui: the gui to embed, a new will be created if None
        """
        self.parent = app
        if ee_gui is None:
            assert graph is not None, "if no ee_gui provided, graph is needed"
            gui_plot = gui.EdgeEditGUI(
                graph, self.reload_gui, None, self.update_movement
            )
            embedding = eeGUI_frame()
        else:
            assert graph is None, "graph is only used if no ee_gui is provided"
            gui_plot = ee_gui
            gui_plot.reloader = self.reload_gui
            embedding = eeGUI_frame()
            graph = gui_plot.graph
        super().__init__(app.osm_edit_window, graph, gui_plot, embedding)
        self.embedding: eeGUI_frame
        self.attribute_editor = AttributeEditor(
            self.embedding.widget, self.embedding, self.gui_plot
        )
        self.gui_plot: gui.EdgeEditGUI = self.gui_plot
        self.gui_plot.pick_listener = self.attribute_editor.show_attributes

    def reload_gui(self) -> None:
        """
        reloads the canvas after a different gui is loaded from disk,
        this method is passed as reloader to the gui

        :return: None
        """
        super().reload_gui()
        self.gui_plot.update_movement = self.update_movement
        self.embedding.chk_move.setChecked(self.gui_plot.move_objects)

    def bind_events(self) -> None:
        """
        binds events of gui

        :return: None
        """
        # disconnect all buttons connections
        for handler in [
            self.embedding.b_save,
            self.embedding.b_load,
            self.embedding.b_undo,
            self.embedding.b_redo,
            self.embedding.b_delete,
            self.embedding.b_split,
            self.embedding.b_new_waypoint,
            self.embedding.b_new_edge,
            self.embedding.b_finalize,
            self.embedding.chk_move,
        ]:
            try:
                handler.disconnect()
            except TypeError:
                # ignore if button is not connected
                pass
        self.embedding.b_save.clicked.connect(self.gui_plot.save)
        self.embedding.b_load.clicked.connect(self.gui_plot.load)
        self.embedding.b_undo.clicked.connect(self.gui_plot.undo)
        self.embedding.b_redo.clicked.connect(self.gui_plot.redo)
        self.embedding.b_delete.clicked.connect(self.gui_plot.delete)
        self.embedding.b_split.clicked.connect(self.gui_plot.split)
        self.embedding.b_new_waypoint.clicked.connect(self.gui_plot.new_waypoint)
        self.embedding.b_new_edge.clicked.connect(self.gui_plot.create_edge)
        self.embedding.b_finalize.clicked.connect(self.finalize)
        self.embedding.b_flip.clicked.connect(self.flip_edge)
        self.embedding.b_set_widths.clicked.connect(self.gui_plot.edit_width)
        self.embedding.chk_move.stateChanged.connect(self.movement_checkbox_changed)

    def flip_edge(self) -> None:
        """
        flips the direction of an edge, but generally not the direction of lanes

        :return: None
        """
        self.attribute_editor.flip_edge()
        if self.gui_plot.last_picked_edge is not None:
            self.gui_plot.last_picked_edge.update_lanes_and_dir()

    def finalize(self) -> None:
        """
        ends the edit process by going on to lane link gui

        :return: None
        """
        try:
            graph = converter.step_collection_2(self.graph)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Internal Error",
                "There was an error during the processing of the graph.\n\n{}"
                .format(e),
                QMessageBox.Ok,
            )
            return
        self.parent.lane_link_embedding(graph)

    def update_movement(self, value: bool) -> None:
        """
        updates the movement checkbox,
        this method is passed to the gui, so it updates, when user switches movements state via shortcut

        :param value: the current value of movement
        :return: None
        """
        if value != self.embedding.chk_move.isChecked():
            self.embedding.chk_move.setChecked(value)

    def movement_checkbox_changed(self):
        """
        handles the event, when the movement checkbox is changed
        the if clause is necessary to prevent cyclic updating of the value

        :return:
        """
        if self.embedding.chk_move.isChecked() != self.gui_plot.move_objects:
            self.gui_plot.move()


class LaneLinkEdit(MapEdit):
    """
    Embedding for lane link GUI
    """

    def __init__(
        self, app: MainApp, graph: Optional[rg.Graph], ll_gui: Optional[gui.LaneLinkGUI]
    ):
        """

        :param app: main pyqt5 app
        :param graph: the graph to edit
        :param ll_gui: the embedded gui object
        """
        self.parent = app
        if ll_gui is None:
            assert graph is not None, "if no ee_gui provided, graph is needed"
            gui_plot = gui.LaneLinkGUI(graph, self.reload_gui)
            embedding = llGUI_frame()
        else:
            assert graph is None, "graph is only used if no ee_gui is provided"
            gui_plot = ll_gui
            gui_plot.reloader = self.reload_gui
            embedding = llGUI_frame()
            graph = gui_plot.graph
        super().__init__(app.osm_edit_window, graph, gui_plot, embedding)
        self.gui_plot: gui.LaneLinkGUI = self.gui_plot

    def bind_events(self) -> None:
        """
        binds events of gui

        :return: None
        """
        # disconnect all buttons connections
        try:
            for handler in [
                self.embedding.b_save,
                self.embedding.b_load,
                self.embedding.b_undo,
                self.embedding.b_redo,
                self.embedding.b_delete,
                self.embedding.b_finalize,
            ]:
                handler.disconnect()
        except TypeError:
            # ignore if button is not connected
            pass
        self.embedding.b_save.clicked.connect(self.gui_plot.save)
        self.embedding.b_load.clicked.connect(self.gui_plot.load)
        self.embedding.b_undo.clicked.connect(self.gui_plot.undo)
        self.embedding.b_redo.clicked.connect(self.gui_plot.redo)
        self.embedding.b_delete.clicked.connect(self.gui_plot.delete)
        self.embedding.b_finalize.clicked.connect(self.finalize)

    def finalize(self):
        """
        end edit process by exporting the benchmark

        :return: None
        """
        # name = config.BENCHMARK_ID
        try:
            graph = converter.step_collection_3(self.graph)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Internal Error",
                "There was an error during the processing of the graph.\n\n{}"
                .format(e),
                QMessageBox.Ok,
            )
            return
        self.parent.callback(ex.convert_to_scenario(graph))
        self.parent.osm_edit_window.close()

class AttributeEditor:
    """
    An editor to edit the attributes of a single edge
    """

    def __init__(
        self, edit_widget: QWidget, gui_frame: eeGUI_frame, ee_gui: gui.EdgeEditGUI
    ):
        """

        :param edit_widget: the widget to display the attribute editor in
        :param gui_frame: the gui window to display the edge editor in
        :param ee_gui: the embedded gui
        """
        self.road_type_indices = {
            "motorway": 0,
            "motorway_link": 1,
            "trunk": 2,
            "trunk_link": 3,
            "primary": 4,
            "primary_link": 5,
            "secondary": 6,
            "secondary_link": 7,
            "tertiary": 8,
            "tertiary_link": 9,
            "unclassified": 10,
            "residential": 11,
            "living_street": 12,
            "service": 13,
            "path": 14,
            "footway": 15,
            "cycleway": 16
        }

        self.road_types = {
            self.road_type_indices[road_type]: road_type
            for road_type in self.road_type_indices
        }

        self.edit_widget: QWidget = edit_widget
        self.co_road_type: QComboBox = gui_frame.co_road_type
        self.sp_lane_count: QSpinBox = gui_frame.sp_lane_count
        self.sp_forward_lanes: QSpinBox = gui_frame.sp_forward_lanes
        self.sp_backward_lanes: QSpinBox = gui_frame.sp_backward_lanes
        self.ch_oneway: QCheckBox = gui_frame.ch_oneway
        self.sp_lane_width: QDoubleSpinBox = gui_frame.sp_lane_width
        self.sp_speed_limit: QSpinBox = gui_frame.sp_speed_limit

        # the warnings in the following block can be ignored
        self.co_road_type.currentIndexChanged.connect(self.road_type_changed)
        self.sp_lane_count.valueChanged.connect(self.lane_count_changed)
        self.sp_forward_lanes.valueChanged.connect(self.forward_lanes_changed)
        self.sp_backward_lanes.valueChanged.connect(self.backward_lanes_changed)
        self.ch_oneway.stateChanged.connect(self.one_way_changed)
        self.sp_lane_width.valueChanged.connect(self.lane_width_changed)
        self.sp_speed_limit.valueChanged.connect(self.speed_limit_changed)

        # self.editing is a bool that indicates, if changes of values in the attribute editor
        # are done without user interaction
        # if this is the case, these values must not trigger the events connected above
        self.editing: bool = False

        self.ee_gui: gui.EdgeEditGUI = ee_gui

        self.selected_edge: Optional[rg.GraphEdge] = None
        self.hide_attributes()

    def hide_attributes(self) -> None:
        """
        hides attribute editor widgets,
        used when user has no selected edge

        :return: None
        """
        self.selected_edge = None
        for child in self.edit_widget.findChildren(QWidget):
            child.hide()

    def show_attributes(self, edge: Optional[rg.GraphEdge]) -> None:
        """
        display widgets of attribute editor, displays all values

        :param edge: selected edge
        :return: None
        """
        # print("edge_picker activated")
        if edge is not None:
            self.editing = True
            self.co_road_type.setCurrentIndex(self.road_type_indices[edge.roadtype])
            self.sp_lane_count.setValue(edge.nr_of_lanes)
            self.sp_forward_lanes.setValue(edge.forward_lanes)
            self.sp_backward_lanes.setValue(edge.backward_lanes)
            self.ch_oneway.setChecked(edge.oneway)
            self.sp_lane_width.setValue(edge.lanewidth)
            self.sp_speed_limit.setValue(int(edge.speedlimit * 3.6))
            self.selected_edge = edge
            for child in self.edit_widget.findChildren(QWidget):
                child.show()
            self.editing = False
        else:
            # print("hide!")
            self.hide_attributes()

    def set_attributes(self) -> None:
        """
        sets values of widgets to edge

        :return: None
        """
        if self.selected_edge is not None:
            assert not self.editing
            self.selected_edge.roadtype = self.road_types[
                self.co_road_type.currentIndex()
            ]
            self.selected_edge.nr_of_lanes = self.sp_lane_count.value()
            self.selected_edge.forward_lanes = self.sp_forward_lanes.value()
            self.selected_edge.backward_lanes = self.sp_backward_lanes.value()
            self.selected_edge.oneway = self.ch_oneway.isChecked()
            self.selected_edge.lanewidth = self.sp_lane_width.value()
            self.selected_edge.speedlimit = self.sp_speed_limit.value() / 3.6
            self.selected_edge.generate_lanes()
            self.selected_edge.turnlanes_forward = None
            self.selected_edge.turnlanes_backward = None
            if self.sp_forward_lanes.value() == 0:
                self.flip_edge()
            if self.ee_gui.last_picked_edge is not None:
                self.ee_gui.last_picked_edge.update_lanes_and_dir()

    def flip_edge(self) -> None:
        """
        flips the edge
        do only use if edge.backward_lanes != 0 or if this is a one-way edge

        :return: None
        """
        if not self.ch_oneway.isChecked():
            forward, backward = (
                self.sp_forward_lanes.value(),
                self.sp_backward_lanes.value(),
            )
            self.editing = True
            self.sp_forward_lanes.setValue(backward)
            self.sp_backward_lanes.setValue(forward)
            self.editing = False
        self.selected_edge.flip()

    def road_type_changed(self) -> None:
        """
        handles the event of a changed type of road

        :return: None
        """
        # self.editing needs to be activated here for the case, that another edge of a different road_type is picked
        if not self.editing:
            print("road type changed")
            self.editing = True
            roadtype = self.road_types[self.co_road_type.currentIndex()]
            assert (
                    config.LANECOUNTS[roadtype] >= 1
            ), "lane count must be >=1 ({})".format(roadtype)
            self.sp_lane_count.setValue(config.LANECOUNTS[roadtype])
            self.sp_forward_lanes.setValue(int(self.sp_lane_count.value() / 2 + 0.5))
            self.sp_backward_lanes.setValue(
                self.sp_lane_count.value() - self.sp_forward_lanes.value()
            )
            self.ch_oneway.setChecked(self.sp_lane_count.value() <= 1)
            self.sp_speed_limit.setValue(config.SPEED_LIMITS[roadtype] / 3.6)
            self.sp_lane_width.setValue(config.LANEWIDTHS[roadtype])
            self.editing = False
            self.set_attributes()

    def lane_count_changed(self) -> None:
        """
        handles the event of a changed lane count

        :return: None
        """
        if not self.editing:
            self.editing = True
            if self.sp_lane_count.value() == 0:
                self.sp_lane_count.setValue(1)
            if self.ch_oneway.isChecked():
                self.sp_forward_lanes.setValue(self.sp_lane_count.value())
            else:
                self.sp_forward_lanes.setValue(
                    int(self.sp_lane_count.value() / 2 + 0.5)
                )
                self.sp_backward_lanes.setValue(
                    self.sp_lane_count.value() - self.sp_forward_lanes.value()
                )
                if self.sp_backward_lanes.value() == 0:
                    self.ch_oneway.setChecked(True)
            self.editing = False
            self.set_attributes()

    def forward_lanes_changed(self) -> None:
        """
        handles the event of changed forward lanes

        :return: None
        """
        if not self.editing:
            self.editing = True
            if self.sp_forward_lanes.value() + self.sp_backward_lanes.value() == 0:
                self.sp_forward_lanes.setValue(1)
            self.sp_lane_count.setValue(
                self.sp_forward_lanes.value() + self.sp_backward_lanes.value()
            )
            if self.sp_forward_lanes.value() == 0:
                self.ch_oneway.setChecked(True)
            self.editing = False
            self.set_attributes()

    def backward_lanes_changed(self) -> None:
        """
        handles the event of changed backward lanes

        :return: None
        """
        if not self.editing:
            self.editing = True
            self.sp_lane_count.setValue(
                self.sp_forward_lanes.value() + self.sp_backward_lanes.value()
            )
            if self.sp_backward_lanes.value() == 0:
                self.ch_oneway.setChecked(True)
            else:
                self.ch_oneway.setChecked(False)
            self.editing = False
            self.set_attributes()

    def one_way_changed(self) -> None:
        """
        handles the event of a changed one way tag

        :return: None
        """
        if not self.editing:
            if self.ch_oneway.isChecked():
                self.sp_backward_lanes.setValue(0)
            else:
                self.sp_backward_lanes.setValue(1)
            self.sp_lane_count.setValue(
                self.sp_forward_lanes.value() + self.sp_backward_lanes.value()
            )
            self.set_attributes()

    def lane_width_changed(self) -> None:
        """
        handles the event of changed lane widths

        :return: None
        """
        if not self.editing:
            if self.sp_lane_width.value() < 0.2:
                self.sp_lane_width.setValue(0.2)
            self.set_attributes()

    def speed_limit_changed(self) -> None:
        """
        handles the event of a changed speed limit

        :return: None
        """
        if not self.editing:
            if self.sp_speed_limit.value() < 1:
                self.sp_speed_limit.setValue(1)
            self.set_attributes()
