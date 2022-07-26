import unittest
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadSignal import *


class TestRoadSignal(unittest.TestCase):
    def test_initialize_signal(self):
        s = "5.3798617751e+01"
        t = "4.3219"
        s_id = "5001573"
        name = "Test Signal"
        s_type = "274"
        s_subtype = "100"
        country = "DE"
        value = "100"
        unit = "km/h"
        text = "example"

        signal = Signal()
        signal.s = s
        self.assertEqual(float(s), signal.s)
        signal.t = t
        self.assertEqual(float(t), signal.t)
        signal.id = s_id
        self.assertEqual(int(s_id), signal.id)
        signal.name = name
        self.assertEqual(name, signal.name)
        for dynamic in ["yes", "no"]:
            signal.dynamic = dynamic
            self.assertEqual(dynamic, signal.dynamic)
        with self.assertRaises(AttributeError):
            signal.dynamic = None
            signal.dynamic = 4
            signal.dynamic = "test"
        for orientation in ["+", "-", "none"]:
            signal.orientation = orientation
            self.assertEqual(orientation, signal.orientation)
        with self.assertRaises(AttributeError):
            signal.orientation = None
            signal.orientation = 2
            signal.orientation = "test"
        signal.country = country
        self.assertEqual(country, signal.country)
        signal.signal_value = value
        self.assertEqual(float(value), signal.signal_value)
        signal.unit = unit
        self.assertEqual(unit, signal.unit)
        signal.text = text
        self.assertEqual(text, signal.text)
        signal.type = s_type
        self.assertEqual(s_type, signal.type)
        signal.subtype = s_subtype
        self.assertEqual(s_subtype, signal.subtype)

    def test_initialize_signal_reference(self):
        s = "5.3798617751e+01"
        t = "4.3219"
        s_id = "5001573"

        signal_reference = SignalReference()
        signal_reference.s = s
        self.assertEqual(float(s), signal_reference.s)
        signal_reference.t = t
        self.assertEqual(float(t), signal_reference.t)
        signal_reference.id = s_id
        self.assertEqual(int(s_id), signal_reference.id)
        for orientation in ["+", "-", "none"]:
            signal_reference.orientation = orientation
            self.assertEqual(orientation, signal_reference.orientation)
        with self.assertRaises(AttributeError):
            signal_reference.orientation = None
            signal_reference.orientation = 2
            signal_reference.orientation = "test"


if __name__ == '__main__':
    unittest.main()
