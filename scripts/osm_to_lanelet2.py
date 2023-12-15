import os

from lxml import etree
from crdesigner.map_conversion.map_conversion_interface import osm_to_commonroad, commonroad_to_lanelet

from commonroad.scenario.scenario import Tag
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.scenario import Location, GeoTransformation
from commonroad.scenario.scenario import Scenario


from crdesigner.config.lanelet2_config import lanelet2_config
import crdesigner.map_conversion.osm2cr.converter_modules.converter as converter
import crdesigner.map_conversion.osm2cr.converter_modules.cr_operations.export as ex
from crdesigner.config.osm_config import osm_config
from crdesigner.map_conversion.osm2cr.converter_modules.osm_operations.downloader import download_around_map
from crdesigner.map_conversion.lanelet2.cr2lanelet import CR2LaneletConverter

from translate import translate

# input_path = ""  # replace empty string
# output_name = ""  # replace empty string
config = lanelet2_config
config.autoware = False
config.use_local_coordinates = False
config.translate = False

lat_offset = 41.024470070
long_offset = 28.890688862
x_offset = 3216096.772764564
y_offset = 5015951.663928764

# 41.0573834,28.7832427
# 649847.15,4546659.31

translate_coordinates = False



# 649398.125505635,4545841.148630586
# 41.050101454,28.777709029

# D-020
# 653069.104282261,4562061.345246037

# Airport
# 41.245786144,28.753681644
# 646941.109851236,4567525.068219149
# 3200845.199018098,5048662.939494990

# YTU
# 41.024470070,28.890688862
# 658955.054736255,4543195.278265686
# 3216096.772764564,5015951.663928764


# scenario = osm_to_commonroad("/home/ataparlar/data/openstreetmap_data/hiratsuka_small/commonroad_data/hiratsukaOSM_small.osm")
scenario = osm_to_commonroad("/home/ataparlar/projects/qgis/hiratsuka_lanelet2_from_osm/data/ytu/ytu_roads_rm_dup_dissolved.osm")
# print(scenario._lanelet_network.lanelets)

# georeference_string = "+proj=longlat +datum=WGS84 +no_defs +type=crs +towgs84=0,0,0"
# georeference_string = "+proj=utm +zone=35 +ellps=WGS84 +lat_ts=41.024470070 +lon_0=28.890688862 +x_0=-500000 +y_0=0 +units=m +no_defs"
# georeference_string = "+proj=merc +ellps=WGS84 +datum=WGS84 +lat_ts=70.0 +lon_0=28.890688862 +x_0=-500000 +y_0=0"
# georeference_string = "+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +k_0=1.02 +lon_0=0 +x_0=0 +y_0=0 +units=m +nadgrids=@null +wktext +no_defs +type=crs"
georeference_string = "EPSG:3857"
location_geotransformation = GeoTransformation(georeference_string, x_offset, y_offset, None, None)
scenario_location = Location(11, lat_offset, long_offset, location_geotransformation, None)


scenario.location = scenario_location





# store converted file as CommonRoad scenario
writer = CommonRoadFileWriter(
    scenario=scenario,
    planning_problem_set=PlanningProblemSet(),
    author="Ata Parlar",
    affiliation="Technical University of Munich",
    source="CommonRoad Scenario Designer",
    tags={Tag.URBAN},
    location=scenario_location
)
writer.write_to_file("/home/ataparlar/projects/lanelet2_converter/commonroad-scenario-designer/export/ytu/ytu_roads_rm_dup_dissolved_commonroad.xml",
                     OverwriteExistingFile.ALWAYS)


# input_path = "export/hiratsukaOSM_small_commonroad.xml"
# output_path = "export/hiratsukaOSM_small_lanelet2.osm"

# commonroad_to_lanelet(input_path, output_path, config)




if scenario:
    l2osm = CR2LaneletConverter(config)
    osm = l2osm(scenario)
    with open("/home/ataparlar/projects/lanelet2_converter/commonroad-scenario-designer/export/ytu/ytu_roads_rm_dup_dissolved_lanelet2.osm", "wb") as file_out:
        file_out.write(
            etree.tostring(
                osm, xml_declaration=True, encoding="UTF-8", pretty_print=True
            )
        )

if translate_coordinates:
    translate(0.0, 0.0, 
              "/home/ataparlar/projects/lanelet2_converter/commonroad-scenario-designer/export/d020_roads_rm_dup_dissolved_lanelet2_wgs84.osm",
                "/home/ataparlar/projects/lanelet2_converter/commonroad-scenario-designer/export/d020_roads_rm_dup_dissolved_lanelet2_wgs84_corrected.osm")



