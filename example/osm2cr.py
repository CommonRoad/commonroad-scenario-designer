from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.file_writer import CommonRoadFileWriter, \
    OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.scenario import Location

from crmapconverter.osm2cr import config

from crmapconverter.osm2cr.converter_modules.intermediate_format.intermediate_format import IntermediateFormat
from crmapconverter.osm2cr.converter_modules import converter
from commonroad.visualization.draw_dispatch_cr import draw_object
from crmapconverter.osm2cr.converter_modules.cr_operations.export import find_bounds
import matplotlib.pyplot as plt

s = converter.Scenario('files/intersection.osm')
map = IntermediateFormat.extract_from_road_graph(s.graph)
scenario = map.to_commonroad_scenario()
problemset = PlanningProblemSet(None)
author = config.AUTHOR
affiliation = config.AFFILIATION
source = config.SOURCE
tags = config.TAGS
location = Location(country=config.Country, federal_state=config.FEDERAL_STATE, gps_latitude=config.GPS_LATITUDE,
                    gps_longitude=config.GPS_LONGITUDE, zipcode=config.ZIPCODE, name=config.LOCATION_NAME,
                    geo_transformation=None)
file = config.SAVE_PATH + config.BENCHMARK_ID + ".xml"
# in the current commonroad version the following line works
file_writer = CommonRoadFileWriter(scenario, problemset, author, affiliation, source, tags, location,
                                   decimal_precision=16)
print("Scenario saved to file "+file)

print("loading scenario from XML")
scenario, problem = CommonRoadFileReader(file).open()
print("drawing scenario")
limits = find_bounds(scenario)
draw_params = { 'lanelet_network': {'draw_intersections': True, 'draw_traffic_signs_in_lanelet': True,
                                    'draw_traffic_signs': True, 'draw_traffic_lights': False}}
draw_object(scenario, plot_limits=limits, draw_params=draw_params, legend={('lanelet_network','intersection','incoming_lanelets_color'):'Incoming lanelets',
                            ('lanelet_network','intersection','successors_left_color'):'Successors left',
                            ('lanelet_network','intersection','successors_straight_color'):'Successors straight',
                            ('lanelet_network','intersection','successors_right_color'):'Successors right',
                            ('lanelet_network','traffic_light','green_color'):'Traffic light green',
                            ('lanelet_network','traffic_light','yellow_color'):'Traffic light yellow',
                            ('lanelet_network','traffic_light','red_color'):'Traffic light red'})
plt.gca().set_aspect("equal")
plt.savefig('files/image_intersection.svg')
plt.show()