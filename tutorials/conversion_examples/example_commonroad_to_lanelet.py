from lxml import etree
from commonroad.common.file_reader import CommonRoadFileReader
from crdesigner.map_conversion.lanelet_lanelet2.cr2lanelet import CR2LaneletConverter
from crdesigner.api import commonroad_to_lanelet


input_path = ""  # replace empty string
output_name = ""  # replace empty string
proj = ""  # replace empty string

# ----------------------------------------------- Option 1: General API ------------------------------------------------
# load CommonRoad file and convert it to lanelet format
commonroad_to_lanelet(input_path, output_name, proj)

# ---------------------------------------- Option 2: Lanelet conversion APIs -------------------------------------------
try:
    commonroad_reader = CommonRoadFileReader(input_path)
    scenario, _ = commonroad_reader.open()
except etree.XMLSyntaxError as xml_error:
    print(f"SyntaxError: {xml_error}")
    print(
        "There was an error during the loading of the selected CommonRoad file.\n"
    )
    scenario = None

if scenario:
    l2osm = CR2LaneletConverter(proj)
    osm = l2osm(scenario)
    with open(f"{output_name}", "wb") as file_out:
        file_out.write(
            etree.tostring(
                osm, xml_declaration=True, encoding="UTF-8", pretty_print=True
            )
        )
