from crmapconverter.sumo_map.sumolib_net.connection import Connection
from xml.etree import cElementTree as ET
from typing import Dict, List
from enum import Enum
from collections import defaultdict


class SumoSignalState(Enum):
    """
    Adapted from: https://sumo.dlr.de/docs/Simulation/Traffic_Lights.html#tllogic62_attributes
    """
    # 'red light' for a signal - vehicles must stop
    RED = "r"
    # 'amber (yellow) light' for a signal -
    # vehicles will start to decelerate if far away from the junction, otherwise they pass
    YELLOW = "y"
    # 'green light' for a signal, no priority -
    # vehicles may pass the junction if no vehicle uses a higher priorised foe stream,
    # otherwise they decelerate for letting it pass.
    # They always decelerate on approach until they are within the configured visibility distance
    GREEN = "g"
    # 'green light' for a signal, priority -
    # vehicles may pass the junction
    GREEN_PRIORITY = "G"
    # 'green right-turn arrow' requires stopping -
    # vehicles may pass the junction if no vehicle uses a higher priorised foe stream.
    # They always stop before passing.
    # This is only generated for junction type traffic_light_right_on_red.
    GREEN_TURN_RIGHT = "s"
    # 'red+yellow light' for a signal, may be used to indicate upcoming
    # green phase but vehicles may not drive yet (shown as orange in the gui)
    RED_YELLOW = "u"
    # 'off - blinking' signal is switched off, blinking light indicates vehicles have to yield
    BLINKING = "o"
    # 'off - no signal' signal is switched off, vehicles have the right of way
    NO_SIGNAL = "O"


class Phase:
    def __init__(self,
                 duration: int,
                 state: List[SumoSignalState],
                 min_dur: int = None,
                 max_dur: int = None,
                 name: str = None,
                 next: List[int] = None):
        """
        Adapted from: https://sumo.dlr.de/docs/Simulation/Traffic_Lights.html#tllogic62_attributes
        :param duration: The duration of the phase (sec)
        :param state: The traffic light states for this phase, see below
        :param min_dur: The minimum duration of the phase when using type actuated. Optional, defaults to duration.
        :param max_dur: The maximum duration of the phase when using type actuated. Optional, defaults to duration.
        :param name: An optional description for the phase. This can be used to establish the correspondence between SUMO-phase-indexing and traffic engineering phase names.
        :param next:
        """
        self.duration = duration
        self.state = state
        self.min_dur = min_dur
        self.max_dur = max_dur
        self.name = name
        self.next = next

    def to_xml(self) -> bytes:
        phase = ET.Element("phase")
        phase.set("duration", str(self.duration))
        phase.set("state", "".join([s.value for s in self.state]))
        if self.min_dur is not None:
            phase.set("minDur", str(self.min_dur))
        if self.max_dur is not None:
            phase.set("maxDur", str(self.max_dur))
        if self.name is not None:
            phase.set("name", str(self.name))
        if self.next is not None:
            phase.set("next", str(self.next))
        return ET.tostring(phase)

    def __str__(self):
        return str(self.to_xml())

    def __repr__(self):
        return str(self)


class SumoTLSType(Enum):
    STATIC = "static"
    ACTUATED = "actuated"
    DELAY_BASED = "delay_based"


class TLSProgram:
    def __init__(self, id: str, offset: int, program_id: str, tls_type: SumoTLSType = SumoTLSType.STATIC):
        """
        Adapted from: https://sumo.dlr.de/docs/Simulation/Traffic_Lights.html#tllogic62_attributes
        :param id: The id of the traffic light. This must be an existing traffic light id in the .net.xml file.
        Typically the id for a traffic light is identical with the junction id.
        The name may be obtained by right-clicking the red/green bars in front of a controlled intersection.
        :param offset: The initial time offset of the program
        :param program_id: The id of the traffic light program; This must be a new program name for the traffic light id.
        Please note that "off" is reserved, see below.
        :param tls_type: The type of the traffic light (fixed phase durations, phase prolongation based on time
        gaps between vehicles (actuated), or on accumulated time loss of queued vehicles (delay_based) )
        """
        self._id = id
        self._type = tls_type
        self._offset = offset
        self._program_id = program_id
        self._phases: List[Phase] = []

    def addPhase(self, phase: Phase):
        self._phases.append(phase)

    def getPhases(self) -> List[Phase]:
        return self._phases

    def getOffset(self) -> int:
        return self._offset

    def toXML(self, ) -> bytes:
        tl = ET.Element("tlLogic")
        tl.set("id", self._id)
        tl.set("type", str(self._type.value))
        tl.set("programID", str(self._program_id))
        tl.set("offset", str(int(self._offset)))
        for phase in self._phases:
            tl.append(ET.fromstring(phase.to_xml()))
        return ET.tostring(tl)

    # def update_state(self, old_idx: int, new_idx: int, new_state: SumoSignalState):
    #

    def __str__(self):
        return str(self.toXML())

    def __repr__(self):
        return str(self)


class TLS:
    """Traffic Light Signal, managing TLSPrograms for SUMO"""

    def __init__(self):
        self._connections: List[Connection] = []
        self._maxConnectionNo = -1
        self._programs: Dict[str, Dict[str, TLSProgram]] = defaultdict(dict)

    def addConnection(self, connection: Connection):
        self._connections.append(connection)

    def getConnections(self) -> List[Connection]:
        return self._connections

    def getPrograms(self) -> Dict[str, Dict[str, TLSProgram]]:
        return self._programs

    def addProgram(self, program: TLSProgram):
        self._programs[program._id][program._program_id] = program

    def removePrograms(self):
        self._programs.clear()

    def toXML(self) -> bytes:
        tl = ET.Element("tlLogics")
        for programs in self._programs.values():
            for program in programs.values():
                tl.append(ET.fromstring(program.toXML()))
        for c in self._connections:
            conn = ET.fromstring(c.toXML())
            tl.append(conn)
        return ET.tostring(tl)

    def __str__(self):
        return str(self.toXML())

    def __repr__(self):
        return str(self)
