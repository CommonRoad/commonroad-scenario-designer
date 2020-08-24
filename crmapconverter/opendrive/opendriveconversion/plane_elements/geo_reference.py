# -*- coding: utf-8 -*-


"""Module to get geographic location information from opendrive"""
import re


def get_geo_reference(geo_reference: str):

    elements = []
    elements.extend(re.split(r'\+', geo_reference))

    longitude = None
    latitude = None

    for string in elements:
        match_lon = re.match('lon_0', string, flags=0)
        if match_lon is not None:
            longitude = float(re.findall(r'\d+\.?\d*', string)[1])
        else:
            pass

        match_lat = re.match('lat_0', string, flags=0)
        if match_lat is not None:
            latitude = float(re.findall(r'\d+\.?\d*', string)[1])
        else:
            pass

    return longitude, latitude
