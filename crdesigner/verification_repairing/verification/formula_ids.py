import enum
from typing import List, Union

# All supported formulas are listed here. The formulas are divided into different types depending on the
# type of the CommonRoad element.


@enum.unique
class GeneralFormulaID(enum.Enum):
    """The IDs of formulas that describe the properties of all types of elements."""

    UNIQUE_ID = "unique_id_all"


@enum.unique
class LaneletFormulaID(enum.Enum):
    """The IDs of formulas that describe the properties of a lanelet."""

    UNIQUE_ID = "unique_id_la"
    SAME_VERTICES_SIZE = "same_vertices_size"
    VERTICES_MORE_THAN_ONE = "vertices_more_than_one"
    EXISTENCE_LEFT_ADJ = "existence_left_adj"
    EXISTENCE_RIGHT_ADJ = "existence_right_adj"
    EXISTENCE_PREDECESSOR = "existence_predecessor"
    EXISTENCE_SUCCESSOR = "existence_successor"
    CONNECTIONS_PREDECESSOR = "connections_predecessor"
    CONNECTIONS_SUCCESSOR = "connections_successor"
    POLYLINES_LEFT_SAME_DIR_PARALLEL_ADJ = "polylines_left_same_dir_parallel_adj"
    POLYLINES_LEFT_OPPOSITE_DIR_PARALLEL_ADJ = "polylines_left_opposite_dir_parallel_adj"
    POLYLINES_RIGHT_SAME_DIR_PARALLEL_ADJ = "polylines_right_same_dir_parallel_adj"
    POLYLINES_RIGHT_OPPOSITE_DIR_PARALLEL_ADJ = "polylines_right_opposite_dir_parallel_adj"
    CONNECTIONS_LEFT_MERGING = "connections_left_merging_adj"
    CONNECTIONS_RIGHT_MERGING = "connections_right_merging_adj"
    CONNECTIONS_LEFT_FORKING = "connections_left_forking_adj"
    CONNECTIONS_RIGHT_FORKING = "connections_right_forking_adj"
    POTENTIAL_SUCCESSOR = "potential_successor"
    POTENTIAL_PREDECESSOR = "potential_predecessor"
    POTENTIAL_LEFT_SAME_DIR_PARALLEL_ADJ = "potential_left_same_dir_parallel_adj"
    POTENTIAL_LEFT_OPPOSITE_DIR_PARALLEL_ADJ = "potential_left_opposite_dir_parallel_adj"
    POTENTIAL_RIGHT_SAME_DIR_PARALLEL_ADJ = "potential_right_same_dir_parallel_adj"
    POTENTIAL_RIGHT_OPPOSITE_DIR_PARALLEL_ADJ = "potential_right_opposite_dir_parallel_adj"
    POTENTIAL_LEFT_MERGING_ADJ = "potential_left_merging_adj"
    POTENTIAL_RIGHT_MERGING_ADJ = "potential_right_merging_adj"
    POTENTIAL_LEFT_FORKING_ADJ = "potential_left_forking_adj"
    POTENTIAL_RIGHT_FORKING_ADJ = "potential_right_forking_adj"
    NON_PREDECESSOR_AS_SUCCESSOR = "non_predecessor_as_successor"
    NON_SUCCESSOR_AS_PREDECESSOR = "non_successor_as_predecessor"
    POLYLINES_INTERSECTION = "polylines_intersection"
    LEFT_SELF_INTERSECTION = "left_self_intersection"
    RIGHT_SELF_INTERSECTION = "right_self_intersection"
    LANELET_TYPES_COMBINATION = "lanelet_types_combination"
    # NON_FOLLOWED_COMPOSABLE_LANELETS = 'non_followed_composable_lanelets'
    # REFERENCED_INTERSECTING_LANELETS = 'referenced_intersecting_lanelets'
    EXISTENCE_TRAFFIC_SIGNS = "existence_traffic_signs"
    EXISTENCE_TRAFFIC_LIGHTS = "existence_traffic_lights"
    EXISTENCE_STOP_LINE_TRAFFIC_SIGNS = "existence_stop_line_traffic_signs"
    EXISTENCE_STOP_LINE_TRAFFIC_LIGHTS = "existence_stop_line_traffic_lights"
    INCLUDED_STOP_LINE_TRAFFIC_SIGNS = "included_stop_line_traffic_signs"
    INCLUDED_STOP_LINE_TRAFFIC_LIGHTS = "included_stop_line_traffic_lights"
    ZERO_OR_TWO_POINTS_STOP_LINE = "zero_or_two_points_stop_line"
    STOP_LINE_POINTS_ON_POLYLINES = "stop_line_points_on_polylines"
    STOP_LINE_REFERENCES = "stop_line_references"
    CONFLICTING_LANELET_DIRECTIONS = "conflicting_lanelet_directions"
    LEFT_RIGHT_BOUNDARY_ASSIGNMENT = "left_right_boundary_assignment"


@enum.unique
class TrafficSignFormulaID(enum.Enum):
    """The IDs of formulas that describe the properties of a traffic sign."""

    AT_LEAST_ONE_TRAFFIC_SIGN_ELEMENT = "at_least_one_traffic_sign_element"
    REFERENCED_TRAFFIC_SIGN = "referenced_traffic_sign"
    GIVEN_ADDITIONAL_VALUE = "given_additional_value"
    VALUE_ADDITIONAL_VALUE_SPEED_SIGN = "valid_additional_value_speed_sign"
    MAXIMAL_DISTANCE_FROM_LANELET = "maximal_distance_from_lanelet"


@enum.unique
class TrafficLightFormulaID(enum.Enum):
    """The IDs of formulas that describe the properties of a traffic light."""

    AT_LEAST_ONE_CYCLE_ELEMENT = "at_least_one_cycle_element"
    # TRAFFIC_LIGHT_PER_INCOMING = 'traffic_light_per_incoming'
    REFERENCED_TRAFFIC_LIGHT = "referenced_traffic_light"
    NON_ZERO_DURATION = "non_zero_duration"
    UNIQUE_STATE_IN_CYCLE = "unique_state_in_cycle"
    CYCLE_STATE_COMBINATIONS = "cycle_state_combinations"
    # EXISTENCE_OUTGOING_RIGHT = 'existence_outgoing_right'
    # EXISTENCE_OUTGOING_STRAIGHT = 'existence_outgoing_straight'
    # EXISTENCE_OUTGOING_LEFT = 'existence_outgoing_left'


@enum.unique
class IntersectionFormulaID(enum.Enum):
    """The IDs of formulas that describe the properties of an intersection."""

    AT_LEAST_TWO_INCOMING_ELEMENTS = "at_least_two_incoming_elements"
    AT_LEAST_ONE_INCOMING_LANELET = "at_least_one_incoming_lanelet"
    EXISTENCE_IS_LEFT_OF = "existence_is_left_of"
    EXISTENCE_INCOMING_LANELETS = "existence_incoming_lanelets"
    INCOMING_INTERSECTION = "incoming_intersection"


FormulaID = Union[
    LaneletFormulaID,
    TrafficSignFormulaID,
    TrafficLightFormulaID,
    IntersectionFormulaID,
    GeneralFormulaID,
]
FormulaTypes = [
    LaneletFormulaID,
    TrafficSignFormulaID,
    TrafficLightFormulaID,
    IntersectionFormulaID,
    GeneralFormulaID,
]


def extract_formula_id(string: str) -> Union[None, FormulaID]:
    """
    Extracts ID of formula from string.

    :param string: String.
    :return: Formula ID; none if the string cannot be matched.
    """
    for formula_id in extract_formula_ids():
        if formula_id.value == string:
            return formula_id

    return None


def extract_formula_ids() -> List[FormulaID]:
    """
    Extracts all formula IDs.

    :return: Formula IDs.
    """
    formula_ids = []
    for formula_id_type in FormulaTypes:
        for formula_id in formula_id_type:
            formula_ids.append(formula_id)

    return formula_ids


def extract_formula_ids_from_strings(strings: List[str]) -> List[FormulaID]:
    """
    Extracts IDs of formulas from strings.

    :param strings: Strings.
    :return: Formula IDs.
    """
    ids = []

    for formula_id in extract_formula_ids():
        if formula_id.value in strings:
            ids.append(formula_id)

    return ids


def extract_formula_ids_by_type(formula_type: enum.EnumMeta) -> List[FormulaID]:
    """
    Extracts all IDs of formulas from a specific type.

    :param formula_type: Formula type.
    :return: Formula IDs of formula type.
    """
    formula_ids_of_type = []
    for formula_id_of_type in formula_type:
        formula_ids_of_type.append(formula_id_of_type)

    return formula_ids_of_type


def filter_formula_ids_by_type(
    formula_ids: List[FormulaID], formula_type: enum.EnumMeta
) -> List[FormulaID]:
    """
    Filters the IDs of formulas by a specific formula type.

    :param formula_ids: Formula IDs.
    :param formula_type: Formula type.
    :return: Formula IDs.
    """
    formula_ids_of_type = extract_formula_ids_by_type(formula_type)

    return list(set(formula_ids).intersection(set(formula_ids_of_type)))
