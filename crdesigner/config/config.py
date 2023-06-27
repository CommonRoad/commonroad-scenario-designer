from commonroad.scenario.traffic_sign import TrafficSignIDGermany, TrafficSignIDZamunda, \
    TrafficSignIDUsa  # type: ignore
from dataclasses import dataclass, field
import dataclasses
from typing import Dict, List, Any, Union
from pathlib import Path
from enum import Enum
from omegaconf import OmegaConf
import inspect


def _dict_to_params(dict_params: Dict, cls: Any) -> Any:
    """
    Converts dictionary to parameter class.

    :param dict_params: Dictionary containing parameters.
    :param cls: Parameter dataclass to which dictionary should be converted to.
    :return: Parameter class.
    """
    fields = dataclasses.fields(cls)
    cls_map = {f.name: f.type for f in fields}
    kwargs = {}
    for k, v in cls_map.items():
        if k not in dict_params:
            continue
        if inspect.isclass(v) and issubclass(v, BaseParam):
            kwargs[k] = _dict_to_params(dict_params[k], cls_map[k])
        else:
            kwargs[k] = dict_params[k]
    return cls(**kwargs)


@dataclass
class BaseParam:
    __initialized: bool = field(init=False, default=False, repr=False)

    def __post_init__(self):
        self.__initialized = True
        # Make sure that the base parameters are propagated to all sub-parameters
        # This cannot be done in the init method, because the sub-parameters are not yet initialized.
        # This is not a noop, as it calls the __setattr__ method.
        # Do not remove!

    def __setattr__(self, name: str, value: Any) -> None:
        if name in {f.name for f in dataclasses.fields(self)}:
            super().__setattr__(name, value)
        if self.__initialized:
            for k, v in self.__dict__.items():
                if isinstance(v, BaseParam):
                    v.__setattr__(name, value)

    def __getitem__(self, item):
        try:
            value = self.__getattribute__(item)
        except AttributeError:
            raise KeyError(f"{item} is not a parameter of {self.__class__.__name__}")
        return value

    def __setitem__(self, key, value):
        try:
            self.__setattr__(key, value)
        except AttributeError:
            raise KeyError(f"{key} is not a parameter of {self.__class__.__name__}")

    @classmethod
    def load(cls, file_path: Union[Path, str], validate_types: bool = True):
        file_path = Path(file_path)
        assert file_path.suffix == ".yaml", f"File type {file_path.suffix} is unsupported! Please use .yaml!"
        loaded_yaml = OmegaConf.load(file_path)
        if validate_types:
            OmegaConf.merge(OmegaConf.structured(ScenarioDesignerParams), loaded_yaml)
        params = _dict_to_params(OmegaConf.to_object(loaded_yaml), cls)
        return params

    def save(self, file_path: Union[Path, str]):
        # Avoid saving private attributes
        dict_cfg = dataclasses.asdict(
                self, dict_factory=lambda items: {key: val for key, val in items if not key.startswith("_")})
        OmegaConf.save(OmegaConf.create(dict_cfg), file_path, resolve=True)


@dataclass
class GeneralParams(BaseParam):
    """General/Common CommonRoad scenario/map parameters"""

    # CommonRoad country ID
    country_id: str = "ZAM"
    # CommonRoad map name
    map_name: str = "MUC"
    # CommonRoad map ID
    map_id: int = 1
    # CommonRoad scenario time step size
    time_step_size: float = 0.1
    # CommonRoad map/scenario author
    author: str = "Sebastian Maierhofer"
    # CommonRoad scenario/map author affiliation
    affiliation: str = "Technical University of Munich"
    # CommonRoad scenario/map source
    source: str = "CommonRoad Scenario Designer"


class ProjectionMethods(str, Enum):
    # projects the lane-network in a way that aligns well with aerial images
    pseudo_mercator = "EPSG:3857"

    utm_default = "+proj=utm +zone=32 +ellps=WGS84"


@dataclass
class Lanelet2ConversionParams(BaseParam):
    """Parameters specific for Lanelet2 conversion"""

    # value of the tolerance for which we mark ways as equal
    ways_are_equal_tolerance: float = 0.001
    # default longitude coordinate (TUM MI building)
    default_lon_coordinate: float = 11.66821
    # default latitude coordinate (TUM MI building)
    default_lat_coordinate: float = 48.26301
    # supported countries for traffic sign cr2lanelet conversion
    supported_countries: List = \
        field(default_factory=lambda: [TrafficSignIDGermany, TrafficSignIDZamunda, TrafficSignIDUsa])
    # prefix dictionary for supported countries for traffic sign cr2lanelet conversion
    supported_countries_prefixes: Dict[str, str] = \
        field(default_factory=lambda: {"TrafficSignIDZamunda": "de",
                                       "TrafficSignIDGermany": "de",
                                       "TrafficSignIDUsa": "us"})
    # lanelet2 subtypes that are available in commonroad
    supported_lanelet2_subtypes: List[str] = \
        field(default_factory=lambda: ["urban", "country", "highway", "busLane", "bicycleLane",
                                       "exitRamp", "sidewalk", "crosswalk"])
    # value of the tolerance (in meters) for which we mark nodes as equal
    node_distance_tolerance: float = 0.01
    # list of priority signs
    priority_signs: List[str] = field(default_factory=lambda: ["PRIORITY", "RIGHT_OF_WAY"])
    # threshold indicating adjacent way
    adjacent_way_distance_tolerance: float = 0.05
    # initial node ID
    start_node_id_value: int = 10
    # string used for the initialization of projection
    proj_string: str = ProjectionMethods.pseudo_mercator.value
    # boolean indicating whether the conversion should be autoware compatible
    autoware: bool = False
    # boolean indicating whether local coordinates should be added
    use_local_coordinates: bool = False
    # boolean indicating whether map should be translated by the location coordinate specified in the CommonRoad map
    translate: bool = False
    # map describes left driving system
    left_driving: bool = False
    # detect left and right adjacencies of lanelets if they do not share a common way
    adjacencies: bool = True


@dataclass
class OpenDRIVEConversionParams(BaseParam):
    """Parameters specific for OpenDRIVE conversion"""

    # Max. error between reference geometry and polyline of vertices
    error_tolerance: float = 0.15
    # Min. step length between two sampling positions on the reference geometry
    min_delta_s: float = 0.5
    # precision with which to convert plane group to lanelet
    precision: float = 0.5
    # mapping of OpenDRIVE driveway lane type to a CommonRoad lanelet type
    driving_default_lanelet_type: str = "urban"
    # activates whether certain lanelet type should be added to all lanelets
    general_lanelet_type_activ: bool = True
    # lanelet type which is added to every lanelet (if activated)
    general_lanelet_type: str = "urban"
    # if active, converts OpenDRIVE lane types only to CommonRoad lanelet
    # types compatible with commonroad-io==2022.1 (probably also even older ones)
    lanelet_types_backwards_compatible: bool = False
    # threshold which is used to determine if a successor of an incoming lane is considered as straight
    intersection_straight_threshold: float = 35.0
    # least angle for lane segment to be added to the graph in degrees.
    # if you edit the graph by hand, a value of 0 is recommended
    lane_segment_angle: float = 5.0
    # string used for the initialization of projection
    proj_string: str = ProjectionMethods.pseudo_mercator.value
    # OpenDRIVE lane types which are considered for conversion
    filter_types: List[str] = \
        field(default_factory=lambda: ["driving", "restricted", "onRamp", "offRamp", "exit", "entry", "sidewalk",
                                       "shoulder", "crosswalk", "bidirectional"])


@dataclass
class ScenarioDesignerParams(BaseParam):
    """Scenario Designer parameters"""

    # general parameters
    general: GeneralParams = field(default_factory=GeneralParams)
    # OpenDRIVE parameters
    opendrive: OpenDRIVEConversionParams = field(default_factory=OpenDRIVEConversionParams)
    # lanelet2 parameters
    lanelet2: Lanelet2ConversionParams = field(default_factory=Lanelet2ConversionParams)
