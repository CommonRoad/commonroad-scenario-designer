#from crmapconverter.io.visualize_commonroad import main
# from crmapconverter.io.gui import main
# from crmapconverter.io.viewer import main
#from crmapconverter.osm2cr.main import convert
from crmapconverter.osm2cr.converter_modules import converter
from crmapconverter.osm2cr import config
from crmapconverter.io import viewer

# convert("../Maps/mittlerer_Ring.osm")

scenario_file = "/home/max/Desktop/Planning/Maps/osm_files/garching_kreuzung_fixed.osm"
target = "/home/max/Desktop/Planning/Maps/cr_files/garching_kreuzung_types.xml"

config.EXTRACT_PATHWAYS = True
scen = converter.GraphScenario(scenario_file)
scen.save_as_cr(target)

viewer.main()