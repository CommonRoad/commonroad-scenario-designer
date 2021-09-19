from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from crdesigner.input_output.gui.toolboxes.toolbox_ui import Toolbox


class MapConversionToolboxUI(Toolbox):
    def __init__(self):
        super().__init__()

    def define_sections(self):
        """reimplement this to define all your sections
        and add them as (title, widget) tuples to self.sections
        """
        self.sections.append(self.create_osm_widget())
        self.sections.append(self.create_opendrive_widget())
        self.sections.append(self.create_lanelet_widget())
        self.sections.append(self.create_sumo_widget())

    def create_sumo_widget(self):
        widget_sumo = QFrame(self.tree)
        layout_sumo = QVBoxLayout(widget_sumo)

        self.button_load_sumo = QPushButton("Load SUMO File")
        self.loaded_sumo_file = QLabel("no file selected")
        self.button_convert_sumo_to_cr = QPushButton("Convert SUMO to CommonRoad")
        self.button_convert_cr_to_sumo = QPushButton("Convert CommonRoad to SUMO")
        self.button_open_sumo_settings = QPushButton("Open SUMO Settings")

        load_sumo_groupbox = QGroupBox()
        layout_load_sumo_groupbox = QVBoxLayout()
        load_sumo_groupbox.setLayout(layout_load_sumo_groupbox)
        layout_load_sumo_groupbox.addWidget(self.button_load_sumo)
        layout_load_sumo_groupbox.addWidget(self.loaded_sumo_file)
        layout_load_sumo_groupbox.addWidget(self.button_convert_sumo_to_cr)
        layout_sumo.addWidget(load_sumo_groupbox)
        layout_sumo.addWidget(self.button_convert_cr_to_sumo)
        layout_sumo.addWidget(self.button_open_sumo_settings)

        title_sumo = "SUMO  Conversion"
        return title_sumo, widget_sumo

    def create_lanelet_widget(self):
        widget_lanelet2 = QFrame(self.tree)
        layout_lanelet2 = QVBoxLayout(widget_lanelet2)

        self.button_load_lanelet2 = QPushButton("Load Lanelet/Lanelet2 File")
        self.loaded_lanelet_file = QLabel("no file selected")
        self.button_convert_cr_to_lanelet2 = QPushButton("Convert CommonRoad to Lanelet/Lanelet2 ")
        self.button_convert_lanelet2_to_cr = QPushButton("Convert Lanelet/Lanelet2 to CommonRoad")

        load_lanelet_groupbox = QGroupBox()
        layout_load_lanelet_groupbox = QVBoxLayout()
        load_lanelet_groupbox.setLayout(layout_load_lanelet_groupbox)
        layout_load_lanelet_groupbox.addWidget(self.button_load_lanelet2)
        layout_load_lanelet_groupbox.addWidget(self.loaded_lanelet_file)
        layout_load_lanelet_groupbox.addWidget(self.button_convert_lanelet2_to_cr)
        layout_lanelet2.addWidget(load_lanelet_groupbox)
        layout_lanelet2.addWidget(self.button_convert_cr_to_lanelet2)

        title_lanelet2 = "Lanelet/Lanelet2  Conversion"
        return title_lanelet2, widget_lanelet2

    def create_opendrive_widget(self):
        widget_opendrive = QFrame(self.tree)
        layout_opendrive = QVBoxLayout(widget_opendrive)

        self.button_load_opendrive = QPushButton("Load OpenDRIVE File")
        self.loaded_opendrive_file = QLabel("no file selected")
        self.button_convert_opendrive = QPushButton("Convert OpenDRIVE to CommonRoad")

        load_opendrive_groupbox = QGroupBox()
        layout_load_opendrive_groupbox = QVBoxLayout()
        load_opendrive_groupbox.setLayout(layout_load_opendrive_groupbox)
        layout_load_opendrive_groupbox.addWidget(self.button_load_opendrive)
        layout_load_opendrive_groupbox.addWidget(self.loaded_opendrive_file)
        layout_load_opendrive_groupbox.addWidget(self.button_convert_opendrive)
        layout_opendrive.addWidget(load_opendrive_groupbox)

        title_opendrive = "OpenDRIVE  Conversion"
        return title_opendrive, widget_opendrive

    def create_osm_widget(self):
        widget_osm = QFrame(self.tree)
        layout_osm = QVBoxLayout(widget_osm)

        self.osm_conversion_coordinate_latitude = QLineEdit()
        self.osm_conversion_coordinate_latitude.setValidator(QDoubleValidator())
        self.osm_conversion_coordinate_latitude.setAlignment(Qt.AlignRight)
        self.osm_conversion_coordinate_latitude.setText("48.262545")
        self.osm_conversion_coordinate_longitude = QLineEdit()
        self.osm_conversion_coordinate_longitude.setValidator(QDoubleValidator())
        self.osm_conversion_coordinate_longitude.setAlignment(Qt.AlignRight)
        self.osm_conversion_coordinate_longitude.setText("11.668124")
        self.button_download_osm_file = QPushButton("Download OSM Map")
        self.osm_download_map_range = QSpinBox()
        self.osm_download_map_range.setMinimum(0)
        self.osm_download_map_range.setMaximum(10000)
        self.osm_download_map_range.setValue(500)
        self.button_load_osm_file = QPushButton("Load Local OSM File")
        self.osm_loading_status = QLabel("no file selected")
        self.button_load_osm_edit_state = QPushButton("Load OSM Edit State")
        self.osm_conversion_edit_manually_selection = QCheckBox("Edit Scenario Manually")
        self.button_start_osm_conversion = QPushButton("Convert OSM to CommonRoad")
        self.button_open_osm_settings = QPushButton("Open OSM Settings")
        layout_osm_conversion_configuration = QFormLayout()

        layout_osm_selection_groupbox = QVBoxLayout()
        osm_selection_groupbox = QGroupBox()
        osm_selection_groupbox.setLayout(layout_osm_selection_groupbox)
        layout_osm_range_groupbox = QFormLayout()
        osm_range_groupbox = QGroupBox()
        osm_range_groupbox.setLayout(layout_osm_range_groupbox)
        layout_osm_range_groupbox.addRow("Latitude:", self.osm_conversion_coordinate_latitude)
        layout_osm_range_groupbox.addRow("Longitude:", self.osm_conversion_coordinate_longitude)
        layout_osm_range_groupbox.addRow("Range:", self.osm_download_map_range)
        layout_osm_range_groupbox.addRow(self.button_download_osm_file)
        layout_osm_selection_groupbox.addWidget(osm_range_groupbox)
        layout_osm_selection_groupbox.addWidget(self.button_load_osm_file)
        layout_osm_selection_groupbox.addWidget(self.osm_loading_status)
        layout_osm_conversion_configuration.addWidget(osm_selection_groupbox)
        layout_osm_conversion_groupbox = QFormLayout()
        osm_conversion_groupbox = QGroupBox()
        osm_conversion_groupbox.setLayout(layout_osm_conversion_groupbox)
        layout_osm_conversion_groupbox.addRow(self.button_load_osm_edit_state)
        layout_osm_conversion_from_osm_groupbox = QFormLayout()
        osm_conversion_from_osm_groupbox = QGroupBox()
        osm_conversion_from_osm_groupbox.setLayout(layout_osm_conversion_from_osm_groupbox)
        layout_osm_conversion_from_osm_groupbox.addRow(self.osm_conversion_edit_manually_selection)
        layout_osm_conversion_from_osm_groupbox.addRow(self.button_start_osm_conversion)
        layout_osm_conversion_groupbox.addWidget(osm_conversion_from_osm_groupbox)
        layout_osm_conversion_configuration.addWidget(osm_conversion_groupbox)
        layout_osm_conversion_configuration.addWidget(self.button_open_osm_settings)
        layout_osm.addLayout(layout_osm_conversion_configuration)

        widget_title = "OSM Conversion"

        return widget_title, widget_osm
