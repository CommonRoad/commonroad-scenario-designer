import itertools
from typing import List, Iterable
import logging
from lxml import etree

tolerance = 0.1


def _print_fail(topic: str, arg_1: str, arg_2: str):
    logging.error("{} fail: arg1: {}, arg2: {}\n".format(topic, arg_1, arg_2))


def elements_equal(e1: etree.Element, e2: etree.Element) -> bool:
    """Test if two element trees are the same.

    :param e1: tree 1
    :param e2: tree 2
    :returns: true if they are equal in tag, text, tail,
    attrib and if children are equal, else false
    :rtype: bool

    """

    if e1.tag != e2.tag and e1.text is not None and e2.text is not None:
        _print_fail("tag", e1.tag, e2.tag)
        return False
    if e1.text != e2.text and e1.text is not None and e2.text is not None:
        try:
            if abs(float(e1.text) - float(e2.text)) < tolerance:
                pass
            else:
                _print_fail("text", e1.text, e2.text)
                return False
        except ValueError:
            return False
    for name, value in e1.attrib.items():
        if e2.attrib.get(name) != value:
            try:  # Only accuracy error
                if abs(float(e2.attrib.get(name)) - float(value)) > tolerance:
                    return False
            except ValueError:
                return False
    for name in e2.attrib.keys():
        if name not in e1.attrib:
            logging.error(f"e2 has an attribute e1 is missing: {name}")
            return False
    if e1.tail != e2.tail:
        _print_fail("tail", e1.tail, e2.tail)
        return False

    return child_elements_equal(e1, e2)


def child_elements_equal(e1: etree.Element, e2: etree.Element) -> bool:
    """Compare the children of two element trees.

    The order of the successor and predecessor children is not relevant.

    Args:
      e1: first element tree
      e2: second element tree
    Return:
      True if they are equal besides of order of successors and predecessors,
        else False.
    """
    ch1 = e1.xpath(("./*[local-name() != 'predecessor' and local-name() != 'successor' and "
                   "local-name() != 'userOneWay' and local-name() != 'trafficSign'"
                    "and local-name() != 'userBidirectional' and local-name() != 'laneletType']"))
    ch2 = e2.xpath("./*[local-name() != 'predecessor' and local-name() != 'successor' "
                   "and local-name() != 'userOneWay' and local-name() != 'trafficSign'"
                   "and local-name() != 'userBidirectional' and local-name() != 'laneletType']")
    ch1_succ = e1.xpath("./*[local-name() = 'successor']")
    ch2_succ = e2.xpath("./*[local-name() = 'successor']")
    ch1_pred = e1.xpath("./*[local-name() = 'predecessor']")
    ch2_pred = e2.xpath("./*[local-name() = 'predecessor']")
    ch1_users = e1.xpath("./*[local-name() = 'userOneWay']")
    ch2_users = e2.xpath("./*[local-name() = 'userOneWay']")
    ch1_traffic_sign = e1.xpath("./*[local-name() = 'trafficSign']")
    ch2_traffic_sign = e2.xpath("./*[local-name() = 'trafficSign']")
    ch1_users_bi = e1.xpath("./*[local-name() = 'userBidirectional']")
    ch2_users_bi = e2.xpath("./*[local-name() = 'userBidirectional']")
    ch1_users_lanelet_types = e1.xpath("./*[local-name() = 'laneletType']")
    ch2_users_lanelet_types = e2.xpath("./*[local-name() = 'laneletType']")

    if len(ch1) != len(ch2):
        _print_fail("length", str(len(ch1)),  str(len(ch2)))
        return False
    if len(ch1_users) != len(ch2_users):
        _print_fail("length", str(len(ch1_users)),  str(len(ch2_users)))
        return False
    if len(ch1_succ) != len(ch2_succ):
        _print_fail("length",  str(len(ch1_succ)),  str(len(ch2_succ)))
        return False
    if len(ch1_pred) != len(ch2_pred):
        _print_fail("length",  str(len(ch1_pred)),  str(len(ch2_pred)))
        return False
    # for ty1 in ch1_users_lanelet_types:
    #     match = False
    #     for ty2 in ch2_users_lanelet_types:
    #         match = elements_equal(ty1, ty2)
    #         if match:
    #             break
    #     if not match:
    #         return False
    for c1, c2 in zip(ch1, ch2):
        if not elements_equal(c1, c2):  # i = 0
            return False
    if not one_permutation_matches(
        ch1_pred, itertools.permutations(ch2_pred)
    ) or not one_permutation_matches(ch1_succ, itertools.permutations(ch2_succ)) or \
            not one_permutation_matches(ch1_users, itertools.permutations(ch2_users)) \
            or not one_permutation_matches(ch1_traffic_sign, itertools.permutations(ch2_traffic_sign))\
            or not one_permutation_matches(ch1_users_bi, itertools.permutations(ch2_users_bi)):
        return False
    return True


def one_permutation_matches(
    list1: List[etree.Element], permutations: Iterable[List[etree.Element]]
):
    """Check whether list1 is equal to one of the permutations.

    Args:
      list1: List of element trees.
      permutations: Iterable which contains all permutations of another
        list of element trees.
    Returns:
      True if list1 matches one of the permutations, else False.
    """
    for perm in permutations:
        if all(elements_equal(c1, c2) for c1, c2 in zip(perm, list1)):
            return True

    return False
