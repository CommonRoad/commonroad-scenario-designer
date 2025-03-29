import logging
import os
from enum import IntEnum

from commonroad.scenario.lanelet import LaneletType
from commonroad.scenario.obstacle import ObstacleType
from commonroad.scenario.traffic_light import TrafficLightDirection, TrafficLightState
from commonroad.scenario.traffic_sign import SupportedTrafficSignCountry

from crdesigner.map_conversion.sumo_map.sumolib_net import (
    ConnectionDirection,
    EdgeType,
    EdgeTypes,
    SignalState,
    VehicleType,
)


class ClusterInstruction(IntEnum):
    """
    Defines which clustering approach is chosen for an intersection
    """

    NO_CLUSTERING = 0
    CLUSTERING = 1
    ZIPPER = 2


directions_CR2SUMO = {
    TrafficLightDirection.RIGHT: ConnectionDirection.RIGHT,
    TrafficLightDirection.STRAIGHT: ConnectionDirection.STRAIGHT,
    TrafficLightDirection.LEFT: ConnectionDirection.LEFT,
    TrafficLightDirection.LEFT_STRAIGHT: ConnectionDirection.PARTLEFT,
    TrafficLightDirection.STRAIGHT_RIGHT: ConnectionDirection.PARTRIGHT,
    TrafficLightDirection.LEFT_RIGHT: ConnectionDirection.PARTLEFT,
    TrafficLightDirection.ALL: ConnectionDirection.STRAIGHT,
}

directions_SUMO2CR = {
    ConnectionDirection.RIGHT: TrafficLightDirection.RIGHT,
    ConnectionDirection.STRAIGHT: TrafficLightDirection.STRAIGHT,
    ConnectionDirection.LEFT: TrafficLightDirection.LEFT,
    ConnectionDirection.PARTLEFT: TrafficLightDirection.LEFT_RIGHT,
    ConnectionDirection.PARTRIGHT: TrafficLightDirection.LEFT_RIGHT,
    ConnectionDirection.TURN: TrafficLightDirection.ALL,
}

# Mapping from CR TrafficLightStates to SUMO Traffic Light states
traffic_light_states_CR2SUMO = {
    TrafficLightState.RED: SignalState.RED,
    TrafficLightState.YELLOW: SignalState.YELLOW,
    TrafficLightState.RED_YELLOW: SignalState.RED_YELLOW,
    TrafficLightState.GREEN: SignalState.GREEN,
    TrafficLightState.INACTIVE: SignalState.NO_SIGNAL,
}
# Mapping from  UMO Traffic Light to CR TrafficLightState states
traffic_light_states_SUMO2CR = {
    SignalState.RED: TrafficLightState.RED,
    SignalState.YELLOW: TrafficLightState.YELLOW,
    SignalState.GREEN: TrafficLightState.GREEN,
    SignalState.GREEN_PRIORITY: TrafficLightState.GREEN,
    SignalState.GREEN_TURN_RIGHT: TrafficLightState.GREEN,
    SignalState.RED_YELLOW: TrafficLightState.RED_YELLOW,
    SignalState.BLINKING: TrafficLightState.INACTIVE,
    SignalState.NO_SIGNAL: TrafficLightState.INACTIVE,
}

# CommonRoad obstacle type to sumo type
VEHICLE_TYPE_CR2SUMO = {
    ObstacleType.UNKNOWN: VehicleType.PASSENGER,
    ObstacleType.CAR: VehicleType.PASSENGER,
    ObstacleType.TRUCK: VehicleType.TRUCK,
    ObstacleType.BUS: VehicleType.BUS,
    ObstacleType.BICYCLE: VehicleType.BICYCLE,
    ObstacleType.PEDESTRIAN: VehicleType.PEDESTRIAN,
    ObstacleType.PRIORITY_VEHICLE: VehicleType.VIP,
    ObstacleType.PARKED_VEHICLE: VehicleType.PASSENGER,
    ObstacleType.TRAIN: VehicleType.RAIL,
    ObstacleType.MOTORCYCLE: VehicleType.MOTORCYCLE,
    ObstacleType.TAXI: VehicleType.TAXI,
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
    ObstacleType.MEDIAN_STRIP: "vehicle",
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
        LaneletType.CROSSWALK: "highway.path",
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
        LaneletType.CROSSWALK: "highway.path",
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
        LaneletType.CROSSWALK: "highway.path",
    },
}

TEMPLATES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates"))
DEFAULT_CFG_FILE = os.path.join(TEMPLATES_DIR, "default.sumo.cfg")


def get_sumo_edge_type(
    edge_types: EdgeTypes, country_id: SupportedTrafficSignCountry, *lanelet_types: LaneletType
) -> EdgeType:
    """
    Determines appropriate SUMO EdgeType for given CommonRoad country_id and lanelet_types
    :param edge_types: Object of all available SUMO edge types
    :param country_id: Country the lanelet_types are from
    :param lanelet_types: LaneletTypes to determine SUMO EdgeType for
    :return:
    """
    default_type = LaneletType.URBAN
    default_country = SupportedTrafficSignCountry.ZAMUNDA
    if not lanelet_types:
        logging.warning(
            f"No Lanelet Type given for sumo_edge_type conversion, falling back to {default_type}"
        )
        return get_sumo_edge_type(edge_types, country_id, default_type)

    supported = set(lanelet_types) & {
        lanelet_type for types in lanelet_type_CR2SUMO.values() for lanelet_type in types.keys()
    }
    try:
        most_common = max(supported, key=list(supported).count)
        return edge_types.types[lanelet_type_CR2SUMO[country_id][most_common]]
    # Max Error
    except ValueError:
        logging.warning(
            f"No LaneletType in {lanelet_types} not supported, falling back to {default_type}"
        )
        return get_sumo_edge_type(edge_types, country_id, default_type)
    # Dict lookup error
    except KeyError as e:
        if country_id in lanelet_type_CR2SUMO and most_common in lanelet_type_CR2SUMO[country_id]:
            raise KeyError(
                f"EdgeType {lanelet_type_CR2SUMO[country_id][most_common]} not in EdgeTypes"
            ) from e
        logging.warning(
            f"({country_id}, {most_common}) is not supported, "
            f"falling_back to: ({default_country}, {default_type})"
        )
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
        return EdgeTypes.from_xml(xml)
    except FileExistsError as e:
        raise RuntimeError(f"Cannot find {country_id.value}.typ.xml file for {country_id}") from e
