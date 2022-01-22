from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.signal import Signal


class Sign(Signal):
    """
    This traffic sign class inherits from Signal class
    which is used to convert CommonRoad sign  to opendrive sign.
    """
    def __init__(self, roadKey, uniqueId, data, laneList) -> None:
        super().__init__(roadKey, uniqueId, data, laneList)
        self.name = "Sign_" + str(self.id)
        self.dynamic = "no"
        self.country = self.getCountry()
        self.type = str(
            self.ODobject.traffic_sign_elements[0].traffic_sign_element_id.value
        )
        self.value = str(self.ODobject.traffic_sign_elements[0].additional_values[0])

        self.road.printSignal(self)

    def __str__(self) -> str:
        return f"""
        s={self.s}
        t={self.t}
        id={self.id}
        name={self.name}
        dynamic={self.dynamic}
        orientation={self.orientation}
        zOffset={self.zOffset}
        country={self.country}
        type={self.type}
        subtype={self.subtype}
        coutryRevision={self.coutryRevision}
        value={self.value}
        unit={self.unit}
        width={self.width}
        height={self.height}
        hOffset={self.hOffset}
        """

    def getCountry(self):
        base = str(self.ODobject.traffic_sign_elements[0].traffic_sign_element_id)
        return base.split("TrafficSignID")[1].split(".")[0].upper()
