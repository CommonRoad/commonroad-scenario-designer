"""
This module provides the possibility to edit the parameters in config.py in a GUI.
To save them permanently, it rewrites config.py with new values.
If you want to add parameters to config.py you also need to add it here in the config_string().

"""

from typing import Dict, Union, List, Optional, Tuple

from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox

from crdesigner.map_conversion.osm2cr import config
from crdesigner.input_output.gui.osm_gui_modules import config_default
from crdesigner.input_output.gui.osm_gui_modules.GUI_resources.lane_counts import Ui_Dialog as Lane_counts
from crdesigner.input_output.gui.osm_gui_modules.GUI_resources.lane_width import Ui_Dialog as Lane_width
from crdesigner.input_output.gui.osm_gui_modules.GUI_resources.settings_ui import Ui_MainWindow \
    as Settings_window
from crdesigner.input_output.gui.osm_gui_modules.GUI_resources.street_types import Ui_Dialog as Street_types
from crdesigner.input_output.gui.osm_gui_modules.GUI_resources.sublayer_types import Ui_Dialog \
    as Sublayer_street_types


class EditStreetTypes:
    """
    Window to select types of roads
    """

    def __init__(self):
        self.dialog = QDialog()
        self.original_accept = self.dialog.accept
        self.dialog.accept = self.accept
        self.dialog.ui = Street_types()
        self.dialog.ui.setupUi(self.dialog)
        self.set_checkboxes()
        self.dialog.exec_()

    def accept(self) -> None:
        """
        accepts the values set in the window and saves them to config.py
        then closes the dialog

        :return: None
        """
        self.save()
        self.original_accept()

    def set_checkboxes(self) -> None:
        """
        initializes values of checkboxes

        :return: None
        """
        all_accepted_highways = config.ACCEPTED_HIGHWAYS_MAINLAYER.copy()
        all_accepted_highways.extend(config.ACCEPTED_HIGHWAYS_SUBLAYER)
        for highway_type in all_accepted_highways:
            getattr(self.dialog.ui, 'chk_' + highway_type).setChecked(
                highway_type in config.ACCEPTED_HIGHWAYS_MAINLAYER
            )

    def save(self) -> None:
        """
        saves values of checkboxes to config.py

        :return: None
        """
        types = dict()
        all_accepted_highways = config.ACCEPTED_HIGHWAYS_MAINLAYER.copy()
        all_accepted_highways.extend(config.ACCEPTED_HIGHWAYS_SUBLAYER)
        for highway_type in all_accepted_highways:
            types[getattr(self.dialog.ui, 'chk_' + highway_type)] = highway_type
        config.ACCEPTED_HIGHWAYS_MAINLAYER = [
            current_type
            for check_box, current_type in types.items()
            if check_box.isChecked()
        ]


class EditLaneCounts:
    """
    Window to edit counts of lanes for street types
    """

    def __init__(self):
        self.dialog = QDialog()
        self.original_accept = self.dialog.accept
        self.dialog.accept = self.accept
        self.dialog.ui = Lane_counts()
        self.dialog.ui.setupUi(self.dialog)
        self.set_spin_boxes()
        self.dialog.exec_()

    def accept(self) -> None:
        """
        saves values to config.py and closes dialog

        :return: None
        """
        self.save()
        self.original_accept()

    def set_spin_boxes(self) -> None:
        """
        initializes values of checkboxes

        :return: None
        """
        for highway_type in list(config.LANECOUNTS.keys()):
            getattr(self.dialog.ui, 'sb_' + highway_type).setValue(
                config.LANECOUNTS[highway_type]
            )

    def save(self) -> None:
        """
        saves values of checkboxes to config.py

        :return: None
        """
        types = dict()
        for highway_type in list(config.LANECOUNTS.keys()):
            types[getattr(self.dialog.ui, 'sb_' + highway_type)] = highway_type
        config.LANECOUNTS = {
            current_type: spin_box.value() for spin_box, current_type in types.items()
        }


class EditLaneWidth:
    """
    Window to edit width of lanes for street types
    """

    def __init__(self):
        self.dialog = QDialog()
        self.original_accept = self.dialog.accept
        self.dialog.accept = self.accept
        self.dialog.ui = Lane_width()
        self.dialog.ui.setupUi(self.dialog)
        self.set_spin_boxes()
        self.dialog.exec_()

    def accept(self) -> None:
        """
        saves values to config.py and closes dialog

        :return: None
        """
        self.save()
        self.original_accept()

    def set_spin_boxes(self) -> None:
        """
        initializes values of checkboxes

        :return: None
        """
        for highway_type in list(config.LANEWIDTHS.keys()):
            getattr(self.dialog.ui, 'sb_' + highway_type).setValue(
                config.LANEWIDTHS[highway_type]
            )

    def save(self) -> None:
        """
        saves values of checkboxes to config.py

        :return: None
        """
        types = dict()
        for highway_type in list(config.LANEWIDTHS.keys()):
            types[getattr(self.dialog.ui, 'sb_' + highway_type)] = highway_type
        config.LANEWIDTHS = {
            current_type: spin_box.value() for spin_box, current_type in types.items()
        }


class EditSpeedLimits:
    """
    Window to edit speed limits for street types
    """

    def __init__(self):
        self.dialog = QDialog()
        self.original_accept = self.dialog.accept
        self.dialog.accept = self.accept
        # here we can reuse the lane count ui as we also need integer spin boxes for each street type
        self.dialog.ui = Lane_counts()
        self.dialog.ui.setupUi(self.dialog)
        self.dialog.setWindowTitle("Edit Speed Limit")
        self.set_spin_boxes()
        self.dialog.exec_()

    def accept(self) -> None:
        """
        saves values to config.py and closes dialog

        :return: None
        """
        self.save()
        self.original_accept()

    def set_spin_boxes(self) -> None:
        """
        initializes values of checkboxes

        :return: None
        """
        for highway_type in list(config.SPEED_LIMITS.keys()):
            getattr(self.dialog.ui, 'sb_' + highway_type).setValue(
                config.SPEED_LIMITS[highway_type]
            )

    def save(self) -> None:
        """
        saves values of checkboxes to config.py

        :return: None
        """
        types = dict()
        for highway_type in list(config.SPEED_LIMITS.keys()):
            types[getattr(self.dialog.ui, 'sb_' + highway_type)] = highway_type
        config.SPEED_LIMITS = {
            current_type: spin_box.value() for spin_box, current_type in types.items()
        }


class EditSublayerWayTypes:
    """
    Window to edit sublayer way types
    """

    def __init__(self):
        self.dialog = QDialog()
        self.original_accept = self.dialog.accept
        self.dialog.accept = self.accept
        self.dialog.ui = Sublayer_street_types()
        self.dialog.ui.setupUi(self.dialog)
        self.set_checkboxes()
        self.dialog.exec_()

    def accept(self) -> None:
        """
        accepts the values set in the window and saves them to config.py
        then closes the dialog

        :return: None
        """
        self.save()
        self.original_accept()

    def set_checkboxes(self) -> None:
        """
        initializes values of checkboxes

        :return: None
        """
        all_accepted_highways = config.ACCEPTED_HIGHWAYS_MAINLAYER.copy()
        all_accepted_highways.extend(config.ACCEPTED_HIGHWAYS_SUBLAYER)
        for highway_type in all_accepted_highways:
            getattr(self.dialog.ui, 'chk_' + highway_type).setChecked(
                highway_type in config.ACCEPTED_HIGHWAYS_SUBLAYER
            )

    def save(self) -> None:
        """
        saves values of checkboxes to config.py

        :return: None
        """
        types = dict()
        all_accepted_highways = config.ACCEPTED_HIGHWAYS_MAINLAYER.copy()
        all_accepted_highways.extend(config.ACCEPTED_HIGHWAYS_SUBLAYER)
        for highway_type in all_accepted_highways:
            types[getattr(self.dialog.ui, 'chk_' + highway_type)] = highway_type
        config.ACCEPTED_HIGHWAYS_SUBLAYER = [
            current_type
            for check_box, current_type in types.items()
            if check_box.isChecked()
        ]


class SettingsMenu:
    """
    Window to edit parameters in config.py
    """

    def __init__(self, main_app, close_action):
        """

        :param main_app: main app
        :param close_action: a functio to call when closeEvent is triggered
        """
        self.app = main_app
        self.close = close_action
        self.window = Settings_window()
        self.window.setupUi(self.app.main_window)
        self.update_ui_values()
        self.connect_events(self.window)

        self.street_type_edit_dialog = None
        self.lane_count_edit_dialog = None
        self.lane_width_edit_dialog = None
        self.speed_limits_edit_dialog = None
        self.edit_sublayer_way_types_dialog = None

        main_app.main_window.show()

    def connect_events(self, window: Settings_window) -> None:
        """
        connects the events of the window to their functions

        :param window: qt setting window
        :return: None
        """
        window.btn_edit_street_types.clicked.connect(self.edit_street_types)
        window.btn_edit_lane_counts.clicked.connect(self.edit_lane_counts)
        window.btn_edit_lane_widths.clicked.connect(self.edit_lane_width)
        window.btn_edit_speed_limits.clicked.connect(self.edit_speed_limits)
        window.btn_edit_sublayer_way_types.clicked.connect(self.edit_sublayer_way_types)

        window.btn_restore_defaults.clicked.connect(self.restore_default_button)
        window.btn_apply.clicked.connect(self.apply_close)
        # window.btn_save.clicked.connect(self.save_button)

    def update_ui_values(self) -> None:
        """
        sets the values of the settings window to the current values of config.py

        :return: None
        """
        window = self.window

        window.le_benchmark_id.setText(config.BENCHMARK_ID)
        window.le_author.setText(config.AUTHOR)
        window.le_affiliation.setText(config.AFFILIATION)
        window.le_source.setText(config.SOURCE)
        window.le_tags.setText(config.TAGS)
        window.sb_time_step_size.setValue(config.TIMESTEPSIZE)

        window.chb_aerial.setChecked(config.AERIAL_IMAGES)
        window.le_img_save_path.setText(config.IMAGE_SAVE_PATH)
        window.sb_zoom_level.setValue(config.ZOOM_LEVEL)
        window.le_bing_maps_key.setText(config.BING_MAPS_KEY)

        window.le_save_path.setText(config.SAVE_PATH)
        window.le_coordinates.setText(
            str(config.DOWNLOAD_COORDINATES[0])
            + ", "
            + str(config.DOWNLOAD_COORDINATES[1])
        )
        window.sb_donwload_radius.setValue(config.DOWNLOAD_EDGE_LENGTH)

        window.chk_load_tunnels.setChecked(config.LOAD_TUNNELS)
        window.chk_make_contiguous.setChecked(config.MAKE_CONTIGUOUS)
        window.chk_split_corners.setChecked(config.SPLIT_AT_CORNER)
        window.chk_use_restrictions.setChecked(config.USE_RESTRICTIONS)

        window.sb_interpolation_distance.setValue(config.INTERPOLATION_DISTANCE)
        window.sb_compression_threshold.setValue(config.COMPRESSION_THRESHOLD)
        window.chk_utm_coordinates.setChecked(config.EXPORT_IN_UTM)
        window.chk_filter_points.setChecked(config.FILTER)

        window.sb_eart_radius.setValue(config.EARTH_RADIUS)
        window.chk_delete_short_edges.setChecked(config.DELETE_SHORT_EDGES)
        window.sb_internal_interpolation_distance.setValue(
            config.INTERPOLATION_DISTANCE_INTERNAL
        )
        window.sb_bezier_parameter.setValue(config.BEZIER_PARAMETER)
        window.sb_intersection_distance.setValue(config.INTERSECTION_DISTANCE)
        window.chk_intersection_distance_respect.setChecked(
            config.INTERSECTION_CROPPING_WITH_RESPECT_TO_ROADS
        )
        window.sb_soft_angle_treshold.setValue(config.SOFT_ANGLE_THRESHOLD)
        window.sb_lane_segment_angle_treshold.setValue(config.LANE_SEGMENT_ANGLE)
        window.sb_cluster_length.setValue(config.CLUSTER_LENGTH)
        window.sb_cluster_length_treshold.setValue(config.LEAST_CLUSTER_LENGTH)
        window.sb_merge_distance.setValue(config.MERGE_DISTANCE)
        
        window.sb_intersection_distance_sublayer.setValue(
            config.INTERSECTION_DISTANCE_SUBLAYER)
        window.chk_extract_sublayer.setChecked(config.EXTRACT_SUBLAYER)

    def save_to_config(self):
        """
        saves the values in the settings window to config
        """

        window = self.window

        config.BENCHMARK_ID = window.le_benchmark_id.text()
        config.AUTHOR = window.le_author.text()
        config.AFFILIATION = window.le_affiliation.text()
        config.SOURCE = window.le_source.text()
        config.TAGS = window.le_tags.text()
        config.TIMESTEPSIZE = window.sb_time_step_size.value()

        config.AERIAL_IMAGES = window.chb_aerial.isChecked()
        config.IMAGE_SAVE_PATH = window.le_img_save_path.text()
        config.ZOOM_LEVEL = window.sb_zoom_level.value()
        config.BING_MAPS_KEY = window.le_bing_maps_key.text()

        config.SAVE_PATH = window.le_save_path.text()
        config.DOWNLOAD_COORDINATES = coordinates_from_text(
            window.le_coordinates.text()
        )[1]
        config.DOWNLOAD_EDGE_LENGTH = window.sb_donwload_radius.value()

        config.LOAD_TUNNELS = window.chk_load_tunnels.isChecked()
        config.MAKE_CONTIGUOUS = window.chk_make_contiguous.isChecked()
        config.SPLIT_AT_CORNER = window.chk_split_corners.isChecked()
        config.USE_RESTRICTIONS = window.chk_use_restrictions.isChecked()

        config.INTERPOLATION_DISTANCE = window.sb_interpolation_distance.value()
        config.COMPRESSION_THRESHOLD = window.sb_compression_threshold.value()
        config.EXPORT_IN_UTM = window.chk_utm_coordinates.isChecked()
        config.FILTER = window.chk_filter_points.isChecked()

        config.EARTH_RADIUS = window.sb_eart_radius.value()
        config.DELETE_SHORT_EDGES = window.chk_delete_short_edges.isChecked()
        config.INTERPOLATION_DISTANCE_INTERNAL = (
            window.sb_internal_interpolation_distance.value()
        )
        config.BEZIER_PARAMETER = window.sb_bezier_parameter.value()
        config.INTERSECTION_DISTANCE = window.sb_intersection_distance.value()
        config.INTERSECTION_CROPPING_WITH_RESPECT_TO_ROADS = (
            window.chk_intersection_distance_respect.isChecked()
        )
        config.SOFT_ANGLE_THRESHOLD = window.sb_soft_angle_treshold.value()
        config.LANE_SEGMENT_ANGLE = window.sb_lane_segment_angle_treshold.value()
        config.CLUSTER_LENGTH = window.sb_cluster_length.value()
        config.LEAST_CLUSTER_LENGTH = window.sb_cluster_length_treshold.value()
        config.MERGE_DISTANCE = window.sb_merge_distance.value()

        config.EXTRACT_SUBLAYER = window.chk_extract_sublayer.isChecked()
        config.INTERSECTION_DISTANCE_SUBLAYER = window.sb_intersection_distance_sublayer.value()

    def has_valid_entries(self) -> bool:
        """ 
        Check if the user input is valid. Otherwise warn the user.

        :return: bool wether the input is valid
        """
        return True

    def edit_street_types(self) -> None:
        """
        allows to edit the accepted street types

        :return: None
        """
        self.street_type_edit_dialog = EditStreetTypes()

    def edit_lane_counts(self) -> None:
        """
        allows to edit the count of lanes for street types

        :return: None
        """
        self.lane_count_edit_dialog = EditLaneCounts()

    def edit_lane_width(self) -> None:
        """
        allows to edit the count of width for street types

        :return: None
        """
        self.lane_width_edit_dialog = EditLaneWidth()

    def edit_speed_limits(self) -> None:
        """
        allows to edit the speed limit for street types

        :return: None
        """
        self.speed_limits_edit_dialog = EditSpeedLimits()

    def edit_sublayer_way_types(self) -> None:
        """
        allows to edit the speed limit for street types

        :return: None
        """
        self.edit_sublayer_way_types_dialog = EditSublayerWayTypes()

    def restore_default_button(self) -> None:
        """
        restores all parameters to default

        :return: None
        """
        set_config_to_default()
        self.update_ui_values()

    def apply_close(self) -> None:
        """
        closes settings if settings could be saved to config
        """
        if self.has_valid_entries():
            self.save_to_config()
            self.close()
        else:
            print("invalid settings")

    def save_button(self) -> None:
        """
        saves settings

        :return: None
        """
        if not coordinates_from_text(self.window.le_coordinates.text())[0]:
            QMessageBox.warning(
                self,
                "Warning",
                "The entered coordinates are invalid! Settings could not be saved.",
                QMessageBox.Ok,
            )
            return
        self.save_to_config()
        write_config()


def coordinates_from_text(
    coords: str
) -> Tuple[bool, Tuple[Optional[float], Optional[float]]]:
    """
    reads coordinates from text

    :param coords: string containing coordinates in structured format
    :return: tuple: 1.true if coordinates are valid, 2.(lat, lon)
    """
    try:
        lat, lon = coords.split(", ")
        lat, lon = float(lat), float(lon)
        return True, (lat, lon)
    except ValueError:
        return False, (None, None)


def write_config():
    """
    overwrites the config file with current values

    :return: None
    """
    global config_string
    file_path, _ = QFileDialog.getSaveFileName(
            None,
            "Store Settings",
            "",
            "python file *.py (*.py)",
            options=QFileDialog.Options(),
        )
    if not file_path:
        return
    if not file_path.endswith(".py"):
        file_path += ".py"
    with open(file_path, "w", encoding="utf-8") as config_file:
        config_file.write(config_string())
        print("Settings saved")

def object_to_string(obj: Union[str, int, float]) -> str:
    """
    converts an object of type str, int or float to a python parsable string

    :param obj: object to convert
    :return: obj in parsable string from
    """
    if isinstance(obj, str):
        return "'" + str(obj) + "'"
    elif isinstance(obj, (int, float)):
        return str(obj)
    else:
        raise TypeError("Only dicts of type string, int or float are supported")


def dict_to_string(
    dictionary: Dict[Union[str, int, float], Union[str, int, float]], indentation: int
) -> str:
    """
    outputs a structured, python parsable string of the dictionary

    :param dictionary: arbitrary dictionary mapping from str/int/float to str/int/float
    :param indentation: number of desired indentations
    :return: parsable string of dict
    """
    if len(dictionary) == 0:
        return "{}"
    result = "{"
    for key, value in dictionary.items():
        result += (
            object_to_string(key)
            + ": "
            + object_to_string(value)
            + ",\n"
            + " " * indentation
        )
    return result[: -indentation - 2] + "}"


def list_to_string(lst: List[Union[str, int, float]], indentation: int) -> str:
    """
    outputs a structured, python parsable string of the list

    :param lst: list to convert
    :param indentation: number of desired indentations
    :return: parsable string of list
    """
    if len(lst) == 0:
        return "[]"
    result = "["
    for element in lst:
        result += object_to_string(element) + ",\n" + " " * indentation
    return result[: -indentation - 2] + "]"


def set_config_to_default() -> None:
    """
    sets the values of config to defaults

    :return: None
    """
    if not dir(config) == dir(config_default):
        print("config_default and config have different names in it's scope")
        return
    for var_name in dir(config_default):
        if not var_name.startswith('__'):
            setattr(config, var_name, getattr(config_default, var_name))


def config_string() -> str:
    """
    returns a python parsable string of the config file with current values

    :return: string to write config.py
    """
    raise RuntimeError("calling deprecated function")
    # TODO update to new config or find better solution
    return f"""\"\"\"
This module holds all parameters necessary for the conversion
\"\"\"

# Benchmark settings
# name of the benchmark
BENCHMARK_ID = \"{config.BENCHMARK_ID}\"
# author of the benchmark
AUTHOR = \"{config.AUTHOR}\"
# affiliation of the benchmark
AFFILIATION = \"{config.AFFILIATION}\"
# source of the benchmark
SOURCE = \"{config.SOURCE}\"
# additional tags for the benchmark
TAGS = \"{config.TAGS}\"
# time step size for the benchmark in seconds
TIMESTEPSIZE = {config.TIMESTEPSIZE}

# Aerial Image Settings
# Use aerial images for edit
AERIAL_IMAGES = {config.AERIAL_IMAGES}
# Path to save downloaded aerial images
IMAGE_SAVE_PATH = \"{config.IMAGE_SAVE_PATH}\"
# The zoom level of Bing Maps tiles
ZOOM_LEVEL = {config.ZOOM_LEVEL}
# The key to access bing maps
BING_MAPS_KEY = \"{config.BING_MAPS_KEY}\"

# Map download Settings
# path to save downloaded files
SAVE_PATH = \"{config.SAVE_PATH}\"
# half width of area downloaded in meters
DOWNLOAD_EDGE_LENGTH = {config.DOWNLOAD_EDGE_LENGTH}
# coordinates in latitude and longitude specifying the center of the downloaded area
DOWNLOAD_COORDINATES = {config.DOWNLOAD_COORDINATES}

# Scenario Settings
# include tunnels in result
LOAD_TUNNELS = {config.LOAD_TUNNELS}
# delete unconnected edges
MAKE_CONTIGUOUS = {config.MAKE_CONTIGUOUS}
# split edges at corners (~90° between two waypoint segments)
# this can help to model the course of roads on parking lots better
SPLIT_AT_CORNER = {config.SPLIT_AT_CORNER}
# use OSM restrictions for linking process
USE_RESTRICTIONS = {config.USE_RESTRICTIONS}
# types of roads extracted from the OSM file
# suitable types: 'motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'unclassified', 'residential',
# 'motorway_link', 'trunk_link', 'primary_link', 'secondary_link', 'tertiary_link', 'living_street', 'service'
ACCEPTED_HIGHWAYS = {list_to_string(config.ACCEPTED_HIGHWAYS, 21)}
# number of lanes for each type of road should be >=1
LANECOUNTS = {dict_to_string(config.LANECOUNTS, 14)}
# width of lanes for each type of road in meters
LANEWIDTHS = {dict_to_string(config.LANEWIDTHS, 14)}
# default speed limit for each type of road in km/h
SPEED_LIMITS = {dict_to_string(config.SPEED_LIMITS, 16)}

# Export Settings
# desired distance between interpolated waypoints in meters
INTERPOLATION_DISTANCE = {config.INTERPOLATION_DISTANCE}
# allowed inaccuracy of exported lines to reduce number of way points in meters
COMPRESSION_THRESHOLD = {config.COMPRESSION_THRESHOLD}
# export the scenario in UTM coordinates
EXPORT_IN_UTM = {config.EXPORT_IN_UTM}
# toggle filtering of negligible waypoints
FILTER = {config.FILTER}

# Internal settings (these can be used to improve the conversion process for individual scenarios)
# radius of the earth used for calculation in meters
EARTH_RADIUS = {config.EARTH_RADIUS}
# delete short edges after cropping
DELETE_SHORT_EDGES = {config.DELETE_SHORT_EDGES}
# distance between waypoints used internally in meters
INTERPOLATION_DISTANCE_INTERNAL = {config.INTERPOLATION_DISTANCE_INTERNAL}
# bezier parameter for interpolation (should be within [0, 0.5])
BEZIER_PARAMETER = {config.BEZIER_PARAMETER}
# distance between roads at intersection used for cropping in meters
INTERSECTION_DISTANCE = {config.INTERSECTION_DISTANCE}
# defines if the distance to other roads is used for cropping
# if false the distance to the center of the intersection is used
INTERSECTION_CROPPING_WITH_RESPECT_TO_ROADS = {config.INTERSECTION_CROPPING_WITH_RESPECT_TO_ROADS}
# threshold above which angles are considered as soft in degrees
SOFT_ANGLE_THRESHOLD = {config.SOFT_ANGLE_THRESHOLD}
# least angle for lane segment to be added to the graph in degrees.
# if you edit the graph by hand, a value of 0 is recommended
LANE_SEGMENT_ANGLE = {config.LANE_SEGMENT_ANGLE}
# least distance between graph nodes to try clustering in meters
CLUSTER_LENGTH = {config.CLUSTER_LENGTH}
# least length of cluster to be added in meters
LEAST_CLUSTER_LENGTH = {config.LEAST_CLUSTER_LENGTH}
# maximal distance between two intersections to which they are merged, if zero, no intersections are merged
MERGE_DISTANCE = {config.MERGE_DISTANCE}

# Toggle edit for user
USER_EDIT = {config.USER_EDIT}

# set of processed turn lanes
# this should only be changed for further development
RECOGNIZED_TURNLANES = {list_to_string(config.RECOGNIZED_TURNLANES, 24)}

"""
