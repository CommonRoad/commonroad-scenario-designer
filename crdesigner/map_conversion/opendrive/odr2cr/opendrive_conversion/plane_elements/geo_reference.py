import re
from typing import Optional, Tuple


def get_geo_reference(geo_reference: str) -> Tuple[Optional[float], Optional[float]]:
    """Gets the geographic location information from the geo string extracted from OpenDRIVE files.

    :param geo_reference: Input string from which longitude and latitude should be extracted.
    :return: longitude and latitude parsed from input string
    """
    elements = []
    elements.extend(re.split(r"\+", geo_reference))

    longitude = None
    latitude = None

    for string in elements:
        match_lon = re.match("lon_0", string, flags=0)
        if match_lon is not None:
            longitude = float(re.findall(r"\d+\.?\d*", string)[1])
        else:
            pass

        match_lat = re.match("lat_0", string, flags=0)
        if match_lat is not None:
            latitude = float(re.findall(r"\d+\.?\d*", string)[1])
        else:
            pass

    return longitude, latitude
