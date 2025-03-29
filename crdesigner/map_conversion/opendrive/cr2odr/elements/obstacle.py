from typing import List, Union

import numpy as np
from commonroad.geometry.polyline_util import (
    compute_polyline_initial_orientation,  # type: ignore
)
from commonroad.geometry.shape import Circle, Polygon, Rectangle  # type: ignore
from commonroad.scenario.obstacle import ObstacleType  # type: ignore
from commonroad.scenario.state import TraceState
from lxml import etree  # type: ignore

from crdesigner.map_conversion.opendrive.cr2odr.elements.road import Road
from crdesigner.map_conversion.opendrive.cr2odr.utils import config


class OpenDRIVEObstacle:
    """
    This class adds object child element to road parent element
    and converts CommonRoad obstacles to OpenDRIVE obstacles
    """

    counting = 0

    def __init__(
        self,
        obstacle_type: ObstacleType,
        lanelets: List[int],
        shape: Union[Rectangle, Polygon, Circle],
        state: TraceState,
    ) -> None:
        """
        This function let class Obstacle to initialize the object with type, lanelets, shape, state
        and converts the CommonRoad obstacles into OpenDRIVE obstacles.

        :param obstacle_type: type of obstacle
        :param lanelets: dictionary with key as lanelet id and value as Obstacle
        :param shape: shape of obstacle
        :param state: state of obstacle which includes position, orientation, time_step
        """
        if not lanelets:
            print("no lanelets")
            return
        road_id = Road.cr_id_to_od[lanelets[0]]
        self.road = Road.roads[road_id]
        self.state = state

        OpenDRIVEObstacle.counting += 1
        self.id = OpenDRIVEObstacle.counting
        self.type = obstacle_type if obstacle_type == config.BUILDING else config.OBSTACLE
        self.object = etree.SubElement(self.road.objects, config.OBJECT_TAG)

        self.object.set(config.ID_TAG, str(self.id))
        self.object.set(config.TYPE_TAG, self.type)
        self.object.set(config.SIGNAL_ORIENTATION_TAG, config.NONE)

        self.set_coordinates()

        self.object.set(
            config.SIGNAL_HEIGHT_TAG, config.OBSTACLE_HEIGHT_VALUE
        )  # should this be hardcoded?

        if isinstance(shape, Rectangle):
            self.set_rectangle(shape)
        elif isinstance(shape, Circle):
            self.set_circle(shape)
        else:
            self.set_polygon(shape)

    def set_coordinates(self) -> None:
        """
        This function sets the object's coordinates according to the road reference line.
        """
        refline = self.road.center
        center = self.state.position
        coords = refline[0] - center

        # get rotation angle of the road reference frame relative to global coordinate system
        hdg = compute_polyline_initial_orientation(self.road.center)

        # apply coordinate translation with the given angle
        s = coords[0] * np.cos(hdg) + coords[1] * np.sin(hdg)
        t = coords[1] * np.cos(hdg) - coords[0] * np.sin(hdg)

        # change sign of coordinates if reference line runs in a negative global direction
        if s < 0:
            s = -s
            t = -t

        orientation = self.state.orientation

        self.object.set(config.GEOMETRY_S_COORDINATE_TAG, str(s))
        self.object.set(config.SIGNAL_T_TAG, str(t))

        self.object.set(config.SIGNAL_ZOFFSET_TAG, config.ZERO)
        self.object.set(config.GEOMETRY_HEADING_TAG, str(orientation))

    def set_circle(self, shape: Circle) -> None:
        """
        This function sets the radius of Circle

        :param shape: shape of obstacle
        """
        self.object.set(config.RADIUS_TAG, str(shape.radius))

    def set_rectangle(self, shape: Rectangle) -> None:
        """
        This function sets the length and width of Rectangle

        :param shape: shape of obstacle
        """
        self.object.set(config.LENGTH_TAG, str(shape.length))
        self.object.set(config.SIGNAL_WIDTH_TAG, str(shape.width))

    def set_polygon(self, shape: Polygon) -> None:
        """
        This function add outline child element to object parent element
        and sets id, outer, closed as attributes of outline.

        :param shape: shape of obstacle
        """
        self.outline = etree.SubElement(self.object, config.OUTLINE_TAG)
        self.outline.set(config.ID_TAG, "0")
        self.outline.set(config.OUTER_TAG, config.TRUE)
        self.outline.set(config.CLOSED_TAG, config.TRUE)

        corner_local_id = 0
        # first and last vertex are the same
        vertices = shape.vertices[:-1]
        for vertex in vertices:
            cornerLocal = etree.SubElement(self.outline, config.CORNER_LOCAL_TAG)
            cornerLocal.set(config.ID_TAG, str(corner_local_id))
            cornerLocal.set(config.U_TAG, str(vertex[0]))
            cornerLocal.set(config.V_TAG, str(vertex[1]))
            cornerLocal.set(config.Z_TAG, config.OBSTACLE_Z_VALUE)
            cornerLocal.set(config.SIGNAL_HEIGHT_TAG, config.OBSTACLE_HEIGHT_VALUE)
            corner_local_id += 1
