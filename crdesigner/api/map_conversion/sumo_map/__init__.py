"""
Configures the necessary variables for the module to work correctly
"""

import os
import sys

# import $SUMO_HOME/tools into the PYTHONPATH once this module is loaded
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
