from pathlib import Path
from typing import Tuple

import kdtree
import pandas as pd


class City:
    def __init__(
        self, lat: float, lng: float, geonameID: int, name: str, country: str, timezone: str
    ):
        self.lat = lat
        self.lng = lng
        self.geonameID = geonameID
        self.name = name
        self.country = country
        self.timezone = timezone

    def __getitem__(self, index):
        if index == 0:
            return self.lat
        elif index == 1:
            return self.lng

    def __len__(self):
        return 2

    def get_label(self) -> str:
        return f"{self.name}_{self.country}_{self.timezone}"

    def __str__(self) -> str:
        return self.get_label()


def create_tree(df: pd.DataFrame) -> kdtree.KDNode:
    assert "lat" in df.columns and "lng" in df.columns, "DataFrame needs 'lat' and 'lng' columns"
    city_list = df.apply(get_city_from_row, axis=1).tolist()
    return kdtree.create(city_list)


def create_tree_from_file(
    file: Path = Path(__file__).parent.joinpath("cities500.zip"),
) -> kdtree.KDNode:
    """
    Create kdtree.KDNode from cities file.

    :param file: zip files that can be downloaded from https://download.geonames.org/export/dump/;
    :return tree: kdtree.KDNode -- data structured into cities
    """
    df = pd.read_csv(
        file,
        compression="zip",
        sep="\t",
        names=[
            "geonameid",
            "name",
            "asciiname",
            "alternatenames",
            "lat",
            "lng",
            "feature class",
            "feature code",
            "country code",
            "cc2",
            "admin1 code",
            "admin2 code",
            "admin3 code",
            "admin4 code",
            "population",
            "elevation",
            "dem",
            "timezone",
            "modification date",
        ],
    )
    tree = create_tree(df)
    return tree


def get_city_from_row(row: pd.Series) -> City:
    """
    Return City object from raw data

    :param row: Raw DataFrame Row
    """
    name = str(row["asciiname"]).replace(" ", "-").replace("/", "-")
    country = str(row["country code"]).replace(" ", "-").replace("/", "-")
    timezone = str(row["timezone"]).replace(" ", "-").replace("/", "-")
    return City(row["lat"], row["lng"], row["geonameid"], name, country, timezone)


def find_nearest_neighbor(tree: kdtree.KDNode, coords: Tuple[float, float]) -> City:
    """
    Finds the nearest neighbor city for a given coordinate tuple (lat, lng) of a city

    :param tree: KDTree consisting of the coordinates of all possible nearest neighbors
    :param coords: Tuple of lat, lng as floats we want to find the nearest neighbor city for
    """
    neighbor, distance = tree.search_nn(coords)
    return neighbor.data
