import enum
import logging
from typing import Dict, List, Set, Tuple, Union

import numpy as np
from commonroad.scenario.lanelet import LineMarking, StopLine
from commonroad.scenario.traffic_light import TrafficLight, TrafficLightDirection
from commonroad.scenario.traffic_sign import (
    TrafficSign,
    TrafficSignElement,
    TrafficSignIDChina,
    TrafficSignIDCountries,
    TrafficSignIDGermany,
    TrafficSignIDRussia,
    TrafficSignIDSpain,
    TrafficSignIDUsa,
    TrafficSignIDZamunda,
)

from crdesigner.map_conversion.common.utils import generate_unique_id, get_default_cycle
from crdesigner.map_conversion.opendrive.cr2odr.elements.road import Road
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_conversion import utils
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadLanes import (
    LaneSection,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadSignal import (
    Signal,
)

import bisect

def extract_traffic_element_id(
    signal_type: str, signal_subtype: str, traffic_sign_enum: enum
) -> Union[
    TrafficSignIDZamunda,
    TrafficSignIDGermany,
    TrafficSignIDUsa,
    TrafficSignIDChina,
    TrafficSignIDSpain,
    TrafficSignIDRussia,
]:
    """Extract the traffic element id from the signal type and subtype string.

    :param signal_type: Signal type of the traffic element
    :param signal_subtype: Subtype of the traffic element
    :param traffic_sign_enum: Enumeration of country-specific traffic signs
    :return: The extracted traffic element id.
    """
    if signal_type in set(item.value for item in traffic_sign_enum):
        element_id = traffic_sign_enum(signal_type)
    elif signal_type + "-" + signal_subtype in set(item.value for item in traffic_sign_enum):
        element_id = traffic_sign_enum(signal_type + "-" + str(signal_subtype))
    elif (
        traffic_sign_enum is TrafficSignIDGermany or traffic_sign_enum is TrafficSignIDZamunda
    ) and signal_type == "252":  # traffic sign ID 252 is replaced by 260
        element_id = traffic_sign_enum("260")
    else:
        logging.warning(
            "OpenDRIVE/traffic_signals.py: Unknown {} of ID {} of subtype {}!".format(
                traffic_sign_enum.__name__, signal_type, signal_subtype
            )
        )
        element_id = traffic_sign_enum.UNKNOWN

    return element_id


def assign_traffic_signals_to_road(
    road: Road,
    traffic_light_dirs: Dict[str, Set[str]],
    traffic_light_lanes: Dict[str, Tuple[int, int]],
) -> Tuple[List[TrafficLight], List[TrafficSign], List[StopLine]]:
    """Extracts traffic_lights, traffic_signs, stop_lines from a road.

    :param road: The road object from which to extract signals.
    :param traffic_light_dirs: Dictionary of traffic light IDs to directions.
    :param traffic_light_lanes: Dictionary of traffic light IDs to lane validity.
    """
    traffic_signs = []
    traffic_lights = []
    stop_lines = []
    # TODO: Stop lines are created and appended to the list for DEU and OpenDrive format.
    # This has been replicated for other countries but has not been tested with a test case
    # Stop lines have a signal type of 294 and are handled differently in the CommonRoad format
    
    for signal in road.signals:
        lanes = (
            (0, 0) if signal.validity_from is None else (signal.validity_from, signal.validity_to)
        )
        """

        calculate the planar coordinates and tangent angle of the reference line at s
        move the signal along the orthogonal direction to (x_t, y_t)
        z_surface = calculate_road_surface_height(road, signal.s, signal.t)
        finally add the signal's own zOffset to get the final Z
        """
        
        position, tangent, _, _ = road.plan_view.calc(signal.s, compute_curvature=False)
        #elevation = calculate_elevation(road.elevation_profile, signal.s)#here elevation = z coordinate
        position = np.array(
            [
                position[0] + signal.t * np.cos(tangent + np.pi / 2),
                position[1] + signal.t * np.sin(tangent + np.pi / 2),
                0,
                #elevation + signal.zOffset,#build xyz coordinate with zOffset
            ]
        )
        if signal.dynamic == "no":
            if (
                signal.signal_value == "-1"
                or signal.signal_value == "-1.0000000000000000e+00"
                or signal.signal_value == "none"
                or signal.signal_value is None
            ):
                additional_values = []
            else:
                if signal.unit == "km/h":
                    additional_values = [str(float(signal.signal_value) / 3.6)]
                else:
                    additional_values = [str(signal.signal_value)]

            signal_country = utils.get_signal_country(signal.country)
            country_stop_line_id = {
                "DEU": "294",
                "ZAM": "294",
                "USA": "294",
                "CHN": "294",
                "ESP": "294",
            }

            if (
                (signal_country == "DEU" or signal_country not in TrafficSignIDCountries.keys())
                and signal.type == "1000003"
                or signal.type == "1000004"
            ):
                continue
            element_id = extract_traffic_element_id(
                signal.type, str(signal.subtype), TrafficSignIDCountries[signal_country]
            )
            if signal.type == country_stop_line_id[signal_country]:
                # Creating stop line object by first calculating the position of the two end points that define the
                # straight stop line
                position_1, position_2 = calculate_stop_line_position(
                    road.lanes.lane_sections, signal, position, tangent
                )
                stop_line = StopLine(position_1, position_2, LineMarking.SOLID)
                road.add_stop_line((stop_line, lanes, signal.s))
                stop_lines.append(stop_line)
            if element_id.value == "":
                continue
            traffic_sign_element = TrafficSignElement(
                traffic_sign_element_id=element_id, additional_values=additional_values
            )
            traffic_sign = TrafficSign(
                traffic_sign_id=generate_unique_id(),
                traffic_sign_elements=list([traffic_sign_element]),
                first_occurrence=None,
                position=position,
                virtual=False,
            )
            traffic_sign.zOffset = signal.zOffset if signal.zOffset is not None else 0.0

            road.add_traffic_sign((traffic_sign, lanes, signal.s))
            traffic_signs.append(traffic_sign)

        elif signal.dynamic == "yes":
            # the three listed here are hard to interpret in commonroad.
            # we ignore such signals in order not cause trouble in traffic simulation
            tdir = TrafficLightDirection.ALL
            if traffic_light_dirs.get(signal.signal_id) is not None:
                t_light = traffic_light_dirs[signal.signal_id]
                if "Right" in t_light and "Straight" in t_light and "Left" in t_light:
                    tdir = TrafficLightDirection.ALL
                elif "Left" in t_light and "Straight" in t_light:
                    tdir = TrafficLightDirection.LEFT_STRAIGHT
                elif "Right" in t_light and "Straight" in t_light:
                    tdir = TrafficLightDirection.STRAIGHT_RIGHT
                elif "Left" in t_light and "Right" in t_light:
                    tdir = TrafficLightDirection.LEFT_RIGHT
                elif "Left" in t_light:
                    tdir = TrafficLightDirection.LEFT
                elif "Right" in t_light:
                    tdir = TrafficLightDirection.RIGHT
                elif "Straight" in t_light:
                    tdir = TrafficLightDirection.STRAIGHT
                else:
                    tdir = TrafficLightDirection.ALL
            lanes = (
                lanes
                if traffic_light_lanes.get(signal.signal_id) is None
                else traffic_light_lanes[signal.signal_id]
            )
            if signal.type != ("1000002" or "1000007" or "1000013"):
                traffic_light = TrafficLight(
                    traffic_light_id=generate_unique_id(),
                    position=position,
                    traffic_light_cycle=get_default_cycle(),
                    direction=tdir,
                )  # TODO remove for new CR-Format
                traffic_light.zOffset = signal.zOffset if signal.zOffset is not None else 0.0
                road.add_traffic_light((traffic_light, lanes, signal.s))
                traffic_lights.append(traffic_light)
            else:
                continue
    return traffic_lights, traffic_signs, stop_lines


def calculate_stop_line_position(
    lane_sections: List[LaneSection], signal: Signal, position: np.ndarray, tangent: float
) -> Tuple[np.ndarray, np.ndarray]:
    """Function to calculate the 2 points that define the stop line which
    is a straight line from one edge of the road to the other.

    :param lane_sections: OpenDRIVE lane_sections list containing the lane_section parsed lane_section class
    :param signal: Signal object, in this case the stop line.
    :param position: initial position as calculated in the get_traffic_signals function
    :param tangent: tangent value as calculated in the get_traffic_signals function
    :return: Positions of the stop line
    """
    total_width = 0
    for lane_section in lane_sections:
        for lane in lane_section.all_lanes:
            # Stop line width only depends on drivable lanes
            if lane.id != 0 and lane.type in ["driving", "onRamp", "offRamp", "exit", "entry"]:
                for width in lane.widths:
                    # Calculating total width of stop line
                    coefficients = width.polynomial_coefficients
                    lane_width = (
                        coefficients[0]
                        + coefficients[1] * signal.s
                        + coefficients[2] * signal.s**2
                        + coefficients[3] * signal.s**3
                    )

                    total_width += lane_width
    position_1 = position
    # Calculating second point of stop line using trigonometry
    position_2 = np.array(
        [
            position[0] - total_width * np.cos(tangent + np.pi / 2),
            position[1] - total_width * np.sin(tangent + np.pi / 2),
        ]
    )
    return position_1, position_2


def get_traffic_signal_references(
    road: Road,
    traffic_light_dirs: Dict[str, Set[str]],
    traffic_light_lanes: Dict[str, Tuple[int, int]],
):
    """Function to extract relevant information from sign references.

    :param road: The road object from which to extract signals.
    :param traffic_light_dirs: Dictionary, where signal directions should be stored.
    :param traffic_light_lanes: Dictionary, where signal lanes should be stored.
    """
    for signal in road.signal_reference:
        if signal.turn_relation is not None:
            if traffic_light_dirs.get(signal.signal_id) is None:
                traffic_light_dirs[signal.signal_id] = set()
            traffic_light_dirs[signal.signal_id].add(signal.turn_relation)
        if signal.validity_to is not None:
            if traffic_light_lanes.get(signal.signal_id) is not None:
                traffic_light_lanes[signal.signal_id] = (
                    min(traffic_light_lanes[signal.signal_id][0], signal.validity_from),
                    max(traffic_light_lanes[signal.signal_id][0], signal.validity_to),
                )
            else:
                traffic_light_lanes[signal.signal_id] = (signal.validity_to, signal.validity_from)

def evaluate_center_elevation(elev_records, s: float) -> float:
    """
    
    according to the elevation_profile.elevations list (records are in ascending order of start_pos),
    find which segment polynomial s falls into, interpolate the polynomial of that segment, and return the centerline height.
    It is completely equivalent to ParametricLane.calc_elevation_central.
    :param elev_records: List of ElevationRecord (each has .start_pos and .polynomial_coefficients)
    :param s: Current longitudinal coordinate of the reference line
    :return: Centerline height z_center
    """
    if not elev_records:
        return 0.0

    # find the index of the last element less than or equal to s
    starts = [rec.start_pos for rec in elev_records]
    idx = bisect.bisect_right(starts, s) - 1
    if idx < 0:
        # If s is smaller than the first segment, take the a value of the first segment's polynomial at ds = 0
        rec = elev_records[0]
    else:
        rec = elev_records[idx]

    # rec.polynomial_coefficients = [a, b, c, d]
    a, b, c, d = rec.polynomial_coefficients
    ds = s - rec.start_pos
    return a + b * ds + c * ds * ds + d * ds * ds * ds


def evaluate_superelevation(sup_records, s: float) -> float:
    """
    
    according to the lateral_profile.superelevations list (records are in ascending order of start_pos),
    find which segment polynomial s falls into, interpolate the polynomial of that segment, and return the superelevation (in radians).
    It is completely equivalent to ParametricLane.calc_superelevation.
    :param sup_records: List of SuperelevationRecord (each has .start_pos and .polynomial_coefficients)
    :param s: Current longitudinal coordinate of the reference line
    :return: superelevation (in radians)
    """
    if not sup_records:
        return 0.0

    starts = [rec.start_pos for rec in sup_records]
    idx = bisect.bisect_right(starts, s) - 1
    if idx < 0:
        rec = sup_records[0]
    else:
        rec = sup_records[idx]

    a, b, c, d = rec.polynomial_coefficients
    ds = s - rec.start_pos
    return a + b * ds + c * (ds**2) + d * (ds**3)


def evaluate_shape_offset(shape_records, s: float, lateral_dist: float) -> float:
    """
    
    according to the lateral_profile.shapes list, each record represents a "cross-sectional shape" polynomial that takes effect at a certain start_pos,
    input the lateral_dist lateral distance into the corresponding Shape polynomial, and then interpolate according to s between the two shape segments.
    It is completely equivalent to ParametricLane.calc_shape.
    :param shape_records: List of ShapeCrossSectionRecord (each has .start_pos, .start_pos_t, .polynomial_coefficients)
                             where .start_pos indicates the s at which this cross-section takes effect,
                             .start_pos_t indicates the starting lateral t value of the polynomial "in this cross-section".
    :param s: Current longitudinal coordinate of the reference line
    :param lateral_dist: Lateral distance |t| from the reference line (centerline) to the current point to be calculated
    :return: shape height value at (s,
    """
    if not shape_records:
        return 0.0

    # find the shape sections before and after s
    s_list = sorted({rec.start_pos for rec in shape_records})
    idx_s = bisect.bisect_right(s_list, s) - 1

    # if s is smaller than the first start_pos, there is no back section; if s is greater than the last, there is no front section
    if idx_s < 0:
        back_s = None
        back_shapes = []
        front_s = s_list[0]
        front_shapes = [rec for rec in shape_records if rec.start_pos == front_s]
    elif idx_s >= len(s_list) - 1:
        # s is after the last section
        back_s = s_list[-1]
        back_shapes = [rec for rec in shape_records if rec.start_pos == back_s]
        front_shapes = []
    else:
        back_s = s_list[idx_s]
        front_s = s_list[idx_s + 1]
        back_shapes = [rec for rec in shape_records if rec.start_pos == back_s]
        front_shapes = [rec for rec in shape_records if rec.start_pos == front_s]

    def lateral_polynomial_value(lateral, recs_at_same_s):
        """
        
        For multiple shape cross-sections at the same start_pos (with different start_pos_t),
        first find which lateral interval [start_pos_t_i, start_pos_t_{i+1}) the lateral_dist falls into,
        then use the corresponding polynomial to interpolate the lateral_dist.
        """
        # first sort by rec.start_pos_t in ascending order
        recs_at_same_s = sorted(recs_at_same_s, key=lambda r: r.start_pos_t)
        t_list = [r.start_pos_t for r in recs_at_same_s]
        # find the index of the last element less than or equal to lateral
        idx_t = bisect.bisect_right(t_list, lateral) - 1
        if idx_t < 0:
            # If the lateral coordinate is smaller than the first t_start, return 0
            return 0.0
        if idx_t >= len(recs_at_same_s) - 1:
            rec = recs_at_same_s[-1]
        else:
            #if lateral < next rec.start_pos_t, use current rec; otherwise also use current rec
            rec = recs_at_same_s[idx_t]

        a, b, c, d = rec.polynomial_coefficients
        dt = lateral - rec.start_pos_t
        return a + b * dt + c * (dt**2) + d * (dt**3)

    #calculate the shape height values of back and front
    if back_s is None:
        back_height = 0.0
    else:
        back_height = lateral_polynomial_value(lateral_dist, back_shapes)

    if not front_shapes:
        front_height = 0.0
        front_s = back_s
    else:
        front_height = lateral_polynomial_value(lateral_dist, front_shapes)

    # if within the same section (back_s == front_s), directly return that value
    if back_s == front_s or front_s is None:
        return back_height

    # or do a linear interpolation between back_s and front_s
    #when s changes, the shape cross-section smoothly transitions from back_shapes to front_shapes
    return float(np.interp(s, [back_s, front_s], [back_height, front_height]))

def calculate_road_surface_height(road: Road, s: float, t: float) -> float:
    """
    
    Return the road surface height at longitudinal s and lateral offset t (excluding the zOffset of
    a specific object),
    equivalent to the part in ParametricLane.calc_border_height("inner", s, …)[0] that "does not add lane‐local <height>".  
    :param road: Road object with elevation_profile and lateral_profile
    :param s:   Longitudinal coordinate on the reference line
    :param t:   Lateral offset, usually negative on the right side and positive on the left side
    :return:    z_surface = centerline elevation + superelevation/shape projection
    """
    # centerline elevation (polynomial interpolation)
    z_center = evaluate_center_elevation(road.elevation_profile.elevations, s)

    # superelevation (polynomial interpolation)
    sup = evaluate_superelevation(road.lateral_profile.superelevations, s)

    # calculate the corresponding shape offset
    # lateral distance from reference line to the point to be calculated
    lateral_dist = abs(t)
    # shape height value at (s, lateral_dist)
    z_shape = evaluate_shape_offset(road.lateral_profile.shapes, s, lateral_dist)

    # project superelevation and shape to height:
    # project method is exactly the same as correction_due_to_superelevation in ParametricLane.calc_border_height:
    proj_sup = np.sin(sup) * (lateral_dist - np.tan(sup) * z_shape)
    proj_shape = z_shape / np.cos(sup) if np.cos(sup) != 0.0 else 0.0
    height_to_ref_line = proj_sup + proj_shape

    # left side t>0 take positive, right side t<0 take negative
    side_coeff = 1.0 if t >= 0.0 else -1.0

    # final road surface height
    return z_center + height_to_ref_line * side_coeff
