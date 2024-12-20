"""
This module provides methods to download and use aerial images from Bing Maps
"""

import json
import os
from io import BytesIO
from queue import Queue
from threading import Thread
from typing import List, Optional, Tuple
from urllib.request import HTTPBasicAuthHandler, build_opener, install_opener, urlopen

import mercantile
import requests
from commonroad.scenario.scenario import Scenario
from PIL import Image
from PIL.JpegImagePlugin import JpegImageFile
from pyproj import Proj

from crdesigner.common.config.gui_config import gui_config
from crdesigner.common.config.osm_config import osm_config as config

# Moved to services/arial data

IMAGE_RESOLUTION = 256

bing_maps_api_response = None

os.makedirs(config.IMAGE_SAVE_PATH, exist_ok=True)


def store_tile(quadkey: str, image: JpegImageFile) -> None:
    """
    This is useful for low internet connection speeds.

    :param quadkey: quadkey of tile
    :param image: the image
    :return: None
    """
    file = config.IMAGE_SAVE_PATH + quadkey + ".jpeg"
    image.save(file, "JPEG")
    return


def load_tile(quadkey: str) -> Optional[JpegImageFile]:
    """
    tries to load a tile from disk

    :param quadkey: quadkey of tile
    :return: the image if present, else None
    """
    try:
        image = Image.open(config.IMAGE_SAVE_PATH + quadkey + ".jpeg")
    except FileNotFoundError:
        image = None
    return image


def get_bin_maps_api_response() -> None:
    """
    gets the required information to interact with bing maps api
    this should be executed once, in every session, the variable is stored globally

    :return: None
    """

    global bing_maps_api_response
    bingMapsKey = gui_config.BING_MAPS_KEY
    if bingMapsKey == "":
        print("_Warning__: No Bing Maps key specified. Go to settings and set Password.")
        return
    request = (
        "http://dev.virtualearth.net/REST/V1/Imagery/Metadata/Aerial?output=json&include=ImageryProviders&key={"
        "}".format(bingMapsKey)
    )

    response = urlopen(request).read()
    response = json.loads(response)
    response = response["resourceSets"][0]["resources"][0]
    bing_maps_api_response = response
    return


def validate_bing_key() -> bool:
    """
    Validates the password specified by BING_MAPS_KEY in the config of the settings.
    :return: bool: True for valid password, False for wrong password
    """
    bingMapsKey = gui_config.BING_MAPS_KEY
    request = (
        "http://dev.virtualearth.net/REST/V1/Imagery/Metadata/Aerial?output=json&include=ImageryProviders&key={"
        "}".format(bingMapsKey)
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:80.0) Gecko/20100101 Firefox/80.0"
    }

    with requests.session() as s:
        # load cookies otherwise an HTTP error occurs
        s.get("http://dev.virtualearth.net/?key={" "}".format(bingMapsKey), headers=headers)

        # get data
        data = s.get(request, headers=headers).json()
        if data["authenticationResultCode"] == "ValidCredentials":
            return True
    return False


def validate_ldbv_credentials() -> bool:
    url = "https://geoservices.bayern.de/wms/v2/ogc_dop20.cgi?service=wms&request=GetMap&version=1.1.1&bbox=11.65541,48.26142,11.66093,48.26386&width=100&height=100&layers=by_dop20c&format=image/jpeg&srs=EPSG:4326"
    ldbv_username = gui_config.LDBV_USERNAME
    ldbv_password = gui_config.LDBV_PASSWORD

    try:
        auth_handler = HTTPBasicAuthHandler()
        auth_handler.add_password(
            realm="WMS DOP20",
            uri="https://geoservices.bayern.de/wms/v2/ogc_dop20.cgi",
            user=ldbv_username,
            passwd=ldbv_password,
        )
        opener = build_opener(auth_handler)
        install_opener(opener)
        urlopen(url).read()
    except Exception:
        return False
    return True


def get_tile(quadkey: str) -> JpegImageFile:
    """
    takes a quadkey, downloads the corresponding tile if not present and converts it to an image

    :param quadkey: quadkey of tile
    :return: image
    """
    assert isinstance(quadkey, str)

    global bing_maps_api_response

    image = load_tile(quadkey)
    if image is None:
        try:
            if bing_maps_api_response is None:
                get_bin_maps_api_response()
            if gui_config.BING_MAPS_KEY == "":
                return
            request = bing_maps_api_response["imageUrl"]
            sub_domain = bing_maps_api_response["imageUrlSubdomains"][0]
            request = request.replace("{subdomain}", sub_domain)
            request = request.replace("{quadkey}", quadkey)
            tile = urlopen(request).read()
            image = Image.open(BytesIO(tile))
            store_tile(quadkey, image)
        except Exception:
            return get_tile(quadkey)
    return image


def get_required_quadkeys(
    west: float, south: float, east: float, north: float, zoom: int
) -> Tuple[List[str], int, int, Tuple[float, float, float, float]]:
    """
    gets quadkeys for all tiles in a region sorted by their x and y value
    returns also the number of different x and y values

    :param west: west end of the region
    :param south: south end of the region
    :param east: east end of the region
    :param north: north end of the region
    :param zoom: zoom level
    :return: tuple of: 1. list of quadkeys, 2. nr of tile columns , 3. nr of tile rows, 4. coordinates of region
    """
    tiles = mercantile.tiles(west, south, east, north, zoom)
    tiles = list(tiles)
    assert len(tiles) > 0

    x_counts = {}
    y_counts = {}
    for tile in tiles:
        x = tile.x
        if x in x_counts:
            x_counts[x] += 1
        else:
            x_counts[x] = 1
        y = tile.y
        if y in y_counts:
            y_counts[y] += 1
        else:
            y_counts[y] = 1

    x_length = next(iter(x_counts.values()))
    y_length = next(iter(y_counts.values()))

    for x, count in x_counts.items():
        assert count == x_length
    for y, count in y_counts.items():
        assert count == y_length

    tiles = sorted(tiles, key=lambda x: (x.x, x.y))
    quadkeys = [mercantile.quadkey(tile) for tile in tiles]

    lnglat_top_left = mercantile.ul(tiles[0])

    horizontal_min = lnglat_top_left.lng
    vertical_max = lnglat_top_left.lat

    bbox_lower_right = mercantile.xy_bounds(tiles[-1])
    lnglat_lower_right = mercantile.lnglat(bbox_lower_right.right, bbox_lower_right.bottom)

    horizontal_max = lnglat_lower_right.lng
    vertical_min = lnglat_lower_right.lat
    extent = (vertical_max, horizontal_min, vertical_min, horizontal_max)
    return quadkeys, x_length, y_length, extent


def put_images_together(images: List[Image.Image], x_count: int, y_count: int) -> Image.Image:
    """
    puts tiles together to one image

    :param images: images in sorted order
    :param x_count: number of columns
    :param y_count: number of rows
    :return: resulting image
    """
    height = x_count * IMAGE_RESOLUTION
    width = y_count * IMAGE_RESOLUTION
    new_im = Image.new("RGB", (width, height))
    for index, image in enumerate(images):
        x = IMAGE_RESOLUTION * (index // x_count)
        y = IMAGE_RESOLUTION * (index % x_count)
        new_im.paste(image, (x, y))
    return new_im


def download_all_images(quadkeys: List[str]) -> List[Image.Image]:
    """
    downloads all images in list

    :param quadkeys: quadkeys of images
    :return: resulting images
    """

    def thread_work():
        while True:
            quadkey = q.get()
            if quadkey is None:
                return
            image = get_tile(quadkey)
            images[quadkey] = image
            q.task_done()

    PARALLEL_REQUESTS = 200
    q = Queue()

    images = {}
    threads = []
    for i in range(PARALLEL_REQUESTS):
        t = Thread(target=thread_work)
        t.start()
        threads.append(t)

    for quadkey in quadkeys:
        q.put(quadkey)

    q.join()
    for i in range(PARALLEL_REQUESTS):
        q.put(None)
    for t in threads:
        t.join()

    result = [images[quadkey] for quadkey in quadkeys]
    return result


def get_aerial_image_bing(
    bounds: Tuple[float, float, float, float], zoom: int = 19
) -> Tuple[Image.Image, Tuple[float, float, float, float]]:
    """
    gets the image and coordinates to a specified aera from bing
    :param bounds: northern, western, southern and eastern bound
    :param zoom: zoom level
    :return: Tuple: 1. image, 2. extent of image
    """
    assert 1 <= zoom <= 23

    lat1, lon1, lat2, lon2 = bounds

    keys, x_count, y_count, extent = get_required_quadkeys(lon1, lat2, lon2, lat1, zoom)
    print("loading {} tiles".format(len(keys)))
    # images = [get_tile(key) for key in keys]
    images = download_all_images(keys)
    image = put_images_together(images, x_count, y_count)
    return image, extent


def get_aerial_image_ldbv(bounds: Tuple[float, float, float, float]) -> Image.Image:
    """
    gets the image and coordinates to a specified area from LDBV

    :param bounds: northern, western, southern and eastern bound
    :return: Image
    """
    lat1, lon1, lat2, lon2 = bounds
    ldbv_username = gui_config.LDBV_USERNAME
    ldbv_password = gui_config.LDBV_PASSWORD

    lat_diff = lat1 - lat2
    lon_diff = lon2 - lon1

    # compute number of pixels of width and height based on coordinate limits (bigger side has always 4000 pixels)
    if lat_diff > lon_diff:
        onep = 4000 / lat_diff
        lon_pixels = int(onep * lon_diff)
        lat_pixels = 4000
    else:
        onep = 4000 / lon_diff
        lat_pixels = int(onep * lat_diff)
        lon_pixels = 4000

    # Reference system of the bbox-coordinates. We use WGS 84 (i.e. the "normal" geodetic system with
    #   longitude and latitude);
    #   for other options, see https://geodatenonline.bayern.de/geodatenonline/seiten/wms_dop20cm?36
    ref_system = "EPSG:4326"
    if ldbv_username == "" or ldbv_password == "":
        url = f"https://geoservices.bayern.de/wms/v2/ogc_dop80_oa.cgi?service=wms&request=GetMap&version=1.1.1&bbox={str(lon1)},{str(lat2)},{str(lon2)},{str(lat1)}&width={str(lat_pixels)}&height={str(lon_pixels)}&layers=by_dop80c&format=image/jpeg&srs={ref_system}"
        auth_handler = HTTPBasicAuthHandler()
        opener = build_opener(auth_handler)
        install_opener(opener)
        tile = urlopen(url).read()
        image = Image.open(BytesIO(tile))
    else:
        url = f"https://geoservices.bayern.de/wms/v2/ogc_dop20.cgi?service=wms&request=GetMap&version=1.1.1&bbox={str(lon1)},{str(lat2)},{str(lon2)},{str(lat1)}&width={str(lat_pixels)}&height={str(lon_pixels)}&layers=by_dop20c&format=image/jpeg&srs={ref_system}"
        auth_handler = HTTPBasicAuthHandler()
        auth_handler.add_password(
            realm="WMS DOP20",
            uri="https://geoservices.bayern.de/wms/v2/ogc_dop20.cgi",
            user=ldbv_username,
            passwd=ldbv_password,
        )
        opener = build_opener(auth_handler)
        install_opener(opener)
        tile = urlopen(url).read()
        image = Image.open(BytesIO(tile))

    return image


def get_aerial_image_limits(
    bounds: Tuple[float, float, float, float], scenario: Scenario
) -> Tuple[float, float, float, float]:
    """
    :param bounds: bounds of the image region as latitude/longitude: (northern, western, southern, eastern)
    :param scenario: CommonRoad scenario
    :return bounds in scenario coordinates: (left, right, bottom, top)
    """
    lat1, lon1, lat2, lon2 = bounds
    proj_string = None
    loc = scenario.location
    if loc is not None and loc.geo_transformation is not None:
        proj_string = loc.geo_transformation.geo_reference
    if proj_string is None:
        proj_string = gui_config.pseudo_mercator
    proj = Proj(proj_string)
    lower_left = proj(longitude=lon1, latitude=lat2)
    upper_right = proj(longitude=lon2, latitude=lat1)
    return (
        lower_left[0] - scenario.location.geo_transformation.x_translation,
        upper_right[0] - scenario.location.geo_transformation.x_translation,
        lower_left[1] - scenario.location.geo_transformation.y_translation,
        upper_right[1] - scenario.location.geo_transformation.y_translation,
    )
