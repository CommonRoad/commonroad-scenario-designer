from typing import Dict

from commonroad.scenario.traffic_sign import TrafficSignElement, TrafficSignIDZamunda

from crdesigner.common.config.osm_config import osm_config as config


class TrafficSignParser:
    """
    This class provides several methods to parse traffic signs, which are extracted
    from the osm file or retrieved from mapillary.com

    """

    def __init__(self, sign: Dict):
        self.sign = sign

    def accept_traffic_sign_element(self, signElement: TrafficSignElement) -> bool:
        if signElement.traffic_sign_element_id.name in config.ACCEPTED_TRAFFIC_SIGNS:
            return True
        if signElement.traffic_sign_element_id.name in config.EXCLUDED_TRAFFIC_SIGNS:
            return False
        if "ALL" in config.ACCEPTED_TRAFFIC_SIGNS:
            return True
        else:
            return False

    def parse_traffic_sign(self):
        elements = []
        for unrelated_sign in str(self.sign["traffic_sign"]).split(";"):
            sign_data = unrelated_sign[3:]

            for sign in sign_data.split(","):
                # speed limit sign
                if sign.startswith("274"):
                    zone = False
                    max_speed = -99.0
                    if sign[4] == "[":
                        max_speed = float(sign[sign.find("[") + 1 : sign.find("]")])
                    elif sign[4] == "-":
                        max_speed = float(sign[5:])

                    # speed limit zone
                    elif sign[3:].startswith(".1"):
                        zone = True
                        if sign[5] == "-" or sign[5] == ":":
                            max_speed = float(sign[6:])
                        else:
                            max_speed = float(sign[sign.find("[") + 1 : sign.find("]")])
                    if max_speed != -99:
                        if not zone:
                            # convert km/h to m/s and add to traffic sign elements
                            max_speed /= 3.6
                            elements.append(
                                TrafficSignElement(TrafficSignIDZamunda.MAX_SPEED, [str(max_speed)])
                            )
                        else:
                            elements.append(
                                TrafficSignElement(
                                    TrafficSignIDZamunda.MAX_SPEED_ZONE_START, [str(max_speed)]
                                )
                            )

                # city limit edge case
                elif sign == "y_limit":
                    elements.append(TrafficSignElement(TrafficSignIDZamunda.TOWN_SIGN, [" "]))

                # regular traffic sign
                else:
                    try:
                        traffic_sign_de = TrafficSignIDZamunda(sign)
                        value = " "
                        # add a value if found in sign
                        if "[" in sign and "]" in sign:
                            value = float(sign[sign.find("[") + 1 : sign.find("]")])
                        elements.append(TrafficSignElement(traffic_sign_de, [value]))
                    # unknown traffic sign
                    except ValueError:
                        print("Unknown traffic sign in" + str(sign_data) + " found")
                        # sign_id = traffic_sign_map['unknown']
                        # value = 'unknown sign'
                        # elements.append(TrafficSignElement(sign_id, [value]))

        elements = list(filter(self.accept_traffic_sign_element, elements))
        return elements

    def parse_mapillary(self) -> TrafficSignElement or None:
        sign_id = None  # TrafficSignIDZamunda.WARNING_ANIMAL_CROSSING_RIGHT
        value = " "  # self.sign['mapillary']

        category = str(self.sign["mapillary"]).split("--")[0]
        name = str(self.sign["mapillary"]).split("--")[1]

        # start parsing

        # warnings
        if category == "warning" and category in config.MAPILLARY_CATEGORIES:
            if "crossroads-with-priority-to-the-right" in name:
                sign_id = TrafficSignIDZamunda.WARNING_RIGHT_BEFORE_LEFT
            elif "warning--steep-ascent" in name:
                sign_id = TrafficSignIDZamunda.WARNING_STEEP_HILL_DOWNWARDS
            elif "slippery-road-surface" in name:
                sign_id = TrafficSignIDZamunda.WARNING_SLIPPERY_ROAD
            elif "roadworks" in name:
                sign_id = TrafficSignIDZamunda.WARNING_CONSTRUCTION_SITE
            elif "construction" in name:
                sign_id = TrafficSignIDZamunda.WARNING_CONSTRUCTION_SITE
            elif "animals" in name:
                sign_id = TrafficSignIDZamunda.WARNING_ANIMAL_CROSSING_RIGHT
            elif name == "crossroads":
                sign_id = TrafficSignIDZamunda.RIGHT_OF_WAY
            else:
                sign_id = TrafficSignIDZamunda.WARNING_DANGER_SPOT
        # regulatory
        elif category == "regulatory" and category in config.MAPILLARY_CATEGORIES:
            if name == "yield":
                sign_id = TrafficSignIDZamunda.YIELD
            elif name == "stop":
                sign_id = TrafficSignIDZamunda.STOP
            elif "give-way-to-oncoming-traffic" in name:
                sign_id = TrafficSignIDZamunda.PRIORITY_OPPOSITE_DIRECTION
            elif "turn-right-ahead" in name:
                sign_id = TrafficSignIDZamunda.TURN_RIGHT_AHEAD
            elif "turn-left-ahead" in name:
                sign_id = TrafficSignIDZamunda.TURN_RIGHT_AHEAD
            elif "roundabout" in name:
                sign_id = TrafficSignIDZamunda.ROUNDABOUT
            elif "one-way-right" in name:
                sign_id = TrafficSignIDZamunda.ONEWAY_RIGHT
            elif "one-way-left" in name:
                sign_id = TrafficSignIDZamunda.ONEWAY_LEFT
            elif name == "keep_left":
                sign_id = TrafficSignIDZamunda.PRESCRIBED_PASSING_LEFT
            elif name == "keep_right":
                sign_id = TrafficSignIDZamunda.PRESCRIBED_PASSING_RIGHT
            elif name == "bicycles-only":
                sign_id = TrafficSignIDZamunda.BIKEWAY
            elif name == "pedestrians-only":
                sign_id = TrafficSignIDZamunda.SIDEWALK
            elif name == "buses-only":
                sign_id = TrafficSignIDZamunda.BUSLANE
            elif name == "no-motor-vehicles-except-motorcycles":
                sign_id = TrafficSignIDZamunda.BAN_CARS
            elif name == "no-heavy-goods-vehicles":
                sign_id = TrafficSignIDZamunda.BAN_TRUCKS
            elif name == "no-bicycles":
                sign_id = TrafficSignIDZamunda.BAN_BICYCLE
            elif name == "no-motorcycles":
                sign_id = TrafficSignIDZamunda.BAN_MOTORCYCLE
            elif name == "no-buses":
                sign_id = TrafficSignIDZamunda.BAN_BUS
            elif name == "no-pedestrians":
                sign_id = TrafficSignIDZamunda.BAN_PEDESTRIAN
            elif "road-closed-to-vehicles" in name:
                sign_id = TrafficSignIDZamunda.BAN_ALL_VEHICLES
            elif name == "weight-limit":
                sign_id = TrafficSignIDZamunda.MAX_WEIGHT
            elif name == "width-limit":
                sign_id = TrafficSignIDZamunda.MAX_WIDTH
            elif name == "height-limit":
                sign_id = TrafficSignIDZamunda.MAX_HEIGHT
            elif name == "length-limit":
                sign_id = TrafficSignIDZamunda.MAX_LENGTH
            elif name == "no-entry":
                sign_id = TrafficSignIDZamunda.NO_ENTRY
            elif name == "no-u-turn":
                sign_id = TrafficSignIDZamunda.U_TURN
            elif "no-motor-vehicles" in name:
                sign_id = TrafficSignIDZamunda.BAN_CAR_TRUCK_BUS_MOTORCYCLE
            elif "end-of-maximum-speed" in name:
                sign_id = TrafficSignIDZamunda.MAX_SPEED_END
                value = name.split("-")[-1]
            elif "advisory-maximum-speed-limit" in name:
                # traffic sign not correct implemented in mapillary yet. Speed is missing.
                pass
            elif "maximum-speed-limit" in name:
                sign_id = TrafficSignIDZamunda.MAX_SPEED
                value = float(name.split("-")[-1]) / 3.6
            elif "end-of-speed-limit-zone" in name:
                sign_id = TrafficSignIDZamunda.MAX_SPEED_ZONE_END
            elif "speed-limit-zone" in name:
                sign_id = TrafficSignIDZamunda.MAX_SPEED_ZONE_START
            elif name == "no-overtaking":
                sign_id = TrafficSignIDZamunda.NO_OVERTAKING_START
            elif name == "no-overtaking-by-heavy-goods-vehicles":
                sign_id = TrafficSignIDZamunda.NO_OVERTAKING_TRUCKS_START
            elif "end-of-maximum-speed-limit" in name:
                sign_id = TrafficSignIDZamunda.MAX_SPEED_END
                value = name.split("-")[-1]
            elif name == "end-of-no-overtaking-by-heavy-goods-vehicles":
                sign_id = TrafficSignIDZamunda.NO_OVERTAKING_TRUCKS_END
            elif name == "end-of-prohibition":
                sign_id = TrafficSignIDZamunda.ALL_MAX_SPEED_AND_OVERTAKING_END
            elif name == "priority-road":
                sign_id = TrafficSignIDZamunda.PRIORITY
            elif name == "priority-over-oncoming-vehicles":
                sign_id = TrafficSignIDZamunda.PRIORITY_OVER_ONCOMING
        # information
        elif category == "information" and category in config.MAPILLARY_CATEGORIES:
            if "minimum-speed" in name:
                sign_id = TrafficSignIDZamunda.MIN_SPEED
                value = str(float(name.split("-")[-1]) / 3.6)
            elif name == "built-up-area":
                sign_id = TrafficSignIDZamunda.TOWN_SIGN
            elif name == "living-street":
                sign_id = TrafficSignIDZamunda.TRAFFIC_CALMED_AREA_START
            elif name == "end-of-living-street":
                sign_id = TrafficSignIDZamunda.TRAFFIC_CALMED_AREA_END
            elif name == "tunnel":
                sign_id = TrafficSignIDZamunda.TUNNEL
            elif name == "motorway":
                sign_id = TrafficSignIDZamunda.INTERSTATE_START
            elif name == "end-of-motorway":
                sign_id = TrafficSignIDZamunda.INTERSTATE_END
            elif name == "limited-access-road":
                sign_id = TrafficSignIDZamunda.HIGHWAY_START
            elif name == "end-of-limited-access-road":
                sign_id = TrafficSignIDZamunda.HIGHWAY_END
            elif name == "pedestrians-crossing":
                sign_id = TrafficSignIDZamunda.PEDESTRIANS_CROSSING
            elif name == "dead-end":
                sign_id = TrafficSignIDZamunda.DEAD_END
        # complementary
        elif category == "complementary" and category in config.MAPILLARY_CATEGORIES:
            if name == "chevron-left":
                sign_id = TrafficSignIDZamunda.DIRECTION_SIGN_LEFT_SINGLE
            elif name == "chevron-right":
                sign_id = TrafficSignIDZamunda.DIRECTION_SIGN_RIGHT_SINGLE

        if sign_id:
            mapillary_element = TrafficSignElement(sign_id, [value])
            if self.accept_traffic_sign_element(mapillary_element):
                return mapillary_element
        return None

    def parse_maxspeed(self):
        sign_id = TrafficSignIDZamunda.MAX_SPEED
        value = self.sign["maxspeed"]
        maxspeed_element = TrafficSignElement(sign_id, [value])
        if self.accept_traffic_sign_element(maxspeed_element):
            return maxspeed_element
        return None
