#Opendrive converter

This is the converter module for opendrive used in CRSD. It can also run outside CRSD for convenient development.

The main part is 'Network' class in 'network.py'. Functions for conversion are defined as instant methods.

To see if information from opendrive is recorded, please check 'crmapconverter/opendriveparser/elements'. Names of the elements are corresponding to names in Opendrive.

To check the functionality, set working directory to folder 'commonroad-map-tool' and run following code.
 
```python
from lxml import etree
from crmapconverter.opendriveconversion.network import Network
from crmapconverter.opendriveparser.parser import parse_opendrive

file_name = "test/xodr_xml_test_files/opendrive-1.xodr"

# use the parser module
opendrive = parse_opendrive(etree.parse(file_name).getroot())

network = Network()

network.load_opendrive(opendrive)
network.export_lanelet_network()
lanelet_network = network.export_lanelet_network()
scenario = network.export_commonroad_scenario()
```

The out put is a CommonRoad sceario object.