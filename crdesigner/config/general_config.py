from crdesigner.config.config_base import BaseConfig, Attribute


class GeneralConfig(BaseConfig):
    """
    This config holds all general settings.
    """

    # CommonRoad country ID
    country_id = Attribute("ZAM", "CommonRoad country ID")
    # CommonRoad map name
    map_name = Attribute("MUC", "CommonRoad map name")
    # CommonRoad map ID
    map_id = Attribute(1, "CommonRoad map ID")
    # CommonRoad scenario time step size
    time_step_size = Attribute(0.1, "CommonRoad scenario time step size")
    # CommonRoad map/scenario author
    author = Attribute("Sebastian Maierhofer", "CommonRoad map/scenario author")
    # CommonRoad scenario/map author affiliation
    affiliation = Attribute("Technical University of Munich", "CommonRoad scenario/map author affiliation")
    # CommonRoad scenario/map source
    source = Attribute("CommonRoad Scenario Designer", "CommonRoad scenario/map source")


general_config = GeneralConfig()
