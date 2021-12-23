from lxml import etree
import numpy as np
from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.road import Road
from commonroad.geometry.shape import Shape, Rectangle, Circle, Polygon
from commonroad.scenario.trajectory import State
import crdesigner.map_conversion.opendrive.cr_to_opendrive.utils.commonroad_ccosy_geometry_util as util

# Obstacle class
class Obstacle:

    counting = 0

    def __init__(self, type, lanelets, shape: Shape, state: State) -> None:

        if not lanelets:
            print("no lanelets")
            return

        roadId = Road.crIdToOD[lanelets[0]]
        self.road = Road.roads[roadId]
        self.state = state

        Obstacle.counting += 1
        self.id = Obstacle.counting
        self.type = type if type == "building" else "obstacle"
        self.object = etree.SubElement(self.road.objects, "object")

        self.object.set("id", str(self.id))
        self.object.set("type", self.type)
        self.object.set("orientation", "none")

        self.setCoordinates()

        self.object.set("height", "1.0")  # should this be hardcoded?

        if isinstance(shape, Rectangle):
            self.setRectangle(shape)
        elif isinstance(shape, Circle):
            self.setCircle(shape)
        else:
            self.setPolygon(shape)

    def setCoordinates(self):
        """
        Sets the object's coordinates according to the road reference line
        """
        refline = self.road.center
        center = self.state.position
        coords = refline[0] - center
        
        #get rotation angle of the road reference frame relative to global coordinate system
        hdg = util.compute_orientation_from_polyline(self.road.center)[0]

        #apply coordinate translation with the given angle
        s = coords[0] * np.cos(hdg) + coords[1] * np.sin(hdg)
        t = coords[1] * np.cos(hdg) - coords[0] * np.sin(hdg)

        #change sign of coordinates if reference line runs in a negative global direction
        if s < 0:
            s = -s
            t = -t

        orientation = self.state.orientation

        self.object.set("s", str(s))
        self.object.set("t", str(t))

        self.object.set("zOffset", "0.0")
        self.object.set("hdg", str(orientation))

    def setCircle(self, shape: Circle):
        self.object.set("radius", str(shape.radius))

    def setRectangle(self, shape: Rectangle):
        self.object.set("length", str(shape.length))
        self.object.set("width", str(shape.width))

    def setPolygon(self, shape: Polygon):
        self.outline = etree.SubElement(self.object, "outline")
        self.outline.set("id", "0")
        self.outline.set("outer", "true")
        self.outline.set("closed", "true")

        id = 0
        # first and last vertex are the same
        vertices = shape.vertices[:-1]
        for vertex in vertices:
            cornerLocal = etree.SubElement(self.outline, "cornerLocal")
            cornerLocal.set("id", str(id))
            cornerLocal.set("u", str(vertex[0]))
            cornerLocal.set("v", str(vertex[1]))
            cornerLocal.set("z", "0")
            cornerLocal.set("height", "1.0")
            id += 1
