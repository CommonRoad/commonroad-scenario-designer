# from typing import List, Set
# from commonroad.scenario.intersection import Intersection, IncomingGroup
#
#
# def intersection_id(intersection: Intersection) -> int:
#     """
#     Returns the ID of the intersection.
#
#     :param intersection: Intersection.
#     :return: Intersection ID.
#     """
#     return intersection.intersection_id
#
#
# def incoming_elements(intersection: Intersection) -> List[IncomingGroup]:
#     """
#     Returns the incoming elements of the intersection.
#
#     :param intersection: Intersection.
#     :return: Incoming elements.
#     """
#     return intersection.incomings
#
#
# def incoming_lanelets(incoming_group: IncomingGroup) -> Set[int]:
#     """
#     Returns the IDs of the incoming lanelets of the incoming element.
#
#     :param incoming_group: Incoming group element.
#     :return: Incoming lanelet IDs.
#     """
#     return incoming_group.incoming_lanelets
