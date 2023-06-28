import unittest
from crdesigner.map_conversion.opendrive.opendrive_conversion.converter import OpenDriveConverter
from crdesigner.map_conversion.opendrive.opendrive_conversion.plane_elements.border import Border
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.road import Road
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadLanes import LaneWidth, Lane, LaneSection


# parameter guessed
MAX_DIST = 20


class TestSamplingForSpirals(unittest.TestCase):

    def test_sampling_for_spirals(self):
        """
        test the sampling as it fails for some scenarios containing spirals
        """
        road = Road()
        road.planView.add_spiral([650, 175], 1.7, 200, 0.007, 0)
        road.id = 1

        section = LaneSection(road)
        section.idx = 0
        section.sPos = 0.0

        lane = Lane(road, section)
        lane.id = 1
        lane_width = LaneWidth(*[4.0, 0.0, 0.0, 0.0], idx=0, start_offset=0)
        lane_width.length = 200
        lane.widths.append(lane_width)

        section.leftLanes.append(lane)

        reference_border = Border()
        reference_border.ref_offset = 0.0
        reference_border.width_coefficient_offsets.append(0.0)
        reference_border.width_coefficients.append([0.0])
        reference_border = OpenDriveConverter.create_reference_border(road.planView, road.lanes.laneOffsets)

        plane_groups = OpenDriveConverter.lane_section_to_parametric_lanes(section, reference_border)

        lv, rv = plane_groups[0].parametric_lanes[0].calc_vertices(error_tolerance=0.15, min_delta_s=0.5)
        for i in range(1, len(lv)):
            self.assertLess(lv[i][0] - lv[i - 1][0], MAX_DIST)
            self.assertLess(lv[i][1] - lv[i - 1][1], MAX_DIST)
        for i in range(1, len(rv)):
            self.assertLess(abs(rv[i][0] - rv[i - 1][0]), MAX_DIST)
            self.assertLess(abs(rv[i][1] - rv[i - 1][1]), MAX_DIST)


if __name__ == '__main__':
    unittest.main()
