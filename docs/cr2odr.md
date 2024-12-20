# OpenDRIVE to CommonRoad Conversion
This conversion allows you to convert a road network description from
[CommonRoad (Version 2020a) format](https://gitlab.lrz.de/tum-cps/commonroad-scenarios/blob/master/documentation/XML_commonRoad_2020a.pdf)
to the
[OpenDRIVE format](https://www.asam.net/standards/detail/opendrive/).

Since the release of the paper, various updates have been implemented in the code to enhance the converter.

## Usage
The CommonRoad to OpenDRIVE conversion can be used via:

- command line interface
- GUI
- Python API

For the relevant command line commands execute
``crdesigner --help``.
Tutorials on how to use the Python APIs can be found in our
[GitHub repository](https://github.com/CommonRoad/commonroad-scenario-designer/tree/develop/tutorials/conversion_examples).


## Implementation Details
This section details the implementation of the CommonRoad to OpenDRIVE converter.
The conversion process translates each structural element of the CommonRoad representation to its OpenDRIVE equivalent.

### Road Construction

The converter constructs OpenDRIVE roads from a given lanelet network using the following seven-step process:

1. **Initialization**:
A random lanelet is selected as a starting point and added to a lane list.
An empty queue (frontier) of lanelets to be explored and a list of visited lanelets (visited) are initialized.
**Lane Extension**:
The lanelist is extended by adding the right and left adjacent neighbors of the current lanelets.
This process is repeated until no new neighbors are found.
The resulting lanelist contains lanelets from right to left, representing the lanes of the OpenDRIVE road.
These lanelets are added to visited.
3. **Reference Path Location**:
The algorithm iterates through the lanelist from right to left to find the point where the driving direction changes.
The left vertices of the lanelet preceding this change (or the last lanelet if no change occurs) are selected as
the basis for the reference path.
4. **Reference Path Construction**:
The reference path is constructed based on the polyline obtained in the previous step.
The curvature at each point of the polyline is determined. The connection between successive points is then
determined based on the curvature difference:
If the curvature of both points is close to zero, they are connected by a line.
If the curvature difference is below a threshold and both points have non-zero curvature, they are connected by an arc.
Otherwise, they are connected by a spiral (clothoid).
5. **Lane ID Assignment**:
Using the constructed reference path as the center lane, lane IDs are assigned to the lanelets in the lanelist.
6. **Lane Width Definition**:
Lane width is determined by measuring the width at the start and end of the corresponding lanelet and linearly
interpolating between these values. This method avoids potential issues with more complex interpolation methods.
7. **Exploration**:
Predecessors and successors of all lanelets in the lanelist that are not in visited are added to the frontier.
A lanelet is then popped from the frontier, the lanelist is cleared, and the process repeats from step 2
with the new lanelet. The process terminates when the frontier is empty.

This breadth-first search explores the CommonRoad lanelet network.
Each constructed road is assigned a unique ID, and mappings between lanelet and road IDs, and between
lanelets and lane IDs, are stored.

### Junction Conversion

CommonRoad intersections are converted to OpenDRIVE junctions after road construction.
In CommonRoad, intersections are defined by incoming elements containing incoming lanelets and their
successors (successorsRight, successorsStraight, or successorsLeft).
The isLeftOf element helps determine priorities.
OpenDRIVE junctions are defined by incoming and connecting roads.

The conversion process iterates over all incoming elements of the CommonRoad intersection:

Incoming Road ID Collection: Collect the road IDs of all incoming lanelets.
Incoming Road Assignment: Add the collected road IDs to the incoming roads of the OpenDRIVE junction.
Successor Collection: Retrieve all successors of the incoming lanelets.
Connecting Road Assignment: Add the IDs of the successors to the connecting roads of the OpenDRIVE junction.
Lane ID Linking: For each successor, link the lane IDs of its predecessor,
and successor lanelets using the stored mapping.

### Object Incorporation

CommonRoad supports traffic signs, traffic lights, and static/dynamic obstacles.
OpenDRIVE uses the Object class for static objects (including obstacles, crosswalks,
and buildings) and the Signal class for traffic signs and lights.
OpenDRIVE objects can have circular, angular, or more complex shapes defined by outline elements
containing cornerRoad or cornerLocal elements. This implementation uses cornerLocal elements.

The converter maps all CommonRoad object types to their corresponding OpenDRIVE classes. For each object:
The lanelet the object belongs to is mapped to the corresponding OpenDRIVE road ID.
Position and orientation are translated to the road's local coordinate system.
Polygonal obstacles are converted to outline elements.

### Road and Lane Linkage

Correct linkage of generated roads is crucial for simulation.
CommonRoad allows multiple successors and predecessors for lanelets, while OpenDRIVE allows only one
link element per road and connection element in a junction.

To address this, a custom linkMap object is used.
Each entry in linkMap corresponds to a road and contains:
- Lanelet Entries: A dictionary mapping each lanelet's unique ID to its predecessors and successors.
- Lane Indices: A dictionary assigning each lanelet its ID on the current road.
- Merge Linkage: A dictionary merging all successors and predecessors of the current road.

This linkMap facilitates both road-to-road and lane-to-lane linkage.

Road Linkage:
- One-to-one road linkages are implemented using elementType="road".
- One-to-many linkages require the creation of artificial junctions (elementType="junction"),
as OpenDRIVE enforces a maximum of one successor/predecessor element per road.

Lane Linkage: If connected roads have the same reference path direction and number of lanes, linkage is straightforward.
If the reference path directions differ, lane mapping is performed using inverted lane IDs.

### Assumptions
- The input CommonRoad scenario must not be invalid. e.g., self-intersecting polylines.
Otherwise, the converted map might be invalid.

#### Open Issues
- Correct lane width: currently, we assume a constant lane width
- Minor issues OpenDRIVE compliance: we will integrate the ASAM OpenDRIVE checker in the future and improve our code accordingly
