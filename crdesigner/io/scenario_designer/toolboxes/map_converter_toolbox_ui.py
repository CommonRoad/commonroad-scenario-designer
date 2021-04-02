from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from crdesigner.io.scenario_designer.toolboxes.toolbox_ui import Toolbox


class MapConversionToolboxUI(Toolbox):
    def __init__(self):
        super().__init__()

    def define_sections(self):
        """reimplement this to define all your sections
        and add them as (title, widget) tuples to self.sections
        """
        #  OSM Section
        widget_osm = QFrame(self.tree)
        layout_osm = QVBoxLayout(widget_osm)


        self.osm_conversion_load_osm_file_selection = QRadioButton("Load OSM File")
        self.osm_conversion_download_osm_file_selection = QRadioButton("Download OSM Map")

        self.button_select_osm_file = QPushButton("Select File")

        self.osm_conversion_coordinate_latitude = QLineEdit()
        self.osm_conversion_coordinate_latitude.setValidator(QDoubleValidator())
        self.osm_conversion_coordinate_latitude.setAlignment(Qt.AlignRight)
        self.osm_conversion_coordinate_longitude = QLineEdit()
        self.osm_conversion_coordinate_longitude.setValidator(QDoubleValidator())
        self.osm_conversion_coordinate_longitude.setAlignment(Qt.AlignRight)

        self.osm_download_map_range = QSpinBox()
        self.osm_download_map_range.setMinimum(0)
        self.osm_download_map_range.setMaximum(10000)

        self.osm_conversion_edit_manually_selection = QCheckBox("Edit Scenario Manually")

        self.button_load_osm_edit_state = QPushButton("Load OSM Edit State")
        self.button_start_osm_conversion = QPushButton("Start Conversion")

        layout_osm_conversion_configuration = QFormLayout()

        layout_osm_file_selection_groupbox = QFormLayout()
        osm_file_selection_groupbox = QGroupBox()
        osm_file_selection_groupbox.setLayout(layout_osm_file_selection_groupbox)
        layout_osm_file_selection_groupbox.addRow(self.osm_conversion_load_osm_file_selection)
        layout_osm_file_selection_groupbox.addRow(self.osm_conversion_download_osm_file_selection)
        layout_osm_file_selection_groupbox.addRow(self.button_select_osm_file)
        layout_osm_conversion_configuration.addWidget(osm_file_selection_groupbox)

        layout_osm_range_groupbox = QFormLayout()
        osm_range_groupbox = QGroupBox()
        osm_range_groupbox.setLayout(layout_osm_range_groupbox)
        layout_osm_range_groupbox.addRow("Latitude:", self.osm_conversion_coordinate_latitude)
        layout_osm_range_groupbox.addRow("Longitude:", self.osm_conversion_coordinate_longitude)
        layout_osm_range_groupbox.addRow("Range:", self.osm_download_map_range)
        layout_osm_conversion_configuration.addWidget(osm_range_groupbox)

        layout_osm_conversion_configuration.addRow(self.osm_conversion_edit_manually_selection)
        layout_osm_conversion_configuration.addRow(self.button_load_osm_edit_state)
        layout_osm_conversion_configuration.addRow(self.button_start_osm_conversion)

        layout_osm.addLayout(layout_osm_conversion_configuration)

        title_osm = "OSM Conversion"
        self.sections.append((title_osm, widget_osm))

        #  OpenDRIVE Section
        widget_opendrive = QFrame(self.tree)
        layout_opendrive = QVBoxLayout(widget_opendrive)

        self.button_load_open_drive = QPushButton("Load OpenDRIVE File")
        open_drive_conversion_configuration = QFormLayout()

        open_drive_conversion_configuration.addRow(self.button_load_open_drive)

        layout_opendrive.addLayout(open_drive_conversion_configuration)

        title_opendrive = "OpenDRIVE  Conversion"
        self.sections.append((title_opendrive, widget_opendrive))

        #  Lanelet/Lanelet2 Section
        widget_lanelet2 = QFrame(self.tree)
        layout_lanelet2 = QVBoxLayout(widget_lanelet2)

        self.button_load_lanelet2 = QPushButton("Load Lanelet2 File")
        lanelet2_conversion_configuration = QFormLayout()

        lanelet2_conversion_configuration.addRow(self.button_load_lanelet2)

        layout_lanelet2.addLayout(lanelet2_conversion_configuration)

        title_lanelet2 = "Lanelet/Lanelet2  Conversion"
        self.sections.append((title_lanelet2, widget_lanelet2))

        #  SUMO Section
        widget_sumo = QFrame(self.tree)
        layout_sumo = QVBoxLayout(widget_sumo)

        self.button_convert_to_sumo = QPushButton("Convert Map to SUMO")
        sumo_conversion_configuration = QFormLayout()

        sumo_conversion_configuration.addRow(self.button_convert_to_sumo)

        layout_sumo.addLayout(sumo_conversion_configuration)

        title_sumo = "SUMO  Conversion"
        self.sections.append((title_sumo, widget_sumo))
