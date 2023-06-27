
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from commonroad.scenario.lanelet import Lanelet
from commonroad.scenario.traffic_sign import *

from crdesigner.ui.gui.controller.toolboxes.road_network_controller.aerial_image_controller import \
    AddAerialImageController
from crdesigner.ui.gui.controller.toolboxes.road_network_controller.intersections_controller import \
    AddIntersectionController
from crdesigner.ui.gui.controller.toolboxes.road_network_controller.lanelet_controller import AddLaneletController
from crdesigner.ui.gui.controller.toolboxes.road_network_controller.traffic_lights_controller import \
    AddTrafficLightsController
from crdesigner.ui.gui.controller.toolboxes.road_network_controller.traffic_signs_controller import \
    AddTrafficSignController
from crdesigner.ui.gui.model.scenario_model import ScenarioModel
from crdesigner.ui.gui.utilities.waitingspinnerwidget import QtWaitingSpinner

from crdesigner.ui.gui.view.toolboxes.road_network_toolbox.road_network_toolbox_ui.road_network_toolbox_ui \
    import RoadNetworkToolboxUI
from crdesigner.map_conversion.osm2cr import config


class RoadNetworkController(QDockWidget, ):

    def __init__(self, mwindow):
        super().__init__("Road Network Toolbox")
        self.scenario_model = mwindow.scenario_model
        self.road_network_toolbox_ui = RoadNetworkToolboxUI(mwindow)
        self.adjust_ui()
        self.mwindow = mwindow
        self.text_browser = mwindow.crdesigner_console_wrapper.text_browser
        self.last_added_lanelet_id = None
        self.tmp_folder = mwindow.tmp_folder
        self.selection_changed_callback = mwindow.animated_viewer_wrapper.cr_viewer.update_plot
        self.initialized = False
        self.update = False
        self.updated_lanelet = False
        self.aerial_map_threshold = config.AERIAL_IMAGE_THRESHOLD

        self.lanelet_controller = AddLaneletController(self, self.scenario_model, self.road_network_toolbox_ui)
        self.traffic_sign_controller = AddTrafficSignController(self, self.scenario_model, self.road_network_toolbox_ui)
        self.traffic_lights_controller = AddTrafficLightsController(self, self.scenario_model,
                                                                    self.road_network_toolbox_ui)
        self.intersection_controller = AddIntersectionController(self, self.scenario_model,
                                                                 self.road_network_toolbox_ui)
        self.aerial_image_controller = AddAerialImageController(self, self.scenario_model, self.road_network_toolbox_ui)

        self.traffic_sign_controller.traffic_sign_ui.initialize_traffic_sign_information()
        self.traffic_lights_controller.traffic_lights_ui.initialize_traffic_light_information()
        self.intersection_controller.intersection_ui.initialize_intersection_information()
        self.set_default_road_network_list_information()

        self.connect_gui_elements()


    def adjust_ui(self):
        """Updates GUI properties like width, etc."""
        self.setFloating(True)
        self.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.setWidget(self.road_network_toolbox_ui)
        self.road_network_toolbox_ui.setMinimumWidth(375)

    def connect_gui_elements(self):
        self.initialized = False
        self.lanelet_controller.connect_gui_lanelet()
        self.traffic_sign_controller.connect_gui_traffic_signs()
        self.traffic_lights_controller.connect_gui_traffic_lights()
        self.intersection_controller.connect_gui_intersection()
        self.aerial_image_controller.connect_gui_aerial_image()

    def refresh_toolbox(self, model: ScenarioModel ):
        self.scenario_model = model
        self.set_default_road_network_list_information()

    def set_default_road_network_list_information(self):
        self.update = True

        self.lanelet_controller.lanelet_ui.set_default_lanelet_information()
        self.traffic_sign_controller.traffic_sign_ui.set_default_traffic_sign_information()
        self.traffic_lights_controller.traffic_lights_ui.set_default_traffic_lights_information()
        self.intersection_controller.intersection_ui.set_default_intersection_information()

        self.update = False

    def initialize_road_network_toolbox(self):
        self.traffic_sign_controller.traffic_sign_ui.initialize_traffic_sign_information()
        self.traffic_lights_controller.traffic_lights_ui.initialize_traffic_light_information()
        self.intersection_controller.intersection_ui.initialize_intersection_information()
        self.set_default_road_network_list_information()
        self.initialized =True

    def get_float(self, str) -> float:
        """
        Validates number and replace , with . to be able to insert german floats

        @return: string argument as valid float if not empty or not - else standard value 5
        """
        if str.text() == "-":
            self.text_browser.append("Inserted value of invalid. Standard value 5 will be used instead.")
        if str.text() and str.text() != "-":
            return float(str.text().replace(",", "."))
        else:
            return 5

    def selected_lanelet(self) -> Union[Lanelet, None]:
        return self.lanelet_controller.selected_lanelet()

    @pyqtSlot(str)
    def stopSpinner(self, data):
        print(data)
        self.scenario_model.stop_spinner()
        self.road_network_toolbox_ui.Spinner.stop()

    def start_spinner(self, spinner: QtWaitingSpinner):
        if (spinner.is_spinning()):
            spinner.stop()
        spinner.start()