# Eclipse SUMO, Simulation of Urban MObility; see https://eclipse.org/sumo
# Copyright (C) 2011-2017 German Aerospace Center (DLR) and others.
# This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v2.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v20.html

# @file    connection.py
# @author  Daniel Krajzewicz
# @author  Laura Bieker
# @author  Karol Stosiek
# @author  Michael Behrisch
# @author  Jakob Erdmann
# @date    2011-11-28
# @version $Id$

from xml.etree import cElementTree as ET
import numpy as np
from typing import Optional


def _to_shape_string(shape: np.ndarray) -> str:
    """
    Convert a collection of points from format shape to string
    :param shape:
    :return: the same shape but in string format
    """
    return " ".join([",".join([str(p) for p in v]) for v in shape])


def _from_shape_string(shape: str) -> np.ndarray:
    """
    Convert a shape string to a ndarray
    :param shape:
    :return:
    """
    return np.asarray([[float(c) for c in coords.split(",")] for coords in shape.split(" ")],
                      dtype=float)


class Connection:
    # constants as defined in sumo/src/utils/xml/SUMOXMLDefinitions.cpp
    LINKDIR_STRAIGHT = "s"
    LINKDIR_TURN = "t"
    LINKDIR_LEFT = "l"
    LINKDIR_RIGHT = "r"
    LINKDIR_PARTLEFT = "L"
    LINKDIR_PARTRIGHT = "R"
    """edge connection for a sumo network"""

    def __init__(self,
                 fromEdge,
                 toEdge,
                 fromLane,
                 toLane,
                 direction=None,
                 tls=None,
                 tllink=None,
                 state=None,
                 viaLaneID=None,
                 shape: Optional[np.ndarray] = None,
                 keepClear=None,
                 contPos=None):
        self._from = fromEdge
        self._to = toEdge
        self._fromLane = int(fromLane)
        self._toLane = int(toLane)
        self._direction = direction
        self._tls = tls
        self._tlLink = tllink
        self._state = state
        self._via = viaLaneID
        self._shape = shape
        self._keepClear = keepClear
        self._contPos = contPos

    def __str__(self):
        return str(self.toXML())

    def getFrom(self):
        return self._from

    def getTo(self):
        return self._to

    def getFromLane(self):
        return self._fromLane

    def getToLane(self):
        return self._toLane

    def getViaLaneID(self):
        return self._via

    def getDirection(self):
        return self._direction

    def getTLSID(self):
        return self._tls

    def getTLLinkIndex(self):
        return self._tlLink

    def getJunctionIndex(self):
        return self._from.getToNode().getLinkIndex(self)

    def getJunction(self):
        return self._from.getToNode()

    def getState(self):
        return self._state

    def getShape(self):
        return self._shape

    def toXML(self) -> bytes:
        """
        Converts this connection to it's xml representation
        """
        c = ET.Element("connection")
        c.set("from", str(self._from))
        c.set("to", str(self._to))
        c.set("fromLane", str(self._fromLane))
        c.set("toLane", str(self._toLane))
        if self._via is not None:
            c.set("via", str(self._via))
        if self._direction is not None:
            c.set("dir", str(self._direction))
        if self._tls is not None:
            c.set("tl", str(self._tls))
        if self._tlLink is not None:
            c.set("linkIndex", str(self._tlLink))
        if self._state is not None:
            c.set("state", str(self._state))
        if self._shape is not None:
            c.set("shape", _to_shape_string(self._shape))
        if self._keepClear is not None:
            c.set("keepClear", "true" if self._keepClear else "false")
        if self._contPos is not None:
            c.set("contPos", str(self._contPos))

        return ET.tostring(c)
