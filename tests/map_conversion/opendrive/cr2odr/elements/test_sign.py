import unittest

import numpy as np
from commonroad.scenario.lanelet import LaneletNetwork, TrafficSign
from commonroad.scenario.traffic_sign import TrafficSignElement, TrafficSignIDGermany
from lxml import etree

from crdesigner.map_conversion.opendrive.cr2odr.elements.road import Road
from crdesigner.map_conversion.opendrive.cr2odr.elements.sign import Sign
from crdesigner.ui.gui.utilities.map_creator import MapCreator


class TestSign(unittest.TestCase):
    def initialize_sign(self):
        # Initialize LaneletNetwork
        self.lanelet = MapCreator.create_straight(2, 8, 9, 1000, set())

        sign_element = TrafficSignElement(TrafficSignIDGermany.MAX_SPEED, additional_values=["13.4112"])
        self.traffic_sign = TrafficSign(
            traffic_sign_id=11513,
            traffic_sign_elements=[sign_element],
            first_occurrence={self.lanelet.lanelet_id},
            position=np.array([0.0, 0.0]),
        )

        self.network = LaneletNetwork()
        self.network.add_lanelet(self.lanelet)
        self.network.add_traffic_sign(self.traffic_sign, {self.lanelet.lanelet_id})

        # Initialize road
        writer = etree.Element("SignTest")
        Road(lane_list=[self.lanelet], number_of_lanes=1, root=writer, junction_id=-1)
        road_id = Road.cr_id_to_od[self.lanelet.lanelet_id]

        # Initialize Sign
        data = [self.traffic_sign, self.lanelet.lanelet_id]
        self.sign = Sign(road_id, self.traffic_sign.traffic_sign_id, data, self.network)

    def test_sign(self):
        # Test initialization is correct
        self.initialize_sign()
        sign = self.sign
        self.assertEqual(str(self.traffic_sign.traffic_sign_id), sign.id)
        self.assertEqual(self.lanelet.lanelet_id, sign.lanelet_id)

        self.assertEqual(self.traffic_sign.traffic_sign_id, sign.od_object.traffic_sign_id)
        self.assertEqual(f"Sign_{self.traffic_sign.traffic_sign_id}", sign.name)
        self.assertEqual("no", sign.dynamic)
        self.assertEqual("GERMANY", sign.get_country())
        self.assertEqual(self.traffic_sign.traffic_sign_elements[0].traffic_sign_element_id.value, sign.type)
        self.assertEqual(self.traffic_sign.traffic_sign_elements[0].additional_values[0], sign.value)

        # Test orientation
        self.assertEqual("+", sign.get_orientation())

        # Test coordinates
        s, t = sign.compute_coordinate()
        self.assertAlmostEqual(0.0, s)
        self.assertAlmostEqual(1.0, t)
