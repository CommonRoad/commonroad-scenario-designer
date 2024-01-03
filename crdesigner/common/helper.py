import os
import site
import sys
from pathlib import Path


def init_sumo():
    """Sets os environment variable for sumo and the system path for sumo tools."""
    tools_path = ""
    for path in site.getsitepackages():
        if "site-packages" in path:
            os.environ["SUMO_HOME"] = str(Path(path + "/sumo"))
            tools_path = str(Path(path + "/sumo/tools"))
            break
    sys.path.insert(0, tools_path)
