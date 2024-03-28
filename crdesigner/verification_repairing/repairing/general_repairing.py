from typing import Tuple

from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.scenario.scenario import ScenarioID

from crdesigner.verification_repairing.repairing.repairing import ElementRepairing


class GeneralRepairing(ElementRepairing):
    """
    The class includes all repairing methods for each supported formula concerning the lanelet element.
    """

    def __init__(self, network: LaneletNetwork, scenario_id: ScenarioID = ScenarioID()):
        """
        Constructor.

        :param network: Lanelet network.
        :param scenario_id: ScenarioID.
        """
        super().__init__(network, scenario_id)
        self._connections = {}
        self._composed_lanelets = {}

    def repair_unique_id(self, location: Tuple[int]):
        """
        Repairs unique_id.
        The function replaces the ID of the corresponding element and
        does not update possible references by other elements.
        We assume those will be updated by lower-level repairing functions.

        :param location: Location of invalid state.
        """
        (element_id,) = location

        element_ids = (
            [lanelet.lanelet_id for lanelet in self._network.lanelets]
            + [sign.traffic_sign_id for sign in self._network.traffic_signs]
            + [light.traffic_light_id for light in self._network.traffic_lights]
            + [intersec.intersection_id for intersec in self._network.intersections]
        )
        # [incg.incoming_id for intersec in self._network.intersections for incg in intersec.incomings]+\
        # [outg.outgoing_id for intersec in self._network.intersections for outg in intersec.outgoings]+\
        # [lanelet.stop_line.stop_line_id for lanelet in self._network.lanelets
        #  if lanelet.stop_line is not None]

        new_id = max(element_ids) + 1

        if (la := self._network.find_lanelet_by_id(element_id)) is not None:
            self._network.remove_lanelet(element_id)
            la.lanelet_id = new_id
            self._network.add_lanelet(la)
            return
        if (tl := self._network.find_traffic_light_by_id(element_id)) is not None:
            lanelets = filter(lambda la: element_id in la.traffic_lights, self._network.lanelets)
            self._network.remove_traffic_light(element_id)
            tl.traffic_light_id = new_id
            self._network.add_traffic_light(tl, set(la.lanelet_id for la in lanelets))
            return
        if (ts := self._network.find_traffic_sign_by_id(element_id)) is not None:
            lanelets = filter(lambda la: element_id in la.traffic_signs, self._network.lanelets)
            self._network.remove_traffic_sign(element_id)
            ts.traffic_sign_id = new_id
            self._network.add_traffic_sign(ts, set(la.lanelet_id for la in lanelets))
            return
        if (intersec := self._network.find_intersection_by_id(element_id)) is not None:
            self._network.remove_intersection(element_id)
            intersec.intersection_id = new_id
            self._network.add_intersection(intersec)
            return
        # if (sl := self._network.find_stop_line_by_id(element_id)) is not None:
        #     lanelets = filter(lambda l: element_id == l.stop_line.stop_line_id, self._network.lanelets)
        #     self._network.remove_stop_line(element_id)
        #     sl.stop_line_id = new_id
        #     self._network.add_stop_line(sl, lanelets)
        #     return
        # if (incg := self._network.find_incoming_group_by_id(element_id)) is not None:
        #     incg.incomgin_id = new_id
        #     return
        # if (outg := self._network.find_outgoing_group_by_id(element_id)) is not None:
        #     outg.outgoing_id = new_id
        #     return
        # if (bound := self._network.find_boundary_by_id(element_id)) is not None:
        #     bound.boundary_id = new_id
        #     return
