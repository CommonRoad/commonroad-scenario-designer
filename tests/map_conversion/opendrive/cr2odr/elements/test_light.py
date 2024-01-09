import unittest

import numpy as np
from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.scenario.traffic_light import (
    TrafficLight,
    TrafficLightCycle,
    TrafficLightCycleElement,
    TrafficLightState,
)
from lxml import etree

from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.light import Light
from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.road import Road
from crdesigner.ui.gui.utilities.map_creator import MapCreator


class TestLight(unittest.TestCase):
    def initialize_light(self):
        # Initialize LaneletNetwork
        self.lanelet = MapCreator.create_straight(2, 8, 9, 1000, set())

        cycle = [(TrafficLightState.RED, 100), (TrafficLightState.GREEN, 100), (TrafficLightState.YELLOW, 100)]
        cycle_element_list = [TrafficLightCycleElement(state[0], state[1]) for state in cycle]
        self.traffic_light = TrafficLight(
            traffic_light_id=123,
            position=np.array([1.0, 0.5]),
            traffic_light_cycle=TrafficLightCycle(cycle_element_list),
        )

        self.network = LaneletNetwork()
        self.network.add_lanelet(self.lanelet)
        self.network.add_traffic_light(self.traffic_light, {self.lanelet.lanelet_id})

        # Initialize road
        writer = etree.Element("LightTest")
        Road(lane_list=[self.lanelet], number_of_lanes=1, root=writer, junction_id=-1)
        road_id = Road.cr_id_to_od[self.lanelet.lanelet_id]

        # Initialize Light
        data = [self.traffic_light, self.lanelet.lanelet_id]
        self.light = Light(road_id, self.traffic_light.traffic_light_id, data, self.network)

    def test_light(self):
        # Test initialization is correct
        self.initialize_light()
        light = self.light
        self.assertEqual(str(self.traffic_light.traffic_light_id), light.id)
        self.assertEqual(self.lanelet.lanelet_id, light.lanelet_id)
        self.assertEqual(self.traffic_light, light.od_object)
        self.assertEqual(self.network, light.lane_list)
        self.assertEqual(f"Light_{self.traffic_light.traffic_light_id}", light.name)
        self.assertEqual(("yes" if self.traffic_light.active else "no"), light.dynamic)

        # Test orientation
        self.assertEqual("+", light.get_orientation())

        # Test coordinates
        s, t = light.compute_coordinate()
        self.assertAlmostEqual(1.0, s)
        self.assertAlmostEqual(-0.5, t)
