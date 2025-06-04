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

        # ——— ①：先计算参考线在 s 处的平面坐标和切线角度 ———
        ref_pos, tangent, _, _ = road.plan_view.calc(
            signal.s, compute_curvature=False
        )
        # 把信号沿正交方向偏移到 (x_t, y_t)
        x_t = ref_pos[0] + signal.t * np.cos(tangent + np.pi/2)
        y_t = ref_pos[1] + signal.t * np.sin(tangent + np.pi/2)

        # ——— ②：调用下面写好的 calculate_road_surface_height —— 
        z_surface = calculate_road_surface_height(road, signal.s, signal.t)

        # ——— ③：再加上信号自身的 zOffset 得到最终 Z ———
        z_t = z_surface + signal.zOffset

        position = np.array([x_t, y_t, z_t])
        """
        position, tangent, _, _ = road.plan_view.calc(signal.s, compute_curvature=False)
        elevation = calculate_elevation(road.elevation_profile, signal.s)#here elevation = z coordinate
        position = np.array(
            [
                position[0] + signal.t * np.cos(tangent + np.pi / 2),
                position[1] + signal.t * np.sin(tangent + np.pi / 2),
                elevation + signal.zOffset,#build xyz coordinate with zOffset
            ]
        )"""
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
    根据 elevation_profile.elevations 列表（记录按 start_pos 升序），
    找到 s 落在哪段多项式里，并对该段多项式做插值，返回中心线高度。
    与 ParametricLane.calc_elevation_central 完全等价。
    :param elev_records: List of ElevationRecord（每个有 .start_pos 和 .polynomial_coefficients）
    :param s: 当前参考线纵向坐标
    :return: 中心线高度 z_center
    """
    if not elev_records:
        return 0.0

    # 找出最后一个 start_pos <= s 的索引
    starts = [rec.start_pos for rec in elev_records]
    idx = bisect.bisect_right(starts, s) - 1
    if idx < 0:
        # s 比第一段还要小，直接取第一段多项式在 ds = 0 时的 a 值
        rec = elev_records[0]
    else:
        rec = elev_records[idx]

    # rec.polynomial_coefficients = [a, b, c, d]
    a, b, c, d = rec.polynomial_coefficients
    ds = s - rec.start_pos
    return a + b * ds + c * ds * ds + d * ds * ds * ds


def evaluate_superelevation(sup_records, s: float) -> float:
    """
    根据 lateral_profile.superelevations 列表，找到 s 落在哪段 superelevation 上，
    用该段 [a,b,c,d] 在 (s - start_pos) 处做多项式插值，返回 superelevation（单位：弧度）。
    与 ParametricLane.calc_superelevation 等价。
    :param sup_records: List of SuperelevationRecord（每个有 .start_pos 和 .polynomial_coefficients）
    :param s: 参考线纵向坐标
    :return: superelevation（弧度）
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
    根据 lateral_profile.shapes 列表，每条记录代表在某个 start_pos 上开始生效的“横断面形状”多项式，
    将 lateral_dist 这个横向距离投入到对应的 Shape 多项式里，再根据 s 在两段 shape 之间插值。
    完全等价于 ParametricLane.calc_shape。
    :param shape_records: List of ShapeCrossSectionRecord（每个有 .start_pos, .start_pos_t, .polynomial_coefficients）
                             其中 .start_pos 表示此断面在哪个 s 开始生效，
                             .start_pos_t 表示“此横断面里”多项式的起始横向 t 值。
    :param s: 当前参考线纵向坐标
    :param lateral_dist: 从参考线（中心线）到当前要计算点的横向距离 |t|
    :return: 该 (s, lateral_dist) 处的 shape 高度值
    """
    if not shape_records:
        return 0.0

    # 1) 找出在 s 处，前一段以及后一段的 shape 断面
    s_list = sorted({rec.start_pos for rec in shape_records})
    idx_s = bisect.bisect_right(s_list, s) - 1

    # 如果 s 比第一个断面 start_pos 还要小，视为没有 back 断面；如果 s 大于最后一个，视为没有 front 断面
    if idx_s < 0:
        back_s = None
        back_shapes = []
        front_s = s_list[0]
        front_shapes = [rec for rec in shape_records if rec.start_pos == front_s]
    elif idx_s >= len(s_list) - 1:
        # s 在最后一个断面之后
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
        对于同一个 start_pos 上可能有多个 shape 断面数据（不同的 start_pos_t），
        先在这些 recs_at_same_s 中，找出落在哪一段横向区间 [start_pos_t_i, start_pos_t_{i+1})，
        然后用对应多项式对 lateral_dist 做插值。
        """
        # 1) 先按 rec.start_pos_t 升序
        recs_at_same_s = sorted(recs_at_same_s, key=lambda r: r.start_pos_t)
        t_list = [r.start_pos_t for r in recs_at_same_s]
        # 找到最后一个 t_start <= lateral 的段
        idx_t = bisect.bisect_right(t_list, lateral) - 1
        if idx_t < 0:
            # 横向坐标比第一个 t_start 还小，返回 0
            return 0.0
        if idx_t >= len(recs_at_same_s) - 1:
            rec = recs_at_same_s[-1]
        else:
            # 如果 lateral < 下一条 rec.start_pos_t，就用当前 rec；否则也用当前 rec
            rec = recs_at_same_s[idx_t]

        a, b, c, d = rec.polynomial_coefficients
        dt = lateral - rec.start_pos_t
        return a + b * dt + c * (dt**2) + d * (dt**3)

    # 2) 计算 back 和 front 的 shape 高度值
    if back_s is None:
        back_height = 0.0
    else:
        back_height = lateral_polynomial_value(lateral_dist, back_shapes)

    if not front_shapes:  # 没有 front，则此处 0
        front_height = 0.0
        front_s = back_s
    else:
        front_height = lateral_polynomial_value(lateral_dist, front_shapes)

    # 3) 如果在同一个断面之内（back_s == front_s），直接返回该值
    if back_s == front_s or front_s is None:
        return back_height

    # 4) 否则，在 [back_s, front_s] 间线性插值
    # 当 s 变化时，shape 断面从 back_shapes 平滑过渡到 front_shapes
    return float(np.interp(s, [back_s, front_s], [back_height, front_height]))

def calculate_road_surface_height(road: Road, s: float, t: float) -> float:
    """
    返回道路在纵向 s、横向偏移 t 处的道路表面高度（不含某一具体物体的 zOffset），
    等价于 ParametricLane.calc_border_height("inner", s, …)[0] 里“不要加 lane‐local <height>”那部分。

    :param road: Road 对象，具有 elevation_profile 和 lateral_profile
    :param s:   参考线上的纵向坐标
    :param t:   横向偏移，右侧常为负，左侧常为正
    :return:    z_surface = 中心线高程 + superelevation/shape 投影
    """
    # 1) 中心线基准高程（多项式插值）
    z_center = evaluate_center_elevation(road.elevation_profile.elevations, s)

    # 2) superelevation 部分
    sup = evaluate_superelevation(road.lateral_profile.superelevations, s)

    # 3) 计算对应 shape 偏移
    #    先计算横向距离线，到中心线上 (abs(t))
    lateral_dist = abs(t)
    #    shape 投影高度
    z_shape = evaluate_shape_offset(road.lateral_profile.shapes, s, lateral_dist)

    # 4) 把 superelevation 和 shape 投影到高度： 
    #    投影方式与 ParametricLane.calc_border_height 中的 correction_due_to_superelevation 完全一致：
    proj_sup = np.sin(sup) * (lateral_dist - np.tan(sup) * z_shape)
    proj_shape = z_shape / np.cos(sup) if np.cos(sup) != 0.0 else 0.0
    height_to_ref_line = proj_sup + proj_shape

    # 5) 左侧 t>0 取正，右侧 t<0 取负
    side_coeff = 1.0 if t >= 0.0 else -1.0

    # 6) 最终道路表面高度
    return z_center + height_to_ref_line * side_coeff
