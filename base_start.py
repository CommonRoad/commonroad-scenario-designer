#from crmapconverter.io.visualize_commonroad import main
# from crmapconverter.io.gui import main
# from crmapconverter.io.viewer import main
#from crmapconverter.osm2cr.main import convert
from crmapconverter.osm2cr.converter_modules import converter

# convert("../Maps/mittlerer_Ring.osm")

scenario_file = "/home/max/Desktop/Planning/Maps/osm_files/only_straigt_test.osm"

converter.Scenario(scenario_file)