from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
)

from crdesigner.ui.gui.utilities.toolbox_ui import Toolbox
from crdesigner.ui.gui.utilities.waitingspinnerwidget import QtWaitingSpinner


class MapConversionToolboxUI(Toolbox):
    def __init__(self, mwindow):
        super().__init__(mwindow)

    def define_sections(self):
        """reimplement this to define all your sections
        and add them as (title, widget) tuples to self.sections
        """
        self.sections.append(self.create_conversion_widget())

    def create_conversion_widget(self):
        widget_con = QFrame(self.tree)
        layout_con = QVBoxLayout(widget_con)

        self.con_groupbox = QGroupBox()
        self.layout_con_groupbox = QFormLayout()
        self.con_groupbox.setLayout(self.layout_con_groupbox)

        self.connecting_radio_button_group = QButtonGroup()

        self.open_drive = QRadioButton("OpenDRIVE")
        self.open_drive.setChecked(False)
        self.connecting_radio_button_group.addButton(self.open_drive)
        font = self.open_drive.font()
        font.setBold(True)
        self.open_drive.setFont(font)

        self.lanelet = QRadioButton("Lanelet/Lanelet2")
        self.lanelet.setChecked(False)
        self.connecting_radio_button_group.addButton(self.lanelet)
        font = self.lanelet.font()
        font.setBold(True)
        self.lanelet.setFont(font)

        self.osm = QRadioButton("OSM")
        self.osm.setChecked(False)
        self.connecting_radio_button_group.addButton(self.osm)
        font = self.osm.font()
        font.setBold(True)
        self.osm.setFont(font)

        self.sumo = QRadioButton("SUMO")
        self.sumo.setChecked(False)
        self.connecting_radio_button_group.addButton(self.sumo)
        font = self.sumo.font()
        font.setBold(True)
        self.sumo.setFont(font)

        self.layout_con_groupbox.addWidget(self.open_drive)
        self.layout_con_groupbox.addWidget(self.lanelet)
        self.layout_con_groupbox.addWidget(self.osm)
        self.layout_con_groupbox.addWidget(self.sumo)

        self.Spinner = QtWaitingSpinner(self, centerOnParent=True)
        self.Spinner.setInnerRadius(7)
        self.Spinner.setNumberOfLines(10)
        self.Spinner.setLineLength(7)
        self.Spinner.setLineWidth(2)

        self.chosen_method = ""

        layout_con.addWidget(self.con_groupbox)
        self.con_groupbox.setMinimumHeight(350)

        title_con = "Conversions"
        return title_con, widget_con

    def adjust_sections(self):
        self.remove_fields()

        if self.open_drive.isChecked():
            self.chosen_method = "open_drive"
            self.init_open_drive()
        elif self.lanelet.isChecked():
            self.chosen_method = "lanelet"
            self.init_lanelet()
        elif self.osm.isChecked():
            self.chosen_method = "osm"
            self.init_osm()
        elif self.sumo.isChecked():
            self.chosen_method = "sumo"
            self.init_sumo()

    def init_open_drive(self):
        self.button_convert_opendrive2cr = QPushButton("Convert OpenDRIVE to CommonRoad")
        self.layout_con_groupbox.insertRow(1, self.button_convert_opendrive2cr)
        self.button_convert_cr2opendrive = QPushButton("Convert CommonRoad to OpenDRIVE")
        self.layout_con_groupbox.insertRow(2, self.button_convert_cr2opendrive)

    def init_lanelet(self):
        self.button_convert_lanelet2_to_cr = QPushButton("Convert Lanelet/Lanelet2 to CommonRoad")
        self.button_convert_cr_to_lanelet2 = QPushButton("Convert CommonRoad to Lanelet/Lanelet2")
        self.layout_con_groupbox.insertRow(2, self.button_convert_lanelet2_to_cr)
        self.layout_con_groupbox.insertRow(3, self.button_convert_cr_to_lanelet2)

    def init_osm(self):
        self.button_start_osm_conversion = QPushButton("Convert OSM to CommonRoad")
        self.button_start_osm_conversion_with_sumo_parser = QPushButton(
            "Convert OSM to CommonRoad using Sumo Parser"
        )
        self.button_start_osm_conversion_with_sumo_parser.setToolTip(
            "The conversion follows the route : \nOsm -> OpenDrive -> CR\nUseful for densed crossing"
        )

        self.connecting_radio_button_group_osm = QButtonGroup()
        self.load_local_file = QRadioButton("Load local file")
        self.load_local_file.setChecked(True)
        self.connecting_radio_button_group_osm.addButton(self.load_local_file)

        self.download_file = QRadioButton("Download file")
        self.connecting_radio_button_group_osm.addButton(self.download_file)

        self.load_local_file.clicked.connect(lambda: self.adjust_osm_fields())
        self.download_file.clicked.connect(lambda: self.adjust_osm_fields())

        self.osm_files = QGridLayout()
        self.osm_files.addWidget(self.load_local_file, 1, 0)
        self.osm_files.addWidget(self.download_file, 1, 1)

        self.layout_con_groupbox.insertRow(3, self.osm_files)

        self.layout_con_groupbox.insertRow(4, self.button_start_osm_conversion)
        self.layout_con_groupbox.insertRow(5, self.button_start_osm_conversion_with_sumo_parser)

    def adjust_osm_fields(self):
        if self.download_file.isChecked():
            self.osm_conversion_coordinate_latitude = QLineEdit()
            self.osm_conversion_coordinate_latitude.setValidator(QDoubleValidator())
            self.osm_conversion_coordinate_latitude.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.osm_conversion_coordinate_latitude.setText("48.262545")
            self.osm_conversion_coordinate_longitude = QLineEdit()
            self.osm_conversion_coordinate_longitude.setValidator(QDoubleValidator())
            self.osm_conversion_coordinate_longitude.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.osm_conversion_coordinate_longitude.setText("11.658142")
            self.osm_download_map_range = QSpinBox()
            self.osm_download_map_range.setMinimum(0)
            self.osm_download_map_range.setMaximum(10000)
            self.osm_download_map_range.setValue(500)

            self.layout_osm_range_groupbox = QFormLayout()
            self.osm_range_groupbox = QGroupBox()
            self.osm_range_groupbox.setLayout(self.layout_osm_range_groupbox)
            self.layout_osm_range_groupbox.addRow(
                "Latitude:", self.osm_conversion_coordinate_latitude
            )
            self.layout_osm_range_groupbox.addRow(
                "Longitude:", self.osm_conversion_coordinate_longitude
            )
            self.layout_osm_range_groupbox.addRow("Range:", self.osm_download_map_range)
            self.layout_con_groupbox.insertRow(4, self.osm_range_groupbox)
        else:
            self.layout_con_groupbox.removeRow(self.osm_range_groupbox)

    def init_sumo(self):
        self.button_convert_sumo_to_cr = QPushButton("Convert SUMO to CommonRoad")
        self.button_convert_cr_to_sumo = QPushButton("Convert CommonRoad to SUMO")
        self.layout_con_groupbox.insertRow(4, self.button_convert_sumo_to_cr)
        self.layout_con_groupbox.insertRow(5, self.button_convert_cr_to_sumo)

    def remove_fields(self):
        if self.chosen_method == "open_drive":
            self.layout_con_groupbox.removeRow(self.button_convert_opendrive2cr)
            self.layout_con_groupbox.removeRow(self.button_convert_cr2opendrive)
        elif self.chosen_method == "lanelet":
            self.layout_con_groupbox.removeRow(self.button_convert_lanelet2_to_cr)
            self.layout_con_groupbox.removeRow(self.button_convert_cr_to_lanelet2)
        elif self.chosen_method == "osm":
            self.layout_con_groupbox.removeRow(self.button_start_osm_conversion)
            self.layout_con_groupbox.removeRow(self.button_start_osm_conversion_with_sumo_parser)
            if self.download_file.isChecked():
                self.layout_con_groupbox.removeRow(self.osm_range_groupbox)
            self.layout_con_groupbox.removeRow(self.osm_files)
        elif self.chosen_method == "sumo":
            self.layout_con_groupbox.removeRow(self.button_convert_sumo_to_cr)
            self.layout_con_groupbox.removeRow(self.button_convert_cr_to_sumo)

    def update_window(self):
        super().update_window()
