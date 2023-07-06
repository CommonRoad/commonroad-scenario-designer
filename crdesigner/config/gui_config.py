from urllib.request import HTTPBasicAuthHandler, build_opener, install_opener, urlopen

import requests

from crdesigner.config.config_base import BaseConfig, Attribute


def validate_bing_key(key) -> bool:
    """
    Validates the password specified by BING_MAPS_KEY in the config of the settings.
    :return: bool: True for valid password, False for wrong password
    """
    if key == "":
        return True

    req = f"http://dev.virtualearth.net/REST/V1/Imagery/Metadata/Aerial?output=json&include=ImageryProviders&key={key}"
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:80.0) Gecko/20100101 Firefox/80.0'}
    try:
        with requests.session() as s:

            # load cookies otherwise an HTTP error occurs
            s.get(f"http://dev.virtualearth.net/?key={key}", headers=headers)

            # get data
            data = s.get(req, headers=headers).json()
            if data['authenticationResultCode'] == 'ValidCredentials':
                return True
    except Exception:
        pass
    return False


def validate_ldbv_credentials(_) -> bool:
    """
    Validates the username and password specified by LDBV_USERNAME and LDBV_PASSWORD in the config of the settings.
    """

    ldbv_username = gui_config.LDBV_USERNAME
    ldbv_password = gui_config.LDBV_PASSWORD

    if ldbv_username == "" or ldbv_password == "":
        return True

    url = "https://geoservices.bayern.de/wms/v2/ogc_dop20.cgi?service=wms&request=GetMap&version=1.1.1&bbox=11.65541," \
          "48.26142,11.66093,48.26386&width=100&height=100&layers=by_dop20c&format=image/jpeg&srs=EPSG:4326"

    try:
        auth_handler = HTTPBasicAuthHandler()
        auth_handler.add_password(realm='WMS DOP20', uri='https://geoservices.bayern.de/wms/v2/ogc_dop20.cgi',
                                  user=ldbv_username, passwd=ldbv_password)
        opener = build_opener(auth_handler)
        install_opener(opener)
        with urlopen(url) as webpage:
            webpage.read()
    except Exception:
        return False
    return True


class GuiConfig(BaseConfig):
    """
    This class contains all settings for the GUI.
    """

    # focus on the selection
    AUTOFOCUS: Attribute = Attribute(False, "Autofocus")
    MWINDOW_TMP_FOLDER_PATH: Attribute = Attribute("/tmp/cr_designer/", "Temporary folder path")
    # default values in default_draw_params
    DRAW_TRAJECTORY: Attribute = Attribute(False, "Draw trajectory")
    DRAW_INTERSECTIONS: Attribute = Attribute(False, "Draw intersections")
    DRAW_OBSTACLE_LABELS: Attribute = Attribute(True, "Draw obstacle labels")
    DRAW_OBSTACLE_ICONS: Attribute = Attribute(False, "Draw obstacle icons")
    DRAW_OBSTACLE_DIRECTION: Attribute = Attribute(False, "Draw obstacle direction")
    DRAW_OBSTACLE_SIGNALS: Attribute = Attribute(True, "Draw obstacle signals")
    DRAW_OCCUPANCY: Attribute = Attribute(False, "Draw occupancy")
    DRAW_TRAFFIC_SIGNS: Attribute = Attribute(False, "Draw traffic signs")
    DRAW_TRAFFIC_LIGHTS: Attribute = Attribute(True, "Draw traffic lights")
    DRAW_INCOMING_LANELETS: Attribute = Attribute(True, "Draw incoming lanelets")
    DRAW_SUCCESSORS: Attribute = Attribute(True, "Draw successors")
    DRAW_INTERSECTION_LABELS: Attribute = Attribute(False, "Draw intersection labels")
    DARKMODE: Attribute = Attribute(False, "Darkmode")
    AXIS_VISIBLE: Attribute = Attribute(value='All', display_name="Axis visible",
                                        options=['All', 'Left/Bottom', 'None'])
    LEGEND: Attribute = Attribute(True, "Legend")
    # The key to access bing maps
    BING_MAPS_KEY: Attribute = Attribute(value="", display_name="Bing maps key", validation=validate_bing_key)
    # Username and password to access LDBV maps
    LDBV_USERNAME: Attribute = Attribute(value="", display_name="LDBV username", validation=validate_ldbv_credentials)
    LDBV_PASSWORD: Attribute = Attribute(value="", display_name="LDBV password", validation=validate_ldbv_credentials)

    # projects the lane-network in a way that aligns well with aerial images
    pseudo_mercator = Attribute("EPSG:3857", "Pseudo Mercator")
    utm_default = Attribute("+proj=utm +zone=32 +ellps=WGS84", "UTM Default")

    # The layout of the settings window
    LAYOUT = [
        ["Appearance", DARKMODE, AXIS_VISIBLE, LEGEND, "Obstacle visualization", DRAW_TRAJECTORY, DRAW_OBSTACLE_LABELS,
         DRAW_OBSTACLE_ICONS, DRAW_OBSTACLE_DIRECTION, DRAW_OBSTACLE_SIGNALS, "Intersection visualization",
         DRAW_INTERSECTIONS, DRAW_INCOMING_LANELETS, DRAW_SUCCESSORS, DRAW_INTERSECTION_LABELS, ],
        ["Other", AUTOFOCUS, DRAW_OCCUPANCY, DRAW_TRAFFIC_SIGNS, DRAW_TRAFFIC_LIGHTS, BING_MAPS_KEY, LDBV_USERNAME,
         LDBV_PASSWORD]]


gui_config = GuiConfig()
