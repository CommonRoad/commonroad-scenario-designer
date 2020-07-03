#from crmapconverter.io.visualize_commonroad import main
# from crmapconverter.io.gui import main
# from crmapconverter.io.viewer import main
#from crmapconverter.osm2cr.main import convert
from crmapconverter.osm2cr.converter_modules import converter
from crmapconverter.osm2cr import config
from crmapconverter.io import viewer

# convert("../Maps/mittlerer_Ring.osm")

source_folder = "/home/max/Desktop/Planning/Maps/osm_files/"
target_folder = "/home/max/Desktop/Planning/Maps/cr_files/ped/"
file_name = "mittlerer_Ring"

config.EXTRACT_PATHWAYS = True
scen = converter.GraphScenario(source_folder + file_name + ".osm")
scen.save_as_cr(target_folder + file_name + ".xml")

viewer.main()