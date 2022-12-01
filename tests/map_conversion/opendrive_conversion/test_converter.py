import unittest
from crdesigner.map_conversion.opendrive.opendrive_conversion.converter import OpenDriveConverter
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.road import Road
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadLanes import Lane, LaneWidth, LaneSection,\
    RoadMark
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.road_record import RoadRecord
from crdesigner.map_conversion.opendrive.opendrive_conversion.plane_elements.border import Border


class TestConverter(unittest.TestCase):
    def test_create_reference_border(self):
        # create road with lanesection and lane
        road = Road()
        road.planView.add_line([0, 0], 1.0, 100)

        # test border with no laneOffsets
        # create ground truth
        true_border = Border()
        true_border.width_coefficient_offsets.append(0.0)
        true_border.width_coefficients.append([0.0])

        self.width_coefficient_offsets = []
        self.width_coefficients = []
        border = OpenDriveConverter.create_reference_border(road.planView, road.lanes.laneOffsets)

        self.assertListEqual(true_border.width_coefficients, border.width_coefficients)
        self.assertListEqual(true_border.width_coefficient_offsets, border.width_coefficient_offsets)

        # test with unequal coefficients and offsets, this should fail
        true_border.width_coefficient_offsets.append(20)
        true_border.width_coefficients.append([5.0, 0, 0, 0])
        self.assertRaises(AssertionError, self.assertListEqual, true_border.width_coefficients,
                          border.width_coefficients)
        self.assertRaises(AssertionError, self.assertListEqual, true_border.width_coefficient_offsets,
                          border.width_coefficient_offsets)

        # test with two lane offsets with same start pos --> only last LaneOffset matters
        lane_offset1 = RoadRecord(*[0.0, 4.851, -0.239, 0.145], start_pos=0)
        road.lanes.laneOffsets.append(lane_offset1)
        lane_offset2 = RoadRecord(*[3.27, 0, 0, 0], start_pos=0)
        road.lanes.laneOffsets.append(lane_offset2)
        border = OpenDriveConverter.create_reference_border(road.planView, road.lanes.laneOffsets)

        true_border.width_coefficients.clear()
        true_border.width_coefficient_offsets.clear()

        true_border.width_coefficients.append([3.27, 0, 0, 0])
        true_border.width_coefficient_offsets.append(0.0)

        self.assertListEqual(true_border.width_coefficients, border.width_coefficients)
        self.assertListEqual(true_border.width_coefficient_offsets, border.width_coefficient_offsets)

        # test with two offsets with different start pos
        road.lanes.laneOffsets.clear()
        lane_offset1 = RoadRecord(*[0.0, 4.123, -0.15, 0.12], start_pos=0.0)
        lane_offset2 = RoadRecord(*[1.25, 0.0, -0.15, 0.1], start_pos=10.0)
        road.lanes.laneOffsets.append(lane_offset1)
        road.lanes.laneOffsets.append(lane_offset2)

        true_border.width_coefficients.clear()
        true_border.width_coefficient_offsets.clear()

        true_border.width_coefficients = [[0.0, 4.123, -0.15, 0.12], [1.25, 0.0, -0.15, 0.1]]
        true_border.width_coefficient_offsets = [0.0, 10]

        border = OpenDriveConverter.create_reference_border(road.planView, road.lanes.laneOffsets)

        self.assertListEqual(true_border.width_coefficients, border.width_coefficients)
        self.assertListEqual(true_border.width_coefficient_offsets, border.width_coefficient_offsets)

    def test_lane_section_to_parametric_lanes(self):
        road = Road()
        road.planView.add_line([0.0, 0.0], 0, 100)
        road.id = 100

        section = LaneSection(road)
        section.idx = 0
        section.sPos = 0.0

        common_lane_width = LaneWidth(*[5.0, 0.0, 0.0, 0.0], idx=0, start_offset=0)
        common_lane_width.length = 100
        right_lane1 = Lane(road, section)
        right_lane1.speed = 30
        right_lane1.id = -1
        right_lane1.widths.append(common_lane_width)
        right_lane2 = Lane(road, section)
        right_lane2.id = -2
        right_lane2.widths.append(common_lane_width)

        center_lane = Lane(road, section)
        center_lane.id = 0
        center_lane.speed = 30


        left_lane1 = Lane(road, section)
        left_lane1.id = 1
        left_lane1.speed = 30
        left_lane1.widths.append(common_lane_width)
        left_lane2 = Lane(road, section)
        left_lane2.id = 2
        left_lane2.widths.append(common_lane_width)
        left_lane3 = Lane(road, section)
        left_lane3.id = 3
        left_lane3.widths.append(common_lane_width)

        section.leftLanes.append(left_lane1)
        section.leftLanes.append(left_lane2)
        section.leftLanes.append(left_lane3)
        section.centerLanes.append(center_lane)
        section.rightLanes.append(right_lane1)
        section.rightLanes.append(right_lane2)

        reference_border = Border()
        reference_border.ref_offset = 0.0
        reference_border.width_coefficient_offsets.append(0.0)
        reference_border.width_coefficients.append([0.0])
        plane_groups = OpenDriveConverter.lane_section_to_parametric_lanes(section, reference_border)

        mark1 = RoadMark()
        mark1.SOffset = 0.0
        mark2 = RoadMark()
        mark2.SOffset = 3.0
        mark3 = RoadMark()
        mark3.SOffset = 5.4
        section.leftLanes[0].road_mark = [mark1, mark2, mark3]
        plane_groups_mark = OpenDriveConverter.lane_section_to_parametric_lanes(section, reference_border)

        # check if correct number of plane_groups is returned
        # check if correct neighbour ids are generated (this is somewhat redundant because of the other tests)
        self.assertEqual(5, len(plane_groups))
        self.assertEqual("100.0.-1.-1", plane_groups[0].id_)
        self.assertEqual("100.0.1.-1", plane_groups[0].inner_neighbour)
        self.assertEqual("100.0.-2.-1", plane_groups[0].outer_neighbour)
        self.assertEqual(100, plane_groups[0].length)
        self.assertEqual(1, len(plane_groups[0].parametric_lanes))
        # check if lane section with no lanes returns empty list
        lane_section_empty = LaneSection(road)
        self.assertListEqual([], OpenDriveConverter.lane_section_to_parametric_lanes(lane_section_empty,
                                                                                     reference_border))

        self.assertEquals(5.4, plane_groups_mark[2].parametric_lanes[0].line_marking.SOffset)

    def test_create_parametric_lane(self):
        road = Road()
        road.id = "100"

        section = LaneSection(road)
        section.idx = 0
        lane = Lane(road, section)
        lane.id = "-1"
        lane.type = "restricted"
        lane.speed = 40

        width = LaneWidth(*[1.0, 0.0, 0.0, 0.0], idx=0, start_offset=0.0)
        lane.widths.append(width)
        mark_idx = 0

        side = "right"
        lane_borders = []

        lane_border1 = Border(0.0)
        lane_border1.reference = road.planView
        lane_border1.width_coefficient_offsets.append(0.0)
        lane_border1.width_coefficients.append([0.0])
        lane_borders.append(lane_border1)

        lane_border2 = Border(0.0)
        lane_border2.reference = road.planView
        lane_border2.width_coefficient_offsets.append(0.0)
        lane_border2.width_coefficients.append([-1.0, 0.0, 0.0, 0.0])
        lane_borders.append(lane_border2)

        parametric_lane = OpenDriveConverter.create_parametric_lane(lane_borders, width, lane, side, mark_idx)

        # test offsets
        true_inner_border_offset = lane.widths[0].start_offset + lane_borders[-1].ref_offset
        true_outer_border_offset = lane.widths[0].start_offset
        self.assertAlmostEqual(true_inner_border_offset, parametric_lane.border_group.inner_border_offset)
        self.assertAlmostEqual(true_outer_border_offset, parametric_lane.border_group.outer_border_offset)
        # test border coefficients
        self.assertListEqual(lane_border1.width_coefficients,
                             parametric_lane.border_group.inner_border.width_coefficients)
        self.assertListEqual(lane_border2.width_coefficients,
                             parametric_lane.border_group.outer_border.width_coefficients)
        # test properties of lane and lane group
        self.assertEquals("100.0.-1.0.0", parametric_lane.id_)
        self.assertEquals(lane.type, parametric_lane.type_)
        self.assertEquals(side, parametric_lane.side)
        self.assertEquals(40, parametric_lane.speed)

    def test_create_outer_lane_border(self):
        road = Road()
        road.planView.add_line([0, 0], 1.0, 100)
        lane_section = LaneSection(road)
        lane_section.sPos = 10

        lane = Lane(road, lane_section)
        lane_width = LaneWidth(*[5.0, 0, 0, 0], idx=0, start_offset=0)
        lane.widths = list([lane_width])
        lane_section.rightLanes.append(lane)

        # test with empty lane_borders: this should fail
        lane_borders = []
        coeff_factor = 1
        self.assertRaises(IndexError, OpenDriveConverter._create_outer_lane_border, lane_borders, lane, coeff_factor)

        # test with a given lane border and a lane width one width
        lane_border1 = Border(0.0)
        lane_border1.reference = road.planView
        lane_border1.width_coefficient_offsets = [0.0, 3.78]
        lane_border1.width_coefficients.append([2.682, 0.103, -0.01, 1.075])
        lane_border1.width_coefficients.append([2.88, 0.0, -0.08, 0.0162])
        lane_borders.append(lane_border1)

        border = OpenDriveConverter._create_outer_lane_border(lane_borders, lane, coeff_factor)
        true_border = Border()
        true_border.ref_offset = 10
        true_border.width_coefficient_offsets = [0.0]
        true_border.width_coefficients = [[5.0, 0, 0, 0]]
        self.assertEqual(true_border.ref_offset, border.ref_offset)
        self.assertListEqual(true_border.width_coefficient_offsets, border.width_coefficient_offsets)
        self.assertListEqual(true_border.width_coefficients, border.width_coefficients)

        # test with two lanewidth objects and coeff_factor of -1
        lane_width2 = LaneWidth(*[3.27, 0, 0.12, 0.05], idx=1, start_offset=10)
        lane.widths.append(lane_width2)
        coeff_factor = -1
        border = OpenDriveConverter._create_outer_lane_border(lane_borders, lane, coeff_factor)

        true_border = Border()
        true_border.width_coefficient_offsets = [0.0, 10.0]
        true_border.width_coefficients = [[-5.0, 0, 0, 0], [-3.27, 0, -0.12, -0.05]]
        true_border.ref_offset = 10
        self.assertEqual(true_border.ref_offset, border.ref_offset)
        self.assertListEqual(true_border.width_coefficient_offsets, border.width_coefficient_offsets)
        self.assertListEqual(true_border.width_coefficients, border.width_coefficients)

    def test_determine_neighbors(self):
        road = Road()
        road.planView.add_poly3([0, 0], 1.0, 100, 3.27, 0, 0.2, 0.01)
        road.id = 100
        lane_section = LaneSection(road)
        lane_section.sPos = 10
        lane_section.idx = 0

        lane0 = Lane(road, lane_section)
        lane0.id = 0
        lane_section.centerLanes.append(lane0)

        lane1 = Lane(road, lane_section)
        lane1.id = -1
        lane_width = LaneWidth(*[5.0, 0, 0, 0], idx=0, start_offset=0)
        lane1.widths = list([lane_width])
        lane_section.rightLanes.append(lane1)

        lane2 = Lane(road, lane_section)
        lane2.id = -2
        lane2.widths = list([lane_width])
        lane_section.rightLanes.append(lane2)

        lane3 = Lane(road, lane_section)
        lane3.id = 1
        lane3.widths = list([lane_width])
        lane_section.leftLanes.append(lane3)

        lane4 = Lane(road, lane_section)
        lane4.id = 2
        lane4.widths = list([lane_width])
        lane_section.leftLanes.append(lane4)

        inner_neighbour_id, outer_neighbour_id, inner_neighbour_same_dir = \
            OpenDriveConverter.determine_neighbours(lane0)
        # not sure about this:
        true_inner = "100.0.1.-1"
        true_outer = "100.0.-2.-1"
        self.assertEqual(true_inner, inner_neighbour_id)
        self.assertEqual(true_outer, outer_neighbour_id)
        self.assertEqual(inner_neighbour_same_dir, False)

        inner_neighbour_id, outer_neighbour_id, inner_neighbour_same_dir = \
            OpenDriveConverter.determine_neighbours(lane1)
        true_inner = "100.0.1.-1"
        true_outer = "100.0.-2.-1"
        self.assertEqual(true_inner, inner_neighbour_id)
        self.assertEqual(true_outer, outer_neighbour_id)
        self.assertEqual(inner_neighbour_same_dir, False)

        inner_neighbour_id, outer_neighbour_id, inner_neighbour_same_dir = \
            OpenDriveConverter.determine_neighbours(lane2)
        true_inner = "100.0.-1.-1"
        true_outer = "100.0.-3.-1"
        self.assertEqual(true_inner, inner_neighbour_id)
        self.assertEqual(true_outer, outer_neighbour_id)
        self.assertEqual(inner_neighbour_same_dir, True)

        inner_neighbour_id, outer_neighbour_id, inner_neighbour_same_dir = \
            OpenDriveConverter.determine_neighbours(lane3)
        true_inner = "100.0.-1.-1"
        true_outer = "100.0.2.-1"
        self.assertEqual(true_inner, inner_neighbour_id)
        self.assertEqual(true_outer, outer_neighbour_id)
        self.assertEqual(inner_neighbour_same_dir, False)

        inner_neighbour_id, outer_neighbour_id, inner_neighbour_same_dir = \
            OpenDriveConverter.determine_neighbours(lane4)
        true_inner = "100.0.1.-1"
        true_outer = "100.0.3.-1"
        self.assertEqual(true_inner, inner_neighbour_id)
        self.assertEqual(true_outer, outer_neighbour_id)
        self.assertEqual(inner_neighbour_same_dir, True)









