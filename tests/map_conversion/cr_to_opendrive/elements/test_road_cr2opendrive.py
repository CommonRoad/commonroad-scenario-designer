import unittest

import numpy as np
from commonroad.geometry.polyline_util import compute_polyline_curvatures, compute_polyline_lengths, \
    compute_polyline_orientations
from lxml import etree
from commonroad.scenario.traffic_sign import TrafficSign, TrafficSignElement, TrafficSignIDZamunda

from crdesigner.configurations.get_configs import get_configs
from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.road import Road
from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.sign import Sign
from crdesigner.map_conversion.opendrive.opendrive_conversion.conversion_lanelet_network import ConversionLaneletNetwork
from tests.map_conversion.opendrive_conversion.test_conversion_lanelet_network import init_lanelet_from_id, \
    add_lanelets_to_network


class TestRoad(unittest.TestCase):

    def setUp(self):
        Road.counting = 20
        Road.cr_id_to_od = dict()
        Road.lane_to_lane = dict()
        Road.lane_2_lane_link = dict()
        Road.link_map = dict()

    def test_initialize_road(self):
        # Given
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        conversion_lanelet_1 = init_lanelet_from_id('79.0.-3.-1')
        conversion_lanelet_2 = init_lanelet_from_id('89.0.4.-1')

        add_lanelets_to_network(conversion_lanelet_network, [conversion_lanelet_1, conversion_lanelet_2])

        lane_list = conversion_lanelet_network.lanelets
        number_of_lanes = 2
        root = etree.Element("OpenDRIVE")
        current = etree.Element("OpenDRIVE")
        junction_id = -1

        # When
        road = Road(lane_list, number_of_lanes, root, current, junction_id)

        # Then
        self.assertEqual(21, Road.counting)
        self.assertEqual({"succ": {}, "pred": {}}, Road.lane_2_lane_link[Road.counting])
        self.assertEqual(-1, road.junction_id)
        expected_links = {'79.0.-3.-1': {'pred': [], 'succ': []}, '89.0.4.-1': {'pred': [], 'succ': []},
                          'laneIndices': {'79.0.-3.-1': -1, '89.0.4.-1': 1}}
        self.assertEqual(expected_links, road.links)
        self.assertEqual(expected_links, Road.link_map[Road.counting])
        self.assertEqual(lane_list, road.lane_list)
        self.assertEqual(number_of_lanes, road.number_of_lanes)
        self.assertEqual(0, road.center_number)

        expected_center = np.array([[0., 1.], [1., 1.], [2., 1.]])
        self.assertTrue((expected_center == road.center).all())

        expected_cr_to_od = {'79.0.-3.-1': 21, '89.0.4.-1': 21}
        self.assertEqual(expected_cr_to_od, road.cr_id_to_od)
        self.assertEqual(root, road.root)

        self.assertEqual("road", road.root[0].tag)

        self.assertEqual("link", road.road[0].tag)

        self.assertEqual("type", road.road[1].tag)
        self.assertEqual(str.format("{0:.16e}", 0), road.road[1].get("s"))
        self.assertEqual("town", road.road[1].get("type"))
        self.assertEqual("type", road.type.tag)
        self.assertEqual(str.format("{0:.16e}", 0), road.type.get("s"))
        self.assertEqual("town", road.type.get("type"))

        self.assertEqual("planView", road.road[2].tag)
        self.assertEqual("elevationProfile", road.road[3].tag)
        self.assertEqual("elevationProfile", road.elevation_profile.tag)
        self.assertEqual("lateralProfile", road.road[4].tag)
        self.assertEqual("lateralProfile", road.lateral_profile.tag)
        self.assertEqual("lanes", road.road[5].tag)
        self.assertEqual("lanes", road.lanes.tag)

        # assert lane_section

        self.assertEqual("objects", road.road[6].tag)
        self.assertEqual("objects", road.objects.tag)
        self.assertEqual("signals", road.road[7].tag)
        self.assertEqual("signals", road.signals.tag)

        self.assertEqual("", road.road.attrib["name"])
        self.assertEqual(str(21), road.road.attrib["id"])
        self.assertEqual("-1", road.road.attrib["junction"])

        expected_lane_indices = {'79.0.-3.-1': -1, '89.0.4.-1': 1}
        self.assertEqual(expected_lane_indices, road.links["laneIndices"])

    def test_add_junction_linkage_successor(self):
        # Given
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        conversion_lanelet_1 = init_lanelet_from_id('79.0.-3.-1')
        conversion_lanelet_2 = init_lanelet_from_id('89.0.4.-1')

        add_lanelets_to_network(conversion_lanelet_network, [conversion_lanelet_1, conversion_lanelet_2])

        lane_list = conversion_lanelet_network.lanelets
        number_of_lanes = 2
        root = etree.Element("OpenDRIVE")
        current = etree.Element("OpenDRIVE")
        junction_id = -1
        road = Road(lane_list, number_of_lanes, root, current, junction_id)
        id = 1
        relation = "successor"

        # When
        road.add_junction_linkage(id, relation)

        # Then
        self.assertEqual("successor", road.element_type.tag)
        self.assertEqual("1", road.element_type.get("elementId"))
        self.assertEqual("junction", road.element_type.get("elementType"))
        self.assertEqual("start", road.element_type.get("contactPoint"))

    def test_add_junction_linkage_predecessor(self):
        # Given
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        conversion_lanelet_1 = init_lanelet_from_id('79.0.-3.-1')
        conversion_lanelet_2 = init_lanelet_from_id('89.0.4.-1')

        add_lanelets_to_network(conversion_lanelet_network, [conversion_lanelet_1, conversion_lanelet_2])

        lane_list = conversion_lanelet_network.lanelets
        number_of_lanes = 2
        root = etree.Element("OpenDRIVE")
        current = etree.Element("OpenDRIVE")
        junction_id = -1
        road = Road(lane_list, number_of_lanes, root, current, junction_id)
        id = 1
        relation = "predecessor"

        # When
        road.add_junction_linkage(id, relation)

        # Then
        self.assertEqual("predecessor", road.element_type.tag)
        self.assertEqual("1", road.element_type.get("elementId"))
        self.assertEqual("junction", road.element_type.get("elementType"))
        self.assertEqual("end", road.element_type.get("contactPoint"))

    def test_add_simple_linkage(self):
        # Given
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        conversion_lanelet_1 = init_lanelet_from_id('79.0.-3.-1')
        conversion_lanelet_2 = init_lanelet_from_id('89.0.4.-1')

        add_lanelets_to_network(conversion_lanelet_network, [conversion_lanelet_1, conversion_lanelet_2])

        lane_list = conversion_lanelet_network.lanelets
        number_of_lanes = 2
        root = etree.Element("OpenDRIVE")
        current = etree.Element("OpenDRIVE")
        junction_id = -1

        road = Road(lane_list, number_of_lanes, root, current, junction_id)

        key = 21
        links = {'succ': [22, 22, 22, 22, 22, 22, 22, 22, 22], 'pred': []}
        len_succ = 1
        len_pred = 0
        curl_links_lanelets = {}
        lane_2_lane = {'succ': {0: [1]}, 'pred': {}}

        # When
        road.add_simple_linkage(key, links, len_succ, len_pred, curl_links_lanelets, lane_2_lane)

        # Then
        self.assertEqual("successor", road.link[-1].tag)
        self.assertEqual("road", road.link[-1].get("elementType"))
        self.assertEqual("22", road.link[-1].get("elementId"))
        self.assertEqual("start", road.link[-1].get("contactPoint"))

    def test_set_child_of_road(self):
        # Given
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        conversion_lanelet_1 = init_lanelet_from_id('79.0.-3.-1')
        conversion_lanelet_2 = init_lanelet_from_id('89.0.4.-1')

        add_lanelets_to_network(conversion_lanelet_network, [conversion_lanelet_1, conversion_lanelet_2])

        lane_list = conversion_lanelet_network.lanelets
        number_of_lanes = 2
        root = etree.Element("OpenDRIVE")
        current = etree.Element("OpenDRIVE")
        junction_id = -1
        road = Road(lane_list, number_of_lanes, root, current, junction_id)
        name = "child_name"

        # When
        road.set_child_of_road(name)

        # Then
        self.assertEqual(name, road.road[len(road.road) - 1].tag)

    def test_set_plan_view(self):
        # Given
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        conversion_lanelet_1 = init_lanelet_from_id('79.0.-3.-1')
        conversion_lanelet_2 = init_lanelet_from_id('89.0.4.-1')

        add_lanelets_to_network(conversion_lanelet_network, [conversion_lanelet_1, conversion_lanelet_2])

        lane_list = conversion_lanelet_network.lanelets
        number_of_lanes = 2
        root = etree.Element("OpenDRIVE")
        current = etree.Element("OpenDRIVE")
        junction_id = -1
        road = Road(lane_list, number_of_lanes, root, current, junction_id)
        name = "child_name"

        # When
        last_item_arclength = road.set_plan_view()

        # Then
        expected_center = np.array([[0., 1.], [1., 1.], [2., 1.]])
        self.assertTrue((expected_center == road.center).all())
        self.assertEqual(2.0, last_item_arclength)

        self.assertEqual("geometry", road.plan_view[-1].tag)
        self.assertEqual(str.format("{0:.16e}", 1), road.plan_view[-1].get("s"))
        self.assertEqual(str.format("{0:.16e}", 1), road.plan_view[-1].get("x"))
        self.assertEqual(str.format("{0:.16e}", 1), road.plan_view[-1].get("y"))
        self.assertEqual(str.format("{0:.16e}", 0), road.plan_view[-1].get("hdg"))
        self.assertEqual(str.format("{0:.16e}", 1), road.plan_view[-1].get("length"))

        self.assertEqual("geometry", road.plan_view[-2].tag)
        self.assertEqual(str.format("{0:.16e}", 0), road.plan_view[-2].get("s"))
        self.assertEqual(str.format("{0:.16e}", 0), road.plan_view[-2].get("x"))
        self.assertEqual(str.format("{0:.16e}", 1), road.plan_view[-2].get("y"))
        self.assertEqual(str.format("{0:.16e}", 0), road.plan_view[-2].get("hdg"))
        self.assertEqual(str.format("{0:.16e}", 1), road.plan_view[-2].get("length"))

    def test_print_line(self):
        # Given
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        conversion_lanelet_1 = init_lanelet_from_id('79.0.-3.-1')
        conversion_lanelet_2 = init_lanelet_from_id('89.0.4.-1')

        add_lanelets_to_network(conversion_lanelet_network, [conversion_lanelet_1, conversion_lanelet_2])

        lane_list = conversion_lanelet_network.lanelets
        number_of_lanes = 2
        root = etree.Element("OpenDRIVE")
        current = etree.Element("OpenDRIVE")
        junction_id = -1
        road = Road(lane_list, number_of_lanes, root, current, junction_id)
        curv = compute_polyline_curvatures(road.center) if len(road.center) > 2 else np.array([[0.0], [0.0]])
        arclength = compute_polyline_lengths(road.center)
        hdg = compute_polyline_orientations(road.center)
        this_length = arclength[1] - arclength[0]
        s = 1.0
        x = 0.
        y = 1.
        hdg = 4
        length = 1.45

        # When
        road.print_line(s, x, y, hdg, length)

        # Then
        self.assertEqual("geometry", road.plan_view[-1].tag)
        self.assertEqual(str.format("{0:.16e}", s), road.plan_view[-1].get("s"))
        self.assertEqual(str.format("{0:.16e}", x), road.plan_view[-1].get("x"))
        self.assertEqual(str.format("{0:.16e}", y), road.plan_view[-1].get("y"))
        self.assertEqual(str.format("{0:.16e}", hdg), road.plan_view[-1].get("hdg"))
        self.assertEqual(str.format("{0:.16e}", length), road.plan_view[-1].get("length"))

    def test_print_spiral(self):
        # Given
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        conversion_lanelet_1 = init_lanelet_from_id('79.0.-3.-1')
        conversion_lanelet_2 = init_lanelet_from_id('89.0.4.-1')

        add_lanelets_to_network(conversion_lanelet_network, [conversion_lanelet_1, conversion_lanelet_2])

        lane_list = conversion_lanelet_network.lanelets
        number_of_lanes = 2
        root = etree.Element("OpenDRIVE")
        current = etree.Element("OpenDRIVE")
        junction_id = -1
        road = Road(lane_list, number_of_lanes, root, current, junction_id)
        s = 1.0
        x = 0.0
        y = 1.0
        hdg = 4.0
        length = 1.45
        curv_start = 0.0
        curv_end = 1.5

        # When
        road.print_spiral(s, x, y, hdg, length, curv_start, curv_end)

        # Then
        self.assertEqual("geometry", road.plan_view[-1].tag)
        self.assertEqual(str.format("{0:.16e}", s), road.plan_view[-1].get("s"))
        self.assertEqual(str.format("{0:.16e}", x), road.plan_view[-1].get("x"))
        self.assertEqual(str.format("{0:.16e}", y), road.plan_view[-1].get("y"))
        self.assertEqual(str.format("{0:.16e}", hdg), road.plan_view[-1].get("hdg"))
        self.assertEqual(str.format("{0:.16e}", length), road.plan_view[-1].get("length"))

        spiral_elem = list(road.plan_view[-1].iter())[-1]
        self.assertEqual("spiral", spiral_elem.tag)
        self.assertEqual(str.format("{0:.16e}", curv_start), spiral_elem.get("curvStart"))
        self.assertEqual(str.format("{0:.16e}", curv_end), spiral_elem.get("curvEnd"))

    def test_print_arc(self):
        # Given
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        conversion_lanelet_1 = init_lanelet_from_id('79.0.-3.-1')
        conversion_lanelet_2 = init_lanelet_from_id('89.0.4.-1')

        add_lanelets_to_network(conversion_lanelet_network, [conversion_lanelet_1, conversion_lanelet_2])

        lane_list = conversion_lanelet_network.lanelets
        number_of_lanes = 2
        root = etree.Element("OpenDRIVE")
        current = etree.Element("OpenDRIVE")
        junction_id = -1
        road = Road(lane_list, number_of_lanes, root, current, junction_id)
        s = 1.0
        x = 0.0
        y = 1.0
        hdg = 4.0
        length = 1.45
        curvature = 0.0002

        # When
        road.print_arc(s, x, y, hdg, length, curvature)

        # Then
        self.assertEqual("geometry", road.plan_view[-1].tag)
        self.assertEqual(str.format("{0:.16e}", s), road.plan_view[-1].get("s"))
        self.assertEqual(str.format("{0:.16e}", x), road.plan_view[-1].get("x"))
        self.assertEqual(str.format("{0:.16e}", y), road.plan_view[-1].get("y"))
        self.assertEqual(str.format("{0:.16e}", hdg), road.plan_view[-1].get("hdg"))
        self.assertEqual(str.format("{0:.16e}", length), road.plan_view[-1].get("length"))

        arc_elem = list(road.plan_view[-1].iter())[-1]
        self.assertEqual("arc", arc_elem.tag)
        self.assertEqual(str.format("{0:.16e}", curvature), arc_elem.get("curvature"))

    def test_print_signal(self):
        # Given
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        conversion_lanelet_1 = init_lanelet_from_id('79.0.-3.-1')
        conversion_lanelet_2 = init_lanelet_from_id('89.0.4.-1')

        add_lanelets_to_network(conversion_lanelet_network, [conversion_lanelet_1, conversion_lanelet_2])

        lane_list = conversion_lanelet_network.lanelets
        number_of_lanes = 2
        root = etree.Element("OpenDRIVE")
        current = etree.Element("OpenDRIVE")
        junction_id = -1
        road = Road(lane_list, number_of_lanes, root, current, junction_id)
        road_key = 21
        unique_id = 0
        element = TrafficSignElement(TrafficSignIDZamunda.WARNING_SLIPPERY_ROAD, [])
        sign1 = TrafficSign(0, list([element]), set(), np.array([4.9, -0.1]), virtual=False)
        data = []
        data.append(sign1)
        data.append("79.0.-3.-1")
        signal = Sign(road_key, unique_id, data, conversion_lanelet_network)

        # When
        road.print_signal(signal)

        # Then
        self.assertEqual("signal", road.signals[-1].tag)

        self.assertEqual("4.9000000000000004e+00", road.signals[-1].get("s"))
        self.assertEqual("-1.1000000000000001e+00", road.signals[-1].get("t"))
        self.assertEqual("0", road.signals[-1].get("id"))
        self.assertEqual("Sign_0", road.signals[-1].get("name"))
        self.assertEqual("no", road.signals[-1].get("dynamic"))
        self.assertEqual("-", road.signals[-1].get("orientation"))
        self.assertEqual("3.3885", road.signals[-1].get("zOffset"))
        self.assertEqual("ZAMUNDA", road.signals[-1].get("country"))
        self.assertEqual("114", road.signals[-1].get("type"))
        self.assertEqual("-1", road.signals[-1].get("subtype"))
        self.assertEqual("2021", road.signals[-1].get("countryRevision"))
        self.assertEqual("-1", road.signals[-1].get("value"))
        self.assertEqual("km/h", road.signals[-1].get("unit"))
        self.assertEqual("0.77", road.signals[-1].get("width"))
        self.assertEqual("0.77", road.signals[-1].get("height"))
        self.assertEqual("0.0", road.signals[-1].get("hOffset"))

    def test_print_signal_ref(self):
        # Given
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        conversion_lanelet_1 = init_lanelet_from_id('79.0.-3.-1')
        conversion_lanelet_2 = init_lanelet_from_id('89.0.4.-1')

        add_lanelets_to_network(conversion_lanelet_network, [conversion_lanelet_1, conversion_lanelet_2])

        lane_list = conversion_lanelet_network.lanelets
        number_of_lanes = 2
        root = etree.Element("OpenDRIVE")
        current = etree.Element("OpenDRIVE")
        junction_id = -1
        road = Road(lane_list, number_of_lanes, root, current, junction_id)
        road_key = 21
        unique_id = 0
        element = TrafficSignElement(TrafficSignIDZamunda.WARNING_SLIPPERY_ROAD, [])
        sign1 = TrafficSign(0, list([element]), set(), np.array([4.9, -0.1]), virtual=False)
        data = []
        data.append(sign1)
        data.append("79.0.-3.-1")
        signal = Sign(road_key, unique_id, data, conversion_lanelet_network)

        # When
        road.print_signal_ref(signal)

        # Then
        self.assertEqual("signalReference", road.signals[-1].tag)

        self.assertEqual("4.9000000000000004e+00", road.signals[-1].get("s"))
        self.assertEqual("-1.1000000000000001e+00", road.signals[-1].get("t"))
        self.assertEqual("0", road.signals[-1].get("id"))
        self.assertEqual("-", road.signals[-1].get("orientation"))

    def test_lane_sections(self):
        # Given
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        conversion_lanelet_1 = init_lanelet_from_id('79.0.-3.-1')
        conversion_lanelet_2 = init_lanelet_from_id('89.0.4.-1')

        add_lanelets_to_network(conversion_lanelet_network, [conversion_lanelet_1, conversion_lanelet_2])

        lane_list = conversion_lanelet_network.lanelets
        number_of_lanes = 2
        root = etree.Element("OpenDRIVE")
        current = etree.Element("OpenDRIVE")
        junction_id = -1
        road = Road(lane_list, number_of_lanes, root, current, junction_id)

        # When
        road.lane_sections()

        # Then
        self.assertEqual("laneSection", road.lanes[-1].tag)
        self.assertEqual(str.format("{0:.16e}", 0), road.lanes[-1].get("s"))

        center = road.lanes[-1][0]
        self.assertEqual("center", center.tag)
        center_lane_pos = road.lanes[-1][0][0]
        self.assertEqual("lane", center_lane_pos.tag)
        self.assertEqual("0", center_lane_pos.get("id"))
        self.assertEqual("driving", center_lane_pos.get("type"))
        self.assertEqual("false", center_lane_pos.get("level"))

        center_link = road.lanes[-1][0][0][0]
        self.assertEqual("link", center_link.tag)

        center_roadmark = road.lanes[-1][0][0][1]
        self.assertEqual(str.format("{0:.16e}", 0), center_roadmark.get("sOffset"))
        self.assertEqual("solid", center_roadmark.get("type"))
        self.assertEqual("standard", center_roadmark.get("weight"))
        self.assertEqual("standard", center_roadmark.get("color"))
        self.assertEqual(str.format("{0:.16e}", 0.13), center_roadmark.get("width"))

        left = road.lanes[-1][1]
        self.assertEqual("left", left.tag)
        left_lane_pos = road.lanes[-1][1][0]
        self.assertEqual("lane", left_lane_pos.tag)
        self.assertEqual("1", left_lane_pos.get("id"))
        self.assertEqual("driving", left_lane_pos.get("type"))
        self.assertEqual("false", left_lane_pos.get("level"))

        left_link = road.lanes[-1][1][0][0]
        self.assertEqual("link", left_link.tag)

        left_width = road.lanes[-1][1][0][1]
        self.assertEqual(str.format("{0:.16e}", 0), left_width.get("sOffset"))
        self.assertEqual("1.9999999999999998e+00", left_width.get("a"))
        self.assertEqual("-7.8504622934188746e-17", left_width.get("b"))
        self.assertEqual(str.format("{0:.16e}", 0), left_width.get("c"))
        self.assertEqual(str.format("{0:.16e}", 0), left_width.get("d"))

        left_roadmark = road.lanes[-1][1][0][2]
        self.assertEqual(str.format("{0:.16e}", 0), left_roadmark.get("sOffset", ))
        self.assertEqual("solid", left_roadmark.get("type"))
        self.assertEqual("standard", left_roadmark.get("weight"))
        self.assertEqual("standard", left_roadmark.get("color"))
        self.assertEqual(str.format("{0:.16e}", 0.13), left_roadmark.get("width"))

        right = road.lanes[-1][2]
        self.assertEqual("right", right.tag)

        right_lane_pos = road.lanes[-1][2][0]
        self.assertEqual("lane", right_lane_pos.tag)
        self.assertEqual("-1", right_lane_pos.get("id"))
        self.assertEqual("driving", right_lane_pos.get("type"))
        self.assertEqual("false", right_lane_pos.get("level"))

        left_link = road.lanes[-1][2][0][0]
        self.assertEqual("link", left_link.tag)

        left_width = road.lanes[-1][2][0][1]
        self.assertEqual(str.format("{0:.16e}", 0), left_width.get("sOffset"))
        self.assertEqual("1.9999999999999998e+00", left_width.get("a"))
        self.assertEqual("-7.8504622934188746e-17", left_width.get("b"))
        self.assertEqual(str.format("{0:.16e}", 0), left_width.get("c"))
        self.assertEqual(str.format("{0:.16e}", 0), left_width.get("d"))

        left_roadmark = road.lanes[-1][2][0][2]
        self.assertEqual(str.format("{0:.16e}", 0), left_roadmark.get("sOffset", ))
        self.assertEqual("solid", left_roadmark.get("type"))
        self.assertEqual("standard", left_roadmark.get("weight"))
        self.assertEqual("standard", left_roadmark.get("color"))
        self.assertEqual(str.format("{0:.16e}", 0.13), left_roadmark.get("width"))

    def test_lane_help(self):
        # Given
        conversion_lanelet_network = ConversionLaneletNetwork(get_configs().opendrive)
        conversion_lanelet_1 = init_lanelet_from_id('79.0.-3.-1')
        conversion_lanelet_2 = init_lanelet_from_id('89.0.4.-1')

        add_lanelets_to_network(conversion_lanelet_network, [conversion_lanelet_1, conversion_lanelet_2])

        lane_list = conversion_lanelet_network.lanelets
        number_of_lanes = 2
        root = etree.Element("OpenDRIVE")
        current = etree.Element("OpenDRIVE")
        junction_id = -1
        road = Road(lane_list, number_of_lanes, root, current, junction_id)
        section = etree.SubElement(road.lanes, "laneSection")
        section.set("s", str.format("{0:.16e}", 0))

        center = etree.SubElement(section, "center")

        # When
        road.lane_help(0, "driving", 0, center, np.array([]), [])

        # Then
        self.assertEqual("lane", center[0].tag)
        self.assertEqual("0", center[0].attrib["id"])
        self.assertEqual("driving", center[0].attrib["type"])
        self.assertEqual("false", center[0].attrib["level"])

        self.assertEqual("link", road.lane_link[0].tag)

        link = list(center[-1].iter())[-2]
        self.assertEqual("link", link.tag)
        # requires more careful check for parent nodes?

        roadmark = list(center[-1].iter())[-1]
        self.assertEqual(str.format("{0:.16e}", 0), roadmark.get("sOffset", ))
        self.assertEqual("solid", roadmark.get("type"))
        self.assertEqual("standard", roadmark.get("weight"))
        self.assertEqual("standard", roadmark.get("color"))
        self.assertEqual(str.format("{0:.16e}", 0.13), roadmark.get("width"))


if __name__ == '__main__':
    unittest.main()
