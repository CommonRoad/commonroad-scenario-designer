"""
This module provides methods to download and use areal images from Bing Maps
"""
import json
import os
from io import BytesIO
from queue import Queue
from threading import Thread
from typing import List, Tuple
from typing import Optional
from urllib.request import urlopen

import mercantile
from PIL import Image
from PIL.JpegImagePlugin import JpegImageFile

from crdesigner.map_conversion.osm2cr import config

IMAGE_RESOLUTION = 256

bing_maps_api_response = None

os.makedirs(config.IMAGE_SAVE_PATH, exist_ok=True)


def store_tile(quadkey: str, image: JpegImageFile) -> None:
    """
    This is useful for low internet connection speeds, but i think it is against the bing license agreements
    It should be removed before publishing this application

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
    bingMapsKey = config.BING_MAPS_KEY
    request = "http://dev.virtualearth.net/REST/V1/Imagery/Metadata/Aerial?output=json&include=ImageryProviders&key={}".format(
        bingMapsKey
    )
    # print(request)
    response = urlopen(request).read()
    response = json.loads(response)
    response = response["resourceSets"][0]["resources"][0]
    bing_maps_api_response = response
    return


def get_tile(quadkey: str) -> JpegImageFile:
    """
    takes a quadkey, downloads the corresponding tile if not present and converts it to an image

    :param quadkey: quadkey of tile
    :return: image
    """
    assert type(quadkey) == str

    global bing_maps_api_response

    image = load_tile(quadkey)
    if image is None:
        try:
            if bing_maps_api_response is None:
                get_bin_maps_api_response()
            request = bing_maps_api_response["imageUrl"]
            sub_domain = bing_maps_api_response["imageUrlSubdomains"][0]
            request = request.replace("{subdomain}", sub_domain)
            request = request.replace("{quadkey}", quadkey)
            print(request)
            tile = urlopen(request).read()
            image = Image.open(BytesIO(tile))
            store_tile(quadkey, image)
        except:
            return get_tile(quadkey)
    return image


def get_required_quadkeys(
    west: float, south: float, east: float, north: float, zoom: int
) -> Tuple[List[str], int, int, List[float]]:
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
        # print(tile)
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
    lnglat_lower_right = mercantile.lnglat(
        bbox_lower_right.right, bbox_lower_right.bottom
    )
    horizontal_max = lnglat_lower_right.lng
    vertical_min = lnglat_lower_right.lat

    extent = [horizontal_min, horizontal_max, vertical_min, vertical_max]
    return quadkeys, x_length, y_length, extent


def put_images_together(
    images: List[Image.Image], x_count: int, y_count: int
) -> Image.Image:
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

    # print("waiting for queue")
    q.join()
    for i in range(PARALLEL_REQUESTS):
        q.put(None)
    # print("waiting for threads")
    for t in threads:
        t.join()
    # print("threads joined")

    result = [images[quadkey] for quadkey in quadkeys]
    return result


def get_aerial_image(
    lat1: float, lon1: float, lat2: float, lon2: float, zoom: int = 19
) -> Tuple[Image.Image, List[float]]:
    """
    gets the image and coordinates to a sepcified aera

    :param lat1: northern  bound
    :param lon1: western bound
    :param lat2: southern bound
    :param lon2: eastern bound
    :param zoom: zoom level
    :return: Tuple: 1. image, 2. extent of image
    """
    assert 1 <= zoom <= 23
    keys, x_count, y_count, extent = get_required_quadkeys(lon1, lat2, lon2, lat1, zoom)
    print("loading {} tiles".format(len(keys)))
    # images = [get_tile(key) for key in keys]
    images = download_all_images(keys)
    image = put_images_together(images, x_count, y_count)
    return image, extent
