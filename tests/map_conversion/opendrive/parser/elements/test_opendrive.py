import unittest
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.opendrive import *
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.road import *
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.junction import *


class TestOpenDrive(unittest.TestCase):
    def test_initialize_Header(self):
        revMajor = "1"
        revMinor = "2"
        name = "test"
        version = "1.00"
        date = "Thu Sep  2 17:18:18 2010"
        north = "0.0000000000000000e+00"
        south = "0.0000000000000000e+00"
        east = "0.0000000000000000e+00"
        west = "0.0000000000000000e+00"
        header = Header(rev_major=revMajor, rev_minor=revMinor, name=name, version=version, date=date,
                        north=north, south=south, east=east, west=west)

        self.assertEqual(revMajor, header.revMajor)
        self.assertEqual(revMinor, header.revMinor)
        self.assertEqual(name, header.name)
        self.assertEqual(version, header.version)
        self.assertEqual(date, header.date)
        self.assertEqual(north, header.north)
        self.assertEqual(south, header.south)
        self.assertEqual(east, header.east)
        self.assertEqual(west, header.west)
        self.assertEqual(None, header.vendor)
        self.assertEqual(None, header.geo_reference)

        vendor = "test"
        header1 = Header(rev_major=revMajor, rev_minor=revMinor, name=name, version=version, date=date, north=north,
                        south=south, east=east, west=west, vendor=vendor)
        self.assertEqual(vendor, header1.vendor)

    def test_initialize_openDrive(self):
        # define header element
        revMajor = "1"
        revMinor = "2"
        name = "test"
        version = "1.00"
        date = "Thu Sep  2 17:18:18 2010"
        north = "0.0000000000000000e+00"
        south = "0.0000000000000000e+00"
        east = "0.0000000000000000e+00"
        west = "0.0000000000000000e+00"
        header = Header(rev_major=revMajor, rev_minor=revMinor, name=name, version=version, date=date, north=north,
                        south=south, east=east, west=west)
        # TODO define road elements
        # TODO define controller elements -> no class/file available yet
        # define junction elements
        junction1 = Junction()
        junction2 = Junction()
        junction3 = Junction()
        junction1.id = 3244000
        junction2.id = 3245000
        junction3.id = 3247000
        # TODO define junction group elements -> no class/file available yet
        # TODO define station elements -> no class/file available yet

        opendrive = OpenDrive()
        # test header element
        opendrive.header = header
        self.assertEqual(header, opendrive.header)
        # test junction element
        opendrive._junctions = [junction1, junction3, junction2]
        self.assertEqual([junction1, junction3, junction2], opendrive.junctions)
        self.assertEqual(junction2, opendrive.getJunction(3245000))


if __name__ == '__main__':
    unittest.main()
