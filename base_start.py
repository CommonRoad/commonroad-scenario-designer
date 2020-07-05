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
# intersect_and_crossing3, mittlerer_Ring, garching_kreuzung_fixed
file_name = "garching_kreuzung_fixed" 

config.EXTRACT_PATHWAYS = True
scen = converter.GraphScenario(source_folder + file_name + ".osm")
scen.save_as_cr(target_folder + file_name + ".xml")

viewer.main()
