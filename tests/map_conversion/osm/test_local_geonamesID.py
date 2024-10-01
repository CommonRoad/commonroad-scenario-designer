import unittest

import crdesigner.map_conversion.osm2cr.converter_modules.utility.geonamesID as geonamesID
from crdesigner.map_conversion.osm2cr.converter_modules.utility.labeling_create_tree import (
    create_tree_from_file,
)


class TestGeonameLabeling(unittest.TestCase):
    def setUp(self) -> None:
        self.tree = create_tree_from_file()

    def test_example1_get_geoname_id(self):
        correct_return = 2892874  # "Karlsfeld_DE_Europe-Berlin"
        self.assertEqual(correct_return, geonamesID.get_geonamesID(48.1787904, 11.5113984, self.tree))
