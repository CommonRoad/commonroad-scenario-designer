import dataclasses
import inspect
import os
import pathlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from omegaconf import OmegaConf

from crdesigner.verification_repairing.verification.formula_ids import FormulaID
from crdesigner.verification_repairing.verification.hol.formula_manager import (
    FormulaManager,
)


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
    """Map Verification base parameters."""

    __initialized: bool = field(init=False, default=False, repr=False)

    def __post_init__(self):
        """Post initialization of base parameter class."""
        # pylint: disable=unused-private-member
        self.__initialized = True
        # Make sure that the base parameters are propagated to all sub-parameters
        # This cannot be done in the init method, because the sub-parameters are not yet initialized.
        # This is not a noop, as it calls the __setattr__ method.
        # Do not remove!

    def __getitem__(self, item: str) -> Any:
        """
        Getter for base parameter value.

        :param: Item for which content should be returned.
        :return: Item value.
        """
        try:
            value = self.__getattribute__(item)
        except AttributeError as e:
            raise KeyError(f"{item} is not a parameter of {self.__class__.__name__}") from e
        return value

    def __setitem__(self, key: str, value: Any):
        """
        Setter for item.

        :param key: Name of item.
        :param value: Value of item.
        """
        try:
            self.__setattr__(key, value)
        except AttributeError as e:
            raise KeyError(f"{key} is not a parameter of {self.__class__.__name__}") from e

    @classmethod
    def load(cls, file_path: Union[pathlib.Path, str], validate_types: bool = True) -> "BaseParam":
        """
        Loads config file and creates parameter class.

        :param file_path: Path to yaml file containing config parameters.
        :param validate_types:  Boolean indicating whether loaded config should be validated against CARLA parameters.
        :return: Base parameter class.
        """
        file_path = pathlib.Path(file_path)
        assert (
            file_path.suffix == ".yaml"
        ), f"File type {file_path.suffix} is unsupported! Please use .yaml!"
        loaded_yaml = OmegaConf.load(file_path)
        if validate_types:
            OmegaConf.merge(OmegaConf.structured(MapVerParams), loaded_yaml)
        params = _dict_to_params(OmegaConf.to_object(loaded_yaml), cls)
        return params

    def save(self, file_path: Union[pathlib.Path, str]):
        """
        Save config parameters to yaml file.

        :param file_path: Path where yaml file should be stored.
        """
        # Avoid saving private attributes
        dict_cfg = dataclasses.asdict(
            self,
            dict_factory=lambda items: {key: val for key, val in items if not key.startswith("_")},
        )
        OmegaConf.save(OmegaConf.create(dict_cfg), file_path, resolve=True)


@dataclass
class VerificationParams:
    """Dataclass storing all information of a verification configuration."""

    formulas: List[FormulaID] = field(default_factory=list)
    excluded_formulas: List[FormulaID] = field(default_factory=list)
    formula_manager: FormulaManager = field(default_factory=FormulaManager)
    max_iterations: int = 5
    num_threads: int = 1
    connection_thresh: float = 1e-8
    border_thresh: float = 1e-6
    potential_connection_thresh: float = 1e-3
    potential_border_thresh: float = 1e-3
    buffer_size: float = 10.0

    assert num_threads > 0, "At least one process is required!"
    assert max_iterations >= 0, "Number of iteration must be positive!"


@dataclass
class PartitioningParams(BaseParam):
    """Dataclass storing all information of a partitioning configuration."""

    partitioned: bool = False
    lanelet_chunk_size: int = 30
    traffic_sign_chunk_size: int = 5
    traffic_light_chunk_size: int = 5
    intersection_chunk_size: int = 2


@dataclass
class EvaluationParams(BaseParam):
    # Evaluation parameters.

    # Boolean indicates whether the scenario should be overwritten.
    overwrite_scenario: bool = False
    # Path to directory of visualized invalid states.
    invalid_states_draw_dir: Optional[str] = None
    # Boolean indicating whether intermediate results should be drawn
    draw_intermediate_errors: bool = False
    # Boolean indicating whether the final result should be drawn
    draw_final_result: bool = True
    # file format which should be used for storing
    file_format: str = "png"
    # Path to directory of visualized partition.
    partition_draw_dir: Optional[str] = None
    # Boolean indicates whether the map should be partitioned before evaluation.
    partitioned: bool = False

    assert invalid_states_draw_dir is None or os.path.exists(
        invalid_states_draw_dir
    ), "The path to the drawing directory is not existent!"
    assert partition_draw_dir is None or (
        os.path.exists(partition_draw_dir) and partitioned
    ), "The path to the drawing directory is not existent or partitioning mode is not selected!"


@dataclass
class MapVerParams(BaseParam):
    """All Map Verification parameters"""

    verification: VerificationParams = field(default_factory=VerificationParams)
    partitioning: PartitioningParams = field(default_factory=PartitioningParams)
    evaluation: EvaluationParams = field(default_factory=EvaluationParams)
