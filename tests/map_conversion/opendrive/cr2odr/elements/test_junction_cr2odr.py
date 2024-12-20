import copy

from lxml import etree

import crdesigner.map_conversion.opendrive.cr2odr.utils.file_writer as fwr
from crdesigner.map_conversion.opendrive.cr2odr.converter import (
    create_linkages,
    process_link_map,
)
from crdesigner.map_conversion.opendrive.cr2odr.elements.junction import Junction
from crdesigner.map_conversion.opendrive.cr2odr.elements.road import Road
from crdesigner.map_conversion.opendrive.cr2odr.utils import config
from tests.map_conversion.opendrive.cr2odr.conversion_base_test import (
    ConversionBaseTestCases,
)


class TestJunction(ConversionBaseTestCases.ConversionBaseTest):
    road_counting = 20

    def setUp(self):
        Road.counting = 20
        Road.cr_id_to_od = {}
        Road.lanelet_to_lane = {}
        Road.lane_2_lane_link = {}
        Road.link_map = {}

    def test_convert_init_junction(self):
        # Given
        # Initialization requires convertion, as it is the easiest way to create all needed elements
        # TODO issue 432: Initialize all elements manually
        Road.counting = 20
        self.prepare_conversion("ZAM_Threewayintersection-1_1_T-1")
        self.prepare_junctions()

        intersection = self.converter.lane_net.intersections[0]

        root = etree.Element(config.OPENDRIVE)

        # When
        junction = Junction(
            intersection.incomings,
            Road.cr_id_to_od,
            Road.lanelet_to_lane,
            self.converter.writer.root,
            self.converter.scenario.lanelet_network,
            intersection.intersection_id,
        )

        # Then
        self.assertEqual(intersection.incomings, junction.incoming)
        self.assertEqual(root.tag, junction.root.tag)
        self.assertEqual(16, junction.id)
        self.assertEqual(config.JUNCTION_TAG, junction.junction.tag)
        self.assertEqual("", junction.junction.get(config.NAME_TAG))
        self.assertEqual(
            str.format(config.ID_FORMAT_PATTERN, 16), junction.junction.get(config.ID_TAG)
        )
        self.assertEqual(config.DEFAULT, junction.junction.get(config.TYPE_TAG))

        # Junction.junction check
        self.checkJunctionJunction(junction)

        # Junction.root check
        self.checkJunctionRoot0(junction)
        self.checkJunctionRoot1(junction)
        # self.checkJunctionRoot2(junction)
        # self.checkJunctionRoot3(junction)
        # self.checkJunctionRoot4(junction)
        # self.checkJunctionRoot5(junction)
        # self.checkJunctionRoot6(junction)
        # self.checkJunctionRoot7(junction)

    def prepare_junctions(self):
        self.converter.writer = fwr.Writer("ZAM_Threewayintersection-1_1_T-1-test.xml", config.TODO)
        lane_list = self.converter.lane_net.lanelets
        lanelet = copy.deepcopy(lane_list[0])
        self.converter.construct_roads([lanelet.lanelet_id])
        self.converter.check_all_visited()
        process_link_map(Road.link_map, Road.lane_2_lane_link)
        create_linkages(Road.link_map, Road.lane_2_lane_link)

    def checkJunctionRoot7(self, junction):
        self.assertEqual(config.JUNCTION_TAG, junction.root[7].tag)
        self.assertEqual("", junction.root[7].get(config.NAME_TAG))
        self.assertEqual("16", junction.root[7].get(config.ID_TAG))
        self.assertEqual(config.DEFAULT, junction.root[7].get(config.TYPE_TAG))
        self.assertEqual(config.JUNCTION_CONNECTION_TAG, junction.root[7][0].tag)
        self.assertEqual("1", junction.root[7][0].get(config.ID_TAG))
        self.assertEqual("21", junction.root[7][0].get(config.JUNCTION_INCOMING_ROAD_TAG))
        self.assertEqual("25", junction.root[7][0].get(config.JUNCTION_CONNECTING_ROAD_TAG))
        self.assertEqual(config.START_TAG, junction.root[7][0].get(config.CONTACT_POINT_TAG))
        self.assertEqual(config.JUNCTION_LANE_LINK_TAG, junction.root[7][0][0].tag)
        self.assertEqual("-1", junction.root[7][0][0].get(config.JUNCTION_FROM_TAG))
        self.assertEqual("-1", junction.root[7][0][0].get(config.JUNCTION_TO_TAG))
        self.assertEqual(config.JUNCTION_CONNECTION_TAG, junction.root[7][1].tag)
        self.assertEqual("2", junction.root[7][1].get(config.ID_TAG))
        self.assertEqual("21", junction.root[7][1].get(config.JUNCTION_INCOMING_ROAD_TAG))
        self.assertEqual("22", junction.root[7][1].get(config.JUNCTION_CONNECTING_ROAD_TAG))
        self.assertEqual(config.START_TAG, junction.root[7][1].get(config.CONTACT_POINT_TAG))
        self.assertEqual(config.JUNCTION_LANE_LINK_TAG, junction.root[7][1][0].tag)
        self.assertEqual("-1", junction.root[7][1][0].get(config.JUNCTION_FROM_TAG))
        self.assertEqual("1", junction.root[7][1][0].get(config.JUNCTION_TO_TAG))
        self.assertEqual(config.JUNCTION_CONNECTION_TAG, junction.root[7][2].tag)
        self.assertEqual("3", junction.root[7][2].get(config.ID_TAG))
        self.assertEqual("26", junction.root[7][2].get(config.JUNCTION_INCOMING_ROAD_TAG))
        self.assertEqual("24", junction.root[7][2].get(config.JUNCTION_CONNECTING_ROAD_TAG))
        self.assertEqual(config.START_TAG, junction.root[7][2].get(config.CONTACT_POINT_TAG))
        self.assertEqual(config.JUNCTION_LANE_LINK_TAG, junction.root[7][2][0].tag)
        self.assertEqual("1", junction.root[7][2][0].get(config.JUNCTION_FROM_TAG))
        self.assertEqual("1", junction.root[7][2][0].get(config.JUNCTION_TO_TAG))
        self.assertEqual(config.JUNCTION_CONNECTION_TAG, junction.root[7][3].tag)
        self.assertEqual("4", junction.root[7][3].get(config.ID_TAG))
        self.assertEqual("26", junction.root[7][3].get(config.JUNCTION_INCOMING_ROAD_TAG))
        self.assertEqual("25", junction.root[7][3].get(config.JUNCTION_CONNECTING_ROAD_TAG))
        self.assertEqual(config.START_TAG, junction.root[7][3].get(config.CONTACT_POINT_TAG))
        self.assertEqual(config.JUNCTION_LANE_LINK_TAG, junction.root[7][3][0].tag)
        self.assertEqual("1", junction.root[7][3][0].get(config.JUNCTION_FROM_TAG))
        self.assertEqual("1", junction.root[7][3][0].get(config.JUNCTION_TO_TAG))
        self.assertEqual(config.JUNCTION_CONNECTION_TAG, junction.root[7][4].tag)
        self.assertEqual("5", junction.root[7][4].get(config.ID_TAG))
        self.assertEqual("23", junction.root[7][4].get(config.JUNCTION_INCOMING_ROAD_TAG))
        self.assertEqual("24", junction.root[7][4].get(config.JUNCTION_CONNECTING_ROAD_TAG))
        self.assertEqual(config.START_TAG, junction.root[7][4].get(config.CONTACT_POINT_TAG))
        self.assertEqual(config.JUNCTION_LANE_LINK_TAG, junction.root[7][4][0].tag)
        self.assertEqual("1", junction.root[7][4][0].get(config.JUNCTION_FROM_TAG))
        self.assertEqual("-1", junction.root[7][4][0].get(config.JUNCTION_TO_TAG))
        self.assertEqual(config.JUNCTION_CONNECTION_TAG, junction.root[7][5].tag)
        self.assertEqual("6", junction.root[7][5].get(config.ID_TAG))
        self.assertEqual("23", junction.root[7][5].get(config.JUNCTION_INCOMING_ROAD_TAG))
        self.assertEqual("22", junction.root[7][5].get(config.JUNCTION_CONNECTING_ROAD_TAG))
        self.assertEqual(config.START_TAG, junction.root[7][5].get(config.CONTACT_POINT_TAG))
        self.assertEqual(config.JUNCTION_LANE_LINK_TAG, junction.root[7][5][0].tag)
        self.assertEqual("1", junction.root[7][5][0].get(config.JUNCTION_FROM_TAG))
        self.assertEqual("-1", junction.root[7][5][0].get(config.JUNCTION_TO_TAG))

    def checkJunctionRoot0(self, junction: Junction):
        self.assertEqual(8, len(junction.root))
        self.assertEqual(config.HEADER_TAG, junction.root[0].tag)
        self.assertEqual("1", junction.root[0].get(config.HEADER_REV_MAJOR_TAG))
        self.assertEqual("6", junction.root[0].get(config.HEADER_REV_MINOR_TAG))
        self.assertEqual(
            config.OBSTACLE_HEIGHT_VALUE, junction.root[0].get(config.HEADER_VERSION_TAG)
        )
        self.assertEqual(
            "ZAM_Threewayintersection-1_1_T-1-test", junction.root[0].get(config.NAME_TAG)
        )
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0), junction.root[0].get(config.NORTH)
        )
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0), junction.root[0].get(config.SOUTH)
        )
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0), junction.root[0].get(config.EAST)
        )
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0), junction.root[0].get(config.WEST)
        )
        self.assertEqual(config.GEO_REFFERENCE_TAG, junction.root[0][0].tag)
        self.assertEqual(f"<![CDATA[{config.TODO}]]>", junction.root[0][0].text)

    def checkJunctionRoot1(self, junction: Junction):
        self.assertEqual(config.ROAD_TAG, junction.root[1].tag)
        self.assertEqual("", junction.root[1].get(config.NAME_TAG))
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 20), junction.root[1].get(config.LENGTH_TAG)
        )
        self.assertEqual("21", junction.root[1].get(config.ID_TAG))
        self.assertEqual("-1", junction.root[1].get(config.JUNCTION_TAG))
        self.assertEqual(config.LINK_TAG, junction.root[1][0].tag)
        self.assertEqual(config.TYPE_TAG, junction.root[1][1].tag)
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0),
            junction.root[1][1].get(config.GEOMETRY_S_COORDINATE_TAG),
        )
        self.assertEqual(config.TOWN_TAG, junction.root[1][1].get(config.TYPE_TAG))
        self.assertEqual(config.PLAN_VIEW_TAG, junction.root[1][2].tag)
        self.assertEqual(config.ELEVATION_PROFILE_TAG, junction.root[1][3].tag)
        self.assertEqual(config.LATERAL_PROFILE_TAG, junction.root[1][4].tag)
        self.assertEqual(config.LANES_TAG, junction.root[1][5].tag)
        self.assertEqual(config.LANE_SECTION_TAG, junction.root[1][5][0].tag)
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0),
            junction.root[1][5][0].get(config.GEOMETRY_S_COORDINATE_TAG),
        )
        self.assertEqual(config.LANE_SECTION_CENTER_TAG, junction.root[1][5][0][0].tag)
        self.assertEqual(config.LANE_TAG, junction.root[1][5][0][0][0].tag)
        self.assertEqual("0", junction.root[1][5][0][0][0].get(config.ID_TAG))
        self.assertEqual("driving", junction.root[1][5][0][0][0].get(config.TYPE_TAG))
        self.assertEqual(config.FALSE, junction.root[1][5][0][0][0].get(config.LEVEL_TAG))
        self.assertEqual(config.LINK_TAG, junction.root[1][5][0][0][0][0].tag)
        self.assertEqual(config.ROAD_MARK_TAG, junction.root[1][5][0][0][0][1].tag)
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0),
            junction.root[1][5][0][0][0][1].get(config.LANE_SOFFSET_TAG),
        )
        self.assertEqual(config.SOLID, junction.root[1][5][0][0][0][1].get(config.TYPE_TAG))
        self.assertEqual(
            config.STANDARD, junction.root[1][5][0][0][0][1].get(config.ROAD_MARK_WEIGHT_TAG)
        )
        self.assertEqual(
            config.STANDARD, junction.root[1][5][0][0][0][1].get(config.ROAD_MARK_COLOR_TAG)
        )
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0.13),
            junction.root[1][5][0][0][0][1].get(config.SIGNAL_WIDTH_TAG),
        )
        self.assertEqual(config.LANE_SECTION_LEFT_TAG, junction.root[1][5][0][1].tag)
        self.assertEqual(config.LANE_TAG, junction.root[1][5][0][1][0].tag)
        self.assertEqual("1", junction.root[1][5][0][1][0].get(config.ID_TAG))
        self.assertEqual("driving", junction.root[1][5][0][1][0].get(config.TYPE_TAG))
        self.assertEqual(config.FALSE, junction.root[1][5][0][1][0].get(config.LEVEL_TAG))
        self.assertEqual(config.LINK_TAG, junction.root[1][5][0][1][0][0].tag)
        self.assertEqual(config.SIGNAL_WIDTH_TAG, junction.root[1][5][0][1][0][1].tag)
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0),
            junction.root[1][5][0][1][0][1].get(config.LANE_SOFFSET_TAG),
        )
        self.assertEqual(
            "2.9999999999999996e+00", junction.root[1][5][0][1][0][1].get(config.LANE_A_TAG)
        )
        self.assertEqual(
            "-1.5700924586837747e-17", junction.root[1][5][0][1][0][1].get(config.LANE_B_TAG)
        )
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0),
            junction.root[1][5][0][1][0][1].get(config.LANE_C_TAG),
        )
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0),
            junction.root[1][5][0][1][0][1].get(config.LANE_D_TAG),
        )
        self.assertEqual(config.ROAD_MARK_TAG, junction.root[1][5][0][1][0][2].tag)
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0),
            junction.root[1][5][0][1][0][2].get(config.LANE_SOFFSET_TAG),
        )
        self.assertEqual(config.SOLID, junction.root[1][5][0][1][0][2].get(config.TYPE_TAG))
        self.assertEqual(
            config.STANDARD, junction.root[1][5][0][1][0][2].get(config.ROAD_MARK_WEIGHT_TAG)
        )
        self.assertEqual(
            config.STANDARD, junction.root[1][5][0][1][0][2].get(config.ROAD_MARK_COLOR_TAG)
        )
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0.13),
            junction.root[1][5][0][1][0][2].get(config.SIGNAL_WIDTH_TAG),
        )
        self.assertEqual(config.LANE_SECTION_RIGHT_TAG, junction.root[1][5][0][2].tag)
        self.assertEqual(config.LANE_TAG, junction.root[1][5][0][2][0].tag)
        self.assertEqual("-1", junction.root[1][5][0][2][0].get(config.ID_TAG))
        self.assertEqual("driving", junction.root[1][5][0][2][0].get(config.TYPE_TAG))
        self.assertEqual(config.FALSE, junction.root[1][5][0][2][0].get(config.LEVEL_TAG))
        self.assertEqual(config.LINK_TAG, junction.root[1][5][0][2][0][0].tag)
        self.assertEqual(config.SIGNAL_WIDTH_TAG, junction.root[1][5][0][2][0][1].tag)
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0),
            junction.root[1][5][0][2][0][1].get(config.LANE_SOFFSET_TAG),
        )
        self.assertEqual(
            "2.9999999999999996e+00", junction.root[1][5][0][2][0][1].get(config.LANE_A_TAG)
        )
        self.assertEqual(
            "-1.5700924586837750e-17", junction.root[1][5][0][2][0][1].get(config.LANE_B_TAG)
        )
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0),
            junction.root[1][5][0][2][0][1].get(config.LANE_C_TAG),
        )
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0),
            junction.root[1][5][0][2][0][1].get(config.LANE_D_TAG),
        )
        self.assertEqual(config.ROAD_MARK_TAG, junction.root[1][5][0][2][0][2].tag)
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0),
            junction.root[1][5][0][2][0][2].get(config.LANE_SOFFSET_TAG),
        )
        self.assertEqual(config.SOLID, junction.root[1][5][0][2][0][2].get(config.TYPE_TAG))
        self.assertEqual(
            config.STANDARD, junction.root[1][5][0][2][0][2].get(config.ROAD_MARK_WEIGHT_TAG)
        )
        self.assertEqual(
            config.STANDARD, junction.root[1][5][0][2][0][2].get(config.ROAD_MARK_COLOR_TAG)
        )
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0.13),
            junction.root[1][5][0][1][0][2].get(config.SIGNAL_WIDTH_TAG),
        )
        self.assertEqual(config.OBJECTS_TAG, junction.root[1][6].tag)
        self.assertEqual(config.SIGNALS_TAG, junction.root[1][7].tag)

    def checkJunctionRoot2(self, junction):
        self.assertEqual(config.ROAD_TAG, junction.root[2].tag)
        self.assertEqual("", junction.root[2].get(config.NAME_TAG))
        self.assertEqual("7.8517087087861750e+00", junction.root[2].get(config.LENGTH_TAG))
        self.assertEqual("22", junction.root[2].get(config.ID_TAG))
        self.assertEqual("16", junction.root[2].get(config.JUNCTION_TAG))
        self.assertEqual(config.LINK_TAG, junction.root[2][0].tag)
        self.assertEqual(config.TYPE_TAG, junction.root[2][1].tag)
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0),
            junction.root[2][1].get(config.GEOMETRY_S_COORDINATE_TAG),
        )
        self.assertEqual(config.TOWN_TAG, junction.root[2][1].get(config.TYPE_TAG))
        self.assertEqual(config.PLAN_VIEW_TAG, junction.root[2][2].tag)
        self.assertEqual(config.GEOMETRY_TAG, junction.root[2][2][0].tag)
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0),
            junction.root[2][2][0].get(config.GEOMETRY_S_COORDINATE_TAG),
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[2][2][0].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-3.5000000000000000e+00", junction.root[2][2][0].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[2][2][0].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("8.2652530493413356e-01", junction.root[2][2][0].get(config.LENGTH_TAG))
        self.assertEqual(config.SPIRAL_TAG, junction.root[2][2][0][0].tag)
        self.assertEqual(
            "9.9797916522530394e-02", junction.root[2][2][0][0].get(config.GEOMETRY_CURV_START_TAG)
        )
        self.assertEqual(
            "2.0008681885663243e-01", junction.root[2][2][0][0].get(config.GEOMETRY_CURV_END_TAG)
        )
        self.assertEqual(config.GEOMETRY_TAG, junction.root[2][2][1].tag)
        self.assertEqual(
            "8.2652530493413356e-01", junction.root[2][2][1].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.4931799999999999e+01", junction.root[2][2][1].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-2.6770000000000000e+00", junction.root[2][2][1].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.7361532484880158e+00", junction.root[2][2][1].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("4.1329322520457523e-01", junction.root[2][2][1].get(config.LENGTH_TAG))
        self.assertEqual(config.SPIRAL_TAG, junction.root[2][2][1][0].tag)
        self.assertEqual(
            "2.0008681885663243e-01", junction.root[2][2][1][0].get(config.GEOMETRY_CURV_START_TAG)
        )
        self.assertEqual(
            "1.9997720530768345e-01", junction.root[2][2][1][0].get(config.GEOMETRY_CURV_END_TAG)
        )
        self.assertEqual(config.GEOMETRY_TAG, junction.root[2][2][2].tag)
        self.assertEqual(
            "1.9962315663324284e+00", junction.root[2][2][2].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.4602892017361071e+01", junction.root[2][2][2].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.5532538394408304e+00", junction.root[2][2][2].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.0718535741262176e+00", junction.root[2][2][2].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("9.9797465125136897e-01", junction.root[2][2][2].get(config.LENGTH_TAG))
        self.assertEqual(config.ARC_TAG, junction.root[2][2][2][0].tag)
        self.assertEqual(
            "1.9997720530768345e-01", junction.root[2][2][2][0].get(config.GEOMETRY_CURVATURE_TAG)
        )
        self.assertEqual(config.GEOMETRY_TAG, junction.root[2][2][3].tag)
        self.assertEqual(
            "2.9942062175837973e+00", junction.root[2][2][3].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.4123511807586731e+01", junction.root[2][2][3].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-6.7795502245488193e-01", junction.root[2][2][3].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.2714414399354665e+00", junction.root[2][2][3].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("9.9799364319587047e-01", junction.root[2][2][3].get(config.LENGTH_TAG))
        self.assertEqual(config.ARC_TAG, junction.root[2][2][3][0].tag)
        self.assertEqual(
            "1.9992399735099053e-01", junction.root[2][2][3][0].get(config.GEOMETRY_CURVATURE_TAG)
        )
        self.assertEqual(config.GEOMETRY_TAG, junction.root[2][2][4].tag)
        self.assertEqual(
            "3.9921998607796678e+00", junction.root[2][2][4].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.3480094364917232e+01", junction.root[2][2][4].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "8.4937700231609806e-02", junction.root[2][2][4].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.4689226485277511e+00", junction.root[2][2][4].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("9.9802816011502449e-01", junction.root[2][2][4].get(config.LENGTH_TAG))
        self.assertEqual(config.ARC_TAG, junction.root[2][2][4][0].tag)
        self.assertEqual(
            "1.9987527769085611e-01", junction.root[2][2][4][0].get(config.GEOMETRY_CURVATURE_TAG)
        )
        self.assertEqual(config.GEOMETRY_TAG, junction.root[2][2][5].tag)
        self.assertEqual(
            "4.9902280208946923e+00", junction.root[2][2][5].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.2699475822634565e+01", junction.root[2][2][5].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "7.0678567186701236e-01", junction.root[2][2][5].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.6738924224341813e+00", junction.root[2][2][5].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("9.9808144180144964e-01", junction.root[2][2][5].get(config.LENGTH_TAG))
        self.assertEqual(config.SPIRAL_TAG, junction.root[2][2][5][0].tag)
        self.assertEqual(
            "2.0053176369749057e-01", junction.root[2][2][5][0].get(config.GEOMETRY_CURV_START_TAG)
        )
        self.assertEqual(config.GEOMETRY_TAG, junction.root[2][2][6].tag)
        self.assertEqual(
            "5.9883094626961419e+00", junction.root[2][2][6].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.1808580878678114e+01", junction.root[2][2][6].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.1567554078507727e+00", junction.root[2][2][6].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.8678175389864404e+00", junction.root[2][2][6].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("9.9811685972454089e-01", junction.root[2][2][6].get(config.LENGTH_TAG))
        self.assertEqual(config.SPIRAL_TAG, junction.root[2][2][6][0].tag)
        self.assertEqual(
            "1.8460836337615408e-01", junction.root[2][2][6][0].get(config.GEOMETRY_CURV_START_TAG)
        )
        self.assertEqual(
            "1.5752388049531971e-01", junction.root[2][2][6][0].get(config.GEOMETRY_CURV_END_TAG)
        )
        self.assertEqual(config.GEOMETRY_TAG, junction.root[2][2][7].tag)
        self.assertEqual(
            "6.9864263224206828e+00", junction.root[2][2][7].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.0847636795890530e+01", junction.root[2][2][7].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.4266141401940253e+00", junction.root[2][2][7].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "3.0552309903253723e+00", junction.root[2][2][7].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("8.5080762935403076e-01", junction.root[2][2][7].get(config.LENGTH_TAG))
        self.assertEqual(config.SPIRAL_TAG, junction.root[2][2][7][0].tag)
        self.assertEqual(
            "1.5752388049531971e-01", junction.root[2][2][7][0].get(config.GEOMETRY_CURV_START_TAG)
        )
        self.assertEqual(
            "1.2845294758092096e-01", junction.root[2][2][7][0].get(config.GEOMETRY_CURV_END_TAG)
        )
        self.assertEqual(config.ELEVATION_PROFILE_TAG, junction.root[2][3].tag)
        self.assertEqual(config.LATERAL_PROFILE_TAG, junction.root[2][4].tag)
        self.assertEqual(config.LANES_TAG, junction.root[2][5].tag)
        self.assertEqual(config.LANE_SECTION_TAG, junction.root[2][5][0].tag)
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0),
            junction.root[2][5][0].get(config.GEOMETRY_S_COORDINATE_TAG),
        )
        self.assertEqual(config.LANE_SECTION_CENTER_TAG, junction.root[2][5][0][0].tag)
        self.assertEqual(config.LANE_TAG, junction.root[2][5][0][0][0].tag)
        self.assertEqual("0", junction.root[2][5][0][0][0].get(config.ID_TAG))
        self.assertEqual("driving", junction.root[2][5][0][0][0].get(config.TYPE_TAG))
        self.assertEqual(config.FALSE, junction.root[2][5][0][0][0].get(config.LEVEL_TAG))
        self.assertEqual(config.LINK_TAG, junction.root[2][5][0][0][0][0].tag)
        self.assertEqual(config.ROAD_MARK_TAG, junction.root[2][5][0][0][0][1].tag)
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0),
            junction.root[2][5][0][0][0][1].get(config.LANE_SOFFSET_TAG),
        )
        self.assertEqual(config.SOLID, junction.root[2][5][0][0][0][1].get(config.TYPE_TAG))
        self.assertEqual(
            config.STANDARD, junction.root[2][5][0][0][0][1].get(config.ROAD_MARK_WEIGHT_TAG)
        )
        self.assertEqual(
            config.STANDARD, junction.root[2][5][0][0][0][1].get(config.ROAD_MARK_COLOR_TAG)
        )
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0.13),
            junction.root[2][5][0][0][0][1].get(config.SIGNAL_WIDTH_TAG),
        )
        self.assertEqual(config.LANE_SECTION_LEFT_TAG, junction.root[2][5][0][1].tag)
        self.assertEqual(config.LANE_TAG, junction.root[2][5][0][1][0].tag)
        self.assertEqual("1", junction.root[2][5][0][1][0].get(config.ID_TAG))
        self.assertEqual("driving", junction.root[2][5][0][1][0].get(config.TYPE_TAG))
        self.assertEqual(config.FALSE, junction.root[2][5][0][1][0].get(config.LEVEL_TAG))
        self.assertEqual(config.LINK_TAG, junction.root[2][5][0][1][0][0].tag)
        self.assertEqual(config.SIGNAL_WIDTH_TAG, junction.root[2][5][0][1][0][1].tag)
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0),
            junction.root[2][5][0][1][0][1].get(config.LANE_SOFFSET_TAG),
        )
        self.assertEqual(
            "2.9999000016667212e+00", junction.root[2][5][0][1][0][1].get(config.LANE_A_TAG)
        )
        self.assertEqual(
            "1.8194390151268435e-05", junction.root[2][5][0][1][0][1].get(config.LANE_B_TAG)
        )
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0),
            junction.root[2][5][0][1][0][1].get(config.LANE_C_TAG),
        )
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0),
            junction.root[2][5][0][1][0][1].get(config.LANE_D_TAG),
        )
        self.assertEqual(config.ROAD_MARK_TAG, junction.root[2][5][0][1][0][2].tag)
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0),
            junction.root[2][5][0][1][0][2].get(config.LANE_SOFFSET_TAG),
        )
        self.assertEqual(config.SOLID, junction.root[2][5][0][1][0][2].get(config.TYPE_TAG))
        self.assertEqual(
            config.STANDARD, junction.root[2][5][0][1][0][2].get(config.ROAD_MARK_WEIGHT_TAG)
        )
        self.assertEqual(
            config.STANDARD, junction.root[2][5][0][1][0][2].get(config.ROAD_MARK_COLOR_TAG)
        )
        self.assertEqual(
            str.format(config.DOUBLE_FORMAT_PATTERN, 0.13),
            junction.root[2][5][0][1][0][2].get(config.SIGNAL_WIDTH_TAG),
        )
        self.assertEqual(config.LANE_SECTION_RIGHT_TAG, junction.root[2][5][0][2].tag)
        self.assertEqual(config.LANE_TAG, junction.root[2][5][0][2][0].tag)
        self.assertEqual("-1", junction.root[2][5][0][2][0].get(config.ID_TAG))
        self.assertEqual("driving", junction.root[2][5][0][2][0].get(config.TYPE_TAG))
        self.assertEqual(config.FALSE, junction.root[2][5][0][2][0].get(config.LEVEL_TAG))
        self.assertEqual(config.LINK_TAG, junction.root[2][5][0][2][0][0].tag)
        self.assertEqual(config.SUCCESSOR_TAG, junction.root[2][5][0][2][0][0][0].tag)
        self.assertEqual("1", junction.root[2][5][0][2][0][0][0].get(config.ID_TAG))
        self.assertEqual(config.PREDECESSOR_TAG, junction.root[2][5][0][2][0][0][1].tag)
        self.assertEqual("1", junction.root[2][5][0][2][0][0][1].get(config.ID_TAG))
        self.assertEqual(config.SIGNAL_WIDTH_TAG, junction.root[2][5][0][2][0][1].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[2][5][0][2][0][1].get(config.LANE_SOFFSET_TAG)
        )
        self.assertEqual(
            "2.9999999999999996e+00", junction.root[2][5][0][2][0][1].get(config.LANE_A_TAG)
        )
        self.assertEqual(
            "-3.0764427084074053e-17", junction.root[2][5][0][2][0][1].get(config.LANE_B_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[2][5][0][2][0][1].get(config.LANE_C_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[2][5][0][2][0][1].get(config.LANE_D_TAG)
        )
        self.assertEqual(config.ROAD_MARK_TAG, junction.root[2][5][0][2][0][2].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[2][5][0][2][0][2].get(config.LANE_SOFFSET_TAG)
        )
        self.assertEqual(config.SOLID, junction.root[2][5][0][2][0][2].get(config.TYPE_TAG))
        self.assertEqual(
            config.STANDARD, junction.root[2][5][0][2][0][2].get(config.ROAD_MARK_WEIGHT_TAG)
        )
        self.assertEqual(
            config.STANDARD, junction.root[2][5][0][2][0][2].get(config.ROAD_MARK_COLOR_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0.13),
            junction.root[2][5][0][1][0][2].get(config.SIGNAL_WIDTH_TAG),
        )
        self.assertEqual(config.OBJECTS_TAG, junction.root[2][6].tag)
        self.assertEqual(config.SIGNALS_TAG, junction.root[2][7].tag)

    def checkJunctionRoot3(self, junction):
        self.assertEqual(config.ROAD_TAG, junction.root[3].tag)
        self.assertEqual("", junction.root[3].get(config.NAME_TAG))
        self.assertEqual("2.0000000002049873e+01", junction.root[3].get(config.LENGTH_TAG))
        self.assertEqual("23", junction.root[3].get(config.ID_TAG))
        self.assertEqual("-1", junction.root[3].get(config.JUNCTION_TAG))
        self.assertEqual(config.LINK_TAG, junction.root[3][0].tag)
        self.assertEqual(config.TYPE_TAG, junction.root[3][1].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[3][1].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(config.TOWN_TAG, junction.root[3][1].get(config.TYPE_TAG))
        self.assertEqual(config.PLAN_VIEW_TAG, junction.root[3][2].tag)
        self.assertEqual(config.GEOMETRY_TAG, junction.root[3][2][0].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[3][2][0].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[3][2][0].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-3.5000000000000000e+00", junction.root[3][2][0].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.5707963267948966e+00", junction.root[3][2][0].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[3][2][0].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[3][2][1].tag)
        self.assertEqual(
            "1.0000000000000000e+00", junction.root[3][2][1].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[3][2][1].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-4.5000000000000000e+00", junction.root[3][2][1].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.5707963267948966e+00", junction.root[3][2][1].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[3][2][1].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[3][2][2].tag)
        self.assertEqual(
            "2.0000000000000000e+00", junction.root[3][2][2].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[3][2][2].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-5.5000000000000000e+00", junction.root[3][2][2].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.5707963267948966e+00", junction.root[3][2][2].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[3][2][2].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[3][2][3].tag)
        self.assertEqual(
            "3.0000000000000000e+00", junction.root[3][2][3].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[3][2][3].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-6.5000000000000000e+00", junction.root[3][2][3].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.5707963267948966e+00", junction.root[3][2][3].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[3][2][3].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[3][2][4].tag)
        self.assertEqual(
            "4.0000000000000000e+00", junction.root[3][2][4].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[3][2][4].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-7.5000000000000000e+00", junction.root[3][2][4].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.5707963267948966e+00", junction.root[3][2][4].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[3][2][4].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[3][2][5].tag)
        self.assertEqual(
            "5.0000000000000000e+00", junction.root[3][2][5].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[3][2][5].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-8.5000000000000000e+00", junction.root[3][2][5].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.5707963267948966e+00", junction.root[3][2][5].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[3][2][5].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[3][2][6].tag)
        self.assertEqual(
            "6.0000000000000000e+00", junction.root[3][2][6].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[3][2][6].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-9.5000000000000000e+00", junction.root[3][2][6].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.5707963267948966e+00", junction.root[3][2][6].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[3][2][6].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[3][2][7].tag)
        self.assertEqual(
            "7.0000000000000000e+00", junction.root[3][2][7].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[3][2][7].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.0500000000000000e+01", junction.root[3][2][7].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.5707963267948966e+00", junction.root[3][2][7].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[3][2][7].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[3][2][8].tag)
        self.assertEqual(
            "8.0000000000000000e+00", junction.root[3][2][8].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[3][2][8].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.1500000000000000e+01", junction.root[3][2][8].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.5708013306197575e+00", junction.root[3][2][8].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("9.9999999989993782e-01", junction.root[3][2][8].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[3][2][9].tag)
        self.assertEqual(
            "8.9999999998999378e+00", junction.root[3][2][9].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.4999994996175140e+01", junction.root[3][2][9].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.2499999999887418e+01", junction.root[3][2][9].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.5708413252199229e+00", junction.root[3][2][9].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[3][2][9].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[3][2][10].tag)
        self.assertEqual(
            "9.9999999998999378e+00", junction.root[3][2][10].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.4999949997750129e+01", junction.root[3][2][10].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.3499999998874989e+01", junction.root[3][2][10].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.5708413252199194e+00", junction.root[3][2][10].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[3][2][10].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[3][2][11].tag)
        self.assertEqual(
            "1.0999999999899938e+01", junction.root[3][2][11].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.4999904999325121e+01", junction.root[3][2][11].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.4499999997862560e+01", junction.root[3][2][11].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.5708013261200182e+00", junction.root[3][2][11].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("9.9999999990001598e-01", junction.root[3][2][11].get(config.LENGTH_TAG))
        self.assertEqual(config.ARC_TAG, junction.root[3][2][11][0].tag)
        self.assertEqual(
            "2.1249381240322324e-05", junction.root[3][2][11][0].get(config.GEOMETRY_CURVATURE_TAG)
        )
        self.assertEqual(config.GEOMETRY_TAG, junction.root[3][2][12].tag)
        self.assertEqual(
            "1.1999999999799954e+01", junction.root[3][2][12].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.4999900000000000e+01", junction.root[3][2][12].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.5499999997750079e+01", junction.root[3][2][12].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.5707963267948966e+00", junction.root[3][2][12].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000018e+00", junction.root[3][2][12].get(config.LENGTH_TAG))
        self.assertEqual(config.ARC_TAG, junction.root[3][2][12][0].tag)
        self.assertEqual(
            "1.2499437534112541e-05", junction.root[3][2][12][0].get(config.GEOMETRY_CURVATURE_TAG)
        )
        self.assertEqual(config.GEOMETRY_TAG, junction.root[3][2][13].tag)
        self.assertEqual(
            "1.2999999999799956e+01", junction.root[3][2][13].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.4999900000000000e+01", junction.root[3][2][13].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.6499999997750081e+01", junction.root[3][2][13].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.5707963267948966e+00", junction.root[3][2][13].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[3][2][13].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[3][2][14].tag)
        self.assertEqual(
            "1.3999999999799956e+01", junction.root[3][2][14].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.4999900000000000e+01", junction.root[3][2][14].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.7499999997750081e+01", junction.root[3][2][14].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.5707963267948966e+00", junction.root[3][2][14].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[3][2][14].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[3][2][15].tag)
        self.assertEqual(
            "1.4999999999799956e+01", junction.root[3][2][15].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.4999900000000000e+01", junction.root[3][2][15].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.8499999997750081e+01", junction.root[3][2][15].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.5707963267948966e+00", junction.root[3][2][15].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[3][2][15].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[3][2][16].tag)
        self.assertEqual(
            "1.5999999999799956e+01", junction.root[3][2][16].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.4999900000000000e+01", junction.root[3][2][16].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.9499999997750081e+01", junction.root[3][2][16].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.5707963267948966e+00", junction.root[3][2][16].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("9.9999999999999822e-01", junction.root[3][2][16].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[3][2][17].tag)
        self.assertEqual(
            "1.6999999999799954e+01", junction.root[3][2][17].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.4999900000000000e+01", junction.root[3][2][17].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-2.0499999997750081e+01", junction.root[3][2][17].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.5707963267948966e+00", junction.root[3][2][17].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("9.9999999999999645e-01", junction.root[3][2][17].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[3][2][18].tag)
        self.assertEqual(
            "1.7999999999799950e+01", junction.root[3][2][18].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.4999900000000000e+01", junction.root[3][2][18].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-2.1499999997750077e+01", junction.root[3][2][18].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.5707963267948966e+00", junction.root[3][2][18].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[3][2][18].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[3][2][19].tag)
        self.assertEqual(
            "1.8999999999799950e+01", junction.root[3][2][19].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.4999900000000000e+01", junction.root[3][2][19].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-2.2499999997750077e+01", junction.root[3][2][19].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.5707963267948966e+00", junction.root[3][2][19].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[3][2][19].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[3][2][20].tag)
        self.assertEqual(
            "1.9999999999799950e+01", junction.root[3][2][20].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.4999900000000000e+01", junction.root[3][2][20].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-2.3499999997750077e+01", junction.root[3][2][20].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.5707963267948966e+00", junction.root[3][2][20].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("2.2499229146433208e-09", junction.root[3][2][20].get(config.LENGTH_TAG))
        self.assertEqual(config.ELEVATION_PROFILE_TAG, junction.root[3][3].tag)
        self.assertEqual(config.LATERAL_PROFILE_TAG, junction.root[3][4].tag)
        self.assertEqual(config.LANES_TAG, junction.root[3][5].tag)
        self.assertEqual(config.LANE_SECTION_TAG, junction.root[3][5][0].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[3][5][0].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(config.LANE_SECTION_CENTER_TAG, junction.root[3][5][0][0].tag)
        self.assertEqual(config.LANE_TAG, junction.root[3][5][0][0][0].tag)
        self.assertEqual("0", junction.root[3][5][0][0][0].get(config.ID_TAG))
        self.assertEqual("driving", junction.root[3][5][0][0][0].get(config.TYPE_TAG))
        self.assertEqual(config.FALSE, junction.root[3][5][0][0][0].get(config.LEVEL_TAG))
        self.assertEqual(config.LINK_TAG, junction.root[3][5][0][0][0][0].tag)
        self.assertEqual(config.ROAD_MARK_TAG, junction.root[3][5][0][0][0][1].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[3][5][0][0][0][1].get(config.LANE_SOFFSET_TAG)
        )
        self.assertEqual(config.SOLID, junction.root[3][5][0][0][0][1].get(config.TYPE_TAG))
        self.assertEqual(
            config.STANDARD, junction.root[3][5][0][0][0][1].get(config.ROAD_MARK_WEIGHT_TAG)
        )
        self.assertEqual(
            config.STANDARD, junction.root[3][5][0][0][0][1].get(config.ROAD_MARK_COLOR_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0.13),
            junction.root[3][5][0][0][0][1].get(config.SIGNAL_WIDTH_TAG),
        )
        self.assertEqual(config.LANE_SECTION_LEFT_TAG, junction.root[3][5][0][1].tag)
        self.assertEqual(config.LANE_TAG, junction.root[3][5][0][1][0].tag)
        self.assertEqual("1", junction.root[3][5][0][1][0].get(config.ID_TAG))
        self.assertEqual("driving", junction.root[3][5][0][1][0].get(config.TYPE_TAG))
        self.assertEqual(config.FALSE, junction.root[3][5][0][1][0].get(config.LEVEL_TAG))
        self.assertEqual(config.LINK_TAG, junction.root[3][5][0][1][0][0].tag)
        self.assertEqual(config.SIGNAL_WIDTH_TAG, junction.root[3][5][0][1][0][1].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[3][5][0][1][0][1].get(config.LANE_SOFFSET_TAG)
        )
        self.assertEqual(
            "2.9999999999999996e+00", junction.root[3][5][0][1][0][1].get(config.LANE_A_TAG)
        )
        self.assertEqual(
            "-1.5700924585071457e-17", junction.root[3][5][0][1][0][1].get(config.LANE_B_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[3][5][0][1][0][1].get(config.LANE_C_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[3][5][0][1][0][1].get(config.LANE_D_TAG)
        )
        self.assertEqual(config.ROAD_MARK_TAG, junction.root[3][5][0][1][0][2].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[3][5][0][1][0][2].get(config.LANE_SOFFSET_TAG)
        )
        self.assertEqual(config.SOLID, junction.root[3][5][0][1][0][2].get(config.TYPE_TAG))
        self.assertEqual(
            config.STANDARD, junction.root[3][5][0][1][0][2].get(config.ROAD_MARK_WEIGHT_TAG)
        )
        self.assertEqual(
            config.STANDARD, junction.root[3][5][0][1][0][2].get(config.ROAD_MARK_COLOR_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0.13),
            junction.root[3][5][0][1][0][2].get(config.SIGNAL_WIDTH_TAG),
        )
        self.assertEqual(config.LANE_SECTION_RIGHT_TAG, junction.root[3][5][0][2].tag)
        self.assertEqual(config.LANE_TAG, junction.root[3][5][0][2][0].tag)
        self.assertEqual("-1", junction.root[3][5][0][2][0].get(config.ID_TAG))
        self.assertEqual("driving", junction.root[3][5][0][2][0].get(config.TYPE_TAG))
        self.assertEqual(config.FALSE, junction.root[3][5][0][2][0].get(config.LEVEL_TAG))
        self.assertEqual(config.LINK_TAG, junction.root[3][5][0][2][0][0].tag)
        self.assertEqual(config.SIGNAL_WIDTH_TAG, junction.root[3][5][0][2][0][1].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[3][5][0][2][0][1].get(config.LANE_SOFFSET_TAG)
        )
        self.assertEqual(
            "2.9999999999999996e+00", junction.root[3][5][0][2][0][1].get(config.LANE_A_TAG)
        )
        self.assertEqual(
            "-1.5700924585071457e-17", junction.root[3][5][0][2][0][1].get(config.LANE_B_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[3][5][0][2][0][1].get(config.LANE_C_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[3][5][0][2][0][1].get(config.LANE_D_TAG)
        )
        self.assertEqual(config.ROAD_MARK_TAG, junction.root[3][5][0][2][0][2].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[3][5][0][2][0][2].get(config.LANE_SOFFSET_TAG)
        )
        self.assertEqual(config.SOLID, junction.root[3][5][0][2][0][2].get(config.TYPE_TAG))
        self.assertEqual(
            config.STANDARD, junction.root[3][5][0][2][0][2].get(config.ROAD_MARK_WEIGHT_TAG)
        )
        self.assertEqual(
            config.STANDARD, junction.root[3][5][0][2][0][2].get(config.ROAD_MARK_COLOR_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0.13),
            junction.root[3][5][0][1][0][2].get(config.SIGNAL_WIDTH_TAG),
        )
        self.assertEqual(config.OBJECTS_TAG, junction.root[3][6].tag)
        self.assertEqual(config.SIGNALS_TAG, junction.root[3][7].tag)

    def checkJunctionRoot4(self, junction):
        self.assertEqual(config.ROAD_TAG, junction.root[4].tag)
        self.assertEqual("", junction.root[4].get(config.NAME_TAG))
        self.assertEqual(str.format("{0:.16e}", 10), junction.root[4].get(config.LENGTH_TAG))
        self.assertEqual("24", junction.root[4].get(config.ID_TAG))
        self.assertEqual("16", junction.root[4].get(config.JUNCTION_TAG))
        self.assertEqual(config.LINK_TAG, junction.root[4][0].tag)
        self.assertEqual(config.TYPE_TAG, junction.root[4][1].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[4][1].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(config.TOWN_TAG, junction.root[4][1].get(config.TYPE_TAG))
        self.assertEqual(config.PLAN_VIEW_TAG, junction.root[4][2].tag)
        self.assertEqual(config.GEOMETRY_TAG, junction.root[4][2][0].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[4][2][0].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[4][2][0].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-3.5000000000000000e+00", junction.root[4][2][0].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[4][2][0].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[4][2][0].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[4][2][1].tag)
        self.assertEqual(
            str.format("{0:.16e}", 1), junction.root[4][2][1].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[4][2][1].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-2.5000000000000000e+00", junction.root[4][2][1].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[4][2][1].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual(str.format("{0:.16e}", 1), junction.root[4][2][1].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[4][2][2].tag)
        self.assertEqual(
            str.format("{0:.16e}", 2), junction.root[4][2][2].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[4][2][2].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-1.5000000000000000e+00", junction.root[4][2][2].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[4][2][2].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual(str.format("{0:.16e}", 1), junction.root[4][2][2].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[4][2][3].tag)
        self.assertEqual(
            str.format("{0:.16e}", 3), junction.root[4][2][3].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[4][2][3].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "-4.9999999999999978e-01", junction.root[4][2][3].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[4][2][3].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual(str.format("{0:.16e}", 1), junction.root[4][2][3].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[4][2][4].tag)
        self.assertEqual(
            str.format("{0:.16e}", 4), junction.root[4][2][4].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[4][2][4].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "5.0000000000000033e-01", junction.root[4][2][4].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[4][2][4].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual(str.format("{0:.16e}", 1), junction.root[4][2][4].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[4][2][5].tag)
        self.assertEqual(
            str.format("{0:.16e}", 5), junction.root[4][2][5].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[4][2][5].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5000000000000000e+00", junction.root[4][2][5].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[4][2][5].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual(str.format("{0:.16e}", 1), junction.root[4][2][5].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[4][2][6].tag)
        self.assertEqual(
            str.format("{0:.16e}", 6), junction.root[4][2][6].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[4][2][6].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.4999999999999996e+00", junction.root[4][2][6].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[4][2][6].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual(str.format("{0:.16e}", 1), junction.root[4][2][6].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[4][2][7].tag)
        self.assertEqual(
            str.format("{0:.16e}", 7), junction.root[4][2][7].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[4][2][7].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "3.4999999999999991e+00", junction.root[4][2][7].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[4][2][7].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual(str.format("{0:.16e}", 1), junction.root[4][2][7].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[4][2][8].tag)
        self.assertEqual(
            str.format("{0:.16e}", 8), junction.root[4][2][8].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[4][2][8].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "4.4999999999999991e+00", junction.root[4][2][8].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[4][2][8].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual(str.format("{0:.16e}", 1), junction.root[4][2][8].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[4][2][9].tag)
        self.assertEqual(
            str.format("{0:.16e}", 9), junction.root[4][2][9].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[4][2][9].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "5.5000000000000000e+00", junction.root[4][2][9].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[4][2][9].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual(str.format("{0:.16e}", 1), junction.root[4][2][9].get(config.LENGTH_TAG))
        self.assertEqual(config.ELEVATION_PROFILE_TAG, junction.root[4][3].tag)
        self.assertEqual(config.LATERAL_PROFILE_TAG, junction.root[4][4].tag)
        self.assertEqual(config.LANES_TAG, junction.root[4][5].tag)
        self.assertEqual(config.LANE_SECTION_TAG, junction.root[4][5][0].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[4][5][0].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(config.LANE_SECTION_CENTER_TAG, junction.root[4][5][0][0].tag)
        self.assertEqual(config.LANE_TAG, junction.root[4][5][0][0][0].tag)
        self.assertEqual("0", junction.root[4][5][0][0][0].get(config.ID_TAG))
        self.assertEqual("driving", junction.root[4][5][0][0][0].get(config.TYPE_TAG))
        self.assertEqual(config.FALSE, junction.root[4][5][0][0][0].get(config.LEVEL_TAG))
        self.assertEqual(config.LINK_TAG, junction.root[4][5][0][0][0][0].tag)
        self.assertEqual(config.ROAD_MARK_TAG, junction.root[4][5][0][0][0][1].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[4][5][0][0][0][1].get(config.LANE_SOFFSET_TAG)
        )
        self.assertEqual(config.SOLID, junction.root[4][5][0][0][0][1].get(config.TYPE_TAG))
        self.assertEqual(
            config.STANDARD, junction.root[4][5][0][0][0][1].get(config.ROAD_MARK_WEIGHT_TAG)
        )
        self.assertEqual(
            config.STANDARD, junction.root[4][5][0][0][0][1].get(config.ROAD_MARK_COLOR_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0.13),
            junction.root[4][5][0][0][0][1].get(config.SIGNAL_WIDTH_TAG),
        )
        self.assertEqual(config.LANE_SECTION_LEFT_TAG, junction.root[4][5][0][1].tag)
        self.assertEqual(config.LANE_TAG, junction.root[4][5][0][1][0].tag)
        self.assertEqual("1", junction.root[4][5][0][1][0].get(config.ID_TAG))
        self.assertEqual("driving", junction.root[4][5][0][1][0].get(config.TYPE_TAG))
        self.assertEqual(config.FALSE, junction.root[4][5][0][1][0].get(config.LEVEL_TAG))
        self.assertEqual(config.LINK_TAG, junction.root[4][5][0][1][0][0].tag)
        self.assertEqual(config.SUCCESSOR_TAG, junction.root[4][5][0][1][0][0][0].tag)
        self.assertEqual("1", junction.root[4][5][0][1][0][0][0].get(config.ID_TAG))
        self.assertEqual(config.PREDECESSOR_TAG, junction.root[4][5][0][1][0][0][1].tag)
        self.assertEqual("-1", junction.root[4][5][0][1][0][0][1].get(config.ID_TAG))
        self.assertEqual(config.SIGNAL_WIDTH_TAG, junction.root[4][5][0][1][0][1].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[4][5][0][1][0][1].get(config.LANE_SOFFSET_TAG)
        )
        self.assertEqual(
            "2.9999999999999996e+00", junction.root[4][5][0][1][0][1].get(config.LANE_A_TAG)
        )
        self.assertEqual(
            "-3.1401849173675501e-17", junction.root[4][5][0][1][0][1].get(config.LANE_B_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[4][5][0][1][0][1].get(config.LANE_C_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[4][5][0][1][0][1].get(config.LANE_D_TAG)
        )
        self.assertEqual(config.ROAD_MARK_TAG, junction.root[4][5][0][1][0][2].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[4][5][0][1][0][2].get(config.LANE_SOFFSET_TAG)
        )
        self.assertEqual(config.SOLID, junction.root[4][5][0][1][0][2].get(config.TYPE_TAG))
        self.assertEqual(
            config.STANDARD, junction.root[4][5][0][1][0][2].get(config.ROAD_MARK_WEIGHT_TAG)
        )
        self.assertEqual(
            config.STANDARD, junction.root[4][5][0][1][0][2].get(config.ROAD_MARK_COLOR_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0.13),
            junction.root[4][5][0][1][0][2].get(config.SIGNAL_WIDTH_TAG),
        )
        self.assertEqual(config.LANE_SECTION_RIGHT_TAG, junction.root[4][5][0][2].tag)
        self.assertEqual(config.LANE_TAG, junction.root[4][5][0][2][0].tag)
        self.assertEqual("-1", junction.root[4][5][0][2][0].get(config.ID_TAG))
        self.assertEqual("driving", junction.root[4][5][0][2][0].get(config.TYPE_TAG))
        self.assertEqual(config.FALSE, junction.root[4][5][0][2][0].get(config.LEVEL_TAG))
        self.assertEqual(config.LINK_TAG, junction.root[4][5][0][2][0][0].tag)
        self.assertEqual(config.SUCCESSOR_TAG, junction.root[4][5][0][2][0][0][0].tag)
        self.assertEqual("-1", junction.root[4][5][0][2][0][0][0].get(config.ID_TAG))
        self.assertEqual(config.PREDECESSOR_TAG, junction.root[4][5][0][2][0][0][1].tag)
        self.assertEqual("1", junction.root[4][5][0][2][0][0][1].get(config.ID_TAG))
        self.assertEqual(config.SIGNAL_WIDTH_TAG, junction.root[4][5][0][2][0][1].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[4][5][0][2][0][1].get(config.LANE_SOFFSET_TAG)
        )
        self.assertEqual(
            "2.9999999999999996e+00", junction.root[4][5][0][2][0][1].get(config.LANE_A_TAG)
        )
        self.assertEqual(
            "-3.1401849173675501e-17", junction.root[4][5][0][2][0][1].get(config.LANE_B_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[4][5][0][2][0][1].get(config.LANE_C_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[4][5][0][2][0][1].get(config.LANE_D_TAG)
        )
        self.assertEqual(config.ROAD_MARK_TAG, junction.root[4][5][0][2][0][2].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[4][5][0][2][0][2].get(config.LANE_SOFFSET_TAG)
        )
        self.assertEqual(config.SOLID, junction.root[4][5][0][2][0][2].get(config.TYPE_TAG))
        self.assertEqual(
            config.STANDARD, junction.root[4][5][0][2][0][2].get(config.ROAD_MARK_WEIGHT_TAG)
        )
        self.assertEqual(
            config.STANDARD, junction.root[4][5][0][2][0][2].get(config.ROAD_MARK_COLOR_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0.13),
            junction.root[4][5][0][1][0][2].get(config.SIGNAL_WIDTH_TAG),
        )
        self.assertEqual(config.OBJECTS_TAG, junction.root[4][6].tag)
        self.assertEqual(config.SIGNALS_TAG, junction.root[4][7].tag)

    def checkJunctionRoot5(self, junction):
        self.assertEqual(config.ROAD_TAG, junction.root[5].tag)
        self.assertEqual("", junction.root[5].get(config.NAME_TAG))
        self.assertEqual("7.8371961908546544e+00", junction.root[5].get(config.LENGTH_TAG))
        self.assertEqual("25", junction.root[5].get(config.ID_TAG))
        self.assertEqual("16", junction.root[5].get(config.JUNCTION_TAG))
        self.assertEqual(config.LINK_TAG, junction.root[5][0].tag)
        self.assertEqual(config.SUCCESSOR_TAG, junction.root[5][0][0].tag)
        self.assertEqual(config.ROAD_TAG, junction.root[5][0][0].get(config.ELEMENT_TYPE_TAG))
        self.assertEqual("26", junction.root[5][0][0].get(config.ELEMENT_ID_TAG))
        self.assertEqual(config.START_TAG, junction.root[5][0][0].get(config.CONTACT_POINT_TAG))
        self.assertEqual(config.PREDECESSOR_TAG, junction.root[5][0][1].tag)
        self.assertEqual(config.ROAD_TAG, junction.root[5][0][1].get(config.ELEMENT_TYPE_TAG))
        self.assertEqual("21", junction.root[5][0][1].get(config.ELEMENT_ID_TAG))
        self.assertEqual(config.END_TAG, junction.root[5][0][1].get(config.CONTACT_POINT_TAG))
        self.assertEqual(config.TYPE_TAG, junction.root[5][1].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[5][1].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(config.TOWN_TAG, junction.root[5][1].get(config.TYPE_TAG))
        self.assertEqual(config.PLAN_VIEW_TAG, junction.root[5][2].tag)
        self.assertEqual(config.GEOMETRY_TAG, junction.root[5][2][0].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[5][2][0].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.0000000000000000e+01", junction.root[5][2][0].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5000000000000000e+00", junction.root[5][2][0].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.0409118667749875e-01", junction.root[5][2][0].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("9.9818846834543962e-01", junction.root[5][2][0].get(config.LENGTH_TAG))
        self.assertEqual(config.SPIRAL_TAG, junction.root[5][2][0][0].tag)
        self.assertEqual(
            "9.6661735391434467e-02", junction.root[5][2][0][0].get(config.GEOMETRY_CURV_START_TAG)
        )
        self.assertEqual(
            "2.0008681885663243e-01", junction.root[5][2][0][0].get(config.GEOMETRY_CURV_END_TAG)
        )
        self.assertEqual(config.GEOMETRY_TAG, junction.root[5][2][1].tag)
        self.assertEqual(
            "9.9818846834543962e-01", junction.root[5][2][1].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.0992785675628028e+01", junction.root[5][2][1].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.6037150934320319e+00", junction.root[5][2][1].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.9831251917929136e-01", junction.root[5][2][1].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("9.9803689483890423e-01", junction.root[5][2][1].get(config.LENGTH_TAG))
        self.assertEqual(config.SPIRAL_TAG, junction.root[5][2][1][0].tag)
        self.assertEqual(
            "1.4823246264093384e-01", junction.root[5][2][1][0].get(config.GEOMETRY_CURV_START_TAG)
        )
        self.assertEqual(
            "1.9999092761075199e-01", junction.root[5][2][1][0].get(config.GEOMETRY_CURV_END_TAG)
        )
        self.assertEqual(config.GEOMETRY_TAG, junction.root[5][2][2].tag)
        self.assertEqual(
            "1.9962253631843438e+00", junction.root[5][2][2].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.1946743086701943e+01", junction.root[5][2][2].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.8970457964224201e+00", junction.root[5][2][2].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "5.0108304111505519e-01", junction.root[5][2][2].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("9.9797478185310817e-01", junction.root[5][2][2].get(config.LENGTH_TAG))
        self.assertEqual(config.ARC_TAG, junction.root[5][2][2][0].tag)
        self.assertEqual(
            "1.9999092761075199e-01", junction.root[5][2][2][0].get(config.GEOMETRY_CURVATURE_TAG)
        )
        self.assertEqual(config.GEOMETRY_TAG, junction.root[5][2][3].tag)
        self.assertEqual(
            "2.9942001450374520e+00", junction.root[5][2][3].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.2822029652913187e+01", junction.root[5][2][3].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.3764486460435799e+00", junction.root[5][2][3].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "7.0061437320409903e-01", junction.root[5][2][3].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("9.9799767868016787e-01", junction.root[5][2][3].get(config.LENGTH_TAG))
        self.assertEqual(config.ARC_TAG, junction.root[5][2][3][0].tag)
        self.assertEqual(
            "1.9990010068967926e-01", junction.root[5][2][3][0].get(config.GEOMETRY_CURVATURE_TAG)
        )
        self.assertEqual(config.GEOMETRY_TAG, junction.root[5][2][4].tag)
        self.assertEqual(
            "3.9921978237176199e+00", junction.root[5][2][4].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.3584945238761392e+01", junction.root[5][2][4].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "3.0198452387613948e+00", junction.root[5][2][4].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "8.9811201246612837e-01", junction.root[5][2][4].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("9.9802551825528640e-01", junction.root[5][2][4].get(config.LENGTH_TAG))
        self.assertEqual(config.ARC_TAG, junction.root[5][2][4][0].tag)
        self.assertEqual(
            "1.9987458546868983e-01", junction.root[5][2][4][0].get(config.GEOMETRY_CURVATURE_TAG)
        )
        self.assertEqual(config.GEOMETRY_TAG, junction.root[5][2][5].tag)
        self.assertEqual(
            "4.9902233419729063e+00", junction.root[5][2][5].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.4206802734301569e+01", junction.root[5][2][5].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "3.8004528164399827e+00", junction.root[5][2][5].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.1031016112701657e+00", junction.root[5][2][5].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("9.9808136990329643e-01", junction.root[5][2][5].get(config.LENGTH_TAG))
        self.assertEqual(config.SPIRAL_TAG, junction.root[5][2][5][0].tag)
        self.assertEqual(
            "2.0054671822491296e-01", junction.root[5][2][5][0].get(config.GEOMETRY_CURV_START_TAG)
        )
        self.assertEqual(
            "1.8461042715064427e-01", junction.root[5][2][5][0].get(config.GEOMETRY_CURV_END_TAG)
        )
        self.assertEqual(config.GEOMETRY_TAG, junction.root[5][2][6].tag)
        self.assertEqual(
            "5.9883047118762027e+00", junction.root[5][2][6].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.4656767524016992e+01", junction.root[5][2][6].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "4.6913501780728453e+00", junction.root[5][2][6].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.2970267268289768e+00", junction.root[5][2][6].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("9.9811694524803141e-01", junction.root[5][2][6].get(config.LENGTH_TAG))
        self.assertEqual(config.SPIRAL_TAG, junction.root[5][2][6][0].tag)
        self.assertEqual(
            "1.8461042715064427e-01", junction.root[5][2][6][0].get(config.GEOMETRY_CURV_START_TAG)
        )
        self.assertEqual(
            "1.5752693710870286e-01", junction.root[5][2][6][0].get(config.GEOMETRY_CURV_END_TAG)
        )
        self.assertEqual(config.GEOMETRY_TAG, junction.root[5][2][7].tag)
        self.assertEqual(
            "6.9864216571242341e+00", junction.root[5][2][7].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.4926620980220282e+01", junction.root[5][2][7].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "5.6522958313573595e+00", junction.root[5][2][7].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.4844393654723524e+00", junction.root[5][2][7].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("8.5077453373042022e-01", junction.root[5][2][7].get(config.LENGTH_TAG))
        self.assertEqual(config.SPIRAL_TAG, junction.root[5][2][7][0].tag)
        self.assertEqual(
            "1.5752693710870286e-01", junction.root[5][2][7][0].get(config.GEOMETRY_CURV_START_TAG)
        )
        self.assertEqual(
            "1.2846240204463380e-01", junction.root[5][2][7][0].get(config.GEOMETRY_CURV_END_TAG)
        )
        self.assertEqual(config.ELEVATION_PROFILE_TAG, junction.root[5][3].tag)
        self.assertEqual(config.LATERAL_PROFILE_TAG, junction.root[5][4].tag)
        self.assertEqual(config.LANES_TAG, junction.root[5][5].tag)
        self.assertEqual(config.LANE_SECTION_TAG, junction.root[5][5][0].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[5][5][0].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(config.LANE_SECTION_CENTER_TAG, junction.root[5][5][0][0].tag)
        self.assertEqual(config.LANE_TAG, junction.root[5][5][0][0][0].tag)
        self.assertEqual("0", junction.root[5][5][0][0][0].get(config.ID_TAG))
        self.assertEqual("driving", junction.root[5][5][0][0][0].get(config.TYPE_TAG))
        self.assertEqual(config.FALSE, junction.root[5][5][0][0][0].get(config.LEVEL_TAG))
        self.assertEqual(config.LINK_TAG, junction.root[5][5][0][0][0][0].tag)
        self.assertEqual(config.ROAD_MARK_TAG, junction.root[5][5][0][0][0][1].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[5][5][0][0][0][1].get(config.LANE_SOFFSET_TAG)
        )
        self.assertEqual(config.SOLID, junction.root[5][5][0][0][0][1].get(config.TYPE_TAG))
        self.assertEqual(
            config.STANDARD, junction.root[5][5][0][0][0][1].get(config.ROAD_MARK_WEIGHT_TAG)
        )
        self.assertEqual(
            config.STANDARD, junction.root[5][5][0][0][0][1].get(config.ROAD_MARK_COLOR_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0.13),
            junction.root[5][5][0][0][0][1].get(config.SIGNAL_WIDTH_TAG),
        )
        self.assertEqual(config.LANE_SECTION_LEFT_TAG, junction.root[5][5][0][1].tag)
        self.assertEqual(config.LANE_TAG, junction.root[5][5][0][1][0].tag)
        self.assertEqual("1", junction.root[5][5][0][1][0].get(config.ID_TAG))
        self.assertEqual("driving", junction.root[5][5][0][1][0].get(config.TYPE_TAG))
        self.assertEqual(config.FALSE, junction.root[5][5][0][1][0].get(config.LEVEL_TAG))
        self.assertEqual(config.LINK_TAG, junction.root[5][5][0][1][0][0].tag)
        self.assertEqual(config.SIGNAL_WIDTH_TAG, junction.root[5][5][0][1][0][1].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[5][5][0][1][0][1].get(config.LANE_SOFFSET_TAG)
        )
        self.assertEqual(
            "3.0000000016666659e+00", junction.root[5][5][0][1][0][1].get(config.LANE_A_TAG)
        )
        self.assertEqual(
            "-3.0324098647227403e-10", junction.root[5][5][0][1][0][1].get(config.LANE_B_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[5][5][0][1][0][1].get(config.LANE_C_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[5][5][0][1][0][1].get(config.LANE_D_TAG)
        )
        self.assertEqual(config.ROAD_MARK_TAG, junction.root[5][5][0][1][0][2].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[5][5][0][1][0][2].get(config.LANE_SOFFSET_TAG)
        )
        self.assertEqual(config.SOLID, junction.root[5][5][0][1][0][2].get(config.TYPE_TAG))
        self.assertEqual(
            config.STANDARD, junction.root[5][5][0][1][0][2].get(config.ROAD_MARK_WEIGHT_TAG)
        )
        self.assertEqual(
            config.STANDARD, junction.root[5][5][0][1][0][2].get(config.ROAD_MARK_COLOR_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0.13),
            junction.root[5][5][0][1][0][2].get(config.SIGNAL_WIDTH_TAG),
        )
        self.assertEqual(config.LANE_SECTION_RIGHT_TAG, junction.root[5][5][0][2].tag)
        self.assertEqual(config.LANE_TAG, junction.root[5][5][0][2][0].tag)
        self.assertEqual("-1", junction.root[5][5][0][2][0].get(config.ID_TAG))
        self.assertEqual("driving", junction.root[5][5][0][2][0].get(config.TYPE_TAG))
        self.assertEqual(config.FALSE, junction.root[5][5][0][2][0].get(config.LEVEL_TAG))
        self.assertEqual(config.LINK_TAG, junction.root[5][5][0][2][0][0].tag)
        self.assertEqual(config.SUCCESSOR_TAG, junction.root[5][5][0][2][0][0][0].tag)
        self.assertEqual("-1", junction.root[5][5][0][2][0][0][0].get(config.ID_TAG))
        self.assertEqual(config.PREDECESSOR_TAG, junction.root[5][5][0][2][0][0][1].tag)
        self.assertEqual("-1", junction.root[5][5][0][2][0][0][1].get(config.ID_TAG))
        self.assertEqual(config.SIGNAL_WIDTH_TAG, junction.root[5][5][0][2][0][1].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[5][5][0][2][0][1].get(config.LANE_SOFFSET_TAG)
        )
        self.assertEqual(
            "2.9999999999999996e+00", junction.root[5][5][0][2][0][1].get(config.LANE_A_TAG)
        )
        self.assertEqual(
            "-3.0764580073237453e-17", junction.root[5][5][0][2][0][1].get(config.LANE_B_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[5][5][0][2][0][1].get(config.LANE_C_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[5][5][0][2][0][1].get(config.LANE_D_TAG)
        )
        self.assertEqual(config.ROAD_MARK_TAG, junction.root[5][5][0][2][0][2].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[5][5][0][2][0][2].get(config.LANE_SOFFSET_TAG)
        )
        self.assertEqual(config.SOLID, junction.root[5][5][0][2][0][2].get(config.TYPE_TAG))
        self.assertEqual(
            config.STANDARD, junction.root[5][5][0][2][0][2].get(config.ROAD_MARK_WEIGHT_TAG)
        )
        self.assertEqual(
            config.STANDARD, junction.root[5][5][0][2][0][2].get(config.ROAD_MARK_COLOR_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0.13),
            junction.root[5][5][0][1][0][2].get(config.SIGNAL_WIDTH_TAG),
        )
        self.assertEqual(config.OBJECTS_TAG, junction.root[5][6].tag)
        self.assertEqual(config.SIGNALS_TAG, junction.root[5][7].tag)

    def checkJunctionRoot6(self, junction):
        self.assertEqual(config.ROAD_TAG, junction.root[6].tag)
        self.assertEqual("", junction.root[6].get(config.NAME_TAG))
        self.assertEqual("2.0000100000000000e+01", junction.root[6].get(config.LENGTH_TAG))
        self.assertEqual("26", junction.root[6].get(config.ID_TAG))
        self.assertEqual("-1", junction.root[6].get(config.JUNCTION_TAG))
        self.assertEqual(config.LINK_TAG, junction.root[6][0].tag)
        self.assertEqual(config.TYPE_TAG, junction.root[6][1].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[6][1].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(config.TOWN_TAG, junction.root[6][1].get(config.TYPE_TAG))
        self.assertEqual(config.PLAN_VIEW_TAG, junction.root[6][2].tag)
        self.assertEqual(config.GEOMETRY_TAG, junction.root[6][2][0].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[6][2][0].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[6][2][0].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "6.4999000000000002e+00", junction.root[6][2][0].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[6][2][0].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[6][2][0].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[6][2][1].tag)
        self.assertEqual(
            "1.0000000000000000e+00", junction.root[6][2][1].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[6][2][1].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "7.4999000000000002e+00", junction.root[6][2][1].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[6][2][1].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[6][2][1].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[6][2][2].tag)
        self.assertEqual(
            "2.0000000000000000e+00", junction.root[6][2][2].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[6][2][2].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "8.4999000000000002e+00", junction.root[6][2][2].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[6][2][2].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[6][2][2].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[6][2][3].tag)
        self.assertEqual(
            "3.0000000000000000e+00", junction.root[6][2][3].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[6][2][3].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "9.4999000000000002e+00", junction.root[6][2][3].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[6][2][3].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[6][2][3].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[6][2][4].tag)
        self.assertEqual(
            "4.0000000000000000e+00", junction.root[6][2][4].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[6][2][4].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.0499900000000000e+01", junction.root[6][2][4].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[6][2][4].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[6][2][4].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[6][2][5].tag)
        self.assertEqual(
            "5.0000000000000000e+00", junction.root[6][2][5].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[6][2][5].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.1499900000000000e+01", junction.root[6][2][5].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[6][2][5].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[6][2][5].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[6][2][6].tag)
        self.assertEqual(
            "6.0000000000000000e+00", junction.root[6][2][6].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[6][2][6].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.2499900000000000e+01", junction.root[6][2][6].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[6][2][6].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[6][2][6].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[6][2][7].tag)
        self.assertEqual(
            "7.0000000000000000e+00", junction.root[6][2][7].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[6][2][7].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.3499900000000000e+01", junction.root[6][2][7].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[6][2][7].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[6][2][7].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[6][2][8].tag)
        self.assertEqual(
            "8.0000000000000000e+00", junction.root[6][2][8].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[6][2][8].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.4499900000000000e+01", junction.root[6][2][8].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[6][2][8].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[6][2][8].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[6][2][9].tag)
        self.assertEqual(
            "9.0000000000000000e+00", junction.root[6][2][9].get(config.GEOMETRY_S_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[6][2][9].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5499900000000000e+01", junction.root[6][2][9].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[6][2][9].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[6][2][9].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[6][2][10].tag)
        self.assertEqual("1.0000000000000000e+01", junction.root[6][2][10].get("s"))
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[6][2][10].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.6499900000000000e+01", junction.root[6][2][10].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[6][2][10].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[6][2][10].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[6][2][11].tag)
        self.assertEqual("1.1000000000000000e+01", junction.root[6][2][11].get("s"))
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[6][2][11].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.7499900000000000e+01", junction.root[6][2][11].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[6][2][11].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[6][2][11].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[6][2][12].tag)
        self.assertEqual("1.2000000000000000e+01", junction.root[6][2][12].get("s"))
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[6][2][12].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.8499900000000000e+01", junction.root[6][2][12].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[6][2][12].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[6][2][12].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[6][2][13].tag)
        self.assertEqual("1.3000000000000000e+01", junction.root[6][2][13].get("s"))
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[6][2][13].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.9499900000000000e+01", junction.root[6][2][13].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[6][2][13].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[6][2][13].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[6][2][14].tag)
        self.assertEqual("1.4000000000000000e+01", junction.root[6][2][14].get("s"))
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[6][2][14].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.0499900000000000e+01", junction.root[6][2][14].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[6][2][14].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[6][2][14].get(config.LENGTH_TAG))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[6][2][15].tag)
        self.assertEqual("1.5000000000000000e+01", junction.root[6][2][15].get("s"))
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[6][2][15].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.1499900000000000e+01", junction.root[6][2][15].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[6][2][15].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[6][2][15].get("length"))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[6][2][16].tag)
        self.assertEqual("1.6000000000000000e+01", junction.root[6][2][16].get("s"))
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[6][2][16].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.2499900000000000e+01", junction.root[6][2][16].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[6][2][16].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[6][2][16].get("length"))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[6][2][17].tag)
        self.assertEqual("1.7000000000000000e+01", junction.root[6][2][17].get("s"))
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[6][2][17].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.3499900000000000e+01", junction.root[6][2][17].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[6][2][17].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[6][2][17].get("length"))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[6][2][18].tag)
        self.assertEqual("1.8000000000000000e+01", junction.root[6][2][18].get("s"))
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[6][2][18].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.4499900000000000e+01", junction.root[6][2][18].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[6][2][18].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[6][2][18].get("length"))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[6][2][19].tag)
        self.assertEqual("1.9000000000000000e+01", junction.root[6][2][19].get("s"))
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[6][2][19].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.5499900000000000e+01", junction.root[6][2][19].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[6][2][19].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("1.0000000000000000e+00", junction.root[6][2][19].get("length"))
        self.assertEqual(config.GEOMETRY_TAG, junction.root[6][2][20].tag)
        self.assertEqual("2.0000000000000000e+01", junction.root[6][2][20].get("s"))
        self.assertEqual(
            "2.5000000000000000e+01", junction.root[6][2][20].get(config.GEOMETRY_X_COORDINATE_TAG)
        )
        self.assertEqual(
            "2.6499900000000000e+01", junction.root[6][2][20].get(config.GEOMETRY_Y_COORDINATE_TAG)
        )
        self.assertEqual(
            "1.5707963267948966e+00", junction.root[6][2][20].get(config.GEOMETRY_HEADING_TAG)
        )
        self.assertEqual("9.9999999999766942e-05", junction.root[6][2][20].get("length"))
        self.assertEqual(config.ELEVATION_PROFILE_TAG, junction.root[6][3].tag)
        self.assertEqual(config.LATERAL_PROFILE_TAG, junction.root[6][4].tag)
        self.assertEqual(config.LANES_TAG, junction.root[6][5].tag)
        self.assertEqual(config.LANE_SECTION_TAG, junction.root[6][5][0].tag)
        self.assertEqual(str.format("{0:.16e}", 0), junction.root[6][5][0].get("s"))
        self.assertEqual(config.LANE_SECTION_CENTER_TAG, junction.root[6][5][0][0].tag)
        self.assertEqual(config.LANE_TAG, junction.root[6][5][0][0][0].tag)
        self.assertEqual("0", junction.root[6][5][0][0][0].get(config.ID_TAG))
        self.assertEqual("driving", junction.root[6][5][0][0][0].get(config.TYPE_TAG))
        self.assertEqual(config.FALSE, junction.root[6][5][0][0][0].get(config.LEVEL_TAG))
        self.assertEqual(config.LINK_TAG, junction.root[6][5][0][0][0][0].tag)
        self.assertEqual(config.ROAD_MARK_TAG, junction.root[6][5][0][0][0][1].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[6][5][0][0][0][1].get(config.LANE_SOFFSET_TAG)
        )
        self.assertEqual(config.SOLID, junction.root[6][5][0][0][0][1].get(config.TYPE_TAG))
        self.assertEqual(
            config.STANDARD, junction.root[6][5][0][0][0][1].get(config.ROAD_MARK_WEIGHT_TAG)
        )
        self.assertEqual(
            config.STANDARD, junction.root[6][5][0][0][0][1].get(config.ROAD_MARK_COLOR_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0.13),
            junction.root[6][5][0][0][0][1].get(config.SIGNAL_WIDTH_TAG),
        )
        self.assertEqual(config.LANE_SECTION_LEFT_TAG, junction.root[6][5][0][1].tag)
        self.assertEqual(config.LANE_TAG, junction.root[6][5][0][1][0].tag)
        self.assertEqual("1", junction.root[6][5][0][1][0].get(config.ID_TAG))
        self.assertEqual("driving", junction.root[6][5][0][1][0].get(config.TYPE_TAG))
        self.assertEqual(config.FALSE, junction.root[6][5][0][1][0].get(config.LEVEL_TAG))
        self.assertEqual(config.LINK_TAG, junction.root[6][5][0][1][0][0].tag)
        self.assertEqual(config.SIGNAL_WIDTH_TAG, junction.root[6][5][0][1][0][1].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[6][5][0][1][0][1].get(config.LANE_SOFFSET_TAG)
        )
        self.assertEqual(
            "2.9999999999999996e+00", junction.root[6][5][0][1][0][1].get(config.LANE_A_TAG)
        )
        self.assertEqual(
            "8.3333120123118806e-11", junction.root[6][5][0][1][0][1].get(config.LANE_B_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[6][5][0][1][0][1].get(config.LANE_C_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[6][5][0][1][0][1].get(config.LANE_D_TAG)
        )
        self.assertEqual(config.ROAD_MARK_TAG, junction.root[6][5][0][1][0][2].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[6][5][0][1][0][2].get(config.LANE_SOFFSET_TAG)
        )
        self.assertEqual(config.SOLID, junction.root[6][5][0][1][0][2].get(config.TYPE_TAG))
        self.assertEqual(
            config.STANDARD, junction.root[6][5][0][1][0][2].get(config.ROAD_MARK_WEIGHT_TAG)
        )
        self.assertEqual(
            config.STANDARD, junction.root[6][5][0][1][0][2].get(config.ROAD_MARK_COLOR_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0.13),
            junction.root[6][5][0][1][0][2].get(config.SIGNAL_WIDTH_TAG),
        )
        self.assertEqual(config.LANE_SECTION_RIGHT_TAG, junction.root[6][5][0][2].tag)
        self.assertEqual(config.LANE_TAG, junction.root[6][5][0][2][0].tag)
        self.assertEqual("-1", junction.root[6][5][0][2][0].get(config.ID_TAG))
        self.assertEqual("driving", junction.root[6][5][0][2][0].get(config.TYPE_TAG))
        self.assertEqual(config.FALSE, junction.root[6][5][0][2][0].get(config.LEVEL_TAG))
        self.assertEqual(config.LINK_TAG, junction.root[6][5][0][2][0][0].tag)
        self.assertEqual(config.SIGNAL_WIDTH_TAG, junction.root[6][5][0][2][0][1].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[6][5][0][2][0][1].get(config.LANE_SOFFSET_TAG)
        )
        self.assertEqual(
            "2.9999999999999996e+00", junction.root[6][5][0][2][0][1].get(config.LANE_A_TAG)
        )
        self.assertEqual(
            "-1.5700846082607336e-17", junction.root[6][5][0][2][0][1].get(config.LANE_B_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[6][5][0][2][0][1].get(config.LANE_C_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[6][5][0][2][0][1].get(config.LANE_D_TAG)
        )
        self.assertEqual(config.ROAD_MARK_TAG, junction.root[6][5][0][2][0][2].tag)
        self.assertEqual(
            str.format("{0:.16e}", 0), junction.root[6][5][0][2][0][2].get(config.LANE_SOFFSET_TAG)
        )
        self.assertEqual(config.SOLID, junction.root[6][5][0][2][0][2].get(config.TYPE_TAG))
        self.assertEqual(
            config.STANDARD, junction.root[6][5][0][2][0][2].get(config.ROAD_MARK_WEIGHT_TAG)
        )
        self.assertEqual(
            config.STANDARD, junction.root[6][5][0][2][0][2].get(config.ROAD_MARK_COLOR_TAG)
        )
        self.assertEqual(
            str.format("{0:.16e}", 0.13),
            junction.root[6][5][0][1][0][2].get(config.SIGNAL_WIDTH_TAG),
        )
        self.assertEqual(config.OBJECTS_TAG, junction.root[6][6].tag)
        self.assertEqual(config.SIGNALS_TAG, junction.root[6][7].tag)

    def checkJunctionJunction(self, junction):
        self.assertEqual(config.JUNCTION_CONNECTION_TAG, junction.junction[0].tag)
        self.assertEqual("1", junction.junction[0].get(config.ID_TAG))
        self.assertEqual("21", junction.junction[0].get(config.JUNCTION_INCOMING_ROAD_TAG))
        self.assertEqual("25", junction.junction[0].get(config.JUNCTION_CONNECTING_ROAD_TAG))
        self.assertEqual(config.START_TAG, junction.junction[0].get(config.CONTACT_POINT_TAG))
        self.assertEqual(config.JUNCTION_LANE_LINK_TAG, junction.junction[0][0].tag)
        self.assertEqual("-1", junction.junction[0][0].get(config.JUNCTION_FROM_TAG))
        self.assertEqual("-1", junction.junction[0][0].get(config.JUNCTION_TO_TAG))
        self.assertEqual(config.JUNCTION_CONNECTION_TAG, junction.junction[1].tag)
        self.assertEqual("2", junction.junction[1].get(config.ID_TAG))
        self.assertEqual("21", junction.junction[1].get(config.JUNCTION_INCOMING_ROAD_TAG))
        self.assertEqual("22", junction.junction[1].get(config.JUNCTION_CONNECTING_ROAD_TAG))
        self.assertEqual(config.START_TAG, junction.junction[1].get(config.CONTACT_POINT_TAG))
        self.assertEqual(config.JUNCTION_LANE_LINK_TAG, junction.junction[1][0].tag)
        self.assertEqual("-1", junction.junction[1][0].get(config.JUNCTION_FROM_TAG))
        self.assertEqual("1", junction.junction[1][0].get(config.JUNCTION_TO_TAG))
        self.assertEqual(config.JUNCTION_CONNECTION_TAG, junction.junction[2].tag)
        self.assertEqual("3", junction.junction[2].get(config.ID_TAG))
        self.assertEqual("26", junction.junction[2].get(config.JUNCTION_INCOMING_ROAD_TAG))
        self.assertEqual("24", junction.junction[2].get(config.JUNCTION_CONNECTING_ROAD_TAG))
        self.assertEqual(config.START_TAG, junction.junction[2].get(config.CONTACT_POINT_TAG))
        self.assertEqual(config.JUNCTION_LANE_LINK_TAG, junction.junction[2][0].tag)
        self.assertEqual("1", junction.junction[2][0].get(config.JUNCTION_FROM_TAG))
        self.assertEqual("1", junction.junction[2][0].get(config.JUNCTION_TO_TAG))
        self.assertEqual(config.JUNCTION_CONNECTION_TAG, junction.junction[3].tag)
        self.assertEqual("4", junction.junction[3].get(config.ID_TAG))
        self.assertEqual("26", junction.junction[3].get(config.JUNCTION_INCOMING_ROAD_TAG))
        self.assertEqual("25", junction.junction[3].get(config.JUNCTION_CONNECTING_ROAD_TAG))
        self.assertEqual(config.START_TAG, junction.junction[3].get(config.CONTACT_POINT_TAG))
        self.assertEqual(config.JUNCTION_LANE_LINK_TAG, junction.junction[3][0].tag)
        self.assertEqual("1", junction.junction[3][0].get(config.JUNCTION_FROM_TAG))
        self.assertEqual("1", junction.junction[3][0].get(config.JUNCTION_TO_TAG))
        self.assertEqual(config.JUNCTION_CONNECTION_TAG, junction.junction[4].tag)
        self.assertEqual("5", junction.junction[4].get(config.ID_TAG))
        self.assertEqual("23", junction.junction[4].get(config.JUNCTION_INCOMING_ROAD_TAG))
        self.assertEqual("24", junction.junction[4].get(config.JUNCTION_CONNECTING_ROAD_TAG))
        self.assertEqual(config.START_TAG, junction.junction[4].get(config.CONTACT_POINT_TAG))
        self.assertEqual(config.JUNCTION_LANE_LINK_TAG, junction.junction[4][0].tag)
        self.assertEqual("1", junction.junction[4][0].get(config.JUNCTION_FROM_TAG))
        self.assertEqual("-1", junction.junction[4][0].get(config.JUNCTION_TO_TAG))
        self.assertEqual(config.JUNCTION_CONNECTION_TAG, junction.junction[5].tag)
        self.assertEqual("6", junction.junction[5].get(config.ID_TAG))
        self.assertEqual("23", junction.junction[5].get(config.JUNCTION_INCOMING_ROAD_TAG))
        self.assertEqual("22", junction.junction[5].get(config.JUNCTION_CONNECTING_ROAD_TAG))
        self.assertEqual(config.START_TAG, junction.junction[5].get(config.CONTACT_POINT_TAG))
        self.assertEqual(config.JUNCTION_LANE_LINK_TAG, junction.junction[5][0].tag)
        self.assertEqual("1", junction.junction[5][0].get(config.JUNCTION_FROM_TAG))
        self.assertEqual("-1", junction.junction[5][0].get(config.JUNCTION_TO_TAG))
