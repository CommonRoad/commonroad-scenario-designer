import unittest
from crdesigner.map_conversion.opendrive.opendrive_conversion.plane_elements.geo_reference import get_geo_reference


class TestGeoReference(unittest.TestCase):
    def test_get_geo_reference(self):
        test1 = "+proj=tmerc +a=6378137 +b=6378137 +lon_0=8.4256947318197106 +x_0=-0 +y_0=-5453802.4935722183 +k=1.0 "\
                 "+units=m +nadgrids=@null +wktext +no_defs"
        long, lat = get_geo_reference(test1)
        self.assertAlmostEqual(8.4256947318197106, long)
        self.assertEqual(None, lat)

        test2 = "+proj=lcc +lat_1=48.66666666666666 +lat_2=53.66666666666666 +lat_0=51 +lon_0=10.5 +x_0=0 +y_0=0 "\
                "+ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs"
        long, lat = get_geo_reference(test2)
        self.assertAlmostEqual(51, lat)
        self.assertAlmostEqual(10.5, long)

        test3 = "+proj=lcc +lat_1=48.66666666666666 +lat_2=53.66666666666666 +x_0=0 +y_0=0 " \
                "+ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs"
        long, lat = get_geo_reference(test3)
        self.assertEqual(None, long)
        self.assertEqual(None, lat)

        test4 = 100
        self.assertRaises(TypeError, get_geo_reference, test4)

        test5 = ""
        lat, long = get_geo_reference(test5)
        self.assertEqual(None, lat)
        self.assertEqual(None, long)


if __name__ == '__main__':
    unittest.main()
