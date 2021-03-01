
from commonroad.scenario.traffic_sign import TrafficLight, TrafficLightCycleElement, TrafficLightState, TrafficLightDirection

class TrafficLightGenerator:
  
    def __init__(self, number_of_incomings):
        self.number_incomings = number_of_incomings

    time_step_multiplier = 1
    circle_length = 100
    current_time_offset = 0
    
    

    def get_cycle(self):
        cycle = [(TrafficLightState.RED, 57*self.time_step_multiplier),
                (TrafficLightState.RED_YELLOW, 3*self.time_step_multiplier),
                (TrafficLightState.GREEN, 37*self.time_step_multiplier),
                (TrafficLightState.YELLOW, 3*self.time_step_multiplier)]
        cycle_element_list = [TrafficLightCycleElement(state[0], state[1]) for state in cycle]
        return cycle_element_list

    def get_time_offset(self):
        
        # TODO Correct offsets for not only 4 incomming intersections

        offset = self.current_time_offset
        self.current_time_offset += int(self.circle_length / 2)
        return offset
        
    def generate_traffic_light(self, position, new_id):
        
        new_traffic_light = TrafficLight(
                                traffic_light_id=new_id,
                                cycle=self.get_cycle(),
                                position=position,
                                time_offset=self.get_time_offset(),
                                direction=TrafficLightDirection.ALL,
                                active=True
                                )
        return new_traffic_light
