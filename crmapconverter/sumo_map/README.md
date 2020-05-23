# Map conversions between CommonRoad and SUMO's .net.xml

## Installation

Install python requirements through

  pip install -r requirements.txt

Furthermore, you need to install SUMO as described here https://sumo.dlr.de/docs/Installing.html.

## Converion of maps
From CommonRoad to net.xml:

  from crmapconverter.sumo_map.cr2sumo import CR2SumoMapConverter

  scenario_path = '/path/to/commonroad_file.xml'
  out_path = '/path/to/output/folder'
  CR2SumoMapConverter.from_file(scenario_path).convert_to_net_file(out_path)

From net.xml to CommonRoad:
  from crmapconverter.sumo_map.sumo2cr import convert_net_to_cr

  net_path = '/path/to/net_file.net.xml'
  out_path = '/path/to/output/folder'
  convert_net_to_cr(net_path, out_path)
