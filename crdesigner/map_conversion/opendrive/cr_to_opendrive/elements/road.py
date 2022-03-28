from lxml import etree
import numpy as np
import warnings
from typing import List, Dict

import crdesigner.map_conversion.opendrive.cr_to_opendrive.utils.commonroad_ccosy_geometry_util as util
from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.sign import Sign

from commonroad.scenario.lanelet import Lanelet
from commonroad.geometry.polyline_util import compute_polyline_orientations, resample_polyline_with_distance, compute_polyline_curvatures, compute_polyline_lengths


class Road:
    """
    This class adds road child element to OpenDRIVE root element
    and converts CommonRoad lanelets to OpenDRIVE roads.
    """
    counting = 20
    roads = {}
    cr_id_to_od = {}
    lane_to_lane = {}

    lane_2_lane_link = {}

    link_map = {}

    CONST = 0.5
    EPSILON = 0.00001
    DEVIAT = 0.001
    STEP = 50

    def __init__(self, lane_list: List[Lanelet], number_of_lanes: int, root: etree._Element,
                 current: Lanelet, junction_id: int) -> None:
        """
        This function let class road to intialize the object with lane_list, number_of_lanes, root etree element,
        current lanelet, junction_id and converts the CommonRoad roads into OpenDRIVE roads.

        :param lane_list: list of lanelets
        :param number_of_lanes: number of lanes on the road
        :param root: OpenDRIVE etree element
        :param current: current lanelet
        :param junction_id: id of junction
        """
        # Supress RankWarning in polyfit
        warnings.simplefilter("ignore", np.RankWarning)

        Road.counting += 1
        Road.roads[Road.counting] = self
        Road.lane_2_lane_link[Road.counting] = {"succ": {}, "pred": {}}
        self.junction_id = junction_id

        # contains etree elements for lanelinks
        self.lane_link = {}

        self.links = {}
        self.inner_links = {}
        for lane in lane_list:
            self.links[lane.lanelet_id] = {
                "succ": lane.successor,
                "pred": lane.predecessor,
            }
        Road.link_map[Road.counting] = self.links

        # determine center lane by finding where driving direction changes
        self.lane_list = lane_list
        self.number_of_lanes = number_of_lanes

        i = 0
        while i < self.number_of_lanes and lane_list[i].adj_left_same_direction:
            i += 1

        self.center_number = i
        self.center = self.lane_list[i].left_vertices

        for i in range(0, number_of_lanes):
            Road.cr_id_to_od[lane_list[i].lanelet_id] = Road.counting

        self.root = root
        self.road = etree.SubElement(root, "road")

        self.link = self.set_child_of_road("link")

        self.type = etree.SubElement(self.road, "type")
        self.type.set("s", str.format("{0:.16e}", 0))
        self.type.set("type", "town")

        # planView - here goes all the geometry stuff
        self.plan_view = self.set_child_of_road("planView")
        length = self.set_plan_view()

        self.elevation_profile = self.set_child_of_road("elevationProfile")
        self.lateral_profile = self.set_child_of_road("lateralProfile")
        self.lanes = self.set_child_of_road("lanes")
        self.lane_sections()

        # objects contain static obstacles
        self.objects = self.set_child_of_road("objects")

        # signals contains traffic signs and traffic lights
        self.signals = self.set_child_of_road("signals")

        self.road.set("name", "")
        self.road.set("length", str.format("{0:.16e}", length))

        self.road.set("id", str.format("{}", Road.counting))

        self.road.set("junction", str(junction_id))

        # add lane indices to links
        self.links["laneIndices"] = self.inner_links

    def add_junction_linkage(self, id: int, relation: str) -> None:
        """
        This function adds relation(successor/predecessor) child element to link parent element.

        :param id: element id
        :param relation: successor/predessor
        """
        self.element_type = etree.SubElement(self.link, relation)
        self.element_type.set("elementId", str(id))
        self.element_type.set("elementType", "junction")
        if relation == "successor":
            self.element_type.set("contactPoint", "start")
        elif relation == "predecessor":
            self.element_type.set("contactPoint", "end")
        else:
            raise ValueError("Relation must be either successor or predecessor")

    def add_simple_linkage(self, key: int, links: Dict[str, List[int]], len_succ: int, len_pred: int,
                           curl_links_lanelets: Dict[int or str, Dict[str, List[int]]],
                           lane_2_lane: Dict[str, Dict[int, List[int]]]) -> None:
        """
        This function add successor/predecessor child element to link parent element and
        each successor/predecessor are linked with its correponding landLink id.
        This happens when a road has exactly one successor/predecessor.

        :param key: curKey
        :param links: A dictionary with successor/predecessor as key and list of road linkage id as value
        :param len_succ: Number of successors
        :param len_pred: Number of predecessors
        :param curl_links_lanelets: A dictionary of road ids and road links with all linkage information
        such as mergeLinkage, roadLinkage, laneIndices
        :param lane_2_lane: A dictionary with successor/predecessor
        as key and dictionaries of corresponding ids as value
        """
        if len_succ == 1:
            successor = self.element_type = etree.SubElement(self.link, "successor")
            successor.set("elementType", "road")
            successor.set("elementId", str(links["succ"][0]))
            successor.set("contactPoint", "start")

            # lane_2_lane linkage
            for lane_id, successors in lane_2_lane["succ"].items():
                for succ_id in successors:
                    succ = etree.SubElement(self.lane_link[lane_id], "successor")
                    succ.set("id", str(succ_id))

        if len_pred == 1:
            predecessor = self.element_type = etree.SubElement(self.link, "predecessor")
            predecessor.set("elementType", "road")
            predecessor.set("elementId", str(links["pred"][0]))
            predecessor.set("contactPoint", "end")

            # lane_2_lane linkage
            for lane_id, predecessors in lane_2_lane["pred"].items():
                for predId in predecessors:
                    pred = etree.SubElement(self.lane_link[lane_id], "predecessor")
                    pred.set("id", str(predId))

    def set_child_of_road(self, name: str) -> etree:
        """
        This function creates child element(name) and add it to road parent element.

        :param name: An elment name to be added to road parent element.
        :return: An etree road element with added child element.
        """
        return etree.SubElement(self.road, name)

    def set_plan_view(self) -> float:
        """
        This function compute geometric elements required for planview.
        Geometric elements such as line, spiral, curve, arclength are computed.

        :return: Last item of arclength list
        """
        self.center = util.remove_duplicates_from_polyline(self.center)
        self.center = resample_polyline_with_distance(self.center, 1)
        curv = compute_polyline_curvatures(self.center)
        arclength = compute_polyline_lengths(self.center)
        hdg = compute_polyline_orientations(self.center)

        if len(self.center) < 1:
            return

        if abs(curv[0]) < self.EPSILON and abs(curv[1]) < self.EPSILON:
            # start with line, if really low curvature
            this_length = arclength[1] - arclength[0]
            self.print_line(
                arclength[0],
                self.center[0][0],
                self.center[0][1],
                hdg[0],
                this_length,
            )

        else:
            # start with spiral if the curvature is slightly higher
            this_length = arclength[1] - arclength[0]

            self.print_spiral(
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
                self.print_spiral(
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
                    self.print_line(
                        arclength[i - 1],
                        self.center[i - 1][0],
                        self.center[i - 1][1],
                        hdg[i - 1],
                        this_length,
                    )

                else:
                    self.print_arc(
                        arclength[i - 1],
                        self.center[i - 1][0],
                        self.center[i - 1][1],
                        hdg[i - 1],
                        this_length,
                        curv[i - 1],
                    )
        return arclength[-1]

    # xodr for lines
    def print_line(self, s: np.float64, x: np.float64, y: np.float64, hdg: np.float64, length: np.float64) -> None:
        """
        This function print line on OpenDrive file.
        Geometry child element is created with corresponding attributes and added to planview parent element.
        Line child element is added to geometry parent element.

        :param s: s-coordinate of start position
        :param x: Start position (x inertial)
        :param y: Start position (y inertial)
        :param hdg: Start orientation (inertial heading)
        :param lenght: Length of the element’s reference line
        """
        geometry = etree.SubElement(self.plan_view, "geometry")
        geometry.set("s", str.format("{0:.16e}", s))
        geometry.set("x", str.format("{0:.16e}", x))
        geometry.set("y", str.format("{0:.16e}", y))
        geometry.set("hdg", str.format("{0:.16e}", hdg))
        geometry.set("length", str.format("{0:.16e}", length))

    # xodr for spirals
    def print_spiral(self, s: np.float64, x: np.float64, y: np.float64, hdg: np.float64,
                     length: np.float64, curv_start: np.float64, curv_end: np.float64) -> None:
        """
        This function print spiral on OpenDrive file.
        Geometry child element is created with corresponding attributes and added to planview parent element.
        Spiral child element is added to geometry parent element.

        :param s: s-coordinate of start position
        :param x: Start position (x inertial)
        :param y: Start position (y inertial)
        :param hdg: Start orientation (inertial heading)
        :param lenght: Length of the element’s reference line
        :param curv_start: Curvature at the start of the element
        :param curv_end: Curvature at the end of the element
        """
        geometry = etree.SubElement(self.plan_view, "geometry")
        geometry.set("s", str.format("{0:.16e}", s))
        geometry.set("x", str.format("{0:.16e}", x))
        geometry.set("y", str.format("{0:.16e}", y))
        geometry.set("hdg", str.format("{0:.16e}", hdg))
        geometry.set("length", str.format("{0:.16e}", length))

        spiral = etree.SubElement(geometry, "spiral")
        spiral.set("curvStart", str.format("{0:.16e}", curv_start))
        spiral.set("curvEnd", str.format("{0:.16e}", curv_end))

    # xodr for arcs
    def print_arc(self, s: np.float64, x: np.float64, y: np.float64, hdg: np.float64,
                  length: np.float64, curvature: np.float64) -> None:
        """
        This function print arc on OpenDrive file.
        Geometry child element is created with corresponding attributes and added to planview parent element.
        Arc child element is added to geometry parent element.

        :param s: s-coordinate of start position
        :param x: Start position (x inertial)
        :param y: Start position (y inertial)
        :param hdg: Start orientation (inertial heading)
        :param lenght: Length of the element’s reference line
        :param curvature: Constant curvature throughout the element
        """
        geometry = etree.SubElement(self.plan_view, "geometry")
        geometry.set("s", str.format("{0:.16e}", s))
        geometry.set("x", str.format("{0:.16e}", x))
        geometry.set("y", str.format("{0:.16e}", y))
        geometry.set("hdg", str.format("{0:.16e}", hdg))
        geometry.set("length", str.format("{0:.16e}", length))

        arc = etree.SubElement(geometry, "arc")
        arc.set("curvature", str.format("{0:.16e}", curvature))

    def print_signal(self, sig: Sign) -> None:
        """
        This function print traffic sign on OpenDrive file.
        Signal child element is created with corresponding attributes and added to road parent element.

        :param sig: Traffic sign
        """
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
        signal.set("countryRevision", sig.country_revision)
        signal.set("value", sig.value)
        signal.set("unit", sig.unit)
        signal.set("width", sig.width)
        signal.set("height", sig.height)
        signal.set("hOffset", sig.hOffset)

    def print_signal_ref(self, sig_ref: Sign) -> None:
        """
        This function print signal reference on OpenDrive file.
        Signal reference child element is created with corresponding attributes and added to road parent element.

        :param sig_ref: Traffic sign reference
        """
        signal_ref = etree.SubElement(self.signals, "signalReference")
        signal_ref.set("s", str.format("{0:.16e}", sig_ref.s))
        signal_ref.set("t", str.format("{0:.16e}", sig_ref.t))
        signal_ref.set("id", sig_ref.id)
        signal_ref.set("orientation", sig_ref.orientation)

    def lane_sections(self) -> None:
        """
        This function add laneSection child element to road parent element and
        left, center (width 0), right elements are added to laneSection.
        Every road node in xodr contains also a lanes node with 1 or
        More lane_sections: left, center (width 0), right
        """
        section = etree.SubElement(self.lanes, "laneSection")
        # i guess this s should not be hardcoded
        section.set("s", str.format("{0:.16e}", 0))

        center = etree.SubElement(section, "center")
        self.lane_help(0, "driving", 0, center, np.array([]), [])

        left = etree.SubElement(section, "left")
        right = etree.SubElement(section, "right")

        # iterates through all the laneSection elements
        for i in range(0, len(self.lane_list)):

            cur = self.lane_list[i]

            # calculate the width of a street
            # for some reason it looks better without resampling
            width_list = np.array(
                list(
                    map(
                        lambda x, y: np.linalg.norm(x - y),
                        cur.right_vertices,
                        cur.left_vertices,
                    )
                )
            )

            dist_list = util.compute_pathlength_from_polyline(cur.center_vertices)
            lane_id = i - self.center_number

            # lanelets to the right should get a negative id
            if lane_id <= 0:
                self.lane_help(lane_id - 1, "driving", 0, right, width_list, dist_list)
                Road.lane_to_lane[self.lane_list[i].lanelet_id] = lane_id - 1
                self.inner_links[self.lane_list[i].lanelet_id] = lane_id - 1

            # lanelets to the left should get a positive id -> opposite driving direction
            else:
                self.lane_help(lane_id, "driving", 0, left, width_list, dist_list)
                Road.lane_to_lane[self.lane_list[i].lanelet_id] = lane_id
                self.inner_links[self.lane_list[i].lanelet_id] = lane_id

    # nice idea to reuse the subelement generation for left center and right
    # produces something like:
    # <lane id="1" type="driving" level="false">
    #     <link/>
    #     <width sOffset="0.0000000000000000e+00" a="3.4996264749930002e+00"
    #       b="0.0000000000000000e+00" c="0.0000000000000000e+00" d="0.0000000000000000e+00"/>
    #     <roadMark sOffset="0.0000000000000000e+00" type="solid" weight="standard"
    #       color="standard" width="1.3000000000000000e-01"/>
    # </lane>

    def lane_help(self, id: int, type: str, level: int, pos: etree._Element,
                  width_list: List[Lanelet], dist_list: np.ndarray) -> None:
        """
        This function add lane child element to parent element which may be right, left or center.
        Link, width, roadMark elements are also added to lane element.

        :param: lane_id
        :param: Type
        :param: Level
        :param: Etree element that can be right, left or center
        :param: Width of a street
        :param: Path length of the polyline
        """
        lane_pos = etree.SubElement(pos, "lane")
        lane_pos.set("id", str.format("{}", id))
        lane_pos.set("type", type)
        lane_pos.set("level", "false")
        lane_link = etree.SubElement(lane_pos, "link")
        self.lane_link[id] = lane_link

        x = [n * self.STEP for n in range(len(width_list))]

        for w in width_list:
            w += self.STEP

        # just do it the good ol' way
        if width_list.size > 1:

            # just trying another method:
            width_list = [width_list[0], width_list[-1]]
            x = [dist_list[0], dist_list[-1]]

            b, a = np.polyfit(x, width_list, 1)

        if id != 0:
            # this should maybe not be hardcoded
            width = etree.SubElement(lane_pos, "width")
            width.set("sOffset", str.format("{0:.16e}", 0))
            width.set("a", str.format("{0:.16e}", a))
            width.set("b", str.format("{0:.16e}", b))
            width.set("c", str.format("{0:.16e}", 0))
            width.set("d", str.format("{0:.16e}", 0))

        roadmark = etree.SubElement(lane_pos, "roadMark")
        # this should maybe not be hardcoded
        roadmark.set("sOffset", str.format("{0:.16e}", 0))
        roadmark.set("type", "solid")
        roadmark.set("weight", "standard")
        roadmark.set("color", "standard")
        roadmark.set("width", str.format("{0:.16e}", 0.13))
