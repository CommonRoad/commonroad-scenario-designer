import unittest

import numpy as np
from commonroad.scenario.traffic_sign import (
    TrafficSign,
    TrafficSignElement,
    TrafficSignIDZamunda,
)
from lxml import etree

from crdesigner.map_conversion.common.conversion_lanelet_network import (
    ConversionLaneletNetwork,
)
from crdesigner.map_conversion.opendrive.cr2odr.elements.road import Road
from crdesigner.map_conversion.opendrive.cr2odr.elements.sign import Sign
from crdesigner.map_conversion.opendrive.cr2odr.utils import config
from tests.map_conversion.opendrive.odr2cr.conversion.test_conversion_lanelet_network import (
    add_lanelets_to_network,
    init_lanelet_from_id,
)


def init_conversion_lanelet_network():
    conversion_lanelet_network = ConversionLaneletNetwork()
    conversion_lanelet_1 = init_lanelet_from_id("79.0.-3.-1")
    conversion_lanelet_2 = init_lanelet_from_id("89.0.4.-1")
    add_lanelets_to_network(conversion_lanelet_network, [conversion_lanelet_1, conversion_lanelet_2])

    return conversion_lanelet_network


def init_road():
    conversion_lanelet_network = init_conversion_lanelet_network()
    lane_list = conversion_lanelet_network.lanelets
    number_of_lanes = 2
    root = etree.Element(config.OPENDRIVE)
    junction_id = -1
    road = Road(lane_list, number_of_lanes, root, junction_id)
    return road, lane_list, number_of_lanes, root, conversion_lanelet_network


class TestRoad(unittest.TestCase):
    def setUp(self):
        Road.counting = 20
        Road.cr_id_to_od = dict()
        Road.lane_to_lane = dict()
        Road.lane_2_lane_link = dict()
        Road.link_map = dict()

    def test_initialize_road(self):
        # Given
        road, lane_list, number_of_lanes, root, conversion_lanelet_network = init_road()

        # Then
        self.assertEqual(21, Road.counting)
        self.assertEqual({config.SUCC_TAG: {}, config.PRED_TAG: {}}, Road.lane_2_lane_link[Road.counting])
        self.assertEqual(-1, road.junction_id)
        expected_links = {
            "79.0.-3.-1": {"pred": [], "succ": []},
            "89.0.4.-1": {"pred": [], "succ": []},
            "laneIndices": {"79.0.-3.-1": -1, "89.0.4.-1": 1},
        }
        self.assertEqual(expected_links, road.links)
        self.assertEqual(expected_links, Road.link_map[Road.counting])
        self.assertEqual(lane_list, road.lane_list)
        self.assertEqual(number_of_lanes, road.number_of_lanes)
        self.assertEqual(0, road.center_number)

        expected_center = np.array([[0.0, 1.0], [1.0, 1.0], [2.0, 1.0]])
        self.assertTrue((expected_center == road.center).all())

        expected_cr_to_od = {"79.0.-3.-1": 21, "89.0.4.-1": 21}
        self.assertEqual(expected_cr_to_od, road.cr_id_to_od)
        self.assertEqual(root, road.root)

        self.assertEqual(config.ROAD_TAG, road.root[0].tag)

        self.assertEqual(config.LINK_TAG, road.road[0].tag)

        self.assertEqual(config.TYPE_TAG, road.road[1].tag)
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0), road.road[1].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(config.TOWN_TAG, road.road[1].get(config.TYPE_TAG))
        self.assertEqual(config.TYPE_TAG, road.type.tag)
        self.assertEqual(str.format(config.DOUBLE_FORMAT_PATTERN, 0), road.type.get(config.GEOMETRY_S_COORDINATE_TAG))
        self.assertEqual(config.TOWN_TAG, road.type.get(config.TYPE_TAG))

        self.assertEqual(config.PLAN_VIEW_TAG, road.road[2].tag)
        self.assertEqual(config.ELEVATION_PROFILE_TAG, road.road[3].tag)
        self.assertEqual(config.ELEVATION_PROFILE_TAG, road.elevation_profile.tag)
        self.assertEqual(config.LATERAL_PROFILE_TAG, road.road[4].tag)
        self.assertEqual(config.LATERAL_PROFILE_TAG, road.lateral_profile.tag)
        self.assertEqual(config.LANES_TAG, road.road[5].tag)
        self.assertEqual(config.LANES_TAG, road.lanes.tag)

        # assert lane_section

        self.assertEqual(config.OBJECTS_TAG, road.road[6].tag)
        self.assertEqual(config.OBJECTS_TAG, road.objects.tag)
        self.assertEqual(config.SIGNALS_TAG, road.road[7].tag)
        self.assertEqual(config.SIGNALS_TAG, road.signals.tag)

        self.assertEqual("", road.road.attrib[config.NAME_TAG])
        self.assertEqual(str(21), road.road.attrib[config.ID_TAG])
        self.assertEqual("-1", road.road.attrib[config.JUNCTION_TAG])

        expected_lane_indices = {"79.0.-3.-1": -1, "89.0.4.-1": 1}
        self.assertEqual(expected_lane_indices, road.links[config.LANE_INDICES_TAG])

    def test_add_junction_linkage_successor(self):
        # Given
        road, lane_list, number_of_lanes, root, conversion_lanelet_network = init_road()
        element_id = 1
        relation = config.SUCCESSOR_TAG

        # When
        road.add_junction_linkage(element_id, relation)

        # Then
        self.assertEqual(config.SUCCESSOR_TAG, road.element_type.tag)
        self.assertEqual("1", road.element_type.get(config.ELEMENT_ID_TAG))
        self.assertEqual(config.JUNCTION_TAG, road.element_type.get(config.ELEMENT_TYPE_TAG))
        self.assertEqual(config.START_TAG, road.element_type.get(config.CONTACT_POINT_TAG))

    def test_add_junction_linkage_predecessor(self):
        # Given
        road, lane_list, number_of_lanes, root, conversion_lanelet_network = init_road()
        element_id = 1
        relation = config.PREDECESSOR_TAG

        # When
        road.add_junction_linkage(element_id, relation)

        # Then
        self.assertEqual(config.PREDECESSOR_TAG, road.element_type.tag)
        self.assertEqual("1", road.element_type.get(config.ELEMENT_ID_TAG))
        self.assertEqual(config.JUNCTION_TAG, road.element_type.get(config.ELEMENT_TYPE_TAG))
        self.assertEqual(config.END_TAG, road.element_type.get(config.CONTACT_POINT_TAG))

    def test_add_simple_linkage(self):
        # Given
        road, lane_list, number_of_lanes, root, conversion_lanelet_network = init_road()

        links = {"succ": [22, 22, 22, 22, 22, 22, 22, 22, 22], "pred": []}
        len_succ = 1
        len_pred = 0
        lane_2_lane = {"succ": {0: [1]}, "pred": {}}

        # When
        road.add_simple_linkage(links, len_succ, len_pred, lane_2_lane)

        # Then
        self.assertEqual(config.SUCCESSOR_TAG, road.link[-1].tag)
        self.assertEqual(config.ROAD_TAG, road.link[-1].get(config.ELEMENT_TYPE_TAG))
        self.assertEqual("22", road.link[-1].get(config.ELEMENT_ID_TAG))
        self.assertEqual(config.START_TAG, road.link[-1].get(config.CONTACT_POINT_TAG))

    def test_set_child_of_road(self):
        # Given
        road, lane_list, number_of_lanes, root, conversion_lanelet_network = init_road()
        name = "child_name"

        # When
        road.set_child_of_road(name)

        # Then
        self.assertEqual(name, road.road[len(road.road) - 1].tag)

    def test_set_plan_view(self):
        # Given
        road, lane_list, number_of_lanes, root, conversion_lanelet_network = init_road()

        # When
        last_item_arclength = road.set_plan_view()

        # Then
        expected_center = np.array([[0.0, 1.0], [1.0, 1.0], [2.0, 1.0]])
        self.assertTrue((expected_center == road.center).all())
        self.assertEqual(2.0, last_item_arclength)

        self.compare_geometry(0, 2, road, 0, 0, 1)

        self.assertEqual(config.GEOMETRY_TAG, road.plan_view[-2].tag)
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0), road.plan_view[-2].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0), road.plan_view[-2].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 1), road.plan_view[-2].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0), road.plan_view[-2].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual(str.format(config.DOUBLE_FORMAT_PATTERN, 2), road.plan_view[-2].get(config.LENGTH_TAG))

    def test_print_line(self):
        # Given
        road, lane_list, number_of_lanes, root, conversion_lanelet_network = init_road()
        s = 1.0
        x = 0.0
        y = 1.0
        hdg = 4
        length = 1.45

        # When
        road.print_line(s, x, y, hdg, length)

        # Then
        self.compare_geometry(hdg, length, road, s, x, y)

    def test_print_spiral(self):
        # Given
        road, lane_list, number_of_lanes, root, conversion_lanelet_network = init_road()
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
        self.compare_geometry(hdg, length, road, s, x, y)

        spiral_elem = list(road.plan_view[-1].iter())[-1]
        self.assertEqual(config.SPIRAL_TAG, spiral_elem.tag)
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, curv_start), spiral_elem.get(config.GEOMETRY_CURV_START_TAG)
        )
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, curv_end), spiral_elem.get(config.GEOMETRY_CURV_END_TAG)
        )

    def compare_geometry(self, hdg, length, road, s, x, y):
        self.assertEqual(config.GEOMETRY_TAG, road.plan_view[-1].tag)
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, s), road.plan_view[-1].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, x), road.plan_view[-1].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, y), road.plan_view[-1].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, hdg), road.plan_view[-1].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual(str.format(config.DOUBLE_FORMAT_PATTERN, length), road.plan_view[-1].get(config.LENGTH_TAG))

    def test_print_arc(self):
        # Given
        road, lane_list, number_of_lanes, root, conversion_lanelet_network = init_road()
        s = 1.0
        x = 0.0
        y = 1.0
        hdg = 4.0
        length = 1.45
        curvature = 0.0002

        # When
        road.print_arc(s, x, y, hdg, length, curvature)

        # Then
        self.compare_geometry(hdg, length, road, s, x, y)

        arc_elem = list(road.plan_view[-1].iter())[-1]
        self.assertEqual(config.ARC_TAG, arc_elem.tag)
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, curvature), arc_elem.get(config.GEOMETRY_CURVATURE_TAG)
        )

    def test_print_signal(self):
        # Given
        road, lane_list, number_of_lanes, root, conversion_lanelet_network = init_road()
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
        self.assertEqual(config.SIGNAL_TAG, road.signals[-1].tag)

        self.assertEqual("4.9000000000000004e+00", road.signals[-1].get(config.GEOMETRY_S_COORDINATE_TAG))
        self.assertEqual("-1.1000000000000001e+00", road.signals[-1].get(config.SIGNAL_T_TAG))
        self.assertEqual("0", road.signals[-1].get(config.ID_TAG))
        self.assertEqual("Sign_0", road.signals[-1].get(config.NAME_TAG))
        self.assertEqual(config.NO, road.signals[-1].get(config.SIGNAL_DYNAMIC_TAG))
        self.assertEqual(config.MINUS_SIGN, road.signals[-1].get(config.SIGNAL_ORIENTATION_TAG))
        self.assertEqual("3.3885", road.signals[-1].get(config.SIGNAL_ZOFFSET_TAG))
        self.assertEqual("GERMANY", road.signals[-1].get(config.SIGNAL_COUNTRY_TAG))
        self.assertEqual("114", road.signals[-1].get(config.TYPE_TAG))
        self.assertEqual("-1", road.signals[-1].get(config.SIGNAL_SUBTYPE_TAG))
        self.assertEqual("2021", road.signals[-1].get(config.SIGNAL_COUNTRY_REVISION_TAG))
        self.assertEqual("-1", road.signals[-1].get(config.SIGNAL_VALUE_TAG))
        self.assertEqual("km/h", road.signals[-1].get(config.SIGNAL_UNIT_TAG))
        self.assertEqual("0.77", road.signals[-1].get(config.SIGNAL_WIDTH_TAG))
        self.assertEqual("0.77", road.signals[-1].get(config.SIGNAL_HEIGHT_TAG))
        self.assertEqual(config.ZERO, road.signals[-1].get(config.SIGNAL_HOFFSET_TAG))

    def test_print_signal_ref(self):
        # Given
        road, lane_list, number_of_lanes, root, conversion_lanelet_network = init_road()
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
        self.assertEqual(config.SIGNAL_REFERENCE_TAG, road.signals[-1].tag)

        self.assertEqual("4.9000000000000004e+00", road.signals[-1].get(config.GEOMETRY_S_COORDINATE_TAG))
        self.assertEqual("-1.1000000000000001e+00", road.signals[-1].get(config.SIGNAL_T_TAG))
        self.assertEqual("0", road.signals[-1].get(config.ID_TAG))
        self.assertEqual(config.MINUS_SIGN, road.signals[-1].get(config.SIGNAL_ORIENTATION_TAG))

    def test_lane_sections(self):
        # Given
        road, lane_list, number_of_lanes, root, conversion_lanelet_network = init_road()

        # When
        road.lane_sections()

        # Then
        self.assertEqual(config.LANE_SECTION_TAG, road.lanes[-1].tag)
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0), road.lanes[-1].get(config.GEOMETRY_S_COORDINATE_TAG)
        )

        center = road.lanes[-1][0]
        self.assertEqual(config.LANE_SECTION_CENTER_TAG, center.tag)
        center_lane_pos = road.lanes[-1][0][0]
        self.assertEqual(config.LANE_TAG, center_lane_pos.tag)
        self.assertEqual("0", center_lane_pos.get(config.ID_TAG))
        self.assertEqual("driving", center_lane_pos.get(config.TYPE_TAG))
        self.assertEqual(config.FALSE, center_lane_pos.get(config.LEVEL_TAG))

        center_link = road.lanes[-1][0][0][0]
        self.assertEqual(config.LINK_TAG, center_link.tag)

        roadmark = road.lanes[-1][0][0][1]
        self.compare_road_mark(roadmark)

        left = road.lanes[-1][1]
        self.assertEqual(config.LANE_SECTION_LEFT_TAG, left.tag)
        left_lane_pos = road.lanes[-1][1][0]
        self.assertEqual(config.LANE_TAG, left_lane_pos.tag)
        self.assertEqual("1", left_lane_pos.get(config.ID_TAG))
        self.assertEqual("driving", left_lane_pos.get(config.TYPE_TAG))
        self.assertEqual(config.FALSE, left_lane_pos.get(config.LEVEL_TAG))

        left_link = road.lanes[-1][1][0][0]
        self.assertEqual(config.LINK_TAG, left_link.tag)

        left_width = road.lanes[-1][1][0][1]
        self.assertEqual(str.format(config.DOUBLE_FORMAT_PATTERN, 0), left_width.get(config.LANE_SOFFSET_TAG))
        self.assertEqual("1.9999999999999998e+00", left_width.get(config.LANE_A_TAG))
        self.assertEqual("-7.8504622934188746e-17", left_width.get(config.LANE_B_TAG))
        self.assertEqual(str.format(config.DOUBLE_FORMAT_PATTERN, 0), left_width.get(config.LANE_C_TAG))
        self.assertEqual(str.format(config.DOUBLE_FORMAT_PATTERN, 0), left_width.get(config.LANE_D_TAG))

        roadmark = road.lanes[-1][1][0][2]
        self.compare_road_mark(roadmark)

        right = road.lanes[-1][2]
        self.assertEqual(config.LANE_SECTION_RIGHT_TAG, right.tag)

        right_lane_pos = road.lanes[-1][2][0]
        self.assertEqual(config.LANE_TAG, right_lane_pos.tag)
        self.assertEqual("-1", right_lane_pos.get(config.ID_TAG))
        self.assertEqual("driving", right_lane_pos.get(config.TYPE_TAG))
        self.assertEqual(config.FALSE, right_lane_pos.get(config.LEVEL_TAG))

        left_link = road.lanes[-1][2][0][0]
        self.assertEqual(config.LINK_TAG, left_link.tag)

        left_width = road.lanes[-1][2][0][1]
        self.assertEqual(str.format(config.DOUBLE_FORMAT_PATTERN, 0), left_width.get(config.LANE_SOFFSET_TAG))
        self.assertEqual("1.9999999999999998e+00", left_width.get(config.LANE_A_TAG))
        self.assertEqual("-7.8504622934188746e-17", left_width.get(config.LANE_B_TAG))
        self.assertEqual(str.format(config.DOUBLE_FORMAT_PATTERN, 0), left_width.get(config.LANE_C_TAG))
        self.assertEqual(str.format(config.DOUBLE_FORMAT_PATTERN, 0), left_width.get(config.LANE_D_TAG))

        roadmark = road.lanes[-1][2][0][2]
        self.compare_road_mark(roadmark)

    def test_lane_help(self):
        # Given
        road, lane_list, number_of_lanes, root, conversion_lanelet_network = init_road()
        section = etree.SubElement(road.lanes, config.LANE_SECTION_TAG)
        section.set(config.GEOMETRY_S_COORDINATE_TAG, str.format(config.DOUBLE_FORMAT_PATTERN, 0))

        center = etree.SubElement(section, config.LANE_SECTION_CENTER_TAG)

        # When
        road.lane_help(0, "driving", 0, center, [], np.array([]))

        # Then
        self.assertEqual("lane", center[0].tag)
        self.assertEqual("0", center[0].attrib[config.ID_TAG])
        self.assertEqual("driving", center[0].attrib[config.TYPE_TAG])
        self.assertEqual(config.FALSE, center[0].attrib[config.LEVEL_TAG])

        self.assertEqual(config.LINK_TAG, road.lane_link[0].tag)

        link = list(center[-1].iter())[-2]
        self.assertEqual(config.LINK_TAG, link.tag)
        # requires more careful check for parent nodes?

        roadmark = list(center[-1].iter())[-1]
        self.compare_road_mark(roadmark)

    def compare_road_mark(self, road_mark):
        self.assertEqual(str.format(config.DOUBLE_FORMAT_PATTERN, 0), road_mark.get(config.LANE_SOFFSET_TAG))
        self.assertEqual(config.SOLID, road_mark.get(config.TYPE_TAG))
        self.assertEqual(config.STANDARD, road_mark.get(config.ROAD_MARK_WEIGHT_TAG))
        self.assertEqual(config.STANDARD, road_mark.get(config.ROAD_MARK_COLOR_TAG))
        self.assertEqual(str.format(config.DOUBLE_FORMAT_PATTERN, 0.13), road_mark.get(config.SIGNAL_WIDTH_TAG))
