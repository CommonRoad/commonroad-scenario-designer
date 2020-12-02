from commonroad.scenario.obstacle import ObstacleType
from commonroad.scenario.traffic_sign import TrafficLightState
from commonroad.scenario.lanelet import LaneletType
from commonroad.scenario.traffic_sign import SupportedTrafficSignCountry
from typing import Tuple, Dict
from xml.etree import ElementTree as ET
import logging
import os

# sumo type to CommonRoad obstacle type
TYPE_MAPPING = {
    'DEFAULT_VEHTYPE': ObstacleType.CAR,
    'passenger': ObstacleType.CAR,
    'truck': ObstacleType.TRUCK,
    'bus': ObstacleType.BUS,
    'bicycle': ObstacleType.BICYCLE,
    'pedestrian': ObstacleType.PEDESTRIAN
}
# sumo type to CommonRoad obstacle type
VEHICLE_TYPE_SUMO2CR = {
    'DEFAULT_VEHTYPE': ObstacleType.CAR,
    'passenger': ObstacleType.CAR,
    'truck': ObstacleType.TRUCK,
    'bus': ObstacleType.BUS,
    'bicycle': ObstacleType.BICYCLE,
    'pedestrian': ObstacleType.PEDESTRIAN
}

# Mapping from CR TrafficLightStates to SUMO Traffic Light states
traffic_light_states_CR2SUMO = {
    TrafficLightState.RED: 'r',
    TrafficLightState.YELLOW: 'y',
    TrafficLightState.RED_YELLOW: 'u',
    TrafficLightState.GREEN: 'G',
    TrafficLightState.INACTIVE: 'O',
}
# Mapping from  UMO Traffic Light to CR TrafficLightState states
traffic_light_states_SUMO2CR = {
    'r': TrafficLightState.RED,
    'y': TrafficLightState.YELLOW,
    'g': TrafficLightState.GREEN,
    'G': TrafficLightState.GREEN,
    's': TrafficLightState.GREEN,
    'u': TrafficLightState.RED_YELLOW,
    'o': TrafficLightState.INACTIVE,
    'O': TrafficLightState.INACTIVE
}

_road_vehicles = [
    "passenger", "private", "taxi", "bus", "coach", "delivery", "truck",
    "trailer", "emergency", "motorcycle", "moped", "bicycle", "evehicle",
    "army", "authority", "vip", "hov", "custom1", "custom2"
]
_bus_vehicles = ["bus", "coach"]
_pedestrian_vehicles = ["pedestrian", "bicycle"]

# ISO-3166 country code mapping to SUMO type file fond in templates/
_lanelet_type_CR2SUMO = {
    SupportedTrafficSignCountry.GERMANY: {
        LaneletType.URBAN: "highway.residential",
        LaneletType.COUNTRY: "highway.primary",
        LaneletType.HIGHWAY: "highway.motorway",
        LaneletType.DRIVE_WAY: "highway.living_street",
        LaneletType.MAIN_CARRIAGE_WAY: "highway.primary",
        LaneletType.ACCESS_RAMP: "highway.secondary",
        LaneletType.EXIT_RAMP: "highway.secondary",
        LaneletType.SHOULDER: "highway.secondary",
        LaneletType.INTERSTATE: "highway.motorway",
        LaneletType.UNKNOWN: "highway.primary",
        LaneletType.BUS_LANE: "highway.bus_guideway",
        LaneletType.BUS_STOP: "highway.bus_guideway",
        LaneletType.BICYCLE_LANE: "highway.cycleway",
        LaneletType.SIDEWALK: "highway.track",
        LaneletType.CROSSWALK: "highway.track"
    }
}

# CommonRoad obstacle type to sumo type
VEHICLE_TYPE_CR2SUMO = {
    ObstacleType.UNKNOWN: "passenger",
    ObstacleType.CAR: "passenger",
    ObstacleType.TRUCK: "truck",
    ObstacleType.BUS: "bus",
    ObstacleType.BICYCLE: "bicycle",
    ObstacleType.PEDESTRIAN: "pedestrian",
    ObstacleType.PRIORITY_VEHICLE: "vip",
    ObstacleType.PARKED_VEHICLE: "passenger",
    ObstacleType.CONSTRUCTION_ZONE: "passenger",
    ObstacleType.TRAIN: "rail",
    ObstacleType.ROAD_BOUNDARY: "custom2",
    ObstacleType.MOTORCYCLE: "motorcycle",
    ObstacleType.TAXI: "taxi",
    ObstacleType.BUILDING: "custom2",
    ObstacleType.PILLAR: "custom2",
    ObstacleType.MEDIAN_STRIP: "custom1"
}

VEHICLE_NODE_TYPE_CR2SUMO = {
    ObstacleType.UNKNOWN: "vehicle",
    ObstacleType.CAR: "vehicle",
    ObstacleType.TRUCK: "vehicle",
    ObstacleType.BUS: "vehicle",
    ObstacleType.BICYCLE: "vehicle",
    ObstacleType.PEDESTRIAN: "pedestrian",
    ObstacleType.PRIORITY_VEHICLE: "vehicle",
    ObstacleType.PARKED_VEHICLE: "vehicle",
    ObstacleType.CONSTRUCTION_ZONE: "vehicle",
    ObstacleType.TRAIN: "vehicle",
    ObstacleType.ROAD_BOUNDARY: "vehicle",
    ObstacleType.MOTORCYCLE: "vehicle",
    ObstacleType.TAXI: "vehicle",
    ObstacleType.BUILDING: "vehicle",
    ObstacleType.PILLAR: "vehicle",
    ObstacleType.MEDIAN_STRIP: "vehicle"
}

TEMPLATES_DIR = os.path.join(__file__, "templates")


def get_sumo_edge_type(country_id: SupportedTrafficSignCountry, lanelet_type: LaneletType) -> Tuple[str, str]:
    if country_id in _lanelet_type_CR2SUMO and lanelet_type in _lanelet_type_CR2SUMO[country_id]:
        filename = os.path.join(TEMPLATES_DIR, f"{country_id}.typ.xml")
        return _lanelet_type_CR2SUMO[country_id][lanelet_type], filename
    elif lanelet_type not in _lanelet_type_CR2SUMO[SupportedTrafficSignCountry.GERMANY]:
        raise RuntimeError(f"LaneletType {str(lanelet_type)} is invalid")
    else:
        logging.warning("SupportedTrafficSignCountry is invalid, using GERMANY instead")
        return get_sumo_edge_type(SupportedTrafficSignCountry.GERMANY, lanelet_type)


def get_type_attributes(type_id: str, filename: str) -> Dict[str, str]:
    xml = ET.parse(filename)
    if not xml:
        return None
    return {
        tpe.tag: tpe.attrib for tpe in xml.getroot().findall("type")
    }
