import dataclasses
from queue import PriorityQueue
from typing import List

from crdesigner.verification_repairing.verification.formula_ids import (
    FormulaID,
    GeneralFormulaID,
    IntersectionFormulaID,
    LaneletFormulaID,
    TrafficLightFormulaID,
    TrafficSignFormulaID,
)


@dataclasses.dataclass
class SpecificationGroup:
    priority: int
    formulas: List[FormulaID]


@dataclasses.dataclass
class GroupsHandler:
    """Class representing the handler of the specification groups."""

    groups: List[SpecificationGroup] = dataclasses.field(
        default_factory=lambda: [
            SpecificationGroup(
                priority=0,
                formulas=[
                    LaneletFormulaID.LEFT_RIGHT_BOUNDARY_ASSIGNMENT,
                    GeneralFormulaID.UNIQUE_ID,
                ],
            ),
            SpecificationGroup(
                priority=1,
                formulas=[
                    LaneletFormulaID.POLYLINES_INTERSECTION,
                    LaneletFormulaID.LEFT_SELF_INTERSECTION,
                    LaneletFormulaID.RIGHT_SELF_INTERSECTION,
                ],
            ),
            SpecificationGroup(
                priority=2,
                formulas=[
                    LaneletFormulaID.SAME_VERTICES_SIZE,
                    LaneletFormulaID.VERTICES_MORE_THAN_ONE,
                    TrafficLightFormulaID.AT_LEAST_ONE_CYCLE_ELEMENT,
                    IntersectionFormulaID.AT_LEAST_ONE_INCOMING_LANELET,
                    TrafficSignFormulaID.AT_LEAST_ONE_TRAFFIC_SIGN_ELEMENT,
                    LaneletFormulaID.STOP_LINE_REFERENCES,
                    LaneletFormulaID.CONFLICTING_LANELET_DIRECTIONS,
                ],
            ),
            SpecificationGroup(
                priority=15,
                formulas=[
                    LaneletFormulaID.EXISTENCE_SUCCESSOR,
                    LaneletFormulaID.EXISTENCE_PREDECESSOR,
                    LaneletFormulaID.EXISTENCE_LEFT_ADJ,
                    LaneletFormulaID.EXISTENCE_RIGHT_ADJ,
                    LaneletFormulaID.POTENTIAL_SUCCESSOR,
                    LaneletFormulaID.POTENTIAL_PREDECESSOR,
                    LaneletFormulaID.POTENTIAL_LEFT_SAME_DIR_PARALLEL_ADJ,
                    LaneletFormulaID.POTENTIAL_LEFT_OPPOSITE_DIR_PARALLEL_ADJ,
                    LaneletFormulaID.POTENTIAL_RIGHT_SAME_DIR_PARALLEL_ADJ,
                    LaneletFormulaID.POTENTIAL_RIGHT_OPPOSITE_DIR_PARALLEL_ADJ,
                    LaneletFormulaID.POTENTIAL_LEFT_MERGING_ADJ,
                    LaneletFormulaID.POTENTIAL_RIGHT_MERGING_ADJ,
                    LaneletFormulaID.POTENTIAL_LEFT_FORKING_ADJ,
                    LaneletFormulaID.POTENTIAL_RIGHT_FORKING_ADJ,
                    LaneletFormulaID.NON_PREDECESSOR_AS_SUCCESSOR,
                    LaneletFormulaID.NON_SUCCESSOR_AS_PREDECESSOR,
                    LaneletFormulaID.EXISTENCE_TRAFFIC_SIGNS,
                    LaneletFormulaID.EXISTENCE_TRAFFIC_LIGHTS,
                    LaneletFormulaID.EXISTENCE_STOP_LINE_TRAFFIC_SIGNS,
                    LaneletFormulaID.EXISTENCE_STOP_LINE_TRAFFIC_LIGHTS,
                    IntersectionFormulaID.EXISTENCE_IS_LEFT_OF,
                    IntersectionFormulaID.EXISTENCE_INCOMING_LANELETS,
                    IntersectionFormulaID.AT_LEAST_TWO_INCOMING_ELEMENTS,
                ],
            ),
            SpecificationGroup(
                priority=20,
                formulas=[
                    LaneletFormulaID.CONNECTIONS_SUCCESSOR,
                    LaneletFormulaID.CONNECTIONS_PREDECESSOR,
                    LaneletFormulaID.POLYLINES_LEFT_SAME_DIR_PARALLEL_ADJ,
                    LaneletFormulaID.POLYLINES_LEFT_OPPOSITE_DIR_PARALLEL_ADJ,
                    LaneletFormulaID.POLYLINES_RIGHT_OPPOSITE_DIR_PARALLEL_ADJ,
                    LaneletFormulaID.POLYLINES_RIGHT_SAME_DIR_PARALLEL_ADJ,
                    LaneletFormulaID.CONNECTIONS_LEFT_MERGING,
                    LaneletFormulaID.CONNECTIONS_RIGHT_MERGING,
                    LaneletFormulaID.CONNECTIONS_LEFT_FORKING,
                    LaneletFormulaID.CONNECTIONS_RIGHT_FORKING,
                    LaneletFormulaID.LANELET_TYPES_COMBINATION,
                    LaneletFormulaID.INCLUDED_STOP_LINE_TRAFFIC_SIGNS,
                    LaneletFormulaID.INCLUDED_STOP_LINE_TRAFFIC_LIGHTS,
                    LaneletFormulaID.ZERO_OR_TWO_POINTS_STOP_LINE,
                    LaneletFormulaID.STOP_LINE_POINTS_ON_POLYLINES,
                    TrafficSignFormulaID.GIVEN_ADDITIONAL_VALUE,
                    TrafficSignFormulaID.VALUE_ADDITIONAL_VALUE_SPEED_SIGN,
                    TrafficSignFormulaID.MAXIMAL_DISTANCE_FROM_LANELET,
                    TrafficLightFormulaID.NON_ZERO_DURATION,
                    TrafficLightFormulaID.UNIQUE_STATE_IN_CYCLE,
                    TrafficLightFormulaID.CYCLE_STATE_COMBINATIONS,
                    IntersectionFormulaID.INCOMING_INTERSECTION,
                ],
            ),
        ]
    )

    _queue: PriorityQueue = dataclasses.field(default_factory=PriorityQueue)

    def __post_init__(self):
        # Builds the queue containing the specification groups ordered by their priorities.
        for group in self.groups:
            self._queue.put((group.priority, group.formulas))

    def is_next_group(self) -> bool:
        """
        Checks whether a further group is contained by the queue.

        :return: Boolean indicates whether a further group is contained.
        """
        return self._queue.qsize() != 0

    def next_group(self) -> List[FormulaID]:
        """
        Returns the next group with the highest order in the current queue.

        :return: Group of formula IDs.
        """
        return self._queue.get()[1]
