import unittest
import numpy as np
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.road import *
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadtype import *
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadLink import *
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadElevationProfile import *
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadLateralProfile import *
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadLanes import *


class TestRoad(unittest.TestCase):
    def test_initialize_road(self):
        road_id = "101"
        name = "test"
        junction = Junction()
        length = "1.908739611160e+03"
        speed1 = Speed(max_speed="50", unit="km/h")
        type1 = RoadType(s_pos="1.3", use_type="motorway", speed=speed1)
        speed2 = Speed(max_speed="30", unit="km/h")
        type2 = RoadType(s_pos="8", use_type="unknown", speed=speed2)
        object1 = Object()
        object2 = Object()
        signal1 = Signal()
        signal2 = Signal()
        s_reference1 = SignalReference()
        s_reference2 = SignalReference()

        road = Road()
        road.id = road_id
        self.assertEqual(101, road.id)
        road.name = name
        self.assertEqual(name, road.name)
        road.junction = junction
        self.assertEqual(junction, road.junction)
        with self.assertRaises(TypeError):
            road.junction = "test"
            road.junction = 3
        pre = Predecessor(element_type="junction", element_id="1", contact_point="start")
        road.link.predecessor = pre
        self.assertEqual(pre, road.link.predecessor)
        road.types.append(type1)
        road.types.append(type2)
        self.assertEqual([type1, type2], road.types)
        road.planView.add_line(start_pos=np.array([0, 0]), heading=1, length=2.3)
        self.assertEqual(2.3, road.planView.length)
        elevation = ElevationRecord(2, 3, 5, 1, start_pos=0)
        road.elevationProfile.elevations.append(elevation)
        self.assertEqual([elevation], road.elevationProfile.elevations)
        super_elevation = Superelevation(2, 3, 1, 5, 4)
        road.lateralProfile.superelevations.append(super_elevation)
        self.assertEqual([super_elevation], road.lateralProfile.superelevations)
        offset = LaneOffset(1, 2, 3, 4, start_pos=3)
        road.lanes.laneOffsets.append(offset)
        self.assertEqual([offset], road.lanes.laneOffsets)
        road.addObject(object1)
        road.addObject(object2)
        self.assertEqual([object1, object2], road.objects)
        with self.assertRaises(TypeError):
            road.addObject("2")
            road.addObject(3)
        road.addSignal(signal1)
        road.addSignal(signal2)
        self.assertEqual([signal1, signal2], road.signals)
        with self.assertRaises(TypeError):
            road.addSignal("2")
            road.addSignal(3)
        road.addSignalReference(s_reference1)
        road.addSignalReference(s_reference2)
        self.assertEqual([s_reference1, s_reference2], road.signalReference)
        with self.assertRaises(TypeError):
            road.addSignalReference("2")
            road.addSignalReference(3)


if __name__ == '__main__':
    unittest.main()
