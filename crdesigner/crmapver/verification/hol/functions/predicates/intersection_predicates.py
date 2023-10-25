# from commonroad.scenario.intersection import Intersection, IncomingGroup
# from commonroad.scenario.lanelet import Lanelet
#
#
# def has_incoming_element(intersection: Intersection, incoming_group: IncomingGroup) -> bool:
#     """
#     Checks whether the intersection has the incoming element.
#
#     :param intersection: Intersection.
#     :param incoming_group: Incoming gropup element.
#     :return: Boolean indicates whether the intersection has the incoming element.
#     """
#     for incoming_elm in intersection.incomings:
#         if incoming_elm.incoming_id == incoming_group.incoming_id:
#             return True
#
#     return False
#
#
# def has_incoming_lanelet(incoming_group: IncomingGroup, lanelet: Lanelet) -> bool:
#     """
#     Checks whether the incoming element has the lanelet.
#
#     :param incoming_group: Incoming group element.
#     :param lanelet: Lanelet.
#     :return: Boolean indicates whether the incoming element has the lanelet.
#     """
#     return lanelet.lanelet_id in incoming_group.incoming_lanelets
