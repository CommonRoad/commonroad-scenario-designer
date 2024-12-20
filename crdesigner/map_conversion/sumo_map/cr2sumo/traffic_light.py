from collections import defaultdict
from typing import Dict, List, Set, Tuple

import numpy as np
from commonroad.scenario.traffic_light import (
    TrafficLight,
    TrafficLightCycle,
    TrafficLightCycleElement,
    TrafficLightState,
)

from crdesigner.map_conversion.sumo_map.sumolib_net import (
    Connection,
    Node,
    NodeType,
    Phase,
    SignalState,
    TLSProgram,
)
from crdesigner.map_conversion.sumo_map.util import (
    compute_max_curvature_from_polyline,
    lines_intersect,
)

from .mapping import traffic_light_states_CR2SUMO


class TrafficLightEncoder:
    def __init__(self, conf):
        self.index = -1
        self.conf = conf

    def encode(
        self,
        node: Node,
        traffic_lights: List[TrafficLight],
        light_2_connections: Dict[TrafficLight, Set[Connection]],
    ) -> Tuple[TLSProgram, List[Connection]]:
        # create SUMO Traffic Light Node
        self.index += 1
        program_id = f"tl_program_{self.index}"
        traffic_light_id = str(node.id)
        node.type = NodeType.TRAFFIC_LIGHT

        time_offset = max(tl.traffic_light_cycle.time_offset for tl in traffic_lights)
        tls_program = TLSProgram(traffic_light_id, time_offset * self.conf.dt, program_id)

        # sync and ungroup light states
        light_states = _sync_traffic_light_cycles(traffic_lights)
        # ungroup light states
        light_states = [
            [s for i, s in enumerate(state) for _ in light_2_connections[traffic_lights[i]]]
            for state in light_states
        ]
        connections: List[Connection] = [
            conn for tl in traffic_lights for conn in light_2_connections[tl]
        ]

        # convert states to SUMO
        sumo_states: List[List[SignalState]] = []
        for state in light_states:
            by_color: Dict[TrafficLightState, Set[int]] = defaultdict(set)
            for i, s in enumerate(state):
                by_color[s.state] |= {i}

            sumo_state = [traffic_light_states_CR2SUMO[s.state] for s in state]
            #
            # Additional conversion rules
            #
            # >= 2 green connections intersect at a time, curving ones have to yield straight ones
            if len(by_color[TrafficLightState.GREEN]) >= 2:
                green_connections = by_color[TrafficLightState.GREEN]

                def dot_connections(a, b):
                    return np.dot(a.shape[-1] - a.shape[0], b.shape[-1] - b.shape[0])

                foes = (
                    [i, j]
                    for i in green_connections
                    for j in green_connections
                    if i < j
                    and lines_intersect(connections[i].shape, connections[j].shape)
                    and dot_connections(connections[i], connections[j]) < 0
                )
                for foe in foes:
                    # make sure foe[0] is more straight than foe[1]
                    if compute_max_curvature_from_polyline(
                        connections[foe[0]].shape
                    ) > compute_max_curvature_from_polyline(connections[foe[1]].shape):
                        foe[0], foe[1] = foe[1], foe[0]
                    # give foe[0] priority
                    sumo_state[foe[0]] = SignalState.GREEN_PRIORITY
                    sumo_state[foe[1]] = SignalState.GREEN

            sumo_states.append(sumo_state)

        # encode states
        for state, sumo_state in zip(light_states, sumo_states):
            dur = state[0].duration * self.conf.dt
            assert dur > 0
            tls_program.add_phase(Phase(dur, sumo_state))

        for i, connection in enumerate(connections):
            connection.tls = tls_program
            connection.tl_link = i

        return tls_program, connections


def _sync_traffic_light_cycles(
    traffic_lights: List[TrafficLight],
) -> List[List[TrafficLightCycleElement]]:
    """
    Synchronizes traffic lights cycles for a list
    :param traffic_lights:
    :return: list of synchronized states
    """
    time_steps = np.lcm.reduce(
        [
            sum(cycle.duration for cycle in tl.traffic_light_cycle.cycle_elements)
            for tl in traffic_lights
        ]
    )
    states = np.array(
        [
            _sample_traffic_light_cycle_to_states(traffic_light.traffic_light_cycle, time_steps)
            for traffic_light in traffic_lights
        ]
    ).T
    res: List[List[TrafficLightCycleElement]] = []
    i = 0
    j = 0
    while i < len(states):
        j = i + 1
        while j < len(states):
            if all(a == b for a, b in zip(states[i], states[j])):
                j += 1
            else:
                break
        res.append([TrafficLightCycleElement(s, j - i) for s in states[i]])
        i = j
    return res


def _sample_traffic_light_cycle_to_states(
    cycle: TrafficLightCycle, max_time: int
) -> List[TrafficLightState]:
    """
    Sample the states of `cycle` for each timestep from 0 to `max_time`.

    :param cycle: The traffic light cycle that should be resampled.
    :param max_time: The time step until which the cycle should be sampled.

    :return: Sampled traffic light states.
    """
    states: List[TrafficLightState] = []
    for i in range(max_time):
        states.append(cycle.get_state_at_time_step(i))
    return states
