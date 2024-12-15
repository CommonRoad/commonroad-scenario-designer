from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from commonroad.scenario.lanelet import LaneletNetwork

from crdesigner.verification_repairing.config import MapVerParams
from crdesigner.verification_repairing.verification.formula_ids import (
    FormulaID,
    FormulaTypes,
    IntersectionFormulaID,
    LaneletFormulaID,
    TrafficLightFormulaID,
    TrafficSignFormulaID,
)
from crdesigner.verification_repairing.verification.satisfaction import InvalidStates


@dataclass
class InvalidState:
    """Dataclass storing all information of an invalid state."""

    formula: FormulaID = LaneletFormulaID.UNIQUE_ID
    element_ids: List[int] = field(default_factory=list)


@dataclass
class MapVerificationResult:
    """Dataclass storing all information of a result of a map verification ."""

    verification_time: float = 0.0
    repairing_time: float = 0.0
    invalid_states: List[InvalidState] = field(default_factory=list)


@dataclass
class MapVerification:
    """Dataclass storing all information of a map verification ."""

    benchmark_id: str = ""
    config: MapVerParams = field(default_factory=MapVerParams)
    map_verification_result: MapVerificationResult = field(default_factory=MapVerificationResult)


@dataclass
class VerificationResult:
    """Dataclass storing all information of a verification run."""

    map_verifications: List[MapVerification] = field(default_factory=list)


def extract_verification_computation_times(
    verification_result: VerificationResult,
) -> Dict[str, float]:
    """
    Extracts computation time required for verification for each map.

    :param verification_result: Verification result.
    :return: Computation times.
    """
    val_times = {}
    for map_verification in verification_result.map_verifications:
        val_times[map_verification.benchmark_id] = (
            map_verification.map_verification_result.verification_time
        )

    return val_times


def extract_repairing_computation_times(
    verification_result: VerificationResult,
) -> Dict[str, float]:
    """
    Extracts computation time required for repairing for each map.

    :param verification_result: Repairing result.
    :return: Computation times.
    """
    rep_times = {}
    for map_verification in verification_result.map_verifications:
        rep_times[map_verification.benchmark_id] = (
            map_verification.map_verification_result.repairing_time
        )

    return rep_times


def extract_benchmark_ids(verification_result: VerificationResult) -> List[str]:
    """
    Extracts benchmark IDs from all map verification s.

    :param verification_result: Verification result.
    :return: Benchmark IDs.
    """
    benchmark_ids = []
    for map_verification in verification_result.map_verifications:
        benchmark_ids.append(map_verification.benchmark_id)
    return benchmark_ids


def extract_invalid_states(
    verification_result: VerificationResult,
) -> Dict[str, Dict[FormulaID, List[int]]]:
    """
    Extracts invalid states from all maps.

    :param verification_result: Verification result.
    :return: Invalid States.
    """
    invalid_states = {}
    for map_verification in verification_result.map_verifications:
        form_invalid_states = {}
        for invalid_state in map_verification.map_verification_result.invalid_states:
            form_invalid_states[invalid_state.formula] = invalid_state.element_ids
        invalid_states[map_verification.benchmark_id] = form_invalid_states

    return invalid_states


def extract_verification_parameters(
    verification_result: VerificationResult,
) -> Dict[str, Tuple[int, int, bool]]:
    """
    Extracts parameters of all map verification s.

    :param verification_result: Verification result.
    :return: Verification parameters.
    """
    verification_params = {}
    for map_verification in verification_result.map_verifications:
        verification_params[map_verification.benchmark_id] = (
            map_verification.config.verification.max_iterations,
            map_verification.config.verification.num_threads,
            map_verification.config.evaluation.partitioned,
        )
    return verification_params


def initial_map_verification(
    verification_result: VerificationResult, benchmark_id: str, config: MapVerParams
) -> MapVerification:
    """
    Initializes a new map verification .

    :param verification_result: Verification result.
    :param benchmark_id: Benchmark ID.
    :param config: Verification config.
    :return: Map verification .
    """
    map_verification = MapVerification(benchmark_id=benchmark_id, config=config)

    formulas = config.verification.formulas
    if config.verification.formulas is None:
        for formula_pool in [
            LaneletFormulaID,
            TrafficSignFormulaID,
            TrafficLightFormulaID,
            IntersectionFormulaID,
        ]:
            for formula in formula_pool:
                formulas.append(formula)
    map_verification.formulas = formulas

    verification_result.map_verifications.append(map_verification)

    return map_verification


def update_map_verification(
    map_verification: MapVerification,
    verification_time: float,
    repairing_time: float,
    invalid_states: InvalidStates,
):
    """
    Updates a map verification .

    :param map_verification : Map verification.
    :param verification_time: Computation time of verification .
    :param repairing_time: Computation time of repairing.
    :param invalid_states: Invalid states.
    """
    map_verification_result = MapVerificationResult(
        verification_time=verification_time, repairing_time=repairing_time
    )

    for formula, locations in invalid_states.items():
        element_ids = []
        for location in locations:
            element_ids.append(location[0])
        map_verification_result.invalid_states.append(
            InvalidState(formula=formula, element_ids=element_ids)
        )

    map_verification.map_verification_result = map_verification_result


@dataclass
class MapVerificationComparison:
    """Dataclass storing all information for comparing map verification s."""

    map_id: str = ""
    comp_time: float = 0.0
    most_violated_spec: Dict[str, int] = field(
        default_factory=lambda: {
            formula.name: 0 for formula_type in FormulaTypes for formula in formula_type
        }
    )
    repairing_time: float = 0.0
    num_invalid_states: int = 0
    executions: int = 0
    distance: float = 0
    traffic_signs: int = 0
    lanelets: int = 0
    traffic_lights: int = 0
    stop_lines: int = 0
    intersections: int = 0

    def update(self, val: MapVerification):
        name_split = val.benchmark_id.split("_", 2)
        map_id = name_split[0] + "_" + name_split[1]
        if self.map_id == "":  # condition needed in case of several executions
            self.map_id = map_id
            for state in val.map_verification_result.invalid_states:
                self.num_invalid_states += len(state.element_ids)
                self.most_violated_spec[state.formula.name] += len(state.element_ids)
        elif self.map_id != map_id:
            return
        self.comp_time += val.map_verification_result.verification_time
        self.repairing_time += val.map_verification_result.repairing_time
        self.executions += 1

    def scenario_meta(self, lanelet_network: LaneletNetwork):
        self.lanelets = len(lanelet_network.lanelets)
        self.intersections = len(lanelet_network.intersections)
        for la in lanelet_network.lanelets:
            self.distance += la.distance[-1]
            self.traffic_signs += len(la.traffic_signs)
            self.traffic_lights += len(la.traffic_lights)
            if la.stop_line is not None:
                self.stop_lines += 1
