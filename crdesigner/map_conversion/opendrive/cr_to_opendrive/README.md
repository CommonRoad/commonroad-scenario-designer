# Conversion from CommonRoad to OpenDRIVE

Usage:

```python
    scenario_name = "DEU_Test-1_1_T-1"

    file_path_in = f"scenarios/{scenario_name}.xml"  # relative path for input
    file_path_out = f"maps/converted/{scenario_name}.xodr"  # relative path for output

    # load the xml file and preprocess it
    data = DataLoader(file_path_in)

    scenario, successors, ids = data.initialize()
    converter = Converter(file_path_in, scenario, successors, ids)
    converter.convert(file_path_out)
```



The DataLoader class also has to option to zero zenter all input coordinates
```python
    data = DataLoader(file_path_in, center=True)
```
Use with caution!

The Converter class implements a convert() function which processes the input
map. The high-level overview looks like this:
```python
    def convert(self, file_path_out):
        # initialize writer object - this will later dump the converted map
        # into an OpenDRIVE map (<file_path_out>.xodr)
        self.writer = fwr.Writer(file_path_out)

        laneList = self.lane_net.lanelets
        # choose lanelet as starting point
        lanelet = copy.deepcopy(laneList[0])

        # this function constructs all roads 
        # using a breadth first search approach
        self.constructRoads([lanelet.lanelet_id])

        # double check that no lanelet was missed
        self.checkAllVisited()

        # These functions are responsible for road as well as junction linkage
        self.processLinkMap(Road.linkMap, Road.lane2lanelink)
        self.createLinkages(Road.linkMap, Road.lane2lanelink)
        self.constructJunctions()
        self.addJunctionLinkage(Road.linkMap)

        # Obstacles, traffic signs and traffic lights conversion
        self.constructObstacles()
        self.populateTrafficElements(Road.crIdToOD)
        self.constructTrafficElements()

        # This function cleans up the converter object
        # which makes it possible to convert multiple files queued up
        # Take a look at run.sh, this script will execute main.py
        # and afterwards will open the converted maps with
        # the opendrive2lanelet-gui tool
        self.finalize()
```

For future work on the converter:
1. Have a look how roads are generated (road.py)
2. Have a look how junctions are generated (junction.py)
3. Read CommonRoad and OpenDRIVE specifications if needed
4. To understand the linkage look into the Road.linkMap object (converter.py)
5. Keep writing tests for your code (test_converter.py)
