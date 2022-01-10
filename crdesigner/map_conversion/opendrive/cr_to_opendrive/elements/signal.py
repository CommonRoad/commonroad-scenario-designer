import numpy as np
from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.road import Road
import crdesigner.map_conversion.opendrive.cr_to_opendrive.utils.commonroad_ccosy_geometry_util as util

class Signal:
    """
    This class converts commonroad traffic signal to opendrive traffic signal
    """
    def __init__(self, roadKey, uniqueId, data, laneList) -> None:
        self.road = Road.roads[roadKey]
        self.id = str(uniqueId)
        self.laneList = laneList
        self.ODobject = data[0]
        self.laneletId = data[1]
        self.zOffset = "3.3885"
        self.subtype = "-1"
        self.coutryRevision = "2021"
        self.unit = "km/h"
        self.width = "0.77"
        self.height = "0.77"
        self.hOffset = "0.0"

        self.s, self.t = self.computeCoordinates()
        self.orientation = self.getOrientation()

    def __str__(self) -> str:
        return f"""
        s={self.s}
        t={self.t}
        id={self.id}
        orientation={self.orientation}
        zOffset={self.zOffset}
        subtype={self.subtype}
        coutryRevision={self.coutryRevision}
        unit={self.unit}
        width={self.width}
        height={self.height}
        hOffset={self.hOffset}
        """

    def computeCoordinates(self):
        """
        This function compute reference line coordinates s,t.

        :return: Coordinate along reference line as s
                 and lateral position, positive to the left within the inertial x/y plane as t.
        """
        coords = self.road.center[0] - self.ODobject.position

        hdg = util.compute_orientation_from_polyline(self.road.center)[0]

        s = coords[0] * np.cos(hdg) + coords[1] * np.sin(hdg)
        t = coords[1] * np.cos(hdg) - coords[0] * np.sin(hdg)

        if s < 0:
            s = -s
            t = -t
        return s, t

    def getOrientation(self):
        """
        This function compute orientation of lanelet.

        :return: Either positive sign or negative sign as string.
        """
        lanelet = self.laneList.find_lanelet_by_id(self.laneletId)
        meanLeft = np.mean(lanelet.left_vertices)
        meanRight = np.mean(lanelet.right_vertices)
        leftDist = np.linalg.norm(meanLeft - self.ODobject.position)
        rightDist = np.linalg.norm(meanRight - self.ODobject.position)
        if leftDist - rightDist < 0:
            return "-"
        else:
            return "+"
