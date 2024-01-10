from commonroad.scenario.traffic_light import (
    TrafficLight,
    TrafficLightCycle,
    TrafficLightCycleElement,
    TrafficLightDirection,
    TrafficLightState,
)

from crdesigner.common.config.osm_config import osm_config as config


class TrafficLightGenerator:
    """
    This class acts as generator for traffic lights, that can be added to multiple types on intersections.
    Traffic light cycles are based on the number of incoming lanes.

    """

    def __init__(self, number_of_incomings):
        self.number_incomings = number_of_incomings

        # cycle phases
        self.cycle = config.TRAFFIC_LIGHT_CYCLE

        # increase red phase if more than 4 incomings
        if number_of_incomings > 4:
            self.cycle["red_phase"] += 50

        # internal variables
        self.cycle_length = sum(self.cycle.values())
        self.current_time_offset = 0

    def get_cycle(self) -> TrafficLightCycle:
        """
        Cycle that is applied to all traffic lights
        """
        cycle = [
            (TrafficLightState.RED, self.cycle["red_phase"]),
            (TrafficLightState.RED_YELLOW, self.cycle["red_yellow_phase"]),
            (TrafficLightState.GREEN, self.cycle["green_phase"]),
            (TrafficLightState.YELLOW, self.cycle["yellow_phase"]),
        ]
        cycle_element_list = [TrafficLightCycleElement(state[0], state[1]) for state in cycle]
        return TrafficLightCycle(cycle_element_list, time_offset=self.get_time_offset())

    def get_time_offset(self):
        """
        Method is used to get cycle offset for the next new traffic light
        """

        offset = self.current_time_offset

        # change time offset for cycle start based on number of incomings
        if self.number_incomings <= 2:
            pass
        elif self.number_incomings <= 4:
            self.current_time_offset += int(self.cycle_length / 2)
        else:  # more than 4 incommings
            self.current_time_offset += int(self.cycle_length / 3)

        return offset

    def generate_traffic_light(self, position, new_id):
        """
        Method to create the new traffic light
        """

        new_traffic_light = TrafficLight(
            traffic_light_id=new_id,
            position=position,
            traffic_light_cycle=self.get_cycle(),
            direction=TrafficLightDirection.ALL,
            active=True,
        )
        return new_traffic_light
