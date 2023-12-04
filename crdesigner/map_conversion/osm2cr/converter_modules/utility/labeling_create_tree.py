import json
import numpy as np
import pandas as pd
import kdtree
from typing import Tuple

class City:
    def __init__(self, lat, lng, name, country, timezone):
        self.lat = lat
        self.lng = lng
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
    
    def getLabel(self):
        return f"{self.name}_{self.country}_{self.timezone}"
    
    def __str__(self):
        return self.getLabel()


def create_tree(df: pd.DataFrame) -> kdtree.KDNode:
    assert 'lat' in df.columns and 'lng' in df.columns, "DataFrame needs \'lat\' and \'lng\' columns"
    city_list = df.apply(get_city_from_row, axis=1).tolist()
    return kdtree.create( city_list)


def get_city_from_row(row: pd.Series) -> City:
    """
    Return City object from raw data
    
    :param1 row: Raw DataFrame Row
    """
    name = str(row['asciiname']).replace(' ', '-').replace('/', '-')
    country = str(row['country code']).replace(' ', '-').replace('/', '-')
    timezone = str(row['timezone']).replace(' ', '-').replace('/', '-')
    return City(row['lat'], row['lng'], name, country, timezone)

def find_nearest_neighbor(tree: kdtree.KDNode, coords: Tuple[float, float]) -> City:
    """
    Finds the nearest neighbor city for a given coordinate tuple (lat, lng) of a city
    
    :param1 kdtree: KDTree consisting of the coordinates of all possible nearest neighbors
    :param2 coords: Tuple of lat, lng as floats we want to find the nearest neighbor city for
    """
    neighbor, distance = tree.search_nn(coords)
    return neighbor.data

