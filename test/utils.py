# -*- coding: utf-8 -*-

"""Utility methods needed for unit testing."""

tolerance = 0.1


def _print_fail(topic, arg_1, arg_2):
    print("{} fail!\n\n{}\n\n{}\n".format(topic, arg_1, arg_2))


def elements_equal(e1, e2) -> bool:
    """Test if two element trees are the same.

    :param e1: tree 1
    :param e2: tree 2
    :returns: true if they are equal in tag, text, tail,
    attrib and if children are equal, else false
    :rtype: bool

    """

    if e1.tag != e2.tag:
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
    if e1.tail != e2.tail:
        _print_fail("tail", e1.tail, e2.tail)
        return False
    if e1.attrib != e2.attrib:
        _print_fail("attrib", e1.attrib, e2.attrib)
        return False
    if len(e1) != len(e2):
        _print_fail("length", len(e1), len(e2))
        return False
    return all(elements_equal(c1, c2) for c1, c2 in zip(e1, e2))
