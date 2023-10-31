import unittest
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadSignal import Signal
from crdesigner.map_conversion.opendrive.opendrive_conversion.plane_elements.traffic_signals import *
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadLanes import *
from commonroad.scenario.traffic_sign import TrafficSignIDGermany


class TestTrafficSignals(unittest.TestCase):
    def setUp(self):
        self.signals = []
        # stop line
        s1 = Signal()
        s1.s = 5
        s1.t = 1
        s1.id = 1
        s1.name = "Signal 1"
        s1.dynamic = "no"
        s1.orientation = "+"
        s1.type = "294"
        s1.country = "DEU"
        s1.value = "-1"
        self.signals.append(s1)

        # faulty signal
        s2 = Signal()
        s2.s = 10
        s2.t = 2
        s2.id = 2
        s2.orientation = "-"
        s2.name = "Signal 2"
        self.signals.append(s2)

        # traffic light
        s3 = Signal()
        s3.s = 15
        s3.t = 2
        s3.id = 3
        s3.orientation = "+"
        s3.name = "Signal 3"
        s3.dynamic = "yes"
        self.signals.append(s3)

        # traffic sign
        s4 = Signal()
        s4.s = 20
        s4.t = 2
        s4.orientation = "-"
        s4.dynamic = "no"
        s4.type = "114"
        s4.country = "ZAM"
        self.signals.append(s4)

        self.roadStraightLine = Road()
        self.roadStraightLine.id = 1
        self.roadStraightLine._length = 50
        self.roadStraightLine.planView.add_line([0, 0], 0.785398, 100)

        self.roadStraightLine.addSignal(s1)
        self.roadStraightLine.addSignal(s2)
        self.roadStraightLine.addSignal(s3)
        self.roadStraightLine.addSignal(s4)

        self.roadMultipleLaneSections = Road()
        self.roadMultipleLaneSections.id = 2
        self.roadMultipleLaneSections._length = 100
        self.roadMultipleLaneSections.planView.add_line([0, 0], 0.523599, 100)
        self.roadMultipleLaneSections.addSignal(s1)
        self.roadMultipleLaneSections.addSignal(s2)
        self.roadMultipleLaneSections.addSignal(s3)
        self.roadMultipleLaneSections.addSignal(s4)

    def test_extract_traffic_element_id(self):
        # test with signal_type and signal_subtype
        element_id = extract_traffic_element_id("103", "10", TrafficSignIDGermany)
        self.assertEqual(element_id, TrafficSignIDGermany.WARNING_LEFT_CURVE)
        # test with signal_type only
        element_id = extract_traffic_element_id("101", "", TrafficSignIDGermany)
        self.assertEqual(element_id, TrafficSignIDGermany.WARNING_DANGER_SPOT)
        # test a traffic sign ID that is solely identified by signal_type with an incorrect data type for
        # signal_subtype
        # noinspection PyTypeChecker
        element_id = extract_traffic_element_id("101", 5, TrafficSignIDGermany)
        self.assertEqual(element_id, TrafficSignIDGermany.WARNING_DANGER_SPOT)
        # test a traffic sign ID that is described by both signal_type and signal_subtype with incorrect data types
        self.assertRaises(TypeError, extract_traffic_element_id, "103", 10, TrafficSignIDGermany)
        self.assertRaises(TypeError, extract_traffic_element_id, 103, 10, TrafficSignIDGermany)
        # test default case when ID does not exist
        element_id = extract_traffic_element_id("00000", "00000", TrafficSignIDGermany)
        self.assertEqual(element_id, TrafficSignIDGermany.UNKNOWN)

    def test_get_traffic_signals(self):
        generate_unique_id(0)
        # true stop line
        line = StopLine(np.array([2.828427818, 4.242640225]), np.array([2.828427818, 4.242640225]), LineMarking.SOLID)
        # true traffic light
        position = np.array([15 * np.cos(0.785398) + (2 * np.cos(0.785398 + np.pi / 2)),
                             15 * np.sin(0.785398) + (2 * np.sin(0.785398 + np.pi / 2))])
        traffic_light = TrafficLight(1, position=position, traffic_light_cycle=get_default_cycle())
        # true traffic sign
        position = np.array([20 * np.cos(0.785398) + (2 * np.cos(0.785398 + np.pi / 2)),
                             20 * np.sin(0.785398) + (2 * np.sin(0.785398 + np.pi / 2))])
        element = TrafficSignElement(TrafficSignIDZamunda.WARNING_SLIPPERY_ROAD, [])
        # noinspection PyTypeChecker
        sign = TrafficSign(1, list([element]), None, position, virtual=False)
        # get the traffic lights, signs and stop lines from the road
        traffic_lights, traffic_signs, stop_lines = get_traffic_signals(self.roadStraightLine)
        # check if the extracted traffic elements are equal to the true objects
        self.assertTrue(stop_lines[0].__eq__(line))
        self.assertTrue(traffic_lights[0].__eq__(traffic_light))
        # traffic signs always get a unique ID, so we copy it to the ground truth
        sign.traffic_sign_id = traffic_signs[0].traffic_sign_id
        self.assertTrue(traffic_signs[0].__eq__(sign))

    def test_calculate_stop_line_position(self):
        road = Road()
        road.id = 1
        road.junction = None
        road._length = 50
        road.planView.add_line(0, 6.5, 100)

        signal = Signal()
        signal.country = "DEU"
        signal.type = "294"
        signal.s = 5
        signal.t = 2.5
        pos_calc, tangent, _, _ = road.planView.calc(signal.s, compute_curvature=False)
        position = np.array([pos_calc[0] + signal.t * np.cos(tangent + np.pi / 2),
                             pos_calc[1] + signal.t * np.sin(tangent + np.pi / 2)])
        position_1, position_2 = calculate_stop_line_position(road.lanes.lane_sections, signal, position, tangent)

        true_pos_2 = np.array(
                [position[0] - 0 * np.cos(tangent + np.pi / 2), position[1] - 0 * np.sin(tangent + np.pi) / 2])
        true_pos_1 = position
        self.assertIsNone(np.testing.assert_almost_equal(true_pos_1, position_1))
        self.assertIsNone(np.testing.assert_almost_equal(true_pos_2, position_2))

    def test_calculate_stop_line_positions2(self):
        lane_section1 = LaneSection(self.roadMultipleLaneSections)
        lane_section1.idx = 0
        lane_section1.sPos = 0
        lane_section1.singleSide = "false"
        lane1 = Lane(self.roadMultipleLaneSections, lane_section1)
        lane1.id = 1
        lane1.type = "driving"
        lane_width1 = LaneWidth(*[5.0, 0, 0, 0], 0, 0)
        lane1.widths = list([lane_width1])
        lane_section1.centerLanes.append(lane1)

        lane_section2 = LaneSection(self.roadMultipleLaneSections)
        lane_section2.idx = 1
        lane_section2.sPos = 0
        lane_section2.singleSide = "false"
        lane2 = Lane(self.roadMultipleLaneSections, lane_section2)
        lane2.id = 2
        lane2.type = "driving"
        lane_width2 = LaneWidth(*[0, 0, 0.09822, -0.0051843], idx=None, start_offset=0)
        lane_width3 = LaneWidth(*[5.22, 0, 0, 0], idx=None, start_offset=1.263)
        lane2.widths = list([lane_width2, lane_width3])
        lane_section2.centerLanes.append(lane2)

        self.roadMultipleLaneSections.lanes.lane_sections.append(lane_section1)
        self.roadMultipleLaneSections.lanes.lane_sections.append(lane_section2)

        # construct ground truth / expected value
        pos_at_s, tangent, _, _ = self.roadMultipleLaneSections.planView.calc(self.signals[0].s, False, False)
        true_first_pos = np.array([pos_at_s[0] + self.signals[0].t * np.cos(tangent + np.pi / 2),
                                   pos_at_s[1] + self.signals[0].t * np.sin(tangent + np.pi / 2)])
        total_width = 5.0 + 0.09822 * self.signals[0].s ** 2 - 0.0051843 * self.signals[0].s ** 3 + 5.22
        true_second_pos = np.array([true_first_pos[0] - total_width * np.cos(tangent + np.pi / 2),
                                    true_first_pos[1] - total_width * np.sin(tangent + np.pi / 2)])

        # get actual value
        first_pos, second_pos = calculate_stop_line_position(self.roadMultipleLaneSections.lanes.lane_sections,
                                                             self.signals[0], true_first_pos, tangent)

        np.testing.assert_almost_equal(true_first_pos, first_pos)
        np.testing.assert_almost_equal(true_second_pos, second_pos)


if __name__ == '__main__':
    unittest.main()
