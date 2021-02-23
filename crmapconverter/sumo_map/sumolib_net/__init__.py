# Eclipse SUMO, Simulation of Urban MObility; see https://eclipse.org/sumo
# Copyright (C) 2008-2017 German Aerospace Center (DLR) and others.
# This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v2.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v20.html

# @file    __init__.py
# @author  Daniel Krajzewicz
# @author  Laura Bieker
# @author  Karol Stosiek
# @author  Michael Behrisch
# @author  Jakob Erdmann
# @author  Robert Hilbrich
# @date    2008-03-27
# @version $Id$
"""
This file contains a content handler for parsing sumo network xml files.
It uses other classes from this module to represent the road network.
"""

from __future__ import print_function
from __future__ import absolute_import
import os
import math
from xml.sax import parse, handler
from collections import defaultdict
from typing import List, Dict, Tuple, Set, Optional, Callable, Union, TypeVar, Iterable
from copy import deepcopy, copy
import numpy as np

import sumolib
import sumolib.files

from xml.etree import cElementTree as ET
from enum import Enum, unique


class Net:
    """The whole sumo network."""

    def __init__(self):
        self._location = {}
        self._id2node = {}
        self._id2edge = {}
        self._crossings_and_walkingAreas = set()
        self._id2tls = {}
        self._nodes = []
        self._edges = []
        self._tlss = []
        self._ranges = [[10000, -10000], [10000, -10000]]
        self._roundabouts = []
        self._rtree = None
        self._allLanes = []
        self._origIdx = None
        self.hasWarnedAboutMissingRTree = False

    @classmethod
    def from_net_xml(cls, filename: str, **others):
        netreader = NetReader(**others)
        try:
            if not os.path.isfile(filename):
                raise Exception(f"Network file {filename} not found")
            parse(filename, netreader)
        except Exception as e:
            raise Exception(
                "Please mind that the network format has changed in 0.13.0, you may need to update your network!") from e
        return netreader.getNet()

    def setLocation(self, netOffset, convBoundary, origBoundary,
                    projParameter):
        self._location["netOffset"] = netOffset
        self._location["convBoundary"] = convBoundary
        self._location["origBoundary"] = origBoundary
        self._location["projParameter"] = projParameter

    def addNode(self, id, type=None, coord=None, incLanes=None, intLanes=None):
        if id is None:
            return None
        if id not in self._id2node:
            n = node.Node(id, type, coord, incLanes, intLanes)
            self._nodes.append(n)
            self._id2node[id] = n
        self.setAdditionalNodeInfo(self._id2node[id], type, coord, incLanes,
                                   intLanes)
        return self._id2node[id]

    def setAdditionalNodeInfo(self,
                              node,
                              type,
                              coord,
                              incLanes,
                              intLanes=None):
        if coord is not None and node._coord is None:
            node._coord = coord
            self._ranges[0][0] = min(self._ranges[0][0], coord[0])
            self._ranges[0][1] = max(self._ranges[0][1], coord[0])
            self._ranges[1][0] = min(self._ranges[1][0], coord[1])
            self._ranges[1][1] = max(self._ranges[1][1], coord[1])
        if incLanes is not None and node._incLanes is None:
            node._incLanes = incLanes
        if intLanes is not None and node._intLanes is None:
            node._intLanes = intLanes
        if type is not None and node._type is None:
            node._type = type

    def addEdge(self, id, fromID, toID, prio, function, name):
        if id not in self._id2edge:
            fromN = self.addNode(fromID)
            toN = self.addNode(toID)
            e = edge.Edge(id, fromN, toN, prio, function, name)
            self._edges.append(e)
            self._id2edge[id] = e
        return self._id2edge[id]

    def addLane(self, edge, speed, length, width, allow=None, disallow=None):
        return lane.Lane(edge, speed, length, width, allow, disallow)

    def addRoundabout(self, nodes, edges=None):
        r = roundabout.Roundabout(nodes, edges)
        self._roundabouts.append(r)
        return r

    def addConnection(self,
                      fromEdge,
                      toEdge,
                      fromlane,
                      tolane,
                      direction,
                      tls,
                      tllink,
                      state,
                      viaLaneID=None):
        conn = connection.Connection(fromEdge, toEdge, fromlane, tolane,
                                     direction, tls, tllink, state, viaLaneID)
        fromEdge.add_outgoing(conn)
        fromlane.add_outgoing(conn)
        toEdge.addIncoming(conn)

    def getEdges(self):
        return self._edges

    def getRoundabouts(self):
        return self._roundabouts

    def hasEdge(self, id):
        return id in self._id2edge

    def getEdge(self, id):
        return self._id2edge[id]

    def getLane(self, laneID):
        edge_id, lane_index = laneID.rsplit("_", 1)
        return self.getEdge(edge_id).getLane(int(lane_index))

    def _initRTree(self, shapeList, includeJunctions=True):
        import rtree
        self._rtree = rtree.index.Index()
        self._rtree.interleaved = True
        for ri, shape in enumerate(shapeList):
            self._rtree.add(ri, shape.getBoundingBox(includeJunctions))

    # Please be aware that the resulting list of edges is NOT sorted
    def getNeighboringEdges(self, x, y, r=0.1, includeJunctions=True):
        edges = []
        try:
            if self._rtree is None:
                self._initRTree(self._edges, includeJunctions)
            for i in self._rtree.intersection((x - r, y - r, x + r, y + r)):
                e = self._edges[i]
                d = sumolib.geomhelper.distancePointToPolygon(
                    (x, y), e.getShape(includeJunctions))
                if d < r:
                    edges.append((e, d))
        except ImportError:
            if not self.hasWarnedAboutMissingRTree:
                print(
                    "Warning: Module 'rtree' not available. Using brute-force fallback"
                )
                self.hasWarnedAboutMissingRTree = True

            for edge in self._edges:
                d = sumolib.geomhelper.distancePointToPolygon(
                    (x, y), edge.getShape(includeJunctions))
                if d < r:
                    edges.append((edge, d))
        return edges

    def getNeighboringLanes(self, x, y, r=0.1, includeJunctions=True):
        lanes = []
        try:
            if self._rtree is None:
                if not self._allLanes:
                    for edge in self._edges:
                        self._allLanes += edge.getLanes()
                self._initRTree(self._allLanes, includeJunctions)
            for i in self._rtree.intersection((x - r, y - r, x + r, y + r)):
                l = self._allLanes[i]
                d = sumolib.geomhelper.distancePointToPolygon(
                    (x, y), l.getShape(includeJunctions))
                if d < r:
                    lanes.append((l, d))
        except ImportError:
            for edge in self._edges:
                for l in edge.getLanes():
                    d = sumolib.geomhelper.distancePointToPolygon(
                        (x, y), l.getShape(includeJunctions))
                    if d < r:
                        lanes.append((l, d))
        return lanes

    def hasNode(self, id):
        return id in self._id2node

    def getNode(self, id):
        return self._id2node[id]

    def getNodes(self):
        return self._nodes

    def getTLSSecure(self, tlid):
        if tlid in self._id2tls:
            tls = self._id2tls[tlid]
        else:
            tls = TLS(tlid)
            self._id2tls[tlid] = tls
            self._tlss.append(tls)
        return tls

    def getTrafficLights(self):
        return self._tlss

    def addTLS(self, tlid, inLane, outLane, linkNo):
        tls = self.getTLSSecure(tlid)
        tls.add_connection(inLane, outLane, linkNo)
        return tls

    def addTLSProgram(self, tlid, programID, offset, type, removeOthers):
        tls = self.getTLSSecure(tlid)
        program = TLSProgram(programID, offset, type)
        if removeOthers:
            tls.clear_programs()
        tls.add_program(program)
        return program

    def setFoes(self, junctionID, index, foes, prohibits):
        self._id2node[junctionID].setFoes(index, foes, prohibits)

    def forbids(self, possProhibitor, possProhibited):
        return possProhibitor.getFrom().getToNode().forbids(
            possProhibitor, possProhibited)

    def getDownstreamEdges(self, edge, distance, stopOnTLS):
        ret = []
        seen = set()
        toProc = []
        toProc.append([edge, 0, []])
        while not len(toProc) == 0:
            ie = toProc.pop()
            if ie[0] in seen:
                continue
            seen.add(ie[0])
            if ie[1] + ie[0].getLength() >= distance:
                ret.append([
                    ie[0], ie[0].getLength() + ie[1] - distance, ie[2], False
                ])
                continue
            if len(ie[0]._incoming) == 0:
                ret.append([ie[0], ie[0].getLength() + ie[1], ie[2], True])
                continue
            mn = []
            hadTLS = False
            for ci in ie[0]._incoming:
                if ci not in seen:
                    prev = copy(ie[2])
                    if stopOnTLS and ci._tls and ci != edge and not hadTLS:
                        ret.append([ie[0], ie[1], prev, True])
                        hadTLS = True
                    else:
                        prev.append(ie[0])
                        mn.append([ci, ie[0].getLength() + ie[1], prev])
            if not hadTLS:
                toProc.extend(mn)
        return ret

    def getEdgesByOrigID(self, origID):
        if self._origIdx is None:
            self._origIdx = defaultdict(set)
            for edge in self._edges:
                for lane in edge.getLanes():
                    for oID in lane.getParam("origId", "").split():
                        self._origIdx[oID].add(edge)
        return self._origIdx[origID]

    def getBBoxXY(self):
        """
        Get the bounding box (bottom left and top right coordinates) for a net;
        Coordinates are in X and Y (not Lat and Lon)

        :return [(bottom_left_X, bottom_left_Y), (top_right_X, top_right_Y)]
        """
        return [(self._ranges[0][0], self._ranges[1][0]),
                (self._ranges[0][1], self._ranges[1][1])]

    # the diagonal of the bounding box of all nodes
    def getBBoxDiameter(self):
        return math.sqrt((self._ranges[0][0] - self._ranges[0][1]) ** 2 +
                         (self._ranges[1][0] - self._ranges[1][1]) ** 2)

    def getGeoProj(self):
        import pyproj
        p1 = self._location["projParameter"].split()
        params = {}
        for p in p1:
            ps = p.split("=")
            if len(ps) == 2:
                params[ps[0]] = ps[1]
            else:
                params[ps[0]] = True
        return pyproj.Proj(projparams=params)

    def getLocationOffset(self):
        """ offset to be added after converting from geo-coordinates to UTM"""
        return list(map(float, self._location["netOffset"].split(",")))

    def convertLonLat2XY(self, lon, lat, rawUTM=False):
        x, y = self.getGeoProj()(lon, lat)
        if rawUTM:
            return x, y
        else:
            x_off, y_off = self.getLocationOffset()
            return x + x_off, y + y_off

    def convertXY2LonLat(self, x, y, rawUTM=False):
        if not rawUTM:
            x_off, y_off = self.getLocationOffset()
            x -= x_off
            y -= y_off
        return self.getGeoProj()(x, y, inverse=True)

    def move(self, dx, dy, dz=0):
        for n in self._nodes:
            n._coord = (n._coord[0] + dx, n._coord[1] + dy, n._coord[2] + dz)
        for e in self._edges:
            for l in e._lanes:
                l._shape = [(p[0] + dx, p[1] + dy, p[2] + dz)
                            for p in l.getShape3D()]
            e.rebuildShape()


class NetReader(handler.ContentHandler):
    """Reads a network, storing the edge geometries, lane numbers and max. speeds"""

    def __init__(self, **others):
        self._net = others.get('net', Net())
        self._currentEdge = None
        self._currentNode = None
        self._currentLane = None
        self._withPhases = others.get('withPrograms', False)
        self._latestProgram = others.get('withLatestPrograms', False)
        if self._latestProgram:
            self._withPhases = True
        self._withConnections = others.get('withConnections', True)
        self._withFoes = others.get('withFoes', True)
        self._withInternal = others.get('withInternal', False)

    def startElement(self, name, attrs):
        if name == 'location':
            self._net.setLocation(attrs["netOffset"], attrs["convBoundary"],
                                  attrs["origBoundary"],
                                  attrs["projParameter"])
        if name == 'edge':
            function = attrs.get('function', '')
            if function == '' or self._withInternal:
                prio = -1
                if 'priority' in attrs:
                    prio = int(attrs['priority'])

                # get the  ids
                edgeID = attrs['id']
                fromNodeID = attrs.get('from', None)
                toNodeID = attrs.get('to', None)

                # for internal junctions use the junction's id for from and to node
                if function == 'internal':
                    fromNodeID = toNodeID = edgeID[1:edgeID.rfind('_')]

                self._currentEdge = self._net.addEdge(edgeID, fromNodeID,
                                                      toNodeID, prio, function,
                                                      attrs.get('name', ''))

                self._currentEdge.setRawShape(
                    convertShape(attrs.get('shape', '')))
            else:
                if function in ['crossing', 'walkingarea']:
                    self._net._crossings_and_walkingAreas.add(attrs['id'])
                self._currentEdge = None
        if name == 'lane' and self._currentEdge is not None:
            width = float(attrs['width']) if 'width' in attrs else 'default'
            self._currentLane = self._net.addLane(self._currentEdge,
                                                  float(attrs['speed']),
                                                  float(attrs['length']),
                                                  width, attrs.get('allow'),
                                                  attrs.get('disallow'))
            self._currentLane.setShape(convertShape(attrs.get('shape', '')))
        if name == 'junction':
            if attrs['id'][0] != ':':
                intLanes = None
                if self._withInternal:
                    intLanes = attrs["intLanes"].split(" ")
                self._currentNode = self._net.addNode(
                    attrs['id'], attrs['type'],
                    tuple(
                        map(float, [
                            attrs['x'], attrs['y'],
                            attrs['z'] if 'z' in attrs else '0'
                        ])), attrs['incLanes'].split(" "), intLanes)
                self._currentNode.setShape(convertShape(attrs.get('shape',
                                                                  '')))
        if name == 'succ' and self._withConnections:  # deprecated
            if attrs['edge'][0] != ':':
                self._currentEdge = self._net.getEdge(attrs['edge'])
                self._currentLane = attrs['lane']
                self._currentLane = int(
                    self._currentLane[self._currentLane.rfind('_') + 1:])
            else:
                self._currentEdge = None
        if name == 'succlane' and self._withConnections:  # deprecated
            lid = attrs['lane']
            if lid[0] != ':' and lid != "SUMO_NO_DESTINATION" and self._currentEdge:
                connected = self._net.getEdge(lid[:lid.rfind('_')])
                tolane = int(lid[lid.rfind('_') + 1:])
                if 'tl' in attrs and attrs['tl'] != "":
                    tl = attrs['tl']
                    tllink = int(attrs['linkIdx'])
                    tlid = attrs['tl']
                    toEdge = self._net.getEdge(lid[:lid.rfind('_')])
                    tolane2 = toEdge._lanes[tolane]
                    tls = self._net.addTLS(
                        tlid, self._currentEdge._lanes[self._currentLane],
                        tolane2, tllink)
                    self._currentEdge.setTLS(tls)
                else:
                    tl = ""
                    tllink = -1
                toEdge = self._net.getEdge(lid[:lid.rfind('_')])
                tolane = toEdge._lanes[tolane]
                viaLaneID = attrs['via']
                self._net.addConnection(
                    self._currentEdge, connected,
                    self._currentEdge._lanes[self._currentLane], tolane,
                    attrs['dir'], tl, tllink, attrs['state'], viaLaneID)
        if name == 'connection' and self._withConnections and (
            attrs['from'][0] != ":" or self._withInternal):
            fromEdgeID = attrs['from']
            toEdgeID = attrs['to']
            if not (fromEdgeID in self._net._crossings_and_walkingAreas
                    or toEdgeID in self._net._crossings_and_walkingAreas):
                fromEdge = self._net.getEdge(fromEdgeID)
                toEdge = self._net.getEdge(toEdgeID)
                fromLane = fromEdge.getLane(int(attrs['fromLane']))
                toLane = toEdge.getLane(int(attrs['toLane']))
                if 'tl' in attrs and attrs['tl'] != "":
                    tl = attrs['tl']
                    tllink = int(attrs['linkIndex'])
                    tls = self._net.addTLS(tl, fromLane, toLane, tllink)
                    fromEdge.setTLS(tls)
                else:
                    tl = ""
                    tllink = -1
                try:
                    viaLaneID = attrs['via']
                except KeyError:
                    viaLaneID = ''

                self._net.addConnection(fromEdge, toEdge, fromLane, toLane,
                                        attrs['dir'], tl, tllink,
                                        attrs['state'], viaLaneID)

        # 'row-logic' is deprecated!!!
        if self._withFoes and name == 'ROWLogic':
            self._currentNode = attrs['id']
        if name == 'logicitem' and self._withFoes:  # deprecated
            self._net.setFoes(self._currentNode, int(attrs['request']),
                              attrs["foes"], attrs["response"])
        if name == 'request' and self._withFoes:
            self._currentNode.setFoes(int(attrs['index']), attrs["foes"],
                                      attrs["response"])
        # tl-logic is deprecated!!! NOTE: nevertheless, this is still used by
        # cr_net_generator... (Leo)
        if self._withPhases and name == 'tlLogic':
            self._currentProgram = self._net.addTLSProgram(
                attrs['id'], attrs['programID'], float(attrs['offset']),
                attrs['type'], self._latestProgram)
        if self._withPhases and name == 'phase':
            self._currentProgram.add_phase(attrs['state'],
                                           int(attrs['duration']))
        if name == 'roundabout':
            self._net.addRoundabout(attrs['nodes'].split(),
                                    attrs['edges'].split())
        if name == 'param':
            if self._currentLane is not None:
                self._currentLane.setParam(attrs['key'], attrs['value'])

        if name == 'neigh':  # added by Lisa
            if self._currentLane is not None:
                self._currentLane.setAdjacentOpposite(attrs['lane'])

    def endElement(self, name):
        if name == 'lane':
            self._currentLane = None
        if name == 'edge':
            self._currentEdge = None
        # 'row-logic' is deprecated!!!
        if name == 'ROWLogic' or name == 'row-logic':
            self._haveROWLogic = False
        # tl-logic is deprecated!!!
        if self._withPhases and (name == 'tlLogic' or name == 'tl-logic'):
            self._currentProgram = None

    def getNet(self):
        return self._net


def convertShape(shapeString):
    """ Convert xml shape string into float tuples.

    This method converts the 2d or 3d shape string from SUMO's xml file
    into a list containing 3d float-tuples. Non existant z coordinates default
    to zero. If shapeString is empty, an empty list will be returned.
    """

    cshape = []
    for pointString in shapeString.split():
        p = [float(e) for e in pointString.split(",")]
        if len(p) == 2:
            cshape.append((p[0], p[1], 0.))
        elif len(p) == 3:
            cshape.append(tuple(p))
        else:
            raise ValueError(
                'Invalid shape point "%s", should be either 2d or 3d' %
                pointString)
    return cshape


#
# Node
#
class Node:
    """ Nodes from a sumo network """

    def __init__(self,
                 id: int,
                 node_type: str,
                 coord,
                 incLanes,
                 intLanes=None,
                 tl=None,
                 right_of_way="default"):
        self._id = id
        self._type = node_type
        self._coord = coord
        self._incoming = []
        self._outgoing = []
        self._foes = {}
        self._prohibits = {}
        self._incLanes = incLanes
        self._intLanes = intLanes
        self._shape3D = None
        self._shape = None
        self._tl = tl
        self._right_of_way = right_of_way

    def getID(self) -> int:
        return self._id

    def setShape(self, shape):
        """Set the shape of the node.

        Shape must be a list containing x,y,z coords as numbers
        to represent the shape of the node.
        """
        for pp in shape:
            if len(pp) != 3:
                raise ValueError('shape point must consist of x,y,z')
        self._shape3D = shape
        self._shape = [(x, y) for x, y, z in shape]

    def getShape(self):
        """Returns the shape of the node in 2d.

        This function returns the shape of the node, as defined in the net.xml
        file. The returned shape is a list containing numerical
        2-tuples representing the x,y coordinates of the shape points.

        If no shape is defined in the xml, an empty list will be returned.
        """

        return self._shape

    def getShape3D(self):
        """Returns the shape of the node in 3d.

        This function returns the shape of the node, as defined in the net.xml
        file. The returned shape is a list containing numerical
        3-tuples representing the x,y,z coordinates of the shape points.

        If no shape is defined in the xml, an empty list will be returned.
        """

        return self._shape3D

    def addOutgoing(self, edge):
        self._outgoing.append(edge)

    def getOutgoing(self):
        return self._outgoing

    def addIncoming(self, edge):
        self._incoming.append(edge)

    def getIncoming(self):
        return self._incoming

    def getInternal(self):
        return self._intLanes

    def getTl(self):
        return self._tl

    def setFoes(self, index, foes, prohibits):
        self._foes[index] = foes
        self._prohibits[index] = prohibits

    def areFoes(self, link1, link2):
        return self._foes[link1][len(self._foes[link1]) - link2 - 1] == '1'

    def getLinkIndex(self, conn):
        ret = 0
        for lane_id in self._incLanes:
            (edge_id, index) = lane_id.split("_")
            edge = [e for e in self._incoming if e.getID() == edge_id][0]
            for candidate_conn in edge.getLane(int(index)).getOutgoing():
                if candidate_conn == conn:
                    return ret
                ret += 1
        return -1

    def forbids(self, possProhibitor, possProhibited):
        possProhibitorIndex = self.getLinkIndex(possProhibitor)
        possProhibitedIndex = self.getLinkIndex(possProhibited)
        if possProhibitorIndex < 0 or possProhibitedIndex < 0:
            return False
        ps = self._prohibits[possProhibitedIndex]
        return ps[-(possProhibitorIndex - 1)] == '1'

    def getCoord(self):
        return tuple(self._coord[:2])

    def getCoord3D(self):
        return self._coord

    def getType(self):
        return self._type

    def setType(self, type: str):
        self._type = type

    def getConnections(self, source=None, target=None):
        incoming = list(self.getIncoming())
        if source:
            incoming = [source]
        conns = []
        for e in incoming:
            for l in e.getLanes():
                all_outgoing = l.getOutgoing()
                outgoing = []
                if target:
                    for o in all_outgoing:
                        if o.getTo() == target:
                            outgoing.append(o)
                else:
                    outgoing = all_outgoing
                conns.extend(outgoing)
        return conns

    def toXML(self) -> str:
        """
        Converts this node to it's xml representation
        TODO: Not all attributes are converted
        """
        node = ET.Element("node")
        node.set("id", str(self._id))
        node.set("type", str(self._type))
        for key, value in zip(["x", "y", "z"][:len(self._coord)], self._coord):
            node.set(key, str(value))
        if self._tl:
            node.set("tl", str(self._tl))
        node.set("rightOfWay", str(self._right_of_way))
        return ET.tostring(node, encoding="unicode")

    def __str__(self):
        return "Node: " + str(self._id)

    def __hash__(self):
        return hash((self._id, self._type))

    def __eq__(self, other):
        return self._id == other._id \
               and self._type == other._type \
               and self._tl == other._tl \
               and self._right_of_way == other._right_of_way

    def __ne__(self, other):
        return not self.__eq__(other)


#
# Edge
#
class Edge:
    """ Edges from a sumo network """

    def __init__(self, id: int, from_node, to_node, type_id: str = "", function: str = "normal", name: str = "",
                 priority: int = 0):
        self._id = id
        self._from = from_node
        self._to = to_node
        self._type = type_id
        self._priority = priority
        if from_node:
            from_node.add_outgoing(self)
        if to_node:
            to_node.addIncoming(self)
        self._lanes = []
        self._speed = None
        self._length = None
        self._incoming = {}
        self._outgoing = {}
        self._shape = None
        self._shapeWithJunctions = None
        self._shape3D = None
        self._shapeWithJunctions3D = None
        self._rawShape = None
        self._rawShape3D = None
        self._function = function
        self._tls = None
        self._name = name

    def setFrom(self, fromN):
        self._from = fromN

    def setTo(self, toN):
        self._to = toN

    def getName(self):
        return self._name

    def isSpecial(self):
        """ Check if the edge has a special function.

        Returns False if edge's function is 'normal', else False, e.g. for
        internal edges or connector edges """

        return self._function != ""

    def getFunction(self):
        return self._function

    def getPriority(self):
        return self._priority

    def getTLS(self):
        return self._tls

    def addLane(self, lane):
        self._lanes.append(lane)
        self._speed = lane.getSpeed()
        self._length = lane.getLength()

    def addOutgoing(self, edge: 'Edge'):
        if edge._to not in self._outgoing:
            self._outgoing[edge._to] = []
        self._outgoing[edge._to].append(edge)

    def addIncoming(self, edge: 'Edge'):
        if edge._from not in self._incoming:
            self._incoming[edge._from] = []
        self._incoming[edge._from].append(edge)

    def setRawShape(self, shape):
        self._rawShape3D = shape

    def getID(self) -> int:
        return self._id

    def getIncoming(self) -> List['Edge']:
        return [e for edges in self._incoming.values() for e in edges]

    def getOutgoing(self) -> List['Edge']:
        return [e for edges in self._outgoing.values() for e in edges]

    def getRawShape(self):
        """Return the shape that was used in cr_net_generator for building this edge (2D)."""
        if self._shape is None:
            self.rebuildShape()
        return self._rawShape

    def getRawShape3D(self):
        """Return the shape that was used in cr_net_generator for building this edge (3D)."""
        if self._shape is None:
            self.rebuildShape()
        return self._rawShape3D

    def getShape(self, includeJunctions=False):
        """Return the 2D shape that is the average of all lane shapes (segment-wise)"""
        if self._shape is None:
            self.rebuildShape()
        if includeJunctions:
            return self._shapeWithJunctions
        return self._shape

    def getShape3D(self, includeJunctions=False):
        if self._shape is None:
            self.rebuildShape()
        if includeJunctions:
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
        assert (xmin != xmax or ymin != ymax or self._function == "internal")
        return (xmin, ymin, xmax, ymax)

    def getClosestLanePosDist(self, point, perpendicular=False):
        minDist = 1e400
        minIdx = None
        minPos = None
        for i, l in enumerate(self._lanes):
            pos, dist = l.getClosestLanePosAndDist(point, perpendicular)
            if dist < minDist:
                minDist = dist
                minIdx = i
                minPos = pos
        return minIdx, minPos, minDist

    def getSpeed(self):
        return self._speed

    def getLaneNumber(self):
        return len(self._lanes)

    def getLane(self, idx):
        return self._lanes[idx]

    def getLanes(self):
        return self._lanes

    def rebuildShape(self):
        numLanes = len(self._lanes)
        if numLanes % 2 == 1:
            self._shape3D = self._lanes[int(numLanes / 2)].getShape3D()
        else:
            self._shape3D = []
            minLen = -1
            for l in self._lanes:
                if minLen == -1 or minLen > len(l.getShape()):
                    minLen = len(l._shape)
            for i in range(minLen):
                x = 0.
                y = 0.
                z = 0.
                for l in self._lanes:
                    x += l.getShape3D()[i][0]
                    y += l.getShape3D()[i][1]
                    z += l.getShape3D()[i][2]
                self._shape3D.append((x / float(numLanes), y / float(numLanes),
                                      z / float(numLanes)))

        self._shapeWithJunctions3D = lane.add_junction_pos(self._shape3D,
                                                           self._from.getCoord3D(),
                                                           self._to.getCoord3D())

        if self._rawShape3D == []:
            self._rawShape3D = [self._from.getCoord3D(), self._to.getCoord3D()]

        # 2d - versions
        self._shape = [(x, y) for x, y, z in self._shape3D]
        self._shapeWithJunctions = [(x, y)
                                    for x, y, z in self._shapeWithJunctions3D]
        self._rawShape = [(x, y) for x, y, z in self._rawShape3D]

    def getLength(self):
        return self._lanes[0].getLength()

    def setTLS(self, tls):
        self._tls = tls

    def getFromNode(self):
        return self._from

    def getToNode(self):
        return self._to

    def is_fringe(self, connections=None):
        """true if this edge has no incoming or no outgoing connections (except turnarounds)
           If connections is given, only those connections are considered"""
        if connections is None:
            return self.is_fringe(self._incoming) or self.is_fringe(
                self._outgoing)
        else:
            cons = sum([c for c in connections.values()], [])
            return len([
                c for c in cons if c._direction != Connection.LINKDIR_TURN
            ]) == 0

    def allows(self, vClass):
        """true if this edge has a lane which allows the given vehicle class"""
        for lane in self._lanes:
            if vClass in lane._allow:
                return True
        return False

    def getType(self):
        return self._type

    def setType(self, value: str):
        self._type = value

    def __repr__(self):
        if self.getFunction() == '':
            return '<edge id="%s" from="%s" to="%s"/>' % (
                self._id, self._from.getID(), self._to.getID())
        else:
            return '<edge id="%s" function="%s"/>' % (self._id,
                                                      self.getFunction())

    def toXML(self) -> str:
        edge = ET.Element("edge")
        edge.set("from", str(self.getFromNode().getID()))
        edge.set("to", str(self.getToNode().getID()))
        edge.set("id", str(self._id))
        if self._type:
            edge.set("type", str(self._type))
        if self._priority:
            edge.set("priority", str(self._priority))
        if self._speed:
            edge.set("speed", str(self._speed))
        if self._length:
            edge.set("length", str(self._length))
        if self._shape:
            edge.set("shape", str(self.getShape()))
        if self._length:
            edge.set("length", str(self._length))
        edge.set("numLanes", str(self.getLaneNumber()))
        edge.set("spreadType", "center")
        edge.set("function", str(self._function))
        for lane in self._lanes:
            edge.append(ET.fromstring(lane.to_xml()))

        return ET.tostring(edge, encoding="unicode")


#
# Lane
#

def add_junction_pos(shape, fromPos, toPos):
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

    def __init__(self, edge: Edge,
                 speed: float,
                 length: float,
                 width: float,
                 allow: List['VehicleType'] = None,
                 disallow: List['VehicleType'] = None,
                 shape: np.ndarray = None):
        self._edge = edge
        self._speed = speed
        self._length = length
        self._width = width
        self._shape = shape if shape is not None else np.empty(0)
        self._shapeWithJunctions = None
        self._shapeWithJunctions3D = None
        self._outgoing: List['Connection'] = []
        self._adjacent_opposite = None  # added by Lisa
        self._allow: List['VehicleType'] = []
        self._disallow: List['VehicleType'] = []
        self._set_allow_disallow(allow, disallow)

        edge.addLane(self)

    def _set_allow_disallow(self, allow: Optional[List['VehicleType']], disallow: Optional[List['VehicleType']]):
        if allow is not None and disallow is not None:
            assert set(allow).isdisjoint(set(disallow))
            self._allow = allow
            self._disallow = disallow
        elif allow:
            self._disallow: List['VehicleType'] = list(set(VehicleType) - set(allow))
        elif disallow:
            self._allow: List['VehicleType'] = list(set(VehicleType) - set(disallow))

    @property
    def edge(self) -> Edge:
        return self._edge

    @edge.setter
    def edge(self, edge: Edge):
        self._edge = edge

    @property
    def speed(self) -> float:
        return self._speed

    @speed.setter
    def speed(self, speed: float):
        self._speed = speed

    @property
    def length(self) -> float:
        return self._length

    @length.setter
    def length(self, length: float):
        self._length = length

    @property
    def width(self) -> float:
        return self._width

    @width.setter
    def width(self, width: float):
        self._width = width

    def setAdjacentOpposite(self, opposite_lane_id):
        self._adjacent_opposite = opposite_lane_id

    def getAdjacentOpposite(self):
        return self._adjacent_opposite

    @property
    def shape(self) -> np.ndarray:
        return self._shape

    @shape.setter
    def shape(self, shape: np.ndarry):
        self._shape = shape

    @property
    def bounding_box(self) -> Tuple[float, float, float, float]:
        s = self.shape
        xmin = float(np.min(s[:, 0]))
        xmax = float(np.max(s[:, 0]))
        ymin = float(np.min(s[:, 1]))
        ymax = float(np.max(s[:, 1]))
        assert (xmin != xmax or ymin != ymax)
        return xmin, ymin, xmax, ymax

    def getClosestLanePosAndDist(self, point, perpendicular=False):
        return sumolib.geomhelper.polygonOffsetAndDistanceToPoint(
            point, self.getShape(), perpendicular)

    def getIndex(self):
        return self._edge._lanes.index(self)

    def getID(self):
        return f"{self._edge._id}_{self.getIndex()}"

    @property
    def outgoing(self) -> List['Connection']:
        return self._outgoing

    def add_outgoing(self, conn: 'Connection'):
        self._outgoing.append(conn)

    @property
    def allow(self) -> List['VehicleType']:
        return self._allow

    @allow.setter
    def allow(self, allow: List['VehicleType']):
        self._set_allow_disallow(allow, None)

    @property
    def disallow(self) -> List['VehicleType']:
        return self._disallow

    @disallow.setter
    def disallow(self, disallow: List['VehicleType']):
        self._set_allow_disallow(None, disallow)

    def to_xml(self) -> str:
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
            lane.set("shape", to_shape_string(self._shape))
        if self._width:
            lane.set("width", str(self._width))
        if self._allow:
            lane.set("allow", " ".join(a.value for a in self._allow))
        if self._disallow:
            lane.set("disallow", " ".join(d.value for d in self._disallow))
        return ET.tostring(lane, encoding="unicode")


#
# Junction
#
class Junction:
    def __init__(self, id: int,
                 j_type: str = "priority",
                 x: float = -1,
                 y: float = -1,
                 inc_lanes: List[Lane] = None,
                 int_lanes: List[Lane] = None,
                 shape: np.ndarray = None):
        self.id = id
        self.type = j_type
        self.x = x
        self.y = y
        self.inc_Lanes = inc_lanes if inc_lanes is not None else []
        self.intLanes = int_lanes if int_lanes is not None else []
        self.shape = shape if shape is not None else np.empty(0)


#
# Connection
#

def to_shape_string(shape: np.ndarray) -> str:
    """
    Convert a collection of points from format shape to string
    :param shape:
    :return: the same shape but in string format
    """
    return " ".join([",".join(str(p) for p in v) for v in shape])


def from_shape_string(shape: str) -> np.ndarray:
    """
    Convert a shape string to a ndarray
    :param shape:
    :return:
    """
    return np.asarray([[float(c) for c in coords.split(",")] for coords in shape.split(" ")], dtype=float)


@unique
class ConnectionDirection(Enum):
    # constants as defined in sumo/src/utils/xml/SUMOXMLDefinitions.cpp
    STRAIGHT = "s"
    TURN = "t"
    LEFT = "l"
    RIGHT = "r"
    PARTLEFT = "L"
    PARTRIGHT = "R"


class Connection:
    """edge connection for a sumo network"""

    def __init__(self,
                 from_edge: Edge, to_edge: Edge, from_lane: Lane, to_lane: Lane,
                 direction: ConnectionDirection = None,
                 tls: 'TLS' = None,
                 tl_link: int = None,
                 state=None,
                 via_lane_id=None,
                 shape: Optional[np.ndarray] = None,
                 keep_clear: bool = None,
                 cont_pos=None):
        self._from = from_edge
        self._to = to_edge
        self._from_lane = from_lane
        self._to_lane = to_lane
        self._direction = direction
        self._tls = tls
        self._tl_link = tl_link
        self._state = state
        self._via = via_lane_id
        self._shape = shape
        self._keep_clear = keep_clear
        self._cont_pos = cont_pos

    @property
    def from_edge(self) -> Edge:
        return self._from

    @from_edge.setter
    def from_edge(self, from_edge: Edge):
        self._from = from_edge

    @property
    def to_edge(self) -> Edge:
        return self._to

    @to_edge.setter
    def to_edge(self, to_edge: Edge):
        self._to = to_edge

    @property
    def from_lane(self) -> Lane:
        return self._from_lane

    @from_lane.setter
    def from_lane(self, from_lane: Lane):
        self._from_lane = from_lane

    @property
    def to_lane(self) -> Lane:
        return self._to_lane

    @to_lane.setter
    def to_lane(self, to_lane: Lane):
        self._to_lane = to_lane

    @property
    def via(self):
        return self._via

    @via.setter
    def via(self, via):
        self._via = via

    @property
    def direction(self):
        return self._direction

    @property
    def tls(self):
        return self._tls

    @property
    def tl_link(self) -> int:
        return self._tl_link

    @tl_link.setter
    def tl_link(self, tl_link: int):
        self._tl_link = tl_link

    def get_junction_index(self):
        return self._from.getToNode().getLinkIndex(self)

    @property
    def junction(self) -> Node:
        return self._from.getToNode()

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        self._state = state

    @property
    def shape(self) -> np.ndarray:
        return self._shape

    @shape.setter
    def shape(self, shape: np.ndarray):
        self._shape = shape

    def to_xml(self) -> str:
        """
        Converts this connection to it's xml representation
        """
        c = ET.Element("connection")
        c.set("from", str(self._from))
        c.set("to", str(self._to))
        c.set("fromLane", str(self._from_lane))
        c.set("toLane", str(self._to_lane))
        if self._via is not None:
            c.set("via", str(self._via))
        if self._direction is not None:
            c.set("dir", str(self._direction))
        if self._tls is not None:
            c.set("tl", str(self._tls))
        if self._tl_link is not None:
            c.set("linkIndex", str(self._tl_link))
        if self._state is not None:
            c.set("state", str(self._state))
        if self._shape is not None:
            c.set("shape", to_shape_string(self._shape))
        if self._keep_clear is not None:
            c.set("keepClear", "true" if self._keep_clear else "false")
        if self._cont_pos is not None:
            c.set("contPos", str(self._cont_pos))
        return ET.tostring(c, encoding="unicode")

    def __str__(self):
        return str(self.to_xml())


#
# Crossings
#

class Crossing:
    def __init__(self,
                 node: Node,
                 edges: Iterable[Edge],
                 priority: bool = None,
                 width: float = None,
                 shape=None,
                 link_index: int = None,
                 link_index_2: int = None,
                 discard: bool = None):
        self.node = node
        self.edges = edges
        self.priority = priority
        self.width = width
        self.shape = shape
        self.link_index = link_index
        self.link_index_2 = link_index_2
        self.discard = discard

    def __str__(self) -> str:
        return str(self.to_xml())

    def to_xml(self) -> str:
        c = ET.Element("crossing")
        c.set("node", str(self.node.getID()))
        c.set("edges", " ".join(str(edge.getID()) for edge in self.edges))
        if self.priority is not None:
            c.set("priority", str(self.priority))
        if self.width is not None:
            c.set("width", str(self.width))
        if self.shape is not None:
            c.set("shape", " ".join([",".join(str(coord) for coord in v) for v in self.shape]))
        if self.link_index is not None:
            c.set("linkIndex", str(self.link_index))
        if self.link_index_2 is not None:
            c.set("linkIndex2", str(self.link_index_2))
        if self.discard is not None:
            c.set("discard", str(self.discard))
        return ET.tostring(c, encoding="unicode")


#
# Edge Type Manager
#
def _bool_to_str(b: bool) -> str:
    return "true" if b else "false"


def _str_to_bool(s: str) -> bool:
    return s == "true"


# generic type
_T = TypeVar("_T")


class EdgeType:
    def __init__(self, id: str,
                 allow: List['VehicleType'] = None,
                 disallow: List['VehicleType'] = None,
                 discard: bool = False,
                 num_lanes: int = -1,
                 oneway=False,
                 priority: int = 0,
                 speed: float = 13.89,
                 sidewalk_width: float = -1):
        """
        Constructs a SUMO Edge Type
        Documentation from: https://sumo.dlr.de/docs/SUMO_edge_type_file.html
        :param id: The name of the road type. This is the only mandatory attribute. For OpenStreetMap data, the name could, for example, be highway.trunk or highway.residential. For ArcView data, the name of the road type is a number.
        :param allow: List of allowed vehicle classes
        :param disallow: List of not allowed vehicle classes
        :param discard: If "yes", edges of that type are not imported. This parameter is optional and defaults to false.
        :param num_lanes: The number of lanes on an edge. This is the default number of lanes per direction.
        :param oneway: If "yes", only the edge for one direction is created during the import. (This attribute makes no sense for SUMO XML descriptions but, for example, for OpenStreetMap files.)
        :param priority: A number, which determines the priority between different road types. netconvert derives the right-of-way rules at junctions from the priority. The number starts with one; higher numbers represent more important roads.
        :param speed: The default (implicit) speed limit in m/s.
        :param sidewalk_width: The default width for added sidewalks (defaults to -1 which disables extra sidewalks).
        """
        self.id = id
        assert not (allow and disallow and set(allow) & set(disallow)), \
            f"allow and disallow contain common elements {set(allow) & set(disallow)}"
        self.allow: List['VehicleType'] = []
        if allow:
            assert set(allow).issubset(set(VehicleType)), \
                f"allow contains invalid classes {set(allow) - set(VehicleType)}"
            self.allow: List['VehicleType'] = allow

        self.disallow: List['VehicleType'] = []
        if disallow:
            assert set(disallow).issubset(set(VehicleType)), \
                f"disallow contains invalid classes {set(disallow) - set(VehicleType)}"
            self.disallow: List['VehicleType'] = disallow

        self.discard = discard
        self.num_lanes = num_lanes
        self.oneway = oneway
        self.priority = priority
        self.speed = speed
        self.sidewalk_width = sidewalk_width

    @classmethod
    def from_xml(cls, xml: str) -> 'EdgeType':
        """
        Creates an instance of this class from the given xml representation
        :param xml:
        :return:
        """
        root = ET.fromstring(xml)

        def get_map(key: str, map: Callable[[str], _T], default: _T) -> _T:
            value = root.get(key)
            return map(value) if value else default

        def str_to_vehicle_type(value: str) -> VehicleType:
            return VehicleType(value)

        return cls(id=root.get("id"),
                   allow=get_map("allow", lambda sp: [str_to_vehicle_type(s) for s in sp.split(" ")], []),
                   disallow=get_map("disallow", lambda sp: [str_to_vehicle_type(s) for s in sp.split(" ")], []),
                   discard=get_map("discard", _str_to_bool, False),
                   num_lanes=get_map("numLanes", int, -1),
                   oneway=get_map("oneway", _str_to_bool, False),
                   priority=get_map("priority", int, 0),
                   speed=get_map("speed", float, 13.89),
                   sidewalk_width=get_map("sidewalkWidth", int, -1))

    def to_xml(self) -> str:
        """
        Converts this node to it's xml representation
        :return: xml representation of this EdgeType
        """
        node = ET.Element("type")
        node.set("id", str(self.id))
        if self.allow:
            node.set("allow", " ".join(a.value for a in self.allow))
        if self.disallow:
            node.set("disallow", " ".join(d.value for d in self.disallow))
        if self.discard:
            node.set("discard", _bool_to_str(self.discard))
        if self.num_lanes != -1:
            node.set("numLanes", str(self.num_lanes))
        if self.oneway:
            node.set("oneway", _bool_to_str(self.oneway))
        if self.priority:
            node.set("priority", str(self.priority))
        if self.speed:
            node.set("speed", f"{self.speed:.2f}")
        if self.sidewalk_width > 0:
            node.set("sidewalkWidth", f"{self.sidewalk_width:.2f}")
        return ET.tostring(node, encoding="unidcode")

    def __str__(self):
        return self.to_xml()


class EdgeTypes:
    def __init__(self, types: Dict[str, EdgeType] = None):
        self.types: Dict[str, EdgeType] = types if types else dict()

    @classmethod
    def from_xml(cls, xml: str) -> 'EdgeTypes':
        root = ET.fromstring(xml)
        types: Dict[str, EdgeType] = {}
        for edge_type in root.iter("type"):
            types[edge_type.get("id")] = EdgeType.from_xml(ET.tostring(edge_type, encoding="unicode"))
        return cls(types)

    def to_xml(self) -> str:
        types = ET.Element("types")
        types.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        types.set("xsi:noNamespaceSchemaLocation", "http://sumo.dlr.de/xsd/types_file.xsd")
        for type_id, type in self.types.items():
            types.append(ET.fromstring(type.to_xml()))
        return ET.tostring(types, encoding="unicode")

    def _create_from_update(self, old_id: str, attr: str, value: any) -> Optional[EdgeType]:
        if old_id not in self.types:
            return None
        edge_type = self.types[old_id]

        val_rep = str(value)
        if isinstance(value, Iterable):
            val_rep = "_".join([str(v) for v in value])

        new_id = f"{edge_type.id}_{attr}_{val_rep}"
        if new_id in self.types:
            return self.types[new_id]

        new_type = deepcopy(edge_type)
        new_type.id = new_id
        setattr(new_type, attr, value)
        self.types[new_type.id] = new_type
        return new_type

    def create_from_update_priority(self, old_id: str, priority: int) -> Optional[EdgeType]:
        return self._create_from_update(old_id, "priority", priority)

    def create_from_update_speed(self, old_id: str, speed: float) -> Optional[EdgeType]:
        return self._create_from_update(old_id, "speed", round(speed, 2))

    def create_from_update_oneway(self, old_id: str, oneway: bool) -> Optional[EdgeType]:
        return self._create_from_update(old_id, "oneway", oneway)

    def create_from_update_allow(self, old_id: str, allow: List[str]) -> Optional[EdgeType]:
        new_type = self._create_from_update(old_id, "allow", allow)
        setattr(new_type, "disallow", list(set(new_type.disallow) - set(new_type.allow)))
        return new_type

    def create_from_update_disallow(self, old_id: str, disallow: List[str]) -> Optional[EdgeType]:
        new_type = self._create_from_update(old_id, "disallow", disallow)
        setattr(new_type, "allow", list(set(new_type.allow) - set(new_type.disallow)))
        return new_type


#
# Traffic Light Systems
#
class SignalState(Enum):
    """
    Adapted from: https://sumo.dlr.de/docs/Simulation/Traffic_Lights.html#tllogic62_attributes
    """
    # 'red light' for a signal - vehicles must stop
    RED = "r"
    # 'amber (yellow) light' for a signal -
    # vehicles will start to decelerate if far away from the junction, otherwise they pass
    YELLOW = "y"
    # 'green light' for a signal, no priority -
    # vehicles may pass the junction if no vehicle uses a higher priorised foe stream,
    # otherwise they decelerate for letting it pass.
    # They always decelerate on approach until they are within the configured visibility distance
    GREEN = "g"
    # 'green light' for a signal, priority -
    # vehicles may pass the junction
    GREEN_PRIORITY = "G"
    # 'green right-turn arrow' requires stopping -
    # vehicles may pass the junction if no vehicle uses a higher priorised foe stream.
    # They always stop before passing.
    # This is only generated for junction type traffic_light_right_on_red.
    GREEN_TURN_RIGHT = "s"
    # 'red+yellow light' for a signal, may be used to indicate upcoming
    # green phase but vehicles may not drive yet (shown as orange in the gui)
    RED_YELLOW = "u"
    # 'off - blinking' signal is switched off, blinking light indicates vehicles have to yield
    BLINKING = "o"
    # 'off - no signal' signal is switched off, vehicles have the right of way
    NO_SIGNAL = "O"


class Phase:
    def __init__(self,
                 duration: float,
                 state: List[SignalState],
                 min_dur: int = None,
                 max_dur: int = None,
                 name: str = None,
                 next: List[int] = None):
        """
        Adapted from: https://sumo.dlr.de/docs/Simulation/Traffic_Lights.html#tllogic62_attributes
        :param duration: The duration of the phase (sec)
        :param state: The traffic light states for this phase, see below
        :param min_dur: The minimum duration of the phase when using type actuated. Optional, defaults to duration.
        :param max_dur: The maximum duration of the phase when using type actuated. Optional, defaults to duration.
        :param name: An optional description for the phase. This can be used to establish the correspondence between SUMO-phase-indexing and traffic engineering phase names.
        :param next:
        """
        self.duration = duration
        self.state = state
        self.min_dur = min_dur
        self.max_dur = max_dur
        self.name = name
        self.next = next

    def to_xml(self) -> str:
        phase = ET.Element("phase")
        phase.set("duration", str(self.duration))
        phase.set("state", "".join([s.value for s in self.state]))
        if self.min_dur is not None:
            phase.set("minDur", str(self.min_dur))
        if self.max_dur is not None:
            phase.set("maxDur", str(self.max_dur))
        if self.name is not None:
            phase.set("name", str(self.name))
        if self.next is not None:
            phase.set("next", str(self.next))
        return ET.tostring(phase, encoding="unicode")

    def __str__(self):
        return str(self.to_xml())

    def __repr__(self):
        return str(self)


class TLSType(Enum):
    """
    The type of the traffic light
     - fixed phase durations,
     - phase prolongation based on time gaps between vehicles (actuated),
     - or on accumulated time loss of queued vehicles (delay_based)
    Adapted from: https://sumo.dlr.de/docs/Simulation/Traffic_Lights.html
    """
    STATIC = "static"
    ACTUATED = "actuated"
    DELAY_BASED = "delay_based"


class TLSProgram:
    def __init__(self, id: str, offset: int, program_id: str, tls_type: TLSType = TLSType.STATIC):
        """
        Adapted from: https://sumo.dlr.de/docs/Simulation/Traffic_Lights.html#tllogic62_attributes
        :param id: The id of the traffic light. This must be an existing traffic light id in the .net.xml file.
        Typically the id for a traffic light is identical with the junction id.
        The name may be obtained by right-clicking the red/green bars in front of a controlled intersection.
        :param offset: The initial time offset of the program
        :param program_id: The id of the traffic light program; This must be a new program name for the traffic light id.
        Please note that "off" is reserved, see below.
        :param tls_type: The type of the traffic light (fixed phase durations, phase prolongation based on time
        gaps between vehicles (actuated), or on accumulated time loss of queued vehicles (delay_based) )
        """
        self._id = id
        self._type = tls_type
        self._offset = offset
        self._program_id = program_id
        self._phases: List[Phase] = []

    @property
    def phases(self) -> List[Phase]:
        return self._phases

    @phases.setter
    def phases(self, phases: List[Phase]):
        self._phases = phases

    @property
    def offset(self) -> int:
        return self._offset

    @offset.setter
    def offset(self, offset: int):
        self._offset = offset

    def add_phase(self, phase: Phase):
        self._phases.append(phase)

    def to_xml(self) -> str:
        tl = ET.Element("tlLogic")
        tl.set("id", self._id)
        tl.set("type", str(self._type.value))
        tl.set("programID", str(self._program_id))
        tl.set("offset", str(int(self._offset)))
        for phase in self._phases:
            tl.append(ET.fromstring(phase.to_xml()))
        return ET.tostring(tl, encoding="unicode")

    # def update_state(self, old_idx: int, new_idx: int, new_state: SumoSignalState):
    #

    def __str__(self):
        return str(self.to_xml())

    def __repr__(self):
        return str(self)


class TLS:
    """Traffic Light Signal, managing TLSPrograms for SUMO"""

    def __init__(self):
        self._connections: List[Connection] = []
        self._maxConnectionNo = -1
        self._programs: Dict[str, Dict[str, TLSProgram]] = defaultdict(dict)

    @property
    def connections(self) -> List[Connection]:
        return self._connections

    def add_connection(self, connection: Connection):
        self._connections.append(connection)

    @property
    def programs(self) -> Dict[str, Dict[str, TLSProgram]]:
        return self._programs

    def add_program(self, program: TLSProgram):
        self._programs[program._id][program._program_id] = program

    def clear_programs(self):
        self._programs.clear()

    def to_xml(self) -> str:
        tl = ET.Element("tlLogics")
        for programs in self._programs.values():
            for program in programs.values():
                tl.append(ET.fromstring(program.to_xml()))
        for c in self._connections:
            conn = ET.fromstring(c.to_xml())
            tl.append(conn)
        return ET.tostring(tl, encoding="unicode")

    def __str__(self):
        return str(self.to_xml())

    def __repr__(self):
        return str(self)


#
# Roundabout
#

class Roundabout:
    def __init__(self, nodes: List[Node], edges: List[Edge] = None):
        self._nodes = nodes
        self._edges = edges if edges is not None else []

    @property
    def nodes(self) -> List[Node]:
        return self._nodes

    @nodes.setter
    def nodes(self, nodes: List[Node]):
        self._nodes = nodes

    @property
    def edges(self) -> List[Edge]:
        return self._edges

    @edges.setter
    def edges(self, edges: List[Edge]):
        self._edges = edges


#
# Enums
#
@unique
class VehicleType(Enum):
    """taken from sumo/src/utils/common/SUMOVehicleClass.cpp
    "public_emergency",  # deprecated
    "public_authority",  # deprecated
    "public_army",       # deprecated
    "public_transport",  # deprecated
    "transport",         # deprecated
    "lightrail",         # deprecated
    "cityrail",          # deprecated
    "rail_slow",         # deprecated
    "rail_fast",         # deprecated
    """
    PRIVATE = "private"
    EMERGENCY = "emergency"
    AUTHORITY = "authority"
    ARMY = "army"
    VIP = "vip"
    PASSENGER = "passenger"
    HOV = "hov"
    TAXI = "taxi"
    BUS = "bus"
    COACH = "coach"
    DELIVERY = "delivery"
    TRUCK = "truck"
    TRAILER = "trailer"
    TRAM = "tram"
    RAIL_URBAN = "rail_urban"
    RAIL = "rail"
    RAIL_ELECTRIC = "rail_electric"
    MOTORCYCLE = "motorcycle"
    MOPED = "moped"
    BICYCLE = "bicycle"
    PEDESTRIAN = "pedestrian"
    EVEHICLE = "evehicle"
    SHIP = "ship"
    CUSTOM1 = "custom1"
    CUSTOM2 = "custom2"


SUMO_VEHICLE_CLASSES: Tuple[str] = tuple(str(vehicle.value) for vehicle in VehicleType)


@unique
class NodeType(Enum):
    """
    Node types:
    If you leave out the type of the node, it is automatically guessed by netconvert but may not be the one you intended.
    The following types are possible, any other string is counted as an error and will yield in a program stop:
    taken from https://sumo.dlr.de/docs/Networks/PlainXML.html#connections_after_joining_nodes
    """

    # priority: Vehicles on a low-priority edge have to wait until vehicles on a high-priority edge
    # have passed the junction.
    PRIORITY = "priority"
    # traffic_light: The junction is controlled by a traffic light (priority rules are used to avoid collisions
    # if conflicting links have green light at the same time).
    TRAFFIC_LIGHT = "traffic_light"
    # traffic_light_unregulated: The junction is controlled by a traffic light without any further rules.
    # This may cause collision if unsafe signal plans are used.
    # Note, that collisions within the intersection will never be detected.
    TRAFFIC_LIGHT_UNREGULATED = "traffic_light_unregulated"
    # traffic_light_right_on_red: The junction is controlled by a traffic light as for type traffic_light.
    # Additionally, right-turning vehicles may drive in any phase whenever it is safe to do so (after stopping once).
    # This behavior is known as right-turn-on-red.
    TRAFFIC_LIGHT_RIGHT_ON_RED = "traffic_light_right_on_red"
    # right_before_left: Vehicles will let vehicles coming from their right side pass.
    RIGHT_BEFORE_LEFT = "right_before_left"
    # unregulated: The junction is completely unregulated - all vehicles may pass without braking;
    # Collision detection on the intersection is disabled but collisions beyond the intersection will
    # detected and are likely to occur.
    UNREGULATED = "unregulated"
    # priority_stop: This works like a priority-junction but vehicles on minor links always have to stop before passing
    PRIORITY_STOP = "priority_stop"
    # allway_stop: This junction works like an All-way stop
    ALLWAY_STOP = "allway_stop"
    # rail_signal: This junction is controlled by a rail signal. This type of junction/control is only useful for rails.
    RAIL_SIGNAL = "rail_signal"
    # rail_crossing: This junction models a rail road crossing.
    # It will allow trains to pass unimpeded and will restrict vehicles via traffic signals when a train is approaching.
    RAIL_CROSSING = "rail_crossing"
    # zipper: This junction connects edges where the number of lanes decreases and traffic needs
    # to merge zipper-style (late merging).
    ZIPPER = "zipper"
