from typing import Set, List
from commonroad.scenario.traffic_sign import TrafficLight, TrafficLightCycleElement, TrafficLightState
import numpy as np


def merge_traffic_light_cycles(traffic_lights: List[TrafficLight]) -> List[List[TrafficLightCycleElement]]:
    time_steps = np.lcm.reduce([sum(cycle.duration for cycle in tl.cycle) for tl in traffic_lights])
    states = np.array([_cycles_to_states(traffic_light.cycle, time_steps)
                       for traffic_light in traffic_lights]).T
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


def _cycles_to_states(cycles: List[TrafficLightCycleElement], max_time: int) -> List[TrafficLightState]:
    states: List[TrafficLightState] = []
    cycle_idx = 0
    length = sum(c.duration for c in cycles)
    for i in range(max_time):
        if (i % length) >= sum(c.duration for c in cycles[:cycle_idx + 1]):
            cycle_idx = (cycle_idx + 1) % len(cycles)
        states.append(cycles[cycle_idx].state)
    return states
