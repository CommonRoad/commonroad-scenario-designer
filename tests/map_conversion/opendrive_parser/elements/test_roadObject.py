import unittest
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadObject import *


class TestRoadObject(unittest.TestCase):
    def test_object(self):
        r_type = 'barrier'
        name = 'random'
        width = '2.3'
        height = '1.3'
        z_offset = '2'
        r_id = '1'
        s = '4'
        t = '2'
        valid_l = '0.0'
        orientation = '+'
        hdg = '1.2'
        pitch = '3.2'
        roll = '0.2'
        r_object = Object()
        r_object.type = r_type
        r_object.name = name
        r_object.width = width
        r_object.height = height
        r_object.zOffset = z_offset
        r_object.id = r_id
        r_object.s = s
        r_object.t = t
        r_object.validLength = valid_l
        r_object.orientation = orientation
        r_object.hdg = hdg
        r_object.pitch = pitch
        r_object.roll = roll

        self.assertEqual(r_type, r_object.type)
        self.assertEqual(name, r_object.name)
        self.assertEqual(float(width), r_object.width)
        self.assertEqual(float(height), r_object.height)
        self.assertEqual(float(z_offset), r_object.zOffset)
        self.assertEqual(int(r_id), r_object.id)
        self.assertEqual(float(s), r_object.s)
        self.assertEqual(float(t), r_object.t)
        self.assertEqual(float(valid_l), r_object.validLength)
        self.assertEqual(orientation, r_object.orientation)
        self.assertEqual(float(hdg), r_object.hdg)
        self.assertEqual(float(pitch), r_object.pitch)
        self.assertEqual(float(roll), r_object.roll)
        with self.assertRaises(AttributeError):
            r_object.type = "test"
            r_object.type = 1
            r_object.type = None
            r_object.orientation = "test"
            r_object.orientation = 3
            r_object.orientation = None


if __name__ == '__main__':
    unittest.main()
