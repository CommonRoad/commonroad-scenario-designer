from crdesigner.common import logging

try:
    from sumocr.interface.sumo_simulation import SumoSimulation  # noqa: F401

    from crdesigner.map_conversion.sumo_map.config import SumoConfig  # noqa: F401
    from crdesigner.map_conversion.sumo_map.cr2sumo.converter import (  # noqa: F401
        CR2SumoMapConverter,
    )

    SUMO_AVAILABLE = True
except ImportError:
    logging.warning(
        "Cannot import SUMO. SUMO simulation will not be offered in Scenario Designer GUI. "
        "The GUI and other map conversions should work."
    )
    SUMO_AVAILABLE = False
