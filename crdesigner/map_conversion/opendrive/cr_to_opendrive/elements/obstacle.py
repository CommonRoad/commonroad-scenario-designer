from lxml import etree
import numpy as np
from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.road import Road
from commonroad.geometry.shape import Shape, Rectangle, Circle, Polygon
from commonroad.scenario.trajectory import State
import crdesigner.map_conversion.opendrive.cr_to_opendrive.utils.commonroad_ccosy_geometry_util as util
from commonroad.scenario import lanelet


class Obstacle:
    """
    This class adds object child element to road parent element
    and converts CommonRoad obstacles to OpenDRIVE obstacles
    """
    counting = 0

    def __init__(self, type: str, lanelets: lanelet, shape: Shape, state: State) -> None:

        if not lanelets:
            print("no lanelets")
            return
        road_id = Road.cr_id_to_od[lanelets[0]]
        self.road = Road.roads[road_id]
        self.state = state

        Obstacle.counting += 1
        self.id = Obstacle.counting
        self.type = type if type == "building" else "obstacle"
        self.object = etree.SubElement(self.road.objects, "object")

        self.object.set("id", str(self.id))
        self.object.set("type", self.type)
        self.object.set("orientation", "none")

        self.set_coordinates()

        self.object.set("height", "1.0")  # should this be hardcoded?

        if isinstance(shape, Rectangle):
            self.set_rectangle(shape)
        elif isinstance(shape, Circle):
            self.set_circle(shape)
        else:
            self.set_polygon(shape)

    def set_coordinates(self):
        """
        This function sets the object's coordinates according to the road reference line.
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

    def set_circle(self, shape: Circle):
        """
        This function sets the radius of Circle
        """
        self.object.set("radius", str(shape.radius))

    def set_rectangle(self, shape: Rectangle):
        """
        This function sets the length and width of Rectangle
        """
        self.object.set("length", str(shape.length))
        self.object.set("width", str(shape.width))

    def set_polygon(self, shape: Polygon):
        """
        This fucntion add outline child element to object parent element
        and sets id, outer, closed as attributes of outline.
        """
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
