from dataclasses import dataclass, field
from typing import Optional
from urllib.request import HTTPBasicAuthHandler, build_opener, install_opener, urlopen

import requests
from commonroad.visualization.draw_params import (
    DynamicObstacleParams,
    IntersectionParams,
    LaneletNetworkParams,
    LaneletParams,
    MPDrawParams,
    OccupancyParams,
    TrafficLightParams,
    TrafficSignParams,
    TrajectoryParams,
)

from crdesigner.common.config.config_base import Attribute, BaseConfig

# projects the lane-network in a way that aligns well with aerial images
pseudo_mercator = "EPSG:3857"
utm_default = "+proj=utm +zone=32 +ellps=WGS84"
lanelet2_default = "ETRF89"


@dataclass
class ColorSchema:
    axis: str = "all"
    background: str = "#f0f0f0"
    color: str = "#0a0a0a"
    font_size: str = "11pt"
    highlight: str = "#c0c0c0"
    highlight_text: str = "#202020"
    second_background: str = "#ffffff"
    disabled: str = "#959595"


@dataclass
class DrawParamsCustom(MPDrawParams):
    color_schema: ColorSchema = field(default_factory=ColorSchema)


def validate_bing_key(key) -> bool:
    """
    Validates the password specified by BING_MAPS_KEY in the config of the settings.
    :return: bool: True for valid password, False for wrong password
    """
    if key == "":
        return True

    req = f"http://dev.virtualearth.net/REST/V1/Imagery/Metadata/Aerial?output=json&include=ImageryProviders&key={key}"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:80.0) Gecko/20100101 Firefox/80.0"
    }
    try:
        with requests.session() as s:
            # load cookies otherwise an HTTP error occurs
            s.get(f"http://dev.virtualearth.net/?key={key}", headers=headers)

            # get data
            data = s.get(req, headers=headers).json()
            if data["authenticationResultCode"] == "ValidCredentials":
                return True
    except Exception:
        pass
    return False


def validate_ldbv_credentials(_) -> bool:
    """
    Validates the username and password specified by LDBV_USERNAME and LDBV_PASSWORD in the config of the settings.
    """

    ldbv_username = gui_config.LDBV_USERNAME
    ldbv_password = gui_config.LDBV_PASSWORD

    if ldbv_username == "" or ldbv_password == "":
        return True

    url = (
        "https://geoservices.bayern.de/wms/v2/ogc_dop20.cgi?service=wms&request=GetMap&version=1.1.1&bbox=11.65541,"
        "48.26142,11.66093,48.26386&width=100&height=100&layers=by_dop20c&format=image/jpeg&srs=EPSG:4326"
    )

    try:
        auth_handler = HTTPBasicAuthHandler()
        auth_handler.add_password(
            realm="WMS DOP20",
            uri="https://geoservices.bayern.de/wms/v2/ogc_dop20.cgi",
            user=ldbv_username,
            passwd=ldbv_password,
        )
        opener = build_opener(auth_handler)
        install_opener(opener)
        with urlopen(url) as webpage:
            webpage.read()
    except Exception:
        return False
    return True


class GuiConfig(BaseConfig):
    """
    This class contains all settings for the GUI.
    """

    # Borders for Scenario/ Zoom
    MAX_LANELET = 100
    MAX_TRAFFIC_SIGNS = 50
    MAX_X_TRESHOLD = 50
    MAX_Y_TRESHOLD = 50
    ZOOM_DETAILED = False

    # focus on the selection
    ENABLE_UNDETAILED_DISPLAY: Attribute = Attribute(True, "Enable undetailed display")
    MWINDOW_TMP_FOLDER_PATH: Attribute = Attribute("/tmp/cr_designer/", "Temporary folder path")
    LOG_ACTIONS_OF_THE_USER: Attribute = Attribute(True, "Log user actions")
    ENABLE_EDITING_CURVED_LANELETS: Attribute = Attribute(True, "Enable editing of curved lanelets")
    # default values in default_draw_params
    DRAW_TRAJECTORY: Attribute = Attribute(False, "Draw trajectory")
    DRAW_DYNAMIC_OBSTACLES: Attribute = Attribute(True, "Draw dynamic obstacles")
    DRAW_OBSTACLE_LABELS: Attribute = Attribute(True, "Draw obstacle labels")
    DRAW_OBSTACLE_ICONS: Attribute = Attribute(False, "Draw obstacle icons")
    DRAW_OBSTACLE_DIRECTION: Attribute = Attribute(False, "Draw obstacle direction")
    DRAW_OBSTACLE_SIGNALS: Attribute = Attribute(True, "Draw obstacle signals")
    DRAW_OCCUPANCY: Attribute = Attribute(False, "Draw occupancy")
    DRAW_TRAFFIC_SIGNS: Attribute = Attribute(False, "Draw traffic signs")
    DRAW_TRAFFIC_LIGHTS: Attribute = Attribute(True, "Draw traffic lights")
    DRAW_INCOMING_LANELETS: Attribute = Attribute(True, "Draw incoming lanelets")
    DRAW_SUCCESSORS: Attribute = Attribute(True, "Draw successors")
    DRAW_INTERSECTION_LABELS: Attribute = Attribute(False, "Draw intersection labels")
    DARKMODE: Attribute = Attribute(False, "Darkmode")
    MODERN_LOOK: Attribute = Attribute(True, display_name="Modern Look")
    AXIS_VISIBLE: Attribute = Attribute(
        value="All", display_name="Axis visible", options=["All", "Left/Bottom", "None"]
    )
    LEGEND: Attribute = Attribute(True, "Legend")
    # The key to access bing maps
    BING_MAPS_KEY: Attribute = Attribute(
        value="", display_name="Bing maps key", validation=validate_bing_key
    )
    # Username and password to access LDBV maps
    LDBV_USERNAME: Attribute = Attribute(
        value="", display_name="LDBV username", validation=validate_ldbv_credentials
    )
    LDBV_PASSWORD: Attribute = Attribute(
        value="", display_name="LDBV password", validation=validate_ldbv_credentials
    )

    # projects the lane-network in a way that aligns well with aerial images
    pseudo_mercator = Attribute(pseudo_mercator, "Pseudo Mercator")
    utm_default = Attribute(utm_default, "UTM Default")

    verify_repair_scenario = Attribute(
        value=True,
        display_name="Verify and Repair Map",
        description="Verify and Repair CommonRoad Map when Loading/Storing Scenario",
    )

    # Default values for obstacle types
    OBSTACLE_SPECS = {
        "car": {"width": "1.610", "length": "4.508", "shape": "Rectangle"},
        "truck": {"width": "2.550", "length": "16.50", "shape": "Rectangle"},
        "bus": {"width": "2.550", "length": "11.95", "shape": "Rectangle"},
        "bicycle": {"width": "0.64", "length": "1.75", "shape": "Rectangle"},
        "pedestrian": {"shape": "Circle", "radius": "0.3"},
        "priorityVehicle": {"width": "1.610", "length": "4.508", "shape": "Rectangle"},
        "parkedVehicle": {"width": "1.610", "length": "4.508", "shape": "Rectangle"},
        "motorcycle": {"width": "1.016", "length": "2.540", "shape": "Rectangle"},
        "taxi": {"width": "1.610", "length": "4.508", "shape": "Rectangle"},
    }

    # The layout of the settings window
    LAYOUT = [
        [
            "Appearance",
            DARKMODE,
            MODERN_LOOK,
            AXIS_VISIBLE,
            LEGEND,
            "Obstacle visualization",
            DRAW_DYNAMIC_OBSTACLES,
            DRAW_TRAJECTORY,
            DRAW_OBSTACLE_LABELS,
            DRAW_OBSTACLE_ICONS,
            DRAW_OBSTACLE_DIRECTION,
            DRAW_OBSTACLE_SIGNALS,
            "Intersection visualization",
            DRAW_INCOMING_LANELETS,
            DRAW_SUCCESSORS,
            DRAW_INTERSECTION_LABELS,
        ],
        [
            "Other",
            ENABLE_EDITING_CURVED_LANELETS,
            ENABLE_UNDETAILED_DISPLAY,
            DRAW_OCCUPANCY,
            DRAW_TRAFFIC_SIGNS,
            DRAW_TRAFFIC_LIGHTS,
            BING_MAPS_KEY,
            LDBV_USERNAME,
            LDBV_PASSWORD,
            LOG_ACTIONS_OF_THE_USER,
            verify_repair_scenario,
        ],
    ]

    def get_draw_params(self) -> DrawParamsCustom:
        """
        :returns: DrawParams based on the settings selected in the GUI Settings window
        """
        return DrawParamsCustom(
            color_schema=self.get_colorscheme(),
            lanelet_network=LaneletNetworkParams(
                traffic_sign=TrafficSignParams(draw_traffic_signs=self.DRAW_TRAFFIC_SIGNS),
                intersection=IntersectionParams(
                    draw_intersections=True,
                    draw_incoming_lanelets=self.DRAW_INCOMING_LANELETS,
                    draw_successors=self.DRAW_SUCCESSORS,
                    show_label=self.DRAW_INTERSECTION_LABELS,
                ),
                traffic_light=TrafficLightParams(draw_traffic_lights=self.DRAW_TRAFFIC_LIGHTS),
            ),
            trajectory=TrajectoryParams(draw_trajectory=self.DRAW_TRAJECTORY),
            occupancy=OccupancyParams(draw_occupancies=self.DRAW_OCCUPANCY),
            dynamic_obstacle=DynamicObstacleParams(
                trajectory=TrajectoryParams(draw_trajectory=self.DRAW_TRAJECTORY),
                draw_icon=self.DRAW_OBSTACLE_ICONS,
                draw_direction=self.DRAW_OBSTACLE_DIRECTION,
                draw_signals=self.DRAW_OBSTACLE_SIGNALS,
                show_label=self.DRAW_OBSTACLE_LABELS,
            ),
        )

    def show_dynamic_obstacles(self) -> bool:
        """
        :returns: Boolean whether dynamic_obstacles should be shown or not
        """
        return self.DRAW_DYNAMIC_OBSTACLES

    def get_undetailed_params(
        self, lanelet_count: int = 0, traffic_sign_count: int = 0
    ) -> Optional[LaneletParams]:
        """
        If the detailed display is enables checks if the scenario should be shown undetailed to gain performance.

        :param lanelet_count: count of the lanelets of the scenario
        :param traffic_sign_count: count of te traffic signs of the scenario
        :returns: LaneletParams if the scenario should be shown undetailed. None otherwise
        """
        if not self.ENABLE_UNDETAILED_DISPLAY:
            return None
        elif lanelet_count <= self.MAX_LANELET and traffic_sign_count <= self.MAX_TRAFFIC_SIGNS:
            return None
        elif not self.ZOOM_DETAILED:
            return None
        else:
            return LaneletParams(
                draw_start_and_direction=False,
                draw_stop_line=False,
                draw_center_bound=False,
                draw_right_bound=True,
                draw_left_bound=True,
                fill_lanelet=False,
                draw_line_markings=False,
            )

    def resize_lanelet_network_when_zoom(
        self, lanelet_count: int, traffic_sign_count: int, x: float, y: float
    ) -> bool:
        """
        Checks wether the lanelet network should be resizued based if the lanelet is big or the zoom level

        :param lanelet_count: count of lanelets
        :param traffic_sign_count: count of the traffic signs
        :param x: x dimension
        :param y: y dimension

        :returns; boolean wheater the lanelet_network should be resized
        """
        return (x <= self.MAX_X_TRESHOLD or y <= self.MAX_Y_TRESHOLD) and (
            lanelet_count > self.MAX_LANELET or traffic_sign_count > self.MAX_TRAFFIC_SIGNS
        )

    def set_zoom_treshold(self, x, y):
        """
        sets the variable within the gui_params to the respective boolean depending on the given x and y dimenensions

        :param x: x dimension
        :param y: y dimension
        """
        if x <= self.MAX_X_TRESHOLD and y <= self.MAX_Y_TRESHOLD:
            self.ZOOM_DETAILED = False
        else:
            self.ZOOM_DETAILED = True

    def get_colorscheme(self) -> ColorSchema:
        """
        gives back the respective ColorSchema depending if the GUI is set to Dark or Light Mode

        :returns: ColorSchema depending on the setting
        """
        if gui_config.DARKMODE:
            colorscheme = ColorSchema(
                axis=gui_config.AXIS_VISIBLE,
                background="#303030",
                color="#f0f0f0",
                highlight="#1e9678",
                second_background="#2c2c2c",
            )
        else:
            colorscheme = ColorSchema(axis=gui_config.AXIS_VISIBLE, background="#f0f0f0")

        return colorscheme

    def logging(self):
        return gui_config.LOG_ACTIONS_OF_THE_USER

    def enabled_curved_lanelet(self):
        return gui_config.ENABLE_EDITING_CURVED_LANELETS

    def sub_curved(self, method_to_sub=None):
        for list_layout in gui_config.LAYOUT:
            for attribute in list_layout:
                if (
                    isinstance(attribute, Attribute)
                    and attribute.display_name == "Enable editing of curved lanelets"
                ):
                    attribute.subscribe(method_to_sub)
                    return

    def get_stylesheet(self) -> str:
        """
        @returns: A string for the stylesheet of the app
        """
        if gui_config.MODERN_LOOK:
            if gui_config.DARKMODE:
                stylesheet = """
                                QWidget {
                                    background-color: 	#303030;  /* White */
                                    font-family: "Verdana";
                                    font-size: 10pt;
                                    color: #FFFFFF
                                }
                                QPushButton {
                                    background-color: #0000FF;  /* Blue */
                                    color: #FFFFFF;  /* White */
                                    border: 1px;
                                    border-style: solid;
                                    border-color: black;
                                    border-radius: 10px;
                                    padding-top: 5px;
                                    padding-bottom: 5px;
                                    padding-left: 1px;
                                    padding-right: 1px;
                                    margin: 2px;

                                }
                                QPushButton:hover {
                                    background-color: #6495ED;  /* Cornflower Blue */
                                }
                                QPushButton:pressed {
                                    background-color: #0000FF;  /* Blue */

                                }
                                QLabel {
                                    color: #FFFFFF;  /* Midnight Blue */
                                    margin: 0px;
                                }
                                QProgressBar {
                                    border: 2px solid #191970;  /* Midnight Blue */
                                    border-radius: 5px;
                                    text-align: center;
                                }
                                QProgressBar::chunk {
                                    background-color: #1E90FF;  /* Dodger Blue */
                                }
                                QComboBox {
                                    background-color: #87CEFA;  /* Light Sky Blue */
                                    color: #191970;  /* Midnight Blue */
                                    border-radius: 5px;
                                    padding: 2px;
                                }
                                QComboBox QAbstractItemView {
                                    background-color: #87CEFA;  /* Light Sky Blue */
                                    color: #191970;  /* Midnight Blue */
                                    selection-background-color: #1E90FF;  /* Dodger Blue */
                                    selection-color: #FFFFFF;  /* White */
                                }
                                QComboBox::drop-down {
                                    border: none;
                                }
                                QLineEdit {
                                    color: #FFFFFF;
                                }

                            """
            else:
                stylesheet = """
                                    QWidget {
                                        background-color: 	#FFFFFF;  /* White */
                                        font-family: "Verdana";
                                        font-size: 10pt;
                                        color: #000000
                                    }
                                    QPushButton {
                                        background-color: #0000FF;  /* Blue */
                                        color: #FFFFFF;  /* White */
                                        border: 1px;
                                        border-style: solid;
                                        border-color: black;
                                        border-radius: 10px;
                                        padding-top: 5px;
                                        padding-bottom: 5px;
                                        padding-left: 1px;
                                        padding-right: 1px;
                                        margin: 2px;

                                    }
                                    QPushButton:hover {
                                        background-color: #6495ED;  /* Cornflower Blue */
                                    }
                                    QPushButton:pressed {
                                        background-color: #0000FF;  /* Blue */

                                    }
                                    QLabel {
                                        color: #191970;  /* Midnight Blue */
                                        margin: 0px;
                                    }
                                    QProgressBar {
                                        border: 2px solid #191970;  /* Midnight Blue */
                                        border-radius: 5px;
                                        text-align: center;
                                    }
                                    QProgressBar::chunk {
                                        background-color: #1E90FF;  /* Dodger Blue */
                                    }
                                    QComboBox {
                                        background-color: #87CEFA;  /* Light Sky Blue */
                                        color: #191970;  /* Midnight Blue */
                                        border-radius: 5px;
                                        padding: 2px;
                                    }
                                    QComboBox QAbstractItemView {
                                        background-color: #87CEFA;  /* Light Sky Blue */
                                        color: #191970;  /* Midnight Blue */
                                        selection-background-color: #1E90FF;  /* Dodger Blue */
                                        selection-color: #FFFFFF;  /* White */
                                    }
                                    QComboBox::drop-down {
                                        border: none;
                                    }
                                    QLineEdit {
                                    color: #000000;
                                    }
                                    QAction {
                                    color: #000000;
                                    }
                                    QToolTip {
                                    color: #000000;
                                    }

                                """
            return stylesheet
        else:
            return ""


gui_config = GuiConfig()
