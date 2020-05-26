import sys
import os
sys.path.append(os.getcwd())
sys.path.append('/home/max/Desktop/Planning/commonroad-io')

from crmapconverter.io.visualize_commonroad import main
# from crmapconverter.io.gui import main
# from crmapconverter.io.viewer import main
from crmapconverter.osm2cr.main import convert

# convert("../Maps/mittlerer_Ring.osm")
main()