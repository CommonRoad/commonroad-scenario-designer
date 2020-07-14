"""
This module provides the possibility to edit the parameters in config.py in a GUI.
To save them permanently, it rewrites config.py with new values.
If you want to add parameters to config.py you also need to add it here in the config_string().

"""

from tkinter import Tk
from tkinter.messagebox import showwarning
from typing import Dict, Union, List, Optional, Tuple

from PyQt5.QtWidgets import QDialog

from crmapconverter.osm2cr import config
from crmapconverter.osm2cr.converter_modules.gui_modules.GUI_resources.lane_counts import (
    Ui_Dialog as Lane_counts,
)
from crmapconverter.osm2cr.converter_modules.gui_modules.GUI_resources.lane_width import (
    Ui_Dialog as Lane_width,
)
from crmapconverter.osm2cr.converter_modules.gui_modules.GUI_resources.settings_ui import (
    Ui_MainWindow as Settings_window,
)
from crmapconverter.osm2cr.converter_modules.gui_modules.GUI_resources.street_types import (
    Ui_Dialog as Street_types,
)


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
        ui: Street_types = self.dialog.ui
        ui.chk_motorway.setChecked("motorway" in config.ACCEPTED_HIGHWAYS)
        ui.chk_trunk.setChecked("trunk" in config.ACCEPTED_HIGHWAYS)
        ui.chk_primary.setChecked("primary" in config.ACCEPTED_HIGHWAYS)
        ui.chk_secondary.setChecked("secondary" in config.ACCEPTED_HIGHWAYS)
        ui.chk_tertiary.setChecked("tertiary" in config.ACCEPTED_HIGHWAYS)
        ui.chk_unclassified.setChecked("unclassified" in config.ACCEPTED_HIGHWAYS)
        ui.chk_residential.setChecked("residential" in config.ACCEPTED_HIGHWAYS)
        ui.chk_motorway_link.setChecked("motorway_link" in config.ACCEPTED_HIGHWAYS)
        ui.chk_trunk_link.setChecked("trunk_link" in config.ACCEPTED_HIGHWAYS)
        ui.chk_primary_link.setChecked("primary_link" in config.ACCEPTED_HIGHWAYS)
        ui.chk_secondary_link.setChecked("secondary_link" in config.ACCEPTED_HIGHWAYS)
        ui.chk_tertiary_link.setChecked("tertiary_link" in config.ACCEPTED_HIGHWAYS)
        ui.chk_living_street.setChecked("living_street" in config.ACCEPTED_HIGHWAYS)
        ui.chk_service.setChecked("service" in config.ACCEPTED_HIGHWAYS)
        ui.chk_path.setChecked("path" in config.ACCEPTED_HIGHWAYS)
        ui.chk_footway.setChecked("footway" in config.ACCEPTED_HIGHWAYS)
        ui.chk_cycleway.setChecked("cycleway" in config.ACCEPTED_HIGHWAYS)

    def save(self) -> None:
        """
        saves values of checkboxes to config.py

        :return: None
        """
        ui = self.dialog.ui
        types = {
            ui.chk_motorway: "motorway",
            ui.chk_trunk: "trunk",
            ui.chk_primary: "primary",
            ui.chk_secondary: "secondary",
            ui.chk_tertiary: "tertiary",
            ui.chk_unclassified: "unclassified",
            ui.chk_residential: "residential",
            ui.chk_motorway_link: "motorway_link",
            ui.chk_trunk_link: "trunk_link",
            ui.chk_primary_link: "primary_link",
            ui.chk_secondary_link: "secondary_link",
            ui.chk_tertiary_link: "tertiary_link",
            ui.chk_living_street: "living_street",
            ui.chk_service: "service",
            ui.chk_path: "path",
            ui.chk_footway: "footway",
            ui.chk_cycleway: "cycleway",
        }
        config.ACCEPTED_HIGHWAYS = [
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
        ui: Lane_counts = self.dialog.ui
        ui.sb_motorway.setValue(config.LANECOUNTS["motorway"])
        ui.sb_trunk.setValue(config.LANECOUNTS["trunk"])
        ui.sb_primary.setValue(config.LANECOUNTS["primary"])
        ui.sb_secondary.setValue(config.LANECOUNTS["secondary"])
        ui.sb_tertiary.setValue(config.LANECOUNTS["tertiary"])
        ui.sb_unclassified.setValue(config.LANECOUNTS["unclassified"])
        ui.sb_residential.setValue(config.LANECOUNTS["residential"])
        ui.sb_motorway_link.setValue(config.LANECOUNTS["motorway_link"])
        ui.sb_trunk_link.setValue(config.LANECOUNTS["trunk_link"])
        ui.sb_primary_link.setValue(config.LANECOUNTS["primary_link"])
        ui.sb_secondary_link.setValue(config.LANECOUNTS["secondary_link"])
        ui.sb_tertiary_link.setValue(config.LANECOUNTS["tertiary_link"])
        ui.sb_living_street.setValue(config.LANECOUNTS["living_street"])
        ui.sb_service.setValue(config.LANECOUNTS["service"])
        ui.sb_path.setValue(config.LANECOUNTS["path"])
        ui.sb_footway.setValue(config.LANECOUNTS["footway"])
        ui.sb_cycleway.setValue(config.LANECOUNTS["cycleway"])

    def save(self) -> None:
        """
        saves values of checkboxes to config.py

        :return: None
        """
        ui = self.dialog.ui
        types = {
            ui.sb_motorway: "motorway",
            ui.sb_trunk: "trunk",
            ui.sb_primary: "primary",
            ui.sb_secondary: "secondary",
            ui.sb_tertiary: "tertiary",
            ui.sb_unclassified: "unclassified",
            ui.sb_residential: "residential",
            ui.sb_motorway_link: "motorway_link",
            ui.sb_trunk_link: "trunk_link",
            ui.sb_primary_link: "primary_link",
            ui.sb_secondary_link: "secondary_link",
            ui.sb_tertiary_link: "tertiary_link",
            ui.sb_living_street: "living_street",
            ui.sb_service: "service",
            ui.sb_path: "path",
            ui.sb_footway: "footway",
            ui.sb_cycleway: "cycleway",
        }
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
        ui: Lane_width = self.dialog.ui
        ui.sb_motorway.setValue(config.LANEWIDTHS["motorway"])
        ui.sb_trunk.setValue(config.LANEWIDTHS["trunk"])
        ui.sb_primary.setValue(config.LANEWIDTHS["primary"])
        ui.sb_secondary.setValue(config.LANEWIDTHS["secondary"])
        ui.sb_tertiary.setValue(config.LANEWIDTHS["tertiary"])
        ui.sb_unclassified.setValue(config.LANEWIDTHS["unclassified"])
        ui.sb_residential.setValue(config.LANEWIDTHS["residential"])
        ui.sb_motorway_link.setValue(config.LANEWIDTHS["motorway_link"])
        ui.sb_trunk_link.setValue(config.LANEWIDTHS["trunk_link"])
        ui.sb_primary_link.setValue(config.LANEWIDTHS["primary_link"])
        ui.sb_secondary_link.setValue(config.LANEWIDTHS["secondary_link"])
        ui.sb_tertiary_link.setValue(config.LANEWIDTHS["tertiary_link"])
        ui.sb_living_street.setValue(config.LANEWIDTHS["living_street"])
        ui.sb_service.setValue(config.LANEWIDTHS["service"])
        ui.sb_path.setValue(config.LANEWIDTHS["path"])
        ui.sb_footway.setValue(config.LANEWIDTHS["footway"])
        ui.sb_cycleway.setValue(config.LANEWIDTHS["cycleway"])

    def save(self) -> None:
        """
        saves values of checkboxes to config.py

        :return: None
        """
        ui = self.dialog.ui
        types = {
            ui.sb_motorway: "motorway",
            ui.sb_trunk: "trunk",
            ui.sb_primary: "primary",
            ui.sb_secondary: "secondary",
            ui.sb_tertiary: "tertiary",
            ui.sb_unclassified: "unclassified",
            ui.sb_residential: "residential",
            ui.sb_motorway_link: "motorway_link",
            ui.sb_trunk_link: "trunk_link",
            ui.sb_primary_link: "primary_link",
            ui.sb_secondary_link: "secondary_link",
            ui.sb_tertiary_link: "tertiary_link",
            ui.sb_living_street: "living_street",
            ui.sb_service: "service",
            ui.sb_path: "path",
            ui.sb_footway: "footway",
            ui.sb_cycleway: "cycleway",
        }
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
        ui: Lane_counts = self.dialog.ui
        ui.sb_motorway.setValue(config.SPEED_LIMITS["motorway"])
        ui.sb_trunk.setValue(config.SPEED_LIMITS["trunk"])
        ui.sb_primary.setValue(config.SPEED_LIMITS["primary"])
        ui.sb_secondary.setValue(config.SPEED_LIMITS["secondary"])
        ui.sb_tertiary.setValue(config.SPEED_LIMITS["tertiary"])
        ui.sb_unclassified.setValue(config.SPEED_LIMITS["unclassified"])
        ui.sb_residential.setValue(config.SPEED_LIMITS["residential"])
        ui.sb_motorway_link.setValue(config.SPEED_LIMITS["motorway_link"])
        ui.sb_trunk_link.setValue(config.SPEED_LIMITS["trunk_link"])
        ui.sb_primary_link.setValue(config.SPEED_LIMITS["primary_link"])
        ui.sb_secondary_link.setValue(config.SPEED_LIMITS["secondary_link"])
        ui.sb_tertiary_link.setValue(config.SPEED_LIMITS["tertiary_link"])
        ui.sb_living_street.setValue(config.SPEED_LIMITS["living_street"])
        ui.sb_service.setValue(config.SPEED_LIMITS["service"])
        ui.sb_path.setValue(config.SPEED_LIMITS["path"])
        ui.sb_footway.setValue(config.SPEED_LIMITS["footway"])
        ui.sb_cycleway.setValue(config.SPEED_LIMITS["cycleway"])

    def save(self) -> None:
        """
        saves values of checkboxes to config.py

        :return: None
        """
        ui = self.dialog.ui
        types = {
            ui.sb_motorway: "motorway",
            ui.sb_trunk: "trunk",
            ui.sb_primary: "primary",
            ui.sb_secondary: "secondary",
            ui.sb_tertiary: "tertiary",
            ui.sb_unclassified: "unclassified",
            ui.sb_residential: "residential",
            ui.sb_motorway_link: "motorway_link",
            ui.sb_trunk_link: "trunk_link",
            ui.sb_primary_link: "primary_link",
            ui.sb_secondary_link: "secondary_link",
            ui.sb_tertiary_link: "tertiary_link",
            ui.sb_living_street: "living_street",
            ui.sb_service: "service",
            ui.sb_path: "path",
            ui.sb_footway: "footway",
            ui.sb_cycleway: "cycleway",
        }
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
        ui: Street_types = self.dialog.ui
        ui.chk_motorway.setChecked("motorway" in config.ACCEPTED_HIGHWAYS_SUBLAYER)
        ui.chk_trunk.setChecked("trunk" in config.ACCEPTED_HIGHWAYS_SUBLAYER)
        ui.chk_primary.setChecked("primary" in config.ACCEPTED_HIGHWAYS_SUBLAYER)
        ui.chk_secondary.setChecked("secondary" in config.ACCEPTED_HIGHWAYS_SUBLAYER)
        ui.chk_tertiary.setChecked("tertiary" in config.ACCEPTED_HIGHWAYS_SUBLAYER)
        ui.chk_unclassified.setChecked("unclassified" in config.ACCEPTED_HIGHWAYS_SUBLAYER)
        ui.chk_residential.setChecked("residential" in config.ACCEPTED_HIGHWAYS_SUBLAYER)
        ui.chk_motorway_link.setChecked("motorway_link" in config.ACCEPTED_HIGHWAYS_SUBLAYER)
        ui.chk_trunk_link.setChecked("trunk_link" in config.ACCEPTED_HIGHWAYS_SUBLAYER)
        ui.chk_primary_link.setChecked("primary_link" in config.ACCEPTED_HIGHWAYS_SUBLAYER)
        ui.chk_secondary_link.setChecked("secondary_link" in config.ACCEPTED_HIGHWAYS_SUBLAYER)
        ui.chk_tertiary_link.setChecked("tertiary_link" in config.ACCEPTED_HIGHWAYS_SUBLAYER)
        ui.chk_living_street.setChecked("living_street" in config.ACCEPTED_HIGHWAYS_SUBLAYER)
        ui.chk_service.setChecked("service" in config.ACCEPTED_HIGHWAYS_SUBLAYER)
        ui.chk_path.setChecked("path" in config.ACCEPTED_HIGHWAYS_SUBLAYER)
        ui.chk_footway.setChecked("footway" in config.ACCEPTED_HIGHWAYS_SUBLAYER)
        ui.chk_cycleway.setChecked("cycleway" in config.ACCEPTED_HIGHWAYS_SUBLAYER)

    def save(self) -> None:
        """
        saves values of checkboxes to config.py

        :return: None
        """
        ui = self.dialog.ui
        types = {
            ui.chk_motorway: "motorway",
            ui.chk_trunk: "trunk",
            ui.chk_primary: "primary",
            ui.chk_secondary: "secondary",
            ui.chk_tertiary: "tertiary",
            ui.chk_unclassified: "unclassified",
            ui.chk_residential: "residential",
            ui.chk_motorway_link: "motorway_link",
            ui.chk_trunk_link: "trunk_link",
            ui.chk_primary_link: "primary_link",
            ui.chk_secondary_link: "secondary_link",
            ui.chk_tertiary_link: "tertiary_link",
            ui.chk_living_street: "living_street",
            ui.chk_service: "service",
            ui.chk_path: "path",
            ui.chk_footway: "footway",
            ui.chk_cycleway: "cycleway",
        }
        config.ACCEPTED_HIGHWAYS_SUBLAYER = [
            current_type
            for check_box, current_type in types.items()
            if check_box.isChecked()
        ]


class SettingsMenu:
    """
    Window to edit parameters in config.py
    """

    def __init__(self, main_app):
        """

        :param main_app: main app
        """
        self.app = main_app
        self.close = self.app.show_start_menu
        self.window = Settings_window()
        self.window.setupUi(self.app.main_window)
        self.update_ui_values()
        self.connect_events(self.window)

        self.street_type_edit_dialog = None
        self.lane_count_edit_dialog = None
        self.lane_width_edit_dialog = None
        self.speed_limits_edit_dialog = None

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
        window.btn_close.clicked.connect(self.close_button)
        window.btn_save.clicked.connect(self.save_button)

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
        window.sb_intersection_distance_sublayer.setValue(
            config.INTERSECTION_DISTANCE_SUBLAYER)
        window.chk_intersection_distance_respect.setChecked(
            config.INTERSECTION_CROPPING_WITH_RESPECT_TO_ROADS
        )
        window.sb_soft_angle_treshold.setValue(config.SOFT_ANGLE_THRESHOLD)
        window.sb_lane_segment_angle_treshold.setValue(config.LANE_SEGMENT_ANGLE)
        window.sb_cluster_length.setValue(config.CLUSTER_LENGTH)
        window.sb_cluster_length_treshold.setValue(config.LEAST_CLUSTER_LENGTH)
        window.sb_merge_distance.setValue(config.MERGE_DISTANCE)

    def save_to_config(self) -> None:
        """
        saves the values in the settings window to config.py

        :return: None
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
        config.INTERSECTION_DISTANCE_SUBLAYER = window.sb_intersection_distance_sublayer.value()
        config.INTERSECTION_CROPPING_WITH_RESPECT_TO_ROADS = (
            window.chk_intersection_distance_respect.isChecked()
        )
        config.SOFT_ANGLE_THRESHOLD = window.sb_soft_angle_treshold.value()
        config.LANE_SEGMENT_ANGLE = window.sb_lane_segment_angle_treshold.value()
        config.CLUSTER_LENGTH = window.sb_cluster_length.value()
        config.LEAST_CLUSTER_LENGTH = window.sb_cluster_length_treshold.value()
        config.MERGE_DISTANCE = window.sb_merge_distance.value()

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
        set_defaults()
        write_config()
        self.update_ui_values()

    def close_button(self) -> None:
        """
        closes settings without saving

        :return: None
        """
        write_config()
        self.close()

    def save_button(self) -> None:
        """
        saves settings

        :return: None
        """
        if not coordinates_from_text(self.window.le_coordinates.text())[0]:
            Tk().withdraw()
            showwarning(
                "Waring",
                "The entered coordinates are invalid! Settings could not be saved.",
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
    with open("config.py", "w", encoding="utf-8") as config_file:
        config_file.write(config_string())


def object_to_string(obj: Union[str, int, float]) -> str:
    """
    converts an object of type str, int or float to a python parsable string

    :param obj: object to convert
    :return: obj in parsable string from
    """
    if type(obj) == str:
        return "'" + str(obj) + "'"
    elif type(obj) in (int, float):
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


def set_defaults() -> None:
    """
    sets the values of config to defaults

    :return: None
    """
    import config_default
    for var_name in dir(config_default):
        if not var_name.startswith('__'):
            setattr(config, var_name, getattr(config_default, var_name))


def config_string() -> str:
    """
    returns a python parsable string of the config file with current values

    :return: string to write config.py
    """
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
