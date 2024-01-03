"""
Default configuration for CommonRoad to SUMO map converter
"""

from typing import List

from commonroad.common.util import Interval
from commonroad.scenario.obstacle import ObstacleType
from commonroad.scenario.scenario import Scenario
from commonroad.scenario.traffic_sign import SupportedTrafficSignCountry
from sumocr.sumo_config.default import DefaultConfig

EGO_ID_START = "egoVehicle"

# CommonRoad ID prefixes
ID_DICT = {"obstacleVehicle": 3, "egoVehicle": 4}


class SumoConfig(DefaultConfig):
    @classmethod
    def from_scenario_name(cls, scenario_name: str):
        """Initialize the config with a scenario name"""
        obj = cls()
        obj.scenario_name = scenario_name
        return obj

    @classmethod
    def from_scenario(cls, scenario: Scenario):
        """Initialize the config with a scenario name"""
        obj = cls()
        obj.scenario_name = str(scenario.scenario_id)
        obj.dt = scenario.dt
        obj.country_id = scenario.scenario_id.country_id
        return obj

    @classmethod
    def from_dict(cls, param_dict: dict):
        """Initialize config from dictionary"""
        obj = cls()
        for param, value in param_dict.items():
            if hasattr(obj, param):
                setattr(obj, param, value)
        return obj

    # logging level for logging module
    logging_level = "INFO"  # select DEBUG, INFO, WARNING, ERROR, CRITICAL

    # conversion
    country_id: SupportedTrafficSignCountry = SupportedTrafficSignCountry.ZAMUNDA
    highway_mode = True  # less aggressive clustering, use zipper junctions for onRamps

    # simulation
    dt = 0.1  # length of simulation step of the interface
    delta_steps = 2  # number of sub-steps simulated in SUMO during every dt
    presimulation_steps = 0  # number of time steps before simulation with ego vehicle starts
    simulation_steps = 300  # number of simulated (and synchronized) time steps
    with_sumo_gui = False
    # lateral resolution > 0 enables SUMO'S sublane model, see https://sumo.dlr.de/docs/Simulation/SublaneModel.html
    lateral_resolution = 1.0
    # re-compute orientation when fetching vehicles from SUMO.
    # Avoids lateral "sliding" at lane changes at computational costs
    compute_orientation = True

    # [m/s] if not None: use this speed limit instead of speed limit from CommonRoad files
    overwrite_speed_limit = 130 / 3.6
    # [m/s] default max. speed for SUMO for unrestricted sped limits
    unrestricted_max_speed_default = 120 / 3.6
    # [m] shifted waiting position at junction (equivalent to SUMO's contPos parameter)
    wait_pos_internal_junctions = -4.0
    # [m/s] default speed limit when no speed_limit is given
    unrestricted_speed_limit_default = 130 / 3.6

    # ego vehicle
    ego_veh_width = 2.0
    ego_veh_length = 5.0
    # number of ego vehicles
    n_ego_vehicles: int = 0
    # if desired ids of ego_vehicle known, specify here
    ego_ids: List[int] = []
    ego_start_time: int = 10
    # desired departure time ego vehicle
    departure_time_ego = 3

    ##
    # ego vehicle sync parameters
    ##
    # Time window to detect the lanelet change in seconds
    lanelet_check_time_window = int(2 / dt)
    # The absolute margin allowed between the planner position and ego position in SUMO
    protection_margin = 2.0
    # Variable can be used  to force the consistency to certain number of steps
    consistency_window = 4
    # Used to limit the sync mechanism only to move xy
    lane_change_sync = False
    # tolerance for detecting start of lane change
    lane_change_tol = 0.00

    ##
    # TRAFFIC GENERATION
    ##
    # probability that vehicles will start at the fringe of the network (edges without
    # predecessor), and end at the fringe of the network (edges without successor).
    fringe_factor: int = 2147483646
    # number of vehicle departures per second
    veh_per_second = 50
    # Interval of departure times for vehicles
    departure_interval_vehicles = Interval(0, 30)
    # max. number of vehicles in route file
    n_vehicles_max: int = 30
    # max. number of vehicles per km / sec
    max_veh_per_km: int = 25
    # random seed for deterministic sumo traffic generation
    random_seed: int = 1234
    random_seed_trip_generation: int = 1234

    # other vehicles size bound (values are sampled from normal distribution within bounds)
    vehicle_length_interval = 0.4
    vehicle_width_interval = 0.2

    # probability distribution of different vehicle classes. Do not need to sum up to 1.
    veh_distribution = {
        ObstacleType.CAR: 4,
        ObstacleType.TRUCK: 0.8,
        ObstacleType.BUS: 0.3,
        ObstacleType.BICYCLE: 0.2,
        ObstacleType.PEDESTRIAN: 0,
    }

    # default vehicle attributes to determine edge restrictions

    # vehicle attributes
    veh_params = {
        # maximum length
        "length": {
            ObstacleType.CAR: 5.0,
            ObstacleType.TRUCK: 7.5,
            ObstacleType.BUS: 12.4,
            ObstacleType.BICYCLE: 2.0,
            ObstacleType.PEDESTRIAN: 0.415,
        },
        # maximum width
        "width": {
            ObstacleType.CAR: 2.0,
            ObstacleType.TRUCK: 2.6,
            ObstacleType.BUS: 2.7,
            ObstacleType.BICYCLE: 0.68,
            ObstacleType.PEDESTRIAN: 0.678,
        },
        "minGap": {
            ObstacleType.CAR: 2.5,
            ObstacleType.TRUCK: 2.5,
            ObstacleType.BUS: 2.5,
            # default 0.5
            ObstacleType.BICYCLE: 1.0,
            ObstacleType.PEDESTRIAN: 0.25,
        },
        "accel": {
            # default 2.9 m/s²
            ObstacleType.CAR: Interval(1.8, 2.9),
            # default 1.3
            ObstacleType.TRUCK: Interval(1, 1.5),
            # default 1.2
            ObstacleType.BUS: Interval(1, 1.4),
            # default 1.2
            ObstacleType.BICYCLE: Interval(1, 1.4),
            # default 1.5
            ObstacleType.PEDESTRIAN: Interval(1.3, 1.7),
        },
        "decel": {
            # default 7.5 m/s²
            ObstacleType.CAR: Interval(4, 6.5),
            # default 4
            ObstacleType.TRUCK: Interval(3, 4.5),
            # default 4
            ObstacleType.BUS: Interval(3, 4.5),
            # default 3
            ObstacleType.BICYCLE: Interval(2.5, 3.5),
            # default 2
            ObstacleType.PEDESTRIAN: Interval(1.5, 2.5),
        },
        "maxSpeed": {
            # default 180/3.6 m/s
            ObstacleType.CAR: 180 / 3.6,
            # default 130/3.6
            ObstacleType.TRUCK: 130 / 3.6,
            # default 85/3.6
            ObstacleType.BUS: 85 / 3.6,
            # default 85/3.6
            ObstacleType.BICYCLE: 25 / 3.6,
            # default 5.4/3.6
            ObstacleType.PEDESTRIAN: 5.4 / 3.6,
        },
    }

    # vehicle behavior
    """
    'minGap': minimum gap between vehicles
    'accel': maximum acceleration allowed
    'decel': maximum deceleration allowed (absolute value)
    'maxSpeed': maximum speed. sumo_default 55.55 m/s (200 km/h)
    'lcStrategic': eagerness for performing strategic lane changing. Higher values result in earlier lane-changing. sumo_default: 1.0
    'lcSpeedGain': eagerness for performing lane changing to gain speed. Higher values result in more lane-changing. sumo_default: 1.0
    'lcCooperative': willingness for performing cooperative lane changing. Lower values result in reduced cooperation. sumo_default: 1.0
    'sigma': [0-1] driver imperfection (0 denotes perfect driving. sumo_default: 0.5
    'speedDev': [0-1] deviation of the speedFactor. sumo_default 0.1
    'speedFactor': [0-1] The vehicles expected multiplicator for lane speed limits. sumo_default 1.0
    'lcMaxSpeedLatStanding': max. lateral speed when vehicle is standing (avoids lateral sliding in standstill)
    """
    driving_params = {
        "lcStrategic": Interval(10, 100),
        "lcSpeedGain": Interval(3, 20),
        "lcCooperative": Interval(1, 3),
        "sigma": Interval(0.5, 0.65),
        "speedDev": Interval(0.1, 0.2),
        "speedFactor": Interval(0.9, 1.1),
        "lcImpatience": Interval(0, 0.5),
        "impatience": Interval(0, 0.5),
        "lcMaxSpeedLatStanding": 0,
        "lcSigma": Interval(0.1, 0.2),
        "lcKeepRight": Interval(0.8, 0.9),
    }
