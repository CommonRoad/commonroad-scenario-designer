"""
This module holds the classes required for the intermediate format
"""

__author__ = "Behtarin Ferdousi"

from crdesigner.map_conversion.common import geometry


class Node:
    """
    Class to represent the nodes in the intermediate format
    """

    def __init__(self, node_id: int, point: geometry.Point):
        """
        Initialize a node element

        :param node_id: unique id for node
        :type node_id: int
        :param point: position of the node
        :type point: geometry.position
        """

        self.id = node_id
        self.point = point
