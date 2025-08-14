from typing import Any, Iterable

from commonroad.scenario.lanelet import Lanelet
from commonroad.scenario.traffic_light import TrafficLight
from commonroad.scenario.traffic_sign import TrafficSign


def equal(val_0: Any, val_1: Any) -> bool:
    """
    Checks whether the first value is equal to the second value.

    :param val_0: First value.
    :param val_1: Second value.
    :return: Boolean indicates whether the first value is equal to the second value.
    """
    return val_0 == val_1


def unequal(val_0: Any, val_1: Any) -> bool:
    """
    Checks whether the first value is unequal to the second value.

    :param val_0: First value.
    :param val_1: Second value.
    :return: Boolean indicates whether the first value is unequal to the second value.
    """
    if (
        isinstance(val_0, Lanelet)
        or isinstance(val_0, TrafficSign)
        or isinstance(val_0, TrafficLight)
    ):
        return val_0 is not val_1
    else:
        return val_0 != val_1


def less(val_0: Any, val_1: Any) -> bool:
    """
    Checks whether the first value is less than the second value.

    :param val_0: First value.
    :param val_1: Second value.
    :return: Boolean indicates whether the first values is less than the second value.
    """
    return val_0 < val_1


def greater(val_0: Any, val_1: Any) -> bool:
    """
    Checks whether the first value is greater than the second value.

    :param val_0: First value.
    :param val_1: Second value.
    :return: Boolean indicates whether the first value is greater than the second value.
    """
    return val_0 > val_1


def less_equal(val_0: Any, val_1: Any) -> bool:
    """
    Checks whether the first value is less than or equal to the second value.

    :param val_0: First value.
    :param val_1: Second value.
    :return: Boolean indicates whether the first value is less than or equal to the second value.
    """
    return val_0 <= val_1


def greater_equal(val_0: Any, val_1: Any) -> bool:
    """
    Checks whether the first value is greater than or equal to the second value.

    :param val_0: First value.
    :param val_1: Second value.
    :return: Boolean indicates whether the first value is greater than or equal to the second value.
    """
    return val_0 >= val_1


def contains(vals: Iterable[Any], val: Any) -> bool:
    """
    Checks whether value is contained by a set of values.

    :param vals: Values.
    :param val: Value.
    :return: Boolean indicates whether the value is contained by a set of values.
    """
    return val in vals
