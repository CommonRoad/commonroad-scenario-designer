from typing import Any, Callable, Dict, Set

from commonroad.scenario.lanelet import LaneletNetwork

from crdesigner.verification_repairing.config import MapVerParams
from crdesigner.verification_repairing.verification.hol.context import Context
from crdesigner.verification_repairing.verification.hol.formula import DomainName
from crdesigner.verification_repairing.verification.hol.functions.predicates import (
    intersection_predicates,
    lanelet_predicates,
    traffic_light_predicates,
    traffic_sign_predicates,
)
from crdesigner.verification_repairing.verification.hol.functions.term_functions import (
    general_functions,
    intersection_functions,
    lanelet_functions,
    traffic_light_functions,
    traffic_sign_functions,
)
from crdesigner.verification_repairing.verification.mapping import Mapping


def _prepare_predicate_funcs() -> Dict[str, Callable]:  # [[Any, ...], bool]]:
    """
    Prepares the functions of predicates.

    :return: Functions of predicates.
    """
    predicate_funcs = {}
    for predicate_functions in [
        lanelet_predicates,
        traffic_sign_predicates,
        traffic_light_predicates,
        intersection_predicates,
    ]:
        for func_name in dir(predicate_functions):
            predicate_func = getattr(predicate_functions, func_name)
            if callable(predicate_func) and not func_name.startswith("__"):
                predicate_funcs[func_name.capitalize()] = predicate_func

    return predicate_funcs


def _prepare_function_funcs() -> Dict[str, Callable]:  # [[Any, ...], Any]]:
    """
    Prepares the functions of term functions.

    :return: Functions of term functions.
    """
    function_funcs = {}
    for function_functions in [
        lanelet_functions,
        traffic_sign_functions,
        traffic_light_functions,
        intersection_functions,
        general_functions,
    ]:
        for func_name in dir(function_functions):
            function_func = getattr(function_functions, func_name)
            if callable(function_func) and not func_name.startswith("__"):
                function_funcs[func_name] = function_func

    return function_funcs


class HOLMapping(Mapping):
    """
    The class is responsible for mapping the CommonRoad elements to supported instances by the corresponding solver.
    """

    def __init__(self, network: LaneletNetwork, config: MapVerParams = MapVerParams()):
        """
        Constructor.

        :param network: Lanelet network.
        :param config: Configuration.
        """

        super().__init__(network, config)
        self._model = None

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, model: Context):
        self._model = model

    def map_lanelet_network(self):
        domain_vals = self._prepare_domains()
        predicate_funcs = _prepare_predicate_funcs()
        function_funcs = _prepare_function_funcs()

        self._model = Context(domain_vals, predicate_funcs, function_funcs)

    def map_verification_paras(self):
        pass

    def _prepare_domains(self) -> Dict[str, Set[Any]]:
        """
        Prepares the domains that include lanelets, traffic signs, traffic lights, etc.

        :return: Domains.
        """
        cycle_elements = []
        for traffic_light in self._network.traffic_lights:
            cycle_elements += (
                traffic_light.traffic_light_cycle.cycle_elements
                if traffic_light.traffic_light_cycle is not None
                else []
            )

        # incoming_groups, outgoing_groups = [], []
        # for intersection in self._network.intersections:
        #     incoming_groups += intersection.incomings
        #     outgoing_groups += intersection.outgoings

        domains = {
            DomainName.LANELETS.value: self._network.lanelets,
            DomainName.TRAFFIC_SIGNS.value: self._network.traffic_signs,
            DomainName.TRAFFIC_LIGHTS.value: self._network.traffic_lights,
            DomainName.INTERSECTIONS.value: self._network.intersections,
            # DomainName.TRAFFIC_LIGHT_CYCLE_ELEMENTS.value: cycle_elements,
            # DomainName.INCOMING_GROUPS.value: incoming_groups,
            # DomainName.OUTGOING_GROUPS.value: outgoing_groups,
            # DomainName.STOP_LINES.value: self._network.stop_lines,
            # DomainName.POLYLINES.value: self._network.boundaries,
            DomainName.AREAS.value: self._network.areas,
        }

        # make domains deterministic
        domains[DomainName.LANELETS.value].sort(key=lambda x: x.lanelet_id)
        domains[DomainName.TRAFFIC_SIGNS.value].sort(key=lambda x: x.traffic_sign_id)
        domains[DomainName.TRAFFIC_LIGHTS.value].sort(key=lambda x: x.traffic_light_id)
        domains[DomainName.INTERSECTIONS.value].sort(key=lambda x: x.intersection_id)
        domains[DomainName.ALL_ELEMENTS.value] = sum(domains.values(), [])

        for name, values in domains.items():
            domains.update({name: set(values)})

        return domains
