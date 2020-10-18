import crmapconverter.sumo_map.sumolib_net.connection as connection


class TLSProgram:
    def __init__(self, id: str, offset: int, type: str):
        self._id = id
        self._type = type
        self._offset = offset
        self._phases = []

    def addPhase(self, state, duration):
        self._phases.append((state, duration))

    def toXML(self, tlsID):
        ret = '  <tlLogic id="%s" type="%s" programID="%s" offset="%s">\n' % (
            tlsID, self._type, self._id, self._offset)
        for p in self._phases:
            ret = ret + \
                '    <phase duration="%s" state="%s"/>\n' % (p[1], p[0])
        ret = ret + '  </tlLogic>\n'
        return ret

    def getOffset(self) -> int:
        return self._offset

    def getPhases(self):
        return self._phases


class TLS:
    """Traffic Light Signal for a sumo network"""
    def __init__(self, id):
        self._id = id
        self._connections = []
        self._maxConnectionNo = -1
        self._programs = {}

    def addConnection(self, connection: connection.Connection):
        self._connections.append(connection)

    def getConnections(self):
        return self._connections

    def getID(self):
        return self._id

    # def getLinks(self):
    #     links = {}
    #     for connection in self._connections:
    #         if connection[2] not in links:
    #             links[connection[2]] = []
    #         links[connection[2]].append(connection)
    #     return links

    # def getEdges(self):
    #     edges = set()
    #     for c in self._connections:
    #         edges.add(c[0].getEdge())
    #     return edges

    def addProgram(self, program: TLSProgram):
        self._programs[program._id] = program

    def removePrograms(self):
        self._programs.clear()

    def toXML(self):
        ret = "<tlLogics>"
        for program_id, program in self._programs.items():
            ret += program.toXML(self._id)
        for c in self._connections:
            ret += c.toXML()
        return ret + "</tlLogics>"

    def getPrograms(self):
        return self._programs
