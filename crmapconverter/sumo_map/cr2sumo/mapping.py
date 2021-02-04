from commonroad.scenario.obstacle import ObstacleType
from commonroad.scenario.traffic_sign import TrafficLightState
from commonroad.scenario.lanelet import LaneletType
from commonroad.scenario.traffic_sign import SupportedTrafficSignCountry
from crmapconverter.sumo_map.sumolib_net.constants import SUMO_VEHICLE_CLASSES
from typing import Tuple, Dict, Set
from crmapconverter.sumo_map.sumolib_net import EdgeTypes, EdgeType
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

# ISO-3166 country code mapping to SUMO type file fond in templates/
lanelet_type_CR2SUMO = {
    SupportedTrafficSignCountry.GERMANY: {
        LaneletType.URBAN: "highway.residential",
        LaneletType.COUNTRY: "highway.primary",
        LaneletType.HIGHWAY: "highway.motorway",
        LaneletType.DRIVE_WAY: "highway.living_street",
        LaneletType.MAIN_CARRIAGE_WAY: "highway.primary",
        LaneletType.ACCESS_RAMP: "highway.primary_link",
        LaneletType.EXIT_RAMP: "highway.primary_link",
        LaneletType.SHOULDER: "highway.primary_link",
        LaneletType.INTERSTATE: "highway.motorway",
        LaneletType.UNKNOWN: "highway.unclassified",
        LaneletType.BUS_LANE: "highway.bus_guideway",
        LaneletType.BUS_STOP: "highway.bus_guideway",
        LaneletType.BICYCLE_LANE: "highway.cycleway",
        LaneletType.SIDEWALK: "highway.path",
        LaneletType.CROSSWALK: "highway.path"
    },
    SupportedTrafficSignCountry.USA: {
        LaneletType.URBAN: "highway.residential",
        LaneletType.COUNTRY: "highway.primary",
        LaneletType.HIGHWAY: "highway.motorway",
        LaneletType.DRIVE_WAY: "highway.living_street",
        LaneletType.MAIN_CARRIAGE_WAY: "highway.primary",
        LaneletType.ACCESS_RAMP: "highway.primary_link",
        LaneletType.EXIT_RAMP: "highway.primary_link",
        LaneletType.SHOULDER: "highway.primary_link",
        LaneletType.INTERSTATE: "highway.motorway",
        LaneletType.UNKNOWN: "highway.unclassified",
        LaneletType.BUS_LANE: "highway.bus_guideway",
        LaneletType.BUS_STOP: "highway.bus_guideway",
        LaneletType.BICYCLE_LANE: "highway.cycleway",
        LaneletType.SIDEWALK: "highway.path",
        LaneletType.CROSSWALK: "highway.path"
    },
    # SupportedTrafficSignCountry.CHINA: {},
    # SupportedTrafficSignCountry.SPAIN: {},
    # SupportedTrafficSignCountry.RUSSIA: {},
    # SupportedTrafficSignCountry.ARGENTINA: {},
    # SupportedTrafficSignCountry.BELGIUM: {},
    # SupportedTrafficSignCountry.FRANCE: {},
    # SupportedTrafficSignCountry.GREECE: {},
    # SupportedTrafficSignCountry.CROATIA: {},
    # SupportedTrafficSignCountry.ITALY: {},
    # SupportedTrafficSignCountry.PUERTO_RICO: {},
    # SupportedTrafficSignCountry.ZAMUNDA: {}
}

TEMPLATES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates"))
DEFAULT_CFG_FILE = os.path.join(TEMPLATES_DIR, "default.sumo.cfg")


def get_sumo_edge_type(edge_types: EdgeTypes,
                       country_id: SupportedTrafficSignCountry,
                       *lanelet_types: LaneletType) -> EdgeType:
    if not lanelet_types:
        logging.warning("No Lanelet Type given for sumo_edge_type conversion, falling back to LaneletType.URBAN")
        return get_sumo_edge_type(edge_types, country_id, LaneletType.COUNTRY)
    lanelet_type = max(set(lanelet_types), key=lanelet_types.count)

    if country_id in lanelet_type_CR2SUMO and lanelet_type in lanelet_type_CR2SUMO[country_id]:
        return edge_types.types[lanelet_type_CR2SUMO[country_id][lanelet_type]]
    elif lanelet_type not in lanelet_type_CR2SUMO[SupportedTrafficSignCountry.GERMANY]:
        raise KeyError(f"LaneletType {str(lanelet_type)} is invalid")
    else:
        logging.warning(f"SupportedTrafficSignCountry {country_id} is invalid, using GERMANY instead")
        return get_sumo_edge_type(edge_types, SupportedTrafficSignCountry.GERMANY, lanelet_type)
