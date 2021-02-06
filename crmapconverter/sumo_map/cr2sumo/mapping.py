from commonroad.scenario.obstacle import ObstacleType
from commonroad.scenario.traffic_sign import TrafficLightState
from commonroad.scenario.lanelet import LaneletType
from commonroad.scenario.traffic_sign import SupportedTrafficSignCountry
from crmapconverter.sumo_map.sumolib_net.constants import SUMO_VEHICLE_CLASSES
from typing import Tuple, Dict, Set
from crmapconverter.sumo_map.sumolib_net import EdgeTypes, EdgeType, SumoVehicles, SumoSignalStates
from xml.etree import ElementTree as ET
import logging
import os

# # sumo type to CommonRoad obstacle type
# TYPE_MAPPING = {
#     'DEFAULT_VEHTYPE': ObstacleType.CAR,
#     'passenger': ObstacleType.CAR,
#     'truck': ObstacleType.TRUCK,
#     'bus': ObstacleType.BUS,
#     'bicycle': ObstacleType.BICYCLE,
#     'pedestrian': ObstacleType.PEDESTRIAN
# }
# # sumo type to CommonRoad obstacle type
# VEHICLE_TYPE_SUMO2CR = {
#     'DEFAULT_VEHTYPE': ObstacleType.CAR,
#     'passenger': ObstacleType.CAR,
#     'truck': ObstacleType.TRUCK,
#     'bus': ObstacleType.BUS,
#     'bicycle': ObstacleType.BICYCLE,
#     'pedestrian': ObstacleType.PEDESTRIAN
# }

# Mapping from CR TrafficLightStates to SUMO Traffic Light states
traffic_light_states_CR2SUMO = {
    TrafficLightState.RED: SumoSignalStates.RED,
    TrafficLightState.YELLOW: SumoSignalStates.YELLOW,
    TrafficLightState.RED_YELLOW: SumoSignalStates.RED_YELLOW,
    TrafficLightState.GREEN: SumoSignalStates.GREEN,
    TrafficLightState.INACTIVE: SumoSignalStates.NO_SIGNAL,
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
    ObstacleType.UNKNOWN: SumoVehicles.PASSENGER,
    ObstacleType.CAR: SumoVehicles.PASSENGER,
    ObstacleType.TRUCK: SumoVehicles.TRUCK,
    ObstacleType.BUS: SumoVehicles.BUS,
    ObstacleType.BICYCLE: SumoVehicles.BICYCLE,
    ObstacleType.PEDESTRIAN: SumoVehicles.PEDESTRIAN,
    ObstacleType.PRIORITY_VEHICLE: SumoVehicles.VIP,
    ObstacleType.PARKED_VEHICLE: SumoVehicles.PASSENGER,
    ObstacleType.TRAIN: SumoVehicles.RAIL,
    ObstacleType.MOTORCYCLE: SumoVehicles.MOTORCYCLE,
    ObstacleType.TAXI: SumoVehicles.TAXI,
    # ObstacleType.CONSTRUCTION_ZONE: SumoVehicles.AUTHORITY,
    # ObstacleType.ROAD_BOUNDARY: SUMO,
    # ObstacleType.BUILDING: "custom2",
    # ObstacleType.PILLAR: "custom2",
    # ObstacleType.MEDIAN_STRIP: "custom1"
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
    SupportedTrafficSignCountry.ZAMUNDA: {
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
    }
}

TEMPLATES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates"))
DEFAULT_CFG_FILE = os.path.join(TEMPLATES_DIR, "default.sumo.cfg")


def get_sumo_edge_type(edge_types: EdgeTypes,
                       country_id: SupportedTrafficSignCountry,
                       *lanelet_types: LaneletType) -> EdgeType:
    """
    Determines appropriate SUMO EdgeType for given CommonRoad country_id and lanelet_types
    :param edge_types: Object of all available SUMO edge types
    :param country_id: Country the lanelet_types are from
    :param lanelet_types: LaneletTypes to determine SUMO EdgeType for
    :return:
    """
    default_type = LaneletType.COUNTRY
    default_country = SupportedTrafficSignCountry.ZAMUNDA
    if not lanelet_types:
        logging.warning(f"No Lanelet Type given for sumo_edge_type conversion, falling back to {default_type}")
        return get_sumo_edge_type(edge_types, country_id, default_type)

    supported = set(lanelet_types) & {lanelet_type
                                      for types in lanelet_type_CR2SUMO.values()
                                      for lanelet_type in types.keys()}
    try:
        most_common = max(supported, key=list(supported).count)
        return edge_types.types[lanelet_type_CR2SUMO[country_id][most_common]]
    # Max Error
    except ValueError:
        logging.warning(f"No LaneletType in {lanelet_types} not supported, falling back to {default_type}")
        return get_sumo_edge_type(edge_types, country_id, default_type)
    # Dict lookup error
    except KeyError as e:
        if country_id in lanelet_type_CR2SUMO and most_common in lanelet_type_CR2SUMO[country_id]:
            raise KeyError(f"EdgeType {lanelet_type_CR2SUMO[country_id][most_common]} not in EdgeTypes") from e
        logging.warning(f"({country_id}, {most_common}) is not supported, "
                        f"falling_back to: ({default_country}, {default_type})")
        return get_sumo_edge_type(edge_types, default_country, default_type)


def get_edge_types_from_template(country_id: SupportedTrafficSignCountry) -> EdgeTypes:
    if country_id not in lanelet_type_CR2SUMO:
        default_country = SupportedTrafficSignCountry.ZAMUNDA
        logging.warning(f"country {country_id} not supported, falling back to {default_country}")
        country_id = default_country
    path = os.path.join(TEMPLATES_DIR, f"{country_id.value}.typ.xml")
    try:
        with open(path, "r") as f:
            xml = f.read()
        return EdgeTypes.from_XML(xml)
    except FileExistsError as e:
        raise RuntimeError(f"Cannot find {country_id.value}.typ.xml file for {country_id}") from e
