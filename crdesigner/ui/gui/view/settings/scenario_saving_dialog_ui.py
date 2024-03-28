from commonroad.scenario.scenario import Tag, TimeOfDay, Underground, Weather
from commonroad.scenario.traffic_sign import SupportedTrafficSignCountry
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator, QFont, QIntValidator
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QWidget,
)

from crdesigner.common.config import gui_config
from crdesigner.ui.gui.utilities.toolbox_ui import CheckableComboBox


class ScenarioSavingDialogUI(QWidget):
    def __init__(self):
        super().__init__()

        self.label_benchmark_id = QLabel("")
        self.label_benchmark_id.setFont(QFont("Arial", 10, QFont.Weight.Bold))

        self.label_directory = QLabel("")
        self.label_directory.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.button_directory = QPushButton("Change Directory")

        self.country = QComboBox()
        country_list = [e.value for e in SupportedTrafficSignCountry]
        self.country.addItems(country_list)

        self.scenario_scene_name = QLineEdit()
        self.scenario_scene_name.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.scenario_scene_id = QSpinBox()
        self.scenario_scene_id.setMinimum(1)
        self.scenario_scene_id.setMaximum(999)

        self.scenario_config_id = QSpinBox()
        self.scenario_config_id.setMinimum(1)
        self.scenario_config_id.setMaximum(999)

        self.prediction_type = QComboBox()
        prediction_type_list = ["T", "S", "P"]
        self.prediction_type.addItems(prediction_type_list)

        self.scenario_prediction_id = QSpinBox()
        self.scenario_prediction_id.setMinimum(1)
        self.scenario_prediction_id.setMaximum(999)

        self.cooperative_scenario = QCheckBox("Cooperative Scenario")

        self.scenario_tags = CheckableComboBox()
        tag_list = [e.value for e in Tag]
        self.scenario_tags.addItems(tag_list)

        self.scenario_time_step_size = QLineEdit()
        self.scenario_time_step_size.setValidator(QDoubleValidator())
        self.scenario_time_step_size.setMaxLength(4)
        self.scenario_time_step_size.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.scenario_author = QLineEdit()
        self.scenario_author.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.scenario_affiliation = QLineEdit()
        self.scenario_affiliation.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.scenario_source = QLineEdit()
        self.scenario_source.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.location_storage_selection = QCheckBox("Store Location")

        self.scenario_geo_anme_id = QLineEdit()
        self.scenario_geo_anme_id.setValidator(QIntValidator())
        self.scenario_geo_anme_id.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.scenario_latitude = QLineEdit()
        self.scenario_latitude.setValidator(QDoubleValidator())
        self.scenario_latitude.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.scenario_longitude = QLineEdit()
        self.scenario_longitude.setValidator(QDoubleValidator())
        self.scenario_longitude.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.scenario_time_of_day = QComboBox()
        time_of_day_list = [e.value for e in TimeOfDay]
        self.scenario_time_of_day.addItems(time_of_day_list)

        self.scenario_weather = QComboBox()
        weather_list = [e.value for e in Weather]
        self.scenario_weather.addItems(weather_list)

        self.scenario_underground = QComboBox()
        underground_list = [e.value for e in Underground]
        self.scenario_underground.addItems(underground_list)

        self.scenario_time_hour = QSpinBox()
        self.scenario_time_hour.setMinimum(0)
        self.scenario_time_hour.setMaximum(23)

        self.scenario_time_minute = QSpinBox()
        self.scenario_time_minute.setMinimum(0)
        self.scenario_time_minute.setMaximum(59)

        self.geo_reference = QComboBox()
        references = [
            gui_config.pseudo_mercator,
            gui_config.utm_default,
            gui_config.lanelet2_default,
            "Enter your own Reference",
        ]
        self.geo_reference.addItems(references)

        self.x_translation = QLineEdit()
        self.x_translation.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.y_translation = QLineEdit()
        self.y_translation.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.button_save = QPushButton("Save Scenario/Map")

        scenario_information = QFormLayout()
        scenario_information.addRow("Benchmark ID", self.label_benchmark_id)
        scenario_information.addRow("Directory", self.label_directory)
        scenario_information.addRow(self.button_directory)
        scenario_information.addRow("Country:", self.country)
        scenario_information.addRow("Scene Name:", self.scenario_scene_name)
        scenario_information.addRow("Scene ID:", self.scenario_scene_id)
        scenario_information.addRow("Initial Config ID:", self.scenario_config_id)
        scenario_information.addRow("Prediction Type:", self.prediction_type)
        scenario_information.addRow("Prediction ID:", self.scenario_prediction_id)
        scenario_information.addRow(self.cooperative_scenario)
        scenario_information.addRow("Tags:", self.scenario_tags)
        scenario_information.addRow("Time Step Size:", self.scenario_time_step_size)
        scenario_information.addRow("Author:", self.scenario_author)
        scenario_information.addRow("Affiliation:", self.scenario_affiliation)
        scenario_information.addRow("Source:", self.scenario_source)
        location_groupbox = QGroupBox()
        layout_location_groupbox = QFormLayout()
        location_groupbox.setLayout(layout_location_groupbox)
        layout_location_groupbox.addRow(self.location_storage_selection)
        layout_location_groupbox.addRow("GeoNameID:", self.scenario_geo_anme_id)
        layout_location_groupbox.addRow("Latitude:", self.scenario_latitude)
        layout_location_groupbox.addRow("Longitude:", self.scenario_longitude)
        layout_location_groupbox.addRow("Time of Day:", self.scenario_time_of_day)
        layout_location_groupbox.addRow("Weather:", self.scenario_weather)
        layout_location_groupbox.addRow("Underground:", self.scenario_underground)
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Time [hh-mm]:"))
        time_layout.addWidget(self.scenario_time_hour)
        time_layout.addWidget(self.scenario_time_minute)
        layout_location_groupbox.addRow(time_layout)
        layout_location_groupbox.addRow("Geo Reference: ", self.geo_reference)
        layout_location_groupbox.addRow("x Translation", self.x_translation)
        layout_location_groupbox.addRow("y Translation", self.y_translation)
        scenario_information.addRow(location_groupbox)
        scenario_information.addRow(self.button_save)

        self.setLayout(scenario_information)
