from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.signal import Signal


# Traffic light class inherits from Signal class
class Light(Signal):
    def __init__(self, roadKey, uniqueId, data, laneList) -> None:
        super().__init__(roadKey, uniqueId, data, laneList)
        self.name = "Light_" + str(self.id)
        self.dynamic = "yes" if self.ODobject.active else "no"
        self.country = "OpenDRIVE"
        self.type = "1000001"
        self.value = "-1"

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
