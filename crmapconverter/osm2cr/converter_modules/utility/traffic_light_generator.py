from commonroad.scenario.traffic_sign import TrafficLight, TrafficLightCycleElement, TrafficLightState, TrafficLightDirection


class TrafficLightGenerator:
    """
    This class acts as generator for traffic lights, that can be added to multiple types on intersections.
    Traffic light cycles are based on the number of incoming lanes.

    """
    def __init__(self, number_of_incomings):
        self.number_incomings = number_of_incomings

        # increase red phase if more than 4 incomings
        if number_of_incomings > 4:
            self.red_phase += 50
    # Multiplier to manipulate cycle evenly
    time_step_multiplier = 1

    # Cycle phases
    red_phase = 57 * time_step_multiplier
    red_yellow_phase = 3 * time_step_multiplier
    green_phase = 37 * time_step_multiplier
    yellow_phase = 3 * time_step_multiplier

    # internal variables
    cycle_length = red_phase + red_yellow_phase + green_phase + yellow_phase
    current_time_offset = 0

    def get_cycle(self):
        """
        Cycle that is applied to all traffic lights
        """
        cycle = [(TrafficLightState.RED, self.red_phase),
                (TrafficLightState.RED_YELLOW, self.red_yellow_phase),
                (TrafficLightState.GREEN, self.green_phase),
                (TrafficLightState.YELLOW, self.yellow_phase)]
        cycle_element_list = [TrafficLightCycleElement(state[0], state[1]) for state in cycle]
        return cycle_element_list

    def get_time_offset(self):
        """
        Method is used to get cycle offset for the next new traffic light
        """

        offset = self.current_time_offset

        # change time offset for cycle start based on number of incomings
        if self.number_incomings <= 4:
            self.current_time_offset += int(self.cycle_length / 2)
        else: # > 4
            self.current_time_offset += int(self.cycle_length / 3)

        return offset
          
    def generate_traffic_light(self, position, new_id):
        """
        Method to create the new traffic light
        """
        
        new_traffic_light = TrafficLight(
                                traffic_light_id=new_id,
                                cycle=self.get_cycle(),
                                position=position,
                                time_offset=self.get_time_offset(),
                                direction=TrafficLightDirection.ALL,
                                active=True
                                )
        return new_traffic_light
