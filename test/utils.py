# -*- coding: utf-8 -*-

"""Utility methods needed for unit testing."""

import itertools
from typing import List, Iterable

from lxml import etree


tolerance = 0.1


def _print_fail(topic: str, arg_1: str, arg_2: str):
    print("{} fail!\n\n{}\n\n{}\n".format(topic, arg_1, arg_2))


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
    if e1.text != e2.text:
        try:
            if abs(float(e1.text) - float(e2.text)) < tolerance:
                # print("Only accuracy error!")
                pass
            else:
                _print_fail("text", e1.text, e2.text)
                return False
        except ValueError:
            _print_fail("text", e1.text, e2.text)
            return False
    for name, value in e1.attrib.items():
        if e2.attrib.get(name) != value or isinstance(value, float) and isinstance(e2.attrib.get(name), float) and not float(e2.attrib.get(name)) - float(value) < 1e-9:
            print(
                f"Attributes do not match: {name}={value}, {name}={e2.attrib.get(name)}"
            )
            return False
    for name in e2.attrib.keys():
        if name not in e1.attrib:
            print(f"e2 has an attribute e1 is missing: {name}")
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
    ch1 = e1.xpath("./*[local-name() != 'predecessor' and local-name() != 'successor']")
    ch2 = e2.xpath("./*[local-name() != 'predecessor' and local-name() != 'successor']")
    ch1_succ = e1.xpath("./*[local-name() = 'successor']")
    ch2_succ = e2.xpath("./*[local-name() = 'successor']")
    ch1_pred = e1.xpath("./*[local-name() = 'predecessor']")
    ch2_pred = e2.xpath("./*[local-name() = 'predecessor']")
    if len(ch1) != len(ch2):
        _print_fail("length", len(ch1), len(ch2))
        return False
    if len(ch1_succ) != len(ch2_succ):
        _print_fail("length", len(ch1_succ), len(ch2_succ))
        return False
    if len(ch1_pred) != len(ch2_pred):
        _print_fail("length", len(ch1_pred), len(ch2_pred))
        return False
    for c1, c2 in zip(ch1, ch2):
        if not elements_equal(c1, c2):  # i = 0
            return False
    if not one_permutation_matches(
        ch1_pred, itertools.permutations(ch2_pred)
    ) or not one_permutation_matches(ch1_succ, itertools.permutations(ch2_succ)):
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
