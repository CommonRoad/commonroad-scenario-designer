# Eclipse SUMO, Simulation of Urban MObility; see https://eclipse.org/sumo
# Copyright (C) 2011-2017 German Aerospace Center (DLR) and others.
# This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v2.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v20.html

# @file    lane.py
# @author  Daniel Krajzewicz
# @author  Laura Bieker
# @author  Karol Stosiek
# @author  Michael Behrisch
# @author  Jakob Erdmann
# @date    2011-11-28
# @version $Id$

from xml.etree import cElementTree as ET
import sumolib.geomhelper

from .constants import SUMO_VEHICLE_CLASSES


def addJunctionPos(shape, fromPos, toPos):
    """Extends shape with the given positions in case they differ from the
    existing endpoints. assumes that shape and positions have the same dimensionality"""
    result = list(shape)
    if fromPos != shape[0]:
        result = [fromPos] + result
    if toPos != shape[-1]:
        result.append(toPos)
    return result


class Lane:
    """ Lanes from a sumo network """

    def __init__(self,
                 edge,
                 speed: float,
                 length: float,
                 width: float,
                 allow=[],
                 disallow=[],
                 shape=[]):
        self._edge = edge
        self._speed = speed
        self._length = length
        self._width = 3.2 if width == 'default' else width  # added by Lisa, 3.2 is sumo default lane width
        self._shape = shape
        self._shape3D = None
        self._shapeWithJunctions = None
        self._shapeWithJunctions3D = None
        self._outgoing = []
        self._adjacent_opposite = None  # added by Lisa
        self._params = {}
        self._allowed = []
        self._disallowed = []
        if allow and disallow:
            self._allowed = allow
            self._disallowed = disallow
        elif allow:
            self._disallowed = list(set(SUMO_VEHICLE_CLASSES) - set(allow))
        elif disallow:
            self._allowed = list(set(SUMO_VEHICLE_CLASSES) - set(disallow))

        edge.addLane(self)

    @property
    def speed(self) -> float:
        return self._speed

    @speed.setter
    def speed(self, speed: float):
        self._speed = speed

    def getSpeed(self):
        return self._speed

    def getLength(self):
        return self._length

    def getWidth(self):
        return self._width

    def setAdjacentOpposite(self, opposite_lane_id):
        self._adjacent_opposite = opposite_lane_id

    def getAdjacentOpposite(self):
        return self._adjacent_opposite

    def setShape(self, shape):
        """Set the shape of the lane

        shape must be a list containing x,y,z coords as numbers
        to represent the shape of the lane
        """
        # for pp in shape:
        #    if len(pp) != 3:
        #        raise ValueError('shape point must consist of x,y,z')

        # self._shape3D = shape
        # self._shape = [(x, y) for x, y, z in shape]
        self._shape = shape

    def getShape(self, includeJunctions=False):
        """Returns the shape of the lane in 2d.

        This function returns the shape of the lane, as defined in the net.xml
        file. The returned shape is a list containing numerical
        2-tuples representing the x,y coordinates of the shape points.

        For includeJunctions=True the returned list will contain
        additionally the coords (x,y) of the fromNode of the
        corresponding edge as first element and the coords (x,y)
        of the toNode as last element.

        For internal lanes, includeJunctions is ignored and the unaltered
        shape of the lane is returned.
        """

        if includeJunctions and not self._edge.isSpecial():
            if self._shapeWithJunctions is None:
                self._shapeWithJunctions = addJunctionPos(
                    self._shape,
                    self._edge.getFromNode().getCoord(),
                    self._edge.getToNode().getCoord())
            return self._shapeWithJunctions
        return self._shape

    def getShape3D(self, includeJunctions=False):
        """Returns the shape of the lane in 3d.

        This function returns the shape of the lane, as defined in the net.xml
        file. The returned shape is a list containing numerical
        3-tuples representing the x,y,z coordinates of the shape points
        where z defaults to zero.

        For includeJunction=True the returned list will contain
        additionally the coords (x,y,z) of the fromNode of the
        corresponding edge as first element and the coords (x,y,z)
        of the toNode as last element.

        For internal lanes, includeJunctions is ignored and the unaltered
        shape of the lane is returned.
        """

        if includeJunctions and not self._edge.isSpecial():
            if self._shapeWithJunctions3D is None:
                self._shapeWithJunctions3D = addJunctionPos(
                    self._shape3D,
                    self._edge.getFromNode().getCoord3D(),
                    self._edge.getToNode().getCoord3D())
            return self._shapeWithJunctions3D
        return self._shape3D

    def getBoundingBox(self, includeJunctions=True):
        s = self.getShape(includeJunctions)
        xmin = s[0][0]
        xmax = s[0][0]
        ymin = s[0][1]
        ymax = s[0][1]
        for p in s[1:]:
            xmin = min(xmin, p[0])
            xmax = max(xmax, p[0])
            ymin = min(ymin, p[1])
            ymax = max(ymax, p[1])
        assert (xmin != xmax or ymin != ymax)
        return (xmin, ymin, xmax, ymax)

    def getClosestLanePosAndDist(self, point, perpendicular=False):
        return sumolib.geomhelper.polygonOffsetAndDistanceToPoint(
            point, self.getShape(), perpendicular)

    def getIndex(self):
        return self._edge._lanes.index(self)

    def getID(self):
        return f"{self._edge._id}_{self.getIndex()}"

    def getEdge(self):
        return self._edge

    def addOutgoing(self, conn):
        self._outgoing.append(conn)

    def getOutgoing(self):
        return self._outgoing

    def setParam(self, key, value):
        self._params[key] = value

    def getParam(self, key, default=None):
        return self._params.get(key, default)

    def getAllowed(self):  # added by Lea
        return self._allowed

    def getDisallowed(self):  # added by Chu
        return self._disallowed

    def toXML(self) -> str:
        """
        Converts this lane to it's xml representation
        """
        lane = ET.Element("lane")
        lane.set("index", str(self.getIndex()))
        if self.speed:
            lane.set("speed", str(self._speed))
        if self._length:
            lane.set("length", str(self._length))
        if len(self._shape) > 0:
            lane.set("shape", _to_shape_string(self._shape))
        if self._width:
            lane.set("width", str(self._width))
        if self._allowed:
            lane.set("allow", " ".join(self._allowed))
        if self._disallowed:
            lane.set("disallow", " ".join(self._disallowed))
        for k, v in self._params:
            lane.set(str(k), str(v))
        return ET.tostring(lane)


def _to_shape_string(shape):
    """
    Convert a collection of points from format shape  to string
    :param shape: a collection of point defining and edge
    :return: the same shape but in string format
    """
    return " ".join([",".join([str(pi) for pi in p]) for p in shape])
