import iso3166

__author__ = "Benjamin Orthen, Stefan Urban"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "0.5.1"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad@lists.lrz.de"
__status__ = "Released"


def encode_road_section_lane_width_id(roadId, sectionId, laneId, widthId):
    """Encodes a road section lane width with an ID.

    :param roadId: ID of road.
    :type roadId: int
    :param sectionId: ID of RoadSection.
    :type sectionId: int
    :param laneId: ID of Lane.
    :type laneId: int
    :param widthId: ID of LaneWidth.
    :type widthId: int
    :return: A new ID concatenated from the input IDs.
    :rtype: str
    """
    return ".".join([str(roadId), str(sectionId), str(laneId), str(widthId)])


def get_signal_country(signal_country: str):
    """
    ISO3166 standard to find 3 letter country id
    :param signal_country: String value of the country.
    :type signal_country: str
    :return: The 3-letter country ID per ISO3166.
    :rtype: str
    """
    signal_country = signal_country.upper()
    if signal_country in iso3166.countries_by_name:
        return iso3166.countries_by_name[signal_country].alpha3
    elif signal_country in iso3166.countries_by_alpha2:
        return iso3166.countries_by_alpha2[signal_country].alpha3
    elif signal_country in iso3166.countries_by_alpha3:
        return signal_country
    else:
        return "ZAM"

# def decode_road_section_lane_width_id(encodedString: str):
#     """

#     Args:
#       encodedString:

#     Returns:

#     """

#     parts = encodedString.split(".")

#     if len(parts) != 4:
#         raise Exception()

#     return (int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]))


# def allCloseToZero(array):
#     """Tests if all elements of array are close to zero.

#     Args:
#       array:

#     Returns:

#     """

#     return numpy.allclose(array, numpy.zeros(numpy.shape(array)))
