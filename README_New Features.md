# Traffic Rules in CommonRoad Map Converter

Traffic Rules are now extracted from Open Street Map format and converted to 
CommonRoad format. Sumo trips can also be generated with the traffic rules 
extracted.
Examples can be demonstrated by running the scripts on example folder with osm 
map with traffic signs and lights. An example osm file is on the mentioned folder.

#### Installation
Activate the Python environment by:
```bash
source venv/bin/activate
```
Then install the dependencies
```bash
pip install -r reequirements.txt
```

#### Usage

Opening of new GUI : 
```bash
python crmapconverter/io/V2_0/gui_2_0.py
```

#### Examples

An example to convert OSM File to CommonRoad Map with traffic sign and traffic signal:  
```bash
python examples/osm2cr.py
```

An example to converting OSM File to Sumo config file and run simulation
```bash
python examples/intermediateformat_to_sumo.py
```
You will find the sumo files on examples/files/sumo/

#### Documentation
For documentation on Intermediate Format and helper methods for Sumo, run
 ```bash
pip install -r doc_requirements.txt
```
Then go to
```bash
cd crmapconverter/osm2cr/convertermodules/intermediate_format/docs
```
Then run
```bash
make html
```
The html file will be found on build/index.html

#### Authors

##### Behtarin Ferdousi
    * OSM traffic rule extraction
    * Intermediate Format
    * Traffic Rule in CommonRoad
    * Intersection Extraction
    * Intermediate Format to SUMO config file
    
#### Vidhit Chandra
    
    1.Intermediate Format to SUMO converter and vice versa.(Code is in SumoIR branch of MPFAV-artificial scenario generation repository)(Has an import bug).
    2.Intermediate Format to SUMO config file,route file,network file generation.
    3.Convert roadgraph in OSM2CR to Intermediate format.