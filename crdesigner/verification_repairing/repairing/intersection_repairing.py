from typing import Tuple

from commonroad.scenario.lanelet import LaneletNetwork

from crdesigner.verification_repairing.repairing.repairing import ElementRepairing


class IntersectionRepairing(ElementRepairing):
    def __init__(self, network: LaneletNetwork):
        """
        Constructor.

        :param network: Lanelet network.
        """
        super().__init__(network)

    def repair_at_least_two_incoming_elements(self, location: Tuple[int]):
        """
        Repairs at_least_two_incoming_elements.

        :param location: Location of invalid state.
        """
        (intersection_id,) = location

        self._network.remove_intersection(intersection_id)

    def repair_at_least_one_incoming_lanelet(self, location: Tuple[int, int]):
        """
        Repairs at_least_one_incoming_lanelet.

        :param location: Location of invalid state.
        """
        intersection_id, incoming_id = location

        intersection = self._network.find_intersection_by_id(intersection_id)

        for incoming in intersection.incomings:
            if incoming_id == incoming.incoming_id:
                intersection.incomings.remove(incoming)

    def repair_existence_is_left_of(self, location: Tuple[int, int]):
        """
        Repairs existence_is_left_of.

        :param location: Location of invalid state.
        """
        intersection_id, incoming_id = location

        intersection = self._network.find_intersection_by_id(intersection_id)
        for incoming in intersection.incomings:
            if incoming_id == incoming.incoming_id:
                incoming.left_of = None

    def repair_existence_incoming_lanelets(self, location: Tuple[int, int, int]):
        """
        Repairs existence_incoming_lanelets.

        :param location: Location of invalid state.
        """
        intersection_id, incoming_id, lanelet_id = location

        intersection = self._network.find_intersection_by_id(intersection_id)
        for incoming in intersection.incomings:
            if incoming_id == incoming.incoming_id:
                incoming.incoming_lanelets.remove(lanelet_id)

    def repair_incoming_intersection(self, location: Tuple[int, int, int, int, int]):
        """
        Repairs incoming_intersection.

        :param location: Location of invalid state.
        """
        pass  # TODO: Implement repairing function
