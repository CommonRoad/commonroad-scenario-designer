from enum import Enum, unique
from typing import Tuple


@unique
class SumoVehicles(Enum):
    """taken from sumo/src/utils/common/SUMOVehicleClass.cpp
    "public_emergency",  # deprecated
    "public_authority",  # deprecated
    "public_army",       # deprecated
    "public_transport",  # deprecated
    "transport",         # deprecated
    "lightrail",         # deprecated
    "cityrail",          # deprecated
    "rail_slow",         # deprecated
    "rail_fast",         # deprecated
    """
    PRIVATE = "private"
    EMERGENCY = "emergency"
    AUTHORITY = "authority"
    ARMY = "army"
    VIP = "vip"
    PASSENGER = "passenger"
    HOV = "hov"
    TAXI = "taxi"
    BUS = "bus"
    COACH = "coach"
    DELIVERY = "delivery"
    TRUCK = "truck"
    TRAILER = "trailer"
    TRAM = "tram"
    RAIL_URBAN = "rail_urban"
    RAIL = "rail"
    RAIL_ELECTRIC = "rail_electric"
    MOTORCYCLE = "motorcycle"
    MOPED = "moped"
    BICYCLE = "bicycle"
    PEDESTRIAN = "pedestrian"
    EVEHICLE = "evehicle"
    SHIP = "ship"
    CUSTOM1 = "custom1"
    CUSTOM2 = "custom2"


SUMO_VEHICLE_CLASSES: Tuple[str] = tuple(str(vehicle.value) for vehicle in SumoVehicles)


@unique
class SumoNodeType(Enum):
    """
    Node types:
    If you leave out the type of the node, it is automatically guessed by netconvert but may not be the one you intended.
    The following types are possible, any other string is counted as an error and will yield in a program stop:
    taken from https://sumo.dlr.de/docs/Networks/PlainXML.html#connections_after_joining_nodes
    """

    # priority: Vehicles on a low-priority edge have to wait until vehicles on a high-priority edge
    # have passed the junction.
    PRIORITY = "priority"
    # traffic_light: The junction is controlled by a traffic light (priority rules are used to avoid collisions
    # if conflicting links have green light at the same time).
    TRAFFIC_LIGHT = "traffic_light"
    # traffic_light_unregulated: The junction is controlled by a traffic light without any further rules.
    # This may cause collision if unsafe signal plans are used.
    # Note, that collisions within the intersection will never be detected.
    TRAFFIC_LIGHT_UNREGULATED = "traffic_light_unregulated"
    # traffic_light_right_on_red: The junction is controlled by a traffic light as for type traffic_light.
    # Additionally, right-turning vehicles may drive in any phase whenever it is safe to do so (after stopping once).
    # This behavior is known as right-turn-on-red.
    TRAFFIC_LIGHT_RIGHT_ON_RED = "traffic_light_right_on_red"
    # right_before_left: Vehicles will let vehicles coming from their right side pass.
    RIGHT_BEFORE_LEFT = "right_before_left"
    # unregulated: The junction is completely unregulated - all vehicles may pass without braking;
    # Collision detection on the intersection is disabled but collisions beyond the intersection will
    # detected and are likely to occur.
    UNREGULATED = "unregulated"
    # priority_stop: This works like a priority-junction but vehicles on minor links always have to stop before passing
    PRIORITY_STOP = "priority_stop"
    # allway_stop: This junction works like an All-way stop
    ALLWAY_STOP = "allway_stop"
    # rail_signal: This junction is controlled by a rail signal. This type of junction/control is only useful for rails.
    RAIL_SIGNAL = "rail_signal"
    # rail_crossing: This junction models a rail road crossing.
    # It will allow trains to pass unimpeded and will restrict vehicles via traffic signals when a train is approaching.
    RAIL_CROSSING = "rail_crossing"
    # zipper: This junction connects edges where the number of lanes decreases and traffic needs
    # to merge zipper-style (late merging).
    ZIPPER = "zipper"
