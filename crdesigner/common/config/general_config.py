from crdesigner.common.config.config_base import Attribute, BaseConfig
from crdesigner.common.config.gui_config import pseudo_mercator


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
    author = Attribute("Max Mustermann", "CommonRoad map/scenario author")
    # CommonRoad scenario/map author affiliation
    affiliation = Attribute(
        "Technical University of Munich", "CommonRoad scenario/map author affiliation"
    )
    # CommonRoad scenario/map source
    source = Attribute("CommonRoad Scenario Designer", "CommonRoad scenario/map source")
    # projection used
    # additional tags for the benchmark
    tags = Attribute("urban", "CommonRoad Tags")
    # projection used for the CommonRoad scenario
    proj_string_cr = Attribute(
        pseudo_mercator, "Projection string", "String used for the initialization of projection"
    )

    LAYOUT = [
        [
            "Default CommonRoad Scenario Information",
            country_id,
            map_name,
            map_id,
            time_step_size,
            author,
            affiliation,
            source,
            tags,
            proj_string_cr,
        ],
    ]


general_config = GeneralConfig()
