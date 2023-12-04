import unittest
import os
import pandas as pd
from pathlib import Path
import crdesigner
import crdesigner.map_conversion.osm2cr.converter_modules.utility.geonamesID as geonamesID
from crdesigner.map_conversion.osm2cr.converter_modules.utility.labeling_create_tree import create_tree


class TestGeonameLabeling(unittest.TestCase):
    def setUp(self) -> None:
        path = Path(crdesigner.__file__).parent.joinpath(
            "map_conversion", "osm2cr", "converter_modules", "utility", "cities500.zip")
        # Source cities500.zip: https://download.geonames.org/export/dump/
        df = pd.read_csv(path, compression='zip', sep='\t',
                         names=[
                             "geonameid ", "name", "asciiname", "alternatenames", "lat", "lng", "feature class", "feature code", "country code", "cc2", "admin1 code",
                             "admin2 code", "admin3 code", "admin4 code", "population", "elevation", "dem", "timezone", "modification date"
                         ])
        self.tree = create_tree(df)

    def test_example1_get_geonameID(self):
        correct_return = "Karlsfeld_DE_Europe-Berlin"
        self.assertEqual(correct_return, geonamesID.get_geonamesID(48.1787904, 11.5113984, self.tree))