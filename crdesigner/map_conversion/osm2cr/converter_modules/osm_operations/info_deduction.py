"""
This module provides the main two methods to complete missing info of roads.
"""

from math import ceil
from typing import Tuple

from crdesigner.common.config.osm_config import osm_config as config
from crdesigner.map_conversion.osm2cr.converter_modules.utility.custom_types import (
    Assumption_info,
    Road_info,
)


def extract_missing_info(info: Road_info) -> Tuple[Road_info, int]:
    """
    deduces missing info if possible

    :param info: information about the road
    :return: the supplemented info and an indicator if a flip of the road is necessary
    """
    flip = False
    (
        nr_of_lanes,
        forward_lanes,
        backward_lanes,
        oneway,
        turn_lanes,
        turn_lanes_forward,
        turn_lanes_backward,
    ) = info

    # turn_lanes in oneway
    if turn_lanes_forward is None and turn_lanes is not None and oneway:
        turn_lanes_forward = turn_lanes

    # number of lanes given turn_lanes override if necessary
    if turn_lanes_forward is not None:
        forward_lanes = len(turn_lanes_forward)
    if turn_lanes_backward is not None:
        backward_lanes = len(turn_lanes_backward)

    # number of lanes given forward_lanes and backward_lanes
    if forward_lanes is not None and backward_lanes is not None:
        if nr_of_lanes is None:
            nr_of_lanes = forward_lanes + backward_lanes
        elif nr_of_lanes < forward_lanes + backward_lanes:
            nr_of_lanes = forward_lanes + backward_lanes

    # number of backward and forward_lanes given the respective other
    if nr_of_lanes is not None:
        if backward_lanes is None and forward_lanes is not None:
            if forward_lanes <= nr_of_lanes:
                backward_lanes = nr_of_lanes - forward_lanes
            else:
                backward_lanes = 0
                nr_of_lanes = forward_lanes + backward_lanes
        if forward_lanes is None and backward_lanes is not None:
            if backward_lanes <= nr_of_lanes:
                forward_lanes = nr_of_lanes - backward_lanes
            else:
                forward_lanes = 0
                nr_of_lanes = forward_lanes + backward_lanes

    # number of backward_lanes in oneway
    if oneway:
        if backward_lanes is not None and backward_lanes > 0:
            # lane information inconsistent overriding oneway
            print("oneway has backwardlanes")
            oneway = False
        else:
            if backward_lanes is None:
                backward_lanes = 0
            if forward_lanes is None and nr_of_lanes is not None:
                forward_lanes = nr_of_lanes

    # assert nr_of_lanes == forward_lanes + backward_lanes
    if forward_lanes is not None:
        if nr_of_lanes is not None:
            if not forward_lanes + backward_lanes == nr_of_lanes:
                # lane information inconsistent, overriding total number
                print(
                    "lane error: {} forward lanes, {} backwardlanes and  {} total lanes, oneway: {}".format(
                        forward_lanes, backward_lanes, nr_of_lanes, oneway
                    )
                )
                nr_of_lanes = forward_lanes + backward_lanes
        elif backward_lanes is not None:
            nr_of_lanes = forward_lanes + backward_lanes
        assert forward_lanes >= 0
    if backward_lanes is not None:
        assert backward_lanes >= 0
    if nr_of_lanes is not None:
        assert nr_of_lanes >= 0

    # create oneway info if missing
    if oneway is None:
        if nr_of_lanes is not None:
            if forward_lanes is not None and forward_lanes == nr_of_lanes:
                oneway = True
            elif backward_lanes is not None and backward_lanes == nr_of_lanes:
                oneway = True
                print("edge of oneway is directed backwards, flipping direction")
                # directions are flipped
                flip = True
                forward_lanes, backward_lanes = backward_lanes, forward_lanes
                turn_lanes_forward, turn_lanes_backward = (
                    turn_lanes_backward,
                    turn_lanes_forward,
                )
        if turn_lanes_forward is not None and turn_lanes_backward is not None:
            oneway = False

    return (
        (
            nr_of_lanes,
            forward_lanes,
            backward_lanes,
            oneway,
            turn_lanes,
            turn_lanes_forward,
            turn_lanes_backward,
        ),
        flip,
    )


def assume_missing_info(lane_info: Road_info, roadtype: str) -> Tuple[Road_info, Assumption_info]:
    """
    assumes still missing info

    :param lane_info:
    :param roadtype: type of the road
    :return: completed info and info about assumptions
    """
    (
        nr_of_lanes,
        forward_lanes,
        backward_lanes,
        oneway,
        turnlanes,
        turnlanes_forward,
        turnlanes_backward,
    ) = lane_info
    lane_nr_assumed, lanes_assumed, oneway_assumed = False, False, False

    # oneway
    if oneway is None:
        oneway = False
        oneway_assumed = True

    # number of lanes
    if nr_of_lanes is None:
        if forward_lanes is None and backward_lanes is None:
            if oneway:
                nr_of_lanes = ceil(config.LANECOUNTS[roadtype] / 2)
            else:
                nr_of_lanes = config.LANECOUNTS[roadtype]
        else:
            sum = 0
            if forward_lanes is not None:
                sum += forward_lanes
            if backward_lanes is not None:
                sum += backward_lanes
            nr_of_lanes = max(
                sum + ceil(config.LANECOUNTS[roadtype] / 2), config.LANECOUNTS[roadtype]
            )
            if oneway:
                nr_of_lanes = max(1, ceil(nr_of_lanes / 2))
        lane_nr_assumed = True

    # number of forward and backward lanes
    if forward_lanes is None or backward_lanes is None:
        lanes_assumed = True
        if oneway:
            backward_lanes = 0
            forward_lanes = nr_of_lanes
        else:
            if forward_lanes is not None:
                backward_lanes = nr_of_lanes - forward_lanes
            elif backward_lanes is not None:
                forward_lanes = nr_of_lanes - backward_lanes
            else:
                backward_lanes = int(nr_of_lanes / 2)
                forward_lanes = nr_of_lanes - backward_lanes
    lane_info = (
        nr_of_lanes,
        forward_lanes,
        backward_lanes,
        oneway,
        turnlanes,
        turnlanes_forward,
        turnlanes_backward,
    )
    assumptions = lane_nr_assumed, lanes_assumed, oneway_assumed

    # assert number of turnlanes matches number of lanes, this should never happen!
    if turnlanes_forward is not None and not len(turnlanes_forward) == forward_lanes:
        print(
            "internal inconsistency! turnlanes {} do not match with {} lanes".format(
                turnlanes_forward, forward_lanes
            )
        )
    if turnlanes_backward is not None and not len(turnlanes_backward) == backward_lanes:
        print(
            "internal inconsistency! turnlanes {} do not match with {} lanes".format(
                turnlanes_backward, backward_lanes
            )
        )
    return lane_info, assumptions
