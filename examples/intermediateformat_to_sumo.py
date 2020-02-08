from crmapconverter.osm2cr.converter_modules.intermediate_format.intermediate_format import IntermediateFormat
from crmapconverter.osm2cr.converter_modules import converter
import os, sys

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")
import traci

SUMO_GUI_BINARY='/usr/bin/sumo-gui' # Enter your path to SUMO GUI

# Generates Intermediate Format from osm map
scenario = converter.Scenario('files/intersection.osm')
map = IntermediateFormat.extract_from_road_graph(scenario.graph)

# Creates sumo config file
config = map.generate_sumo_config_file()

# Simulates with traci
traci.start([SUMO_GUI_BINARY, "-c", config, "--step-length", str(0.01)])