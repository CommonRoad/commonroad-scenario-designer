from typing import List

from PyQt6.QtWidgets import QFileDialog


class Observable:
    def __init__(
        self,
        value,
    ):
        self._value = value
        self._observers = []

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        for obs in self._observers:
            obs(value)
        self._value = value

    def silent_set(self, value):
        self._value = value

    def subscribe(self, observer):
        self._observers.append(observer)


def find_invalid_ref_of_traffic_lights(scenario) -> List[int]:
    """find references to traffic lights that do not exist"""
    invalid_refs = []
    for lanelet in scenario.lanelet_network.lanelets:
        for t_light_ref in set(lanelet.traffic_lights):
            if not scenario.lanelet_network.find_traffic_light_by_id(t_light_ref):
                invalid_refs.append(t_light_ref)
    return invalid_refs


def find_invalid_ref_of_traffic_signs(scenario) -> List[int]:
    """find references to traffic signs that do not exist"""
    invalid_refs = []
    for lanelet in scenario.lanelet_network.lanelets:
        for t_sign_ref in set(lanelet.traffic_signs):
            if not scenario.lanelet_network.find_traffic_sign_by_id(t_sign_ref):
                invalid_refs.append(t_sign_ref)
    return invalid_refs


def find_invalid_lanelet_polygons(scenario) -> List[int]:
    """find lanelets with invalid polygon"""
    lanelet_ids = []
    for lanelet in scenario.lanelet_network.lanelets:
        polygon = lanelet.polygon.shapely_object
        if not polygon.is_valid:
            lanelet_ids.append(lanelet.lanelet_id)
    return lanelet_ids


def select_local_file(parent, file_type: str, file_ending: str) -> str:
    file_path, _ = QFileDialog.getOpenFileName(
        None,
        "Select {} file to convert".format(file_type),
        "",
        "{} files *.{} (*.{})".format(file_type, file_ending, file_ending),
    )
    return file_path
