from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from crmapconverter.io.scenario_designer.gui_src import CR_Scenario_Designer  # do not remove!!!
from crmapconverter.io.scenario_designer.toolboxes.toolbox_ui import Toolbox, CheckableComboBox

from commonroad.scenario.scenario import Tag, TimeOfDay, Weather, Underground
from commonroad.scenario.traffic_sign import SupportedTrafficSignCountry


class ScenarioToolbox(Toolbox):
    def __init__(self):
        super().__init__()
       # self.sections.append(self.define_sections())

    def define_sections(self):
        """reimplement this to define all your sections
        and add them as (title, widget) tuples to self.sections
        """
        widget_scenario = QFrame(self.tree)
        layout_scenario = QVBoxLayout(widget_scenario)

        self.label_benchmark_id = QLabel("")
        self.label_benchmark_id.setFont(QFont("Arial", 10, QFont.Bold))
        self.label_benchmark_id = QLabel("Straight lanelet parameters")

        self.country = QComboBox()
        country_list = [e.value for e in SupportedTrafficSignCountry]
        self.country.addItems(country_list)

        self.scenario_scene_id = QSpinBox()
        self.scenario_scene_id.setMinimum(1)
        self.scenario_scene_id.setMaximum(999)

        self.scenario_scene_id = QSpinBox()
        self.scenario_scene_id.setMinimum(1)
        self.scenario_scene_id.setMaximum(999)

        self.scenario_config_id = QSpinBox()
        self.scenario_config_id.setMinimum(1)
        self.scenario_config_id.setMaximum(999)

        self.prediction_type = QComboBox()
        prediction_type_list = ["S", "T", "P"]
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
        self.scenario_time_step_size.setAlignment(Qt.AlignRight)

        self.scenario_author = QLineEdit()
        self.scenario_author.setAlignment(Qt.AlignRight)

        self.scenario_affiliation = QLineEdit()
        self.scenario_affiliation.setAlignment(Qt.AlignRight)

        self.scenario_source = QLineEdit()
        self.scenario_source.setAlignment(Qt.AlignRight)

        self.scenario_date = QDateEdit()

        self.scenario_geo_anme_id = QLineEdit()
        self.scenario_geo_anme_id.setAlignment(Qt.AlignRight)

        self.scenario_latitude = QLineEdit()
        self.scenario_latitude.setValidator(QDoubleValidator())
        self.scenario_latitude.setAlignment(Qt.AlignRight)

        self.scenario_longitude = QLineEdit()
        self.scenario_longitude.setValidator(QDoubleValidator())
        self.scenario_longitude.setAlignment(Qt.AlignRight)

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

        scenario_information = QFormLayout()
        scenario_information.addRow("Benchmark ID", self.label_benchmark_id)
        scenario_information.addRow("Country", self.country)
        scenario_information.addRow("Scene ID", self.scenario_scene_id)
        scenario_information.addRow("Initial Config ID", self.scenario_config_id)
        scenario_information.addRow("Prediction Type", self.prediction_type)
        scenario_information.addRow("Prediction ID", self.scenario_prediction_id)
        scenario_information.addRow(self.cooperative_scenario)
        scenario_information.addRow("Tags", self.scenario_tags)
        scenario_information.addRow("Time Step Size", self.scenario_time_step_size)
        scenario_information.addRow("Author", self.scenario_author)
        scenario_information.addRow("Affiliation", self.scenario_affiliation)
        scenario_information.addRow("Source", self.scenario_source)
        scenario_information.addRow("Date", self.scenario_date)
        scenario_information.addRow("GeoNameID", self.scenario_geo_anme_id)
        scenario_information.addRow("Latitude", self.scenario_latitude)
        scenario_information.addRow("Longitude", self.scenario_longitude)
        scenario_information.addRow("Time of Day", self.scenario_time_of_day)
        scenario_information.addRow("Weather", self.scenario_weather)
        scenario_information.addRow("Underground", self.scenario_underground)
        scenario_information.addRow("Time", self.scenario_time_hour)

        layout_scenario.addLayout(scenario_information)

        widget_title = "Scenario"

        self.sections.append((widget_title, widget_scenario))