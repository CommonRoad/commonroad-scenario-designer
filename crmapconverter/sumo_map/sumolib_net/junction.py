from typing import List
import crmapconverter.sumo_map.sumolib_net.lane as lane


class Junction:
    def __init__(self,
                 id: int,
                 j_type: str = "priority",
                 x: float = -1,
                 y: float = -1,
                 incLanes: List[lane.Lane] = [],
                 intLanes: List[lane.Lane] = [],
                 shape: List[tuple] = ""):
        self.id = id
        self.type = j_type
        self.x = x
        self.y = y
        self.inc_Lanes = incLanes
        self.intLanes = intLanes
        self.shape = shape