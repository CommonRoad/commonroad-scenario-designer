from lxml import etree
from datetime import datetime
import crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.road as Road


class Writer(object):
    """
    This class creates a opendrive file. The xml etree element is written as opendrive file.
    """
    def __init__(self, file_path_out: str):
        self.file_path_out = file_path_out
        self.root = etree.Element("OpenDRIVE")
        etree.indent(self.root, space="    ")
        self.writeHeader()
        self.tree = etree.ElementTree(self.root)

    def save(self):
        """
        This function writes the opendrive file.
        """
        etree.indent(self.root, space="    ")
        self.tree.write(
            self.file_path_out,
            xml_declaration=True,
            method="xml",
            encoding="UTF-8",
            pretty_print=True,
        )

    # TODO: does this need to be <header></header> or is <header/> fine?
    def writeHeader(self):
        """
        This function creates header child element with various attributes and add it to Opendrive root element.
        """
        name = self.file_path_out.split("/")[-1].split(".")[0]
        self.header = etree.SubElement(self.root, "header")
        self.header.set("revMajor", "1")
        self.header.set("revMinor", "6")
        self.header.set("version", "1.0")
        self.header.set("name", name)
        mydate = datetime.now()
        self.header.set("date", mydate.isoformat())
        val = 0
        self.header.set("north", str.format("{0:.16e}", val))
        self.header.set("south", str.format("{0:.16e}", val))
        self.header.set("east", str.format("{0:.16e}", val))
        self.header.set("west", str.format("{0:.16e}", val))
        self.geoReference = etree.SubElement(self.header, "geoReference")
        # TODO: do we need to convert the gps latitude and longitude
        # into something like that:   <![CDATA[epsg:25833]]>    ?
        self.geoId = etree.SubElement(self.geoReference, "TODO")

    def setChildOfRoad(self, name: str) -> etree:
        """
        This function add subelement to road parent element

        :param name: name of subelement to be added
        :return: road element xml with specific sub element
        """
        return etree.SubElement(self.road, name)

    def createRoadChilds(self):
        """
        This function creates child elements for road parent element.
        """
        # subelement link - TODO
        self.link = self.setChildOfRoad("link")

        # subelement type - TODO
        self.type = self.setChildOfRoad("type")

        # subelement planview - TODO
        self.planView = self.setChildOfRoad("planView")

        # subelement elevationProfile - TODO
        self.elevationProfile = self.setChildOfRoad("elevationProfile")

        # subelement lateralProfile - TODO
        self.lateralProfile = self.setChildOfRoad("lateralProfile")

        # subelement lanes - TODO
        self.lanes = self.setChildOfRoad("lanes")

        # subelement objects - TODO
        self.objects = self.setChildOfRoad("objects")

        # subelement signals - TODO
        self.signals = self.setChildOfRoad("signals")

    # this will later take a road element
    def writeRoad(self):
        """
        This function add road child element with various attributes to Opendrive root element.
        """
        # subelement road
        # set self.road for every road so that we dont overwrite existing roads
        self.road = etree.SubElement(self.root, "road")
        self.createRoadChilds()

        # Write type - TODO
        self.type.set("s", str.format("{0:.16e}", 0))
        self.type.set("type", "town")

        # road name - TODO
        self.road.set("name", "")

        # road length - TODO this needs to be stored in the road object
        self.road.set("length", str.format("{0:.16e}", 10))  # road.length))

        # road id - TODO this needs to be stored in the road object
        self.road.set("id", str.format("{}", 100))  # road.counting))

        # road junction - TODO this needs to be stored in the road object
        self.road.set("junction", str.format("{}", -1))  # road.junction))

    def printLine(self, s, x, y, hdg, length):
        """
        This function add geometry child element with various attribute to planView parent element and 
        then add line child element to geometry parent element
        """
        geometry = etree.SubElement(self.planView, "geometry")
        geometry.set("s", str.format("{0:.16e}", s))
        geometry.set("x", str.format("{0:.16e}", x))
        geometry.set("y", str.format("{0:.16e}", y))
        geometry.set("hdg", str.format("{0:.16e}", hdg))
        geometry.set("length", str.format("{0:.16e}", length))

        line = etree.SubElement(geometry, "line")

    def printSpiral(self, s, x, y, hdg, length, curvStart, curvEnd):
        """
        This function add geometry child element with various attribute to planView parent element and 
        then add spiral child element to geometry parent element
        """
        geometry = etree.SubElement(self.planView, "geometry")
        geometry.set("s", str.format("{0:.16e}", s))
        geometry.set("x", str.format("{0:.16e}", x))
        geometry.set("y", str.format("{0:.16e}", y))
        geometry.set("hdg", str.format("{0:.16e}", hdg))
        geometry.set("length", str.format("{0:.16e}", length))

        spiral = etree.SubElement(geometry, "spiral")
        spiral.set("curvStart", str.format("{0:.16e}", curvStart))
        spiral.set("curvEnd", str.format("{0:.16e}", curvEnd))

    def printArc(self, s, x, y, hdg, length, curvature):
        """
        This function add geometry child element with various attribute to planView parent element and 
        then add arc child element to geometry parent element
        """
        geometry = etree.SubElement(self.planView, "geometry")
        geometry.set("s", str.format("{0:.16e}", s))
        geometry.set("x", str.format("{0:.16e}", x))
        geometry.set("y", str.format("{0:.16e}", y))
        geometry.set("hdg", str.format("{0:.16e}", hdg))
        geometry.set("length", str.format("{0:.16e}", length))

        arc = etree.SubElement(geometry, "arc")
        arc.set("curvature", str.format("{0:.16e}", curvature))
