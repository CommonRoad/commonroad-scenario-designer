"""
Default configuration for CommonRoad to SUMO map converter
"""


class CR2SumoNetConfig:
    # [m/s] if not None: use this speed limit instead of speed limit from CommonRoad files
    overwrite_speed_limit = 130/3.6
    # [m/s] default max. speed for SUMO for unrestricted sped limits
    unrestricted_max_speed_default = 120 / 3.6
    # [m] distance threshold under which nodes are merged to one junction
    max_node_distance = 10
    # [m] shifted waiting position at junction (equivalent to SUMO's contPos parameter)
    wait_pos_internal_junctions = -4.0
    # [m/s] default speed limit when no speed_limit is given
    unrestricted_speed_limit_default = 130 / 3.6

    # default vehicle attributes to determine edge restrictions
    veh_params = {
        # maximum length
        'length': {
            'passenger': 4.7,
            'truck': 7.5,
            'bus': 12.4,
            'bicycle': 2.,
            'pedestrian': 0.415
        },
        # maximum width
        'width': {
            'passenger': 2.,
            'truck': 2.6,
            'bus': 2.7,
            'bicycle': 0.68,
            'pedestrian': 0.678
        }
    }

    @classmethod
    def from_dict(cls, param_dict:dict):
        """Initialize config from dictionary"""
        obj = cls()
        for param, value in param_dict.items():
            if hasattr(obj, param):
                setattr(obj, param, value)
        return obj