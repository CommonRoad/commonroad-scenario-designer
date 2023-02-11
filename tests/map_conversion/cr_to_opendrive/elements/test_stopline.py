import unittest
import numpy as np
from lxml import etree

from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.road import Road
from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.stop_line import StopLine
from commonroad.scenario.lanelet import StopLine as Stop_line, LineMarking, LaneletNetwork
from crdesigner.ui.gui.mwindow.service_layer.map_creator import MapCreator


class TestStopLine(unittest.TestCase):
    def initialize_stop_line(self):
        # Initialize simple LaneletNetwork
        lanelet_id = 1000
        self.stop_line = Stop_line(start=np.array([0, 0]), end=np.array([0, 1]), line_marking=LineMarking.SOLID)
        self.lanelet = MapCreator.create_straight(2, 8, 9, lanelet_id, set(), stop_line=self.stop_line)

        self.network = LaneletNetwork()
        self.network.add_lanelet(self.lanelet)

        # Initialize road
        writer = etree.Element("StopLineTest")
        Road(lane_list=[self.lanelet], number_of_lanes=1, root=writer, junction_id=-1)
        road_id = Road.cr_id_to_od[self.lanelet.lanelet_id]

        # Initialize Stop Line
        data = [self.lanelet.stop_line, self.lanelet.lanelet_id]
        self.stop = StopLine(road_id, self.lanelet.lanelet_id, data, self.network)

    def test_stopline(self):
        # Test initialization is correct
        self.initialize_stop_line()
        self.assertEqual(str(self.lanelet.lanelet_id), self.stop.id)
        self.assertEqual(self.lanelet.lanelet_id, self.stop.lanelet_id)
        self.assertEqual(self.stop_line, self.stop.od_object)
        self.assertEqual(self.network, self.stop.lane_list)
        self.assertEqual(f"StopLine_{self.lanelet.lanelet_id}", self.stop.name)

        # Test orientation
        self.assertEqual('+', self.stop.get_orientation())

        # Test coordinates
        s, t = self.stop.compute_coordinate()
        self.assertAlmostEqual(0.0, s)
        self.assertAlmostEqual(1.0, t)
