from lxml import etree
import numpy as np
import warnings

import crdesigner.map_conversion.opendrive.cr_to_opendrive.utils.commonroad_ccosy_geometry_util as util


# Road class
class Road:
    counting = 20
    roads = {}
    crIdToOD = {}
    laneToLane = {}

    lane2lanelink = {}

    linkMap = {}

    CONST = 0.5
    EPSILON = 0.00001
    DEVIAT = 0.001
    STEP = 50

    def __init__(self, laneList, numberOfLanes, root, current, junctionId):

        # Supress RankWarning in polyfit
        warnings.simplefilter("ignore", np.RankWarning)

        Road.counting += 1
        Road.roads[Road.counting] = self
        Road.lane2lanelink[Road.counting] = {"succ": {}, "pred": {}}
        self.junctionId = junctionId

        # contains etree elements for lanelinks
        self.laneLink = {}

        self.links = {}
        self.innerLinks = {}
        for lane in laneList:
            self.links[lane.lanelet_id] = {
                "succ": lane.successor,
                "pred": lane.predecessor,
            }
        Road.linkMap[Road.counting] = self.links

        # determine center lane by finding where driving direction changes
        self.laneList = laneList
        self.numberOfLanes = numberOfLanes

        i = 0
        while i < self.numberOfLanes and laneList[i].adj_left_same_direction:
            i += 1

        self.centerNumber = i
        self.center = self.laneList[i].left_vertices

        for i in range(0, numberOfLanes):
            Road.crIdToOD[laneList[i].lanelet_id] = Road.counting

        self.root = root
        self.road = etree.SubElement(root, "road")

        self.link = self.setChildOfRoad("link")

        self.type = etree.SubElement(self.road, "type")
        self.type.set("s", str.format("{0:.16e}", 0))
        self.type.set("type", "town")

        # planView - here goes all the geometry stuff
        self.planView = self.setChildOfRoad("planView")
        length = self.setPlanView()

        self.elevationProfile = self.setChildOfRoad("elevationProfile")
        self.lateralProfile = self.setChildOfRoad("lateralProfile")
        self.lanes = self.setChildOfRoad("lanes")
        self.laneSections()

        # objects contain static obstacles
        self.objects = self.setChildOfRoad("objects")

        # signals contains traffic signs and traffic lights
        self.signals = self.setChildOfRoad("signals")

        self.road.set("name", "")
        self.road.set("length", str.format("{0:.16e}", length))

        self.road.set("id", str.format("{}", Road.counting))

        self.road.set("junction", str(junctionId))

        # add lane indices to links
        self.links["laneIndices"] = self.innerLinks

    def addJunctionLinkage(self, id, relation):
        self.elementType = etree.SubElement(self.link, relation)
        self.elementType.set("elementId", str(id))
        self.elementType.set("elementType", "junction")
        if relation == "successor":
            self.elementType.set("contactPoint", "start")
        elif relation == "predecessor":
            self.elementType.set("contactPoint", "end")
        else:
            raise ValueError("Relation must be either successor or predecessor")

    def addSimpleLinkage(
        self, key, links, lenSucc, lenPred, curLinksLanelets, lane2lane
    ):
        if lenSucc == 1:
            successor = self.elementType = etree.SubElement(self.link, "successor")
            successor.set("elementType", "road")
            successor.set("elementId", str(links["succ"][0]))
            successor.set("contactPoint", "start")

            # lane2lane linkage
            for laneId, successors in lane2lane["succ"].items():
                for succId in successors:
                    succ = etree.SubElement(self.laneLink[laneId], "successor")
                    succ.set("id", str(succId))

        if lenPred == 1:
            predecessor = self.elementType = etree.SubElement(self.link, "predecessor")
            predecessor.set("elementType", "road")
            predecessor.set("elementId", str(links["pred"][0]))
            predecessor.set("contactPoint", "end")

            # lane2lane linkage
            for laneId, predecessors in lane2lane["pred"].items():
                for predId in predecessors:
                    pred = etree.SubElement(self.laneLink[laneId], "predecessor")
                    pred.set("id", str(predId))

    def setChildOfRoad(self, name):
        return etree.SubElement(self.road, name)

    def setPlanView(self):
        self.center = util.remove_duplicates_from_polyline(self.center)
        self.center = util.resample_polyline(self.center, 1)
        curv = util.compute_curvature_from_polyline(self.center)
        arclength = util.compute_pathlength_from_polyline(self.center)
        hdg = util.compute_orientation_from_polyline(self.center)

        if len(self.center) < 1:
            return

        if abs(curv[0]) < self.EPSILON and abs(curv[1]) < self.EPSILON:
            # start with line, if really low curvature
            this_length = arclength[1] - arclength[0]
            self.printLine(
                arclength[0],
                self.center[0][0],
                self.center[0][1],
                hdg[0],
                this_length,
            )

        else:
            # start with spiral if the curvature is slightly higher
            this_length = arclength[1] - arclength[0]
            self.printSpiral(
                arclength[0],
                self.center[0][0],
                self.center[0][1],
                hdg[0],
                this_length,
                curv[0],
                curv[1],
            )

        # loop through all the points in the polyline check if
        # the delta curvature is below DEVIAT
        # could be more smooth, if needed, with resampling with a
        # smaller stepsize
        for i in range(2, len(self.center)):

            if abs(curv[i] - curv[i - 1]) > self.DEVIAT:

                this_length = arclength[i] - arclength[i - 1]
                self.printSpiral(
                    arclength[i - 1],
                    self.center[i - 1][0],
                    self.center[i - 1][1],
                    hdg[i - 1],
                    this_length,
                    curv[i - 1],
                    curv[i],
                )

            else:

                this_length = arclength[i] - arclength[i - 1]
                if abs(curv[i - 1]) < self.EPSILON:
                    self.printLine(
                        arclength[i - 1],
                        self.center[i - 1][0],
                        self.center[i - 1][1],
                        hdg[i - 1],
                        this_length,
                    )

                else:
                    self.printArc(
                        arclength[i - 1],
                        self.center[i - 1][0],
                        self.center[i - 1][1],
                        hdg[i - 1],
                        this_length,
                        curv[i - 1],
                    )

        return arclength[-1]

    # xodr for lines
    def printLine(self, s, x, y, hdg, length):
        geometry = etree.SubElement(self.planView, "geometry")
        geometry.set("s", str.format("{0:.16e}", s))
        geometry.set("x", str.format("{0:.16e}", x))
        geometry.set("y", str.format("{0:.16e}", y))
        geometry.set("hdg", str.format("{0:.16e}", hdg))
        geometry.set("length", str.format("{0:.16e}", length))

        line = etree.SubElement(geometry, "line")

    # xodr for spirals
    def printSpiral(self, s, x, y, hdg, length, curvStart, curvEnd):

        geometry = etree.SubElement(self.planView, "geometry")
        geometry.set("s", str.format("{0:.16e}", s))
        geometry.set("x", str.format("{0:.16e}", x))
        geometry.set("y", str.format("{0:.16e}", y))
        geometry.set("hdg", str.format("{0:.16e}", hdg))
        geometry.set("length", str.format("{0:.16e}", length))

        spiral = etree.SubElement(geometry, "spiral")
        spiral.set("curvStart", str.format("{0:.16e}", curvStart))
        spiral.set("curvEnd", str.format("{0:.16e}", curvEnd))

    # xodr for arcs
    def printArc(self, s, x, y, hdg, length, curvature):

        geometry = etree.SubElement(self.planView, "geometry")
        geometry.set("s", str.format("{0:.16e}", s))
        geometry.set("x", str.format("{0:.16e}", x))
        geometry.set("y", str.format("{0:.16e}", y))
        geometry.set("hdg", str.format("{0:.16e}", hdg))
        geometry.set("length", str.format("{0:.16e}", length))

        arc = etree.SubElement(geometry, "arc")
        arc.set("curvature", str.format("{0:.16e}", curvature))

    def printSignal(self, sig):
        signal = etree.SubElement(self.signals, "signal")
        signal.set("s", str.format("{0:.16e}", sig.s))
        signal.set("t", str.format("{0:.16e}", sig.t))
        signal.set("id", sig.id)
        signal.set("name", sig.name)
        signal.set("dynamic", sig.dynamic)
        signal.set("orientation", sig.orientation)
        signal.set("zOffset", sig.zOffset)
        signal.set("country", sig.country)
        signal.set("type", sig.type)
        signal.set("subtype", sig.subtype)
        signal.set("coutryRevision", sig.coutryRevision)
        signal.set("value", sig.value)
        signal.set("unit", sig.unit)
        signal.set("width", sig.width)
        signal.set("height", sig.height)
        signal.set("hOffset", sig.hOffset)

    def printSignalRef(self, sigRef):
        signalRef = etree.SubElement(self.signals, "signalReference")
        signalRef.set("s", str.format("{0:.16e}", sigRef.s))
        signalRef.set("t", str.format("{0:.16e}", sigRef.t))
        signalRef.set("id", sigRef.id)
        signalRef.set("orientation", sigRef.orientation)

    # every road node in xodr conatains also a lanes node with 1 or
    # more laneSections: left, center (width 0), right
    def laneSections(self):
        section = etree.SubElement(self.lanes, "laneSection")
        # i guess this s should not be hardcoded
        section.set("s", str.format("{0:.16e}", 0))

        center = etree.SubElement(section, "center")
        self.laneHelp(0, "driving", 0, center, np.array([]), [])

        left = etree.SubElement(section, "left")
        right = etree.SubElement(section, "right")

        # iterates through all the laneSection elements
        for i in range(0, len(self.laneList)):

            cur = self.laneList[i]

            # calculate the width of a street
            # for some reason it looks better without resampling
            widthList = np.array(
                list(
                    map(
                        lambda x, y: np.linalg.norm(x - y),
                        cur.right_vertices,
                        cur.left_vertices,
                    )
                )
            )

            distList = util.compute_pathlength_from_polyline(cur.center_vertices)


            laneId = i - self.centerNumber

            # lanelets to the right should get a negative id
            if laneId <= 0:
                self.laneHelp(laneId - 1, "driving", 0, right, widthList, distList)
                Road.laneToLane[self.laneList[i].lanelet_id] = laneId - 1
                self.innerLinks[self.laneList[i].lanelet_id] = laneId - 1

            # lanelets to the left should get a positive id -> opposite driving direction
            else:
                self.laneHelp(laneId, "driving", 0, left, widthList, distList)
                Road.laneToLane[self.laneList[i].lanelet_id] = laneId
                self.innerLinks[self.laneList[i].lanelet_id] = laneId

    # nice idea to reuse the subelement generation for left center and right
    # produces something like:
    # <lane id="1" type="driving" level="false">
    #     <link/>
    #     <width sOffset="0.0000000000000000e+00" a="3.4996264749930002e+00" b="0.0000000000000000e+00" c="0.0000000000000000e+00" d="0.0000000000000000e+00"/>
    #     <roadMark sOffset="0.0000000000000000e+00" type="solid" weight="standard" color="standard" width="1.3000000000000000e-01"/>
    # </lane>
    def laneHelp(self, id, type, level, pos, widthList, distList):

        lanePos = etree.SubElement(pos, "lane")
        lanePos.set("id", str.format("{}", id))
        lanePos.set("type", type)
        lanePos.set("level", "false")
        laneLink = etree.SubElement(lanePos, "link")
        self.laneLink[id] = laneLink

        x = [n * self.STEP for n in range(len(widthList))]

        for w in widthList:
            w += self.STEP

        # just do it the good ol' way
        if widthList.size > 1:

            # just trying another method:
            widthList = [widthList[0], widthList[-1]]
            x = [distList[0], distList[-1]]

            b, a = np.polyfit(x, widthList, 1)


        if id != 0:
            # this should maybe not be hardcoded
            width = etree.SubElement(lanePos, "width")
            width.set("sOffset", str.format("{0:.16e}", 0))
            width.set("a", str.format("{0:.16e}", a))
            width.set("b", str.format("{0:.16e}", b))
            width.set("c", str.format("{0:.16e}", 0))
            width.set("d", str.format("{0:.16e}", 0))

        roadmark = etree.SubElement(lanePos, "roadMark")
        # this should maybe not be hardcoded
        roadmark.set("sOffset", str.format("{0:.16e}", 0))
        roadmark.set("type", "solid")
        roadmark.set("weight", "standard")
        roadmark.set("color", "standard")
        roadmark.set("width", str.format("{0:.16e}", 0.13))
