import unittest

from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.junction import (
    LaneLink,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadLanes import (
    Lane,
    LaneBorder,
    LaneOffset,
    Lanes,
    LaneSection,
    LaneWidth,
    LeftLanes,
    RightLanes,
    RoadMark,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.parser import Road


class TestRoadLanes(unittest.TestCase):
    def test_initialize_lanes(self):
        offset1 = LaneOffset(1, 2, 3, 4, start_pos=3)
        offset2 = LaneOffset(1, 2, 3, 4, start_pos=1)
        offset3 = LaneOffset(1, 3, 2, 4, start_pos=2)
        road = Road()
        lane_section1 = LaneSection(road)
        lane_section1.sPos = 5
        lane_section2 = LaneSection(road)
        lane_section2.sPos = 3
        lane_section3 = LaneSection(road)
        lane_section3.sPos = 6

        lanes = Lanes()
        lanes.lane_offsets.append(offset1)
        lanes.lane_offsets.append(offset2)
        lanes.lane_offsets.append(offset3)
        lanes.lane_sections.append(lane_section1)
        lanes.lane_sections.append(lane_section2)
        lanes.lane_sections.append(lane_section3)
        self.assertEqual([offset2, offset3, offset1], lanes.lane_offsets)
        self.assertEqual([lane_section2, lane_section1, lane_section3], lanes.lane_sections)

    def test_get_lane_section(self):
        road = Road()
        lane_section1 = LaneSection(road)
        lane_section1.sPos = 5
        lane_section1.idx = 1
        lane_section2 = LaneSection(road)
        lane_section2.sPos = 3
        lane_section2.idx = 0
        lane_section3 = LaneSection(road)
        lane_section3.sPos = 6
        lane_section3.idx = 2

        lanes = Lanes()
        lanes.lane_sections.append(lane_section1)
        lanes.lane_sections.append(lane_section2)
        lanes.lane_sections.append(lane_section3)
        self.assertEqual(lane_section2, lanes.get_lane_section(0))

    def test_get_last_lane_section_idx(self):
        road = Road()
        lane_section1 = LaneSection(road)
        lane_section1.sPos = 5
        lane_section2 = LaneSection(road)
        lane_section2.sPos = 3
        lane_section3 = LaneSection(road)
        lane_section3.sPos = 6

        lanes = Lanes()
        lanes.lane_sections.append(lane_section1)
        lanes.lane_sections.append(lane_section2)
        lanes.lane_sections.append(lane_section3)
        self.assertEqual(2, lanes.get_last_lane_section_idx())

    def test_initialize_lane_offset(self):
        a, b, c, d = 2.0, 3.0, 5.0, 1.0
        start_pos = 0

        offset = LaneOffset(a, b, c, d, start_pos=start_pos)

        self.assertEqual(offset.start_pos, start_pos)
        self.assertEqual([a, b, c, d], offset.polynomial_coefficients)

    def test_initialize_left_lanes(self):
        p_road = Road()
        lane_section = LaneSection(p_road)
        lane1 = Lane(p_road, lane_section)
        lane2 = Lane(p_road, lane_section)
        lane3 = Lane(p_road, lane_section)
        lane4 = Lane(p_road, lane_section)
        lane1.id = 5
        lane2.id = 2
        lane3.id = 6
        lane4.id = 3
        l_lanes = LeftLanes()
        l_lanes.lanes.append(lane1)
        l_lanes.lanes.append(lane2)
        l_lanes.lanes.append(lane3)
        l_lanes.lanes.append(lane4)
        self.assertEqual([lane2, lane4, lane1, lane3], l_lanes.lanes)

        r_lanes = RightLanes()
        r_lanes.lanes.append(lane1)
        r_lanes.lanes.append(lane2)
        r_lanes.lanes.append(lane3)
        r_lanes.lanes.append(lane4)
        self.assertEqual([lane3, lane1, lane4, lane2], r_lanes.lanes)

    def test_initialize_lane_link(self):
        lane_link = LaneLink()
        lane_link.predecessorId = "-1"
        lane_link.successorId = "1"

        self.assertEqual(lane_link.predecessorId, "-1")
        self.assertEqual(lane_link.successorId, "1")

    def test_initialize_width(self):
        a, b, c, d = 2.0, 3.0, 5.0, 1.0
        idx = 1
        start_offset = 2.0
        lane_width = LaneWidth(a, b, c, d, idx=idx, start_offset=start_offset)
        lane_width.length = 3.4

        self.assertEqual(lane_width.polynomial_coefficients, [a, b, c, d])
        self.assertEqual(lane_width.idx, 1)
        self.assertEqual(lane_width.start_offset, 2.0)
        self.assertEqual(lane_width.length, 3.4)

    def test_initialize_lane(self):
        road = Road()
        lane_section = LaneSection(road)
        lane1 = Lane(road, lane_section)
        lane2 = Lane(road, lane_section)
        lane1.id = "4"
        types = lane1.laneTypes
        levels = ["true", "false"]
        lane1.link.successorId = "3"
        lane1.link.predecessorId = "5"
        a, b, c, d = 2.0, 3.0, 5.0, 1.0
        idx1 = 2
        start_offset1 = 4.0
        lane_width1 = LaneWidth(a, b, a, d, idx=idx1, start_offset=start_offset1)
        idx2 = 0
        start_offset2 = 0.0
        lane_width2 = LaneWidth(a, d, c, d, idx=idx2, start_offset=start_offset2)
        idx3 = 1
        start_offset3 = 2.0
        lane_width3 = LaneWidth(c, b, c, d, idx=idx3, start_offset=start_offset3)
        lane1.widths.append(lane_width1)
        lane1.widths.append(lane_width2)
        lane1.widths.append(lane_width3)
        a, b, c, d = 1.3, 2.4, 5.1, 1.0
        idx1 = 2
        start_offset1 = 4.0
        lane_border1 = LaneBorder(a, b, a, d, idx=idx1, start_offset=start_offset1)
        idx2 = 0
        start_offset2 = 0.0
        lane_border2 = LaneBorder(a, d, c, d, idx=idx2, start_offset=start_offset2)
        idx3 = 1
        start_offset3 = 2.0
        lane_border3 = LaneBorder(c, b, c, d, idx=idx3, start_offset=start_offset3)
        lane1.borders.append(lane_border1)
        lane1.borders.append(lane_border2)
        lane1.borders.append(lane_border3)
        road_mark = RoadMark()
        lane1.road_mark = road_mark

        self.assertEqual(road, lane1.parent_road)
        self.assertEqual(4, lane1.id)
        for lane_type in types:
            lane1.type = lane_type
            self.assertEqual(lane_type, lane1.type)
        with self.assertRaises(Exception):
            lane2.type = "test_wrong_type"
            lane2.type = 2
            lane2.type = None
        lane1.level = levels[0]
        self.assertEqual(True, lane1.level)
        lane1.level = levels[1]
        self.assertEqual(False, lane1.level)
        with self.assertRaises(AttributeError):
            lane2.level = "wrong_attribute"
            lane2.level = 4
            lane2.level = None
        self.assertEqual(3, lane1.link.successorId)
        self.assertEqual(5, lane1.link.predecessorId)
        self.assertEqual([lane_width2, lane_width3, lane_width1], lane1.widths)
        self.assertEqual(lane_width1, lane1.getWidth(2))
        self.assertEqual(lane_width3, lane1.getWidth(1))
        self.assertEqual(2, lane1.get_last_lane_width_idx())
        # in parser.py the setter of widths is used to assign the parameters of the borders attribute to the widths
        # attribute
        lane2.widths = lane1.borders
        self.assertEqual(lane1.borders, lane2.widths)
        self.assertEqual([lane_border2, lane_border3, lane_border1], lane1.borders)
        self.assertEqual(road_mark, lane1.road_mark)

    def test_lane_section(self):
        p_road = Road()
        lane_section = LaneSection(road=p_road)
        values = ["true", "false"]
        lane1 = Lane(p_road, lane_section)
        lane2 = Lane(p_road, lane_section)
        lane3 = Lane(p_road, lane_section)
        lane1.id = 5
        lane2.id = 4
        lane3.id = 6
        lane_section.left_lanes.append(lane1)
        lane_section.center_lanes.append(lane2)
        lane_section.right_lanes.append(lane3)
        lane_section.idx = 1
        lane_section.sPos = 1.2

        self.assertEqual(1, lane_section.idx)
        self.assertEqual(1.2, lane_section.sPos)
        lane_section.single_side = values[0]
        self.assertEqual(True, lane_section.single_side)
        lane_section.single_side = values[1]
        self.assertEqual(False, lane_section.single_side)
        lane_section.single_side = None
        self.assertEqual(False, lane_section.single_side)
        with self.assertRaises(AttributeError):
            lane_section.single_side = "wrong value"
            lane_section.single_side = 2
        self.assertEqual([lane1], lane_section.left_lanes)
        self.assertEqual([lane2], lane_section.center_lanes)
        self.assertEqual([lane3], lane_section.right_lanes)
        self.assertEqual([lane1, lane2, lane3], lane_section.all_lanes)
        self.assertEqual(lane2, lane_section.get_lane(4))
        self.assertEqual(None, lane_section.get_lane(1))
        self.assertEqual(p_road, lane_section.parent_road)

    def test_road_mark(self):
        road_mark = RoadMark()
        road_mark.SOffset = "1.32"
        road_mark.type = "solid broken"
        road_mark.weight = "bold"

        self.assertEqual(1.32, road_mark.SOffset)
        self.assertEqual("solid broken", road_mark.type)
        self.assertEqual("bold", road_mark.weight)


if __name__ == "__main__":
    unittest.main()
