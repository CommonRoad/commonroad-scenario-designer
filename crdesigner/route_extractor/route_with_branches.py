#!/usr/bin/env python3
"""
Route with Branches Network Extractor

Extracts a SUMO network that includes:
1. The main route from a KML file
2. All branching roads connected to the main route (for traffic simulation)

This allows vehicles to enter/exit the main route from side streets during simulation.

Usage:
    python route_with_branches.py --net input.net.xml --kml route.kml --output output.net.xml
    python route_with_branches.py --net ../Converter/SUMO/aa.net.xml --kml Google_KML_maps/Gandy2Herbana.kml --output Extracted_routes/test.net.xml

Options:
    --branch-depth N    How many levels of branches to include (default: 1)
                        1 = only roads directly connected to main route
                        2 = roads connected to those branches, etc.
    --radius M          Search radius in meters for finding edges (default: 100)
"""

import argparse
import os
import subprocess
import sys
import shutil
import tempfile
import xml.etree.ElementTree as ET
from collections import deque

try:
    import sumolib
    from fastkml import kml
    from pygeoif.geometry import LineString
except ImportError as e:
    print(f"Error: Missing required package: {e}")
    print("Install with: pip install sumolib fastkml pygeoif")
    sys.exit(1)

# Vehicle classes not recognized by older SUMO versions
UNKNOWN_VEHICLE_CLASSES = {'container', 'cable_car', 'subway', 'aircraft', 'wheelchair', 'scooter', 'drone'}


def extract_route_from_kml(kml_path: str) -> list[tuple[float, float]]:
    """Extract lon/lat coordinates from all KML LineStrings."""
    k = kml.KML.parse(kml_path)
    route_lonlat = []

    def extract_linestrings(feature):
        if hasattr(feature, 'geometry') and feature.geometry is not None:
            geom = feature.geometry
            if isinstance(geom, LineString):
                for coord in geom.coords:
                    lon, lat = coord[0], coord[1]
                    route_lonlat.append((lon, lat))
        if hasattr(feature, 'features'):
            for sub in feature.features:
                extract_linestrings(sub)

    extract_linestrings(k)
    return route_lonlat


def find_main_route_edges(net, route_lonlat: list[tuple[float, float]], search_radius: float = 50.0) -> list[str]:
    """Find SUMO edges along the route coordinates and fill gaps using shortest path."""
    route_xy = [net.convertLonLat2XY(lon, lat) for lon, lat in route_lonlat]

    # First pass: find edges directly under KML coordinates
    initial_edges = []
    seen_edges = set()

    for x, y in route_xy:
        neighbors = net.getNeighboringEdges(x, y, search_radius)
        if neighbors:
            neighbors = sorted(neighbors, key=lambda e: e[1])
            closest_edge = neighbors[0][0]
            edge_id = closest_edge.getID()
            if edge_id not in seen_edges:
                initial_edges.append(edge_id)
                seen_edges.add(edge_id)

    if len(initial_edges) < 2:
        return initial_edges

    # Second pass: fill gaps using shortest path
    print(f"    Initial edges: {len(initial_edges)}, connecting gaps...")
    final_edges = []
    final_seen = set()

    for i, edge_id in enumerate(initial_edges):
        if edge_id not in final_seen:
            final_edges.append(edge_id)
            final_seen.add(edge_id)

        if i < len(initial_edges) - 1:
            curr_edge = net.getEdge(edge_id)
            next_edge_id = initial_edges[i + 1]
            next_edge = net.getEdge(next_edge_id)

            if curr_edge.getToNode().getID() != next_edge.getFromNode().getID():
                try:
                    path_edges, _ = net.getShortestPath(curr_edge, next_edge, vClass="passenger")
                    if path_edges and len(path_edges) > 1:
                        for path_edge in path_edges[1:]:
                            pid = path_edge.getID()
                            if pid not in final_seen:
                                final_edges.append(pid)
                                final_seen.add(pid)
                except Exception:
                    pass

    print(f"    After gap filling: {len(final_edges)} edges")
    return final_edges


def find_branch_edges(net, main_route_edges: set[str], branch_depth: int = 1) -> set[str]:
    """
    Find all edges that branch off from the main route.

    Args:
        net: SUMO network
        main_route_edges: Set of edge IDs on the main route
        branch_depth: How many levels of branches to include
                     1 = edges directly connected to main route nodes
                     2 = edges connected to those, etc.

    Returns:
        Set of all branch edge IDs (including main route edges)
    """
    all_edges = set(main_route_edges)

    # Collect all nodes on the main route
    main_route_nodes = set()
    for edge_id in main_route_edges:
        try:
            edge = net.getEdge(edge_id)
            main_route_nodes.add(edge.getFromNode().getID())
            main_route_nodes.add(edge.getToNode().getID())
        except Exception:
            continue

    print(f"    Main route has {len(main_route_nodes)} nodes")

    # BFS to find branches up to specified depth
    current_frontier_nodes = main_route_nodes.copy()

    for depth in range(branch_depth):
        next_frontier_nodes = set()
        new_edges_at_depth = set()

        for node_id in current_frontier_nodes:
            try:
                node = net.getNode(node_id)
            except Exception:
                continue

            # Get all incoming edges to this node
            for edge in node.getIncoming():
                edge_id = edge.getID()
                if edge_id not in all_edges:
                    new_edges_at_depth.add(edge_id)
                    # Add the from-node for next iteration
                    next_frontier_nodes.add(edge.getFromNode().getID())

            # Get all outgoing edges from this node
            for edge in node.getOutgoing():
                edge_id = edge.getID()
                if edge_id not in all_edges:
                    new_edges_at_depth.add(edge_id)
                    # Add the to-node for next iteration
                    next_frontier_nodes.add(edge.getToNode().getID())

        print(f"    Depth {depth + 1}: found {len(new_edges_at_depth)} new branch edges")
        all_edges.update(new_edges_at_depth)
        current_frontier_nodes = next_frontier_nodes - main_route_nodes  # Don't re-explore main route nodes

    return all_edges


def strip_unknown_vehicle_classes(xml_file: str) -> None:
    """Remove unknown vehicle classes from allow/disallow attributes."""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    modified = False

    for elem in root.iter():
        for attr in ['allow', 'disallow']:
            if attr in elem.attrib:
                classes = elem.attrib[attr].split()
                filtered = [c for c in classes if c not in UNKNOWN_VEHICLE_CLASSES]
                if len(filtered) != len(classes):
                    elem.attrib[attr] = ' '.join(filtered)
                    modified = True

    if modified:
        tree.write(xml_file, encoding="UTF-8", xml_declaration=True)


def convert_to_plain_xml(net_file: str, output_dir: str, base_name: str = "network") -> dict[str, str]:
    """Convert SUMO net.xml to plain XML files using netconvert."""
    os.makedirs(output_dir, exist_ok=True)

    plain_files = {
        'nod': os.path.join(output_dir, f"{base_name}.nod.xml"),
        'edg': os.path.join(output_dir, f"{base_name}.edg.xml"),
        'con': os.path.join(output_dir, f"{base_name}.con.xml"),
        'tll': os.path.join(output_dir, f"{base_name}.tll.xml"),
        'typ': os.path.join(output_dir, f"{base_name}.typ.xml"),
    }

    cmd = [
        'netconvert',
        '--sumo-net-file', net_file,
        '--plain-output-prefix', os.path.join(output_dir, base_name),
        '--ignore-errors'
    ]

    subprocess.run(cmd, capture_output=True, text=True)

    missing = [k for k, v in plain_files.items() if not os.path.exists(v)]
    if missing:
        print(f"Error: Missing plain XML files: {missing}")
        sys.exit(1)

    for f in plain_files.values():
        strip_unknown_vehicle_classes(f)

    return plain_files


def filter_plain_xml(plain_files: dict[str, str], route_edges: set[str], output_dir: str) -> dict[str, str]:
    """Filter plain XML files to keep only route-related elements."""
    os.makedirs(output_dir, exist_ok=True)
    filtered_files = {}

    # 1. Filter edges and collect needed nodes
    edg_tree = ET.parse(plain_files['edg'])
    edg_root = edg_tree.getroot()

    needed_nodes = set()
    edges_to_remove = []

    for edge in edg_root.findall("edge"):
        edge_id = edge.get("id")
        if edge_id not in route_edges:
            edges_to_remove.append(edge)
        else:
            from_node = edge.get("from")
            to_node = edge.get("to")
            if from_node:
                needed_nodes.add(from_node)
            if to_node:
                needed_nodes.add(to_node)

    for edge in edges_to_remove:
        edg_root.remove(edge)

    # Filter roundabouts - keep only if all edges are in our set
    for roundabout in list(edg_root.findall("roundabout")):
        edges_attr = roundabout.get("edges", "")
        roundabout_edges = edges_attr.split() if edges_attr else []
        if not all(e in route_edges for e in roundabout_edges):
            edg_root.remove(roundabout)

    filtered_files['edg'] = os.path.join(output_dir, os.path.basename(plain_files['edg']))
    edg_tree.write(filtered_files['edg'], encoding="UTF-8", xml_declaration=True)

    # 2. Filter nodes
    nod_tree = ET.parse(plain_files['nod'])
    nod_root = nod_tree.getroot()

    for node in list(nod_root.findall("node")):
        if node.get("id") not in needed_nodes:
            nod_root.remove(node)

    filtered_files['nod'] = os.path.join(output_dir, os.path.basename(plain_files['nod']))
    nod_tree.write(filtered_files['nod'], encoding="UTF-8", xml_declaration=True)

    # 3. Filter connections
    con_tree = ET.parse(plain_files['con'])
    con_root = con_tree.getroot()

    for con in list(con_root.findall("connection")):
        if con.get("from") not in route_edges or con.get("to") not in route_edges:
            con_root.remove(con)

    filtered_files['con'] = os.path.join(output_dir, os.path.basename(plain_files['con']))
    con_tree.write(filtered_files['con'], encoding="UTF-8", xml_declaration=True)

    # 4. Filter traffic lights
    tll_tree = ET.parse(plain_files['tll'])
    tll_root = tll_tree.getroot()

    for tll in list(tll_root.findall("tlLogic")):
        if tll.get("id") not in needed_nodes:
            tll_root.remove(tll)

    for con in list(tll_root.findall("connection")):
        if con.get("from") not in route_edges or con.get("to") not in route_edges:
            tll_root.remove(con)

    filtered_files['tll'] = os.path.join(output_dir, os.path.basename(plain_files['tll']))
    tll_tree.write(filtered_files['tll'], encoding="UTF-8", xml_declaration=True)

    # 5. Copy type file
    typ_tree = ET.parse(plain_files['typ'])
    filtered_files['typ'] = os.path.join(output_dir, os.path.basename(plain_files['typ']))
    typ_tree.write(filtered_files['typ'], encoding="UTF-8", xml_declaration=True)

    return filtered_files


def rebuild_network(filtered_files: dict[str, str], output_file: str) -> None:
    """Rebuild SUMO network from filtered plain XML files."""
    cmd = [
        'netconvert',
        '--node-files', filtered_files['nod'],
        '--edge-files', filtered_files['edg'],
        '--connection-files', filtered_files['con'],
        '--tllogic-files', filtered_files['tll'],
        '--type-files', filtered_files['typ'],
        '--ignore-errors',
        '-o', output_file
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if not os.path.exists(output_file):
        print(f"Error: Failed to create SUMO network: {result.stderr}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Extract SUMO network with main route + branching roads for simulation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --net ../Converter/SUMO/aa.net.xml --kml Google_KML_maps/Gandy2Herbana.kml -o Extracted_routes/test.net.xml
  %(prog)s --net map.net.xml --kml route.kml -o output.net.xml --branch-depth 2

The --branch-depth option controls how many levels of side roads to include:
  1 (default): Only roads directly connected to the main route
  2: Roads connected to those branches as well
  etc.
        """
    )
    parser.add_argument('--net', '-n', required=True,
                        help='Input SUMO network file (.net.xml)')
    parser.add_argument('--kml', '-k', required=True,
                        help='Google Maps KML file with route')
    parser.add_argument('--output', '-o', required=True,
                        help='Output SUMO network file (.net.xml)')
    parser.add_argument('--radius', '-r', type=float, default=100.0,
                        help='Search radius in meters for edge detection (default: 100)')
    parser.add_argument('--branch-depth', '-d', type=int, default=1,
                        help='Depth of branching roads to include (default: 1)')

    args = parser.parse_args()

    # Validate inputs
    if not os.path.exists(args.net):
        print(f"Error: Network file not found: {args.net}")
        sys.exit(1)
    if not os.path.exists(args.kml):
        print(f"Error: KML file not found: {args.kml}")
        sys.exit(1)

    # Create output directory if needed
    output_dir = os.path.dirname(os.path.abspath(args.output))
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    temp_dir = tempfile.mkdtemp(prefix="route_branches_")

    try:
        print("\n" + "="*60)
        print("ROUTE WITH BRANCHES NETWORK EXTRACTOR")
        print("="*60)

        # Step 1: Load network and extract route
        print(f"\n[1/4] Loading network: {args.net}")
        net = sumolib.net.readNet(args.net)
        total_edges = len(net.getEdges())
        print(f"      Total edges in network: {total_edges}")

        print(f"\n[2/4] Extracting route from: {args.kml}")
        route_lonlat = extract_route_from_kml(args.kml)
        print(f"      Found {len(route_lonlat)} coordinate points")

        print(f"\n[3/4] Finding edges (radius: {args.radius}m, branch-depth: {args.branch_depth})")

        # Find main route edges
        print("  Finding main route edges...")
        main_route_edges = find_main_route_edges(net, route_lonlat, args.radius)
        print(f"    Main route: {len(main_route_edges)} edges")

        if not main_route_edges:
            print("Error: No edges found on main route. Try increasing --radius")
            sys.exit(1)

        # Find branch edges
        print("  Finding branch edges...")
        all_edges = find_branch_edges(net, set(main_route_edges), args.branch_depth)
        print(f"    Total edges (with branches): {len(all_edges)}")

        # Step 2: Filter and rebuild network
        print(f"\n[4/4] Building filtered network...")

        print("  Converting to plain XML...")
        plain_dir = os.path.join(temp_dir, "plain")
        plain_files = convert_to_plain_xml(args.net, plain_dir, "network")

        print("  Filtering network elements...")
        filtered_dir = os.path.join(temp_dir, "filtered")
        filtered_files = filter_plain_xml(plain_files, all_edges, filtered_dir)

        print("  Rebuilding network...")
        rebuild_network(filtered_files, args.output)

        output_size = os.path.getsize(args.output) / 1024

        # Summary
        print("\n" + "="*60)
        print("COMPLETE")
        print("="*60)
        print(f"  Input network:  {total_edges} edges")
        print(f"  Main route:     {len(main_route_edges)} edges")
        print(f"  With branches:  {len(all_edges)} edges")
        print(f"  Output file:    {args.output} ({output_size:.1f} KB)")
        print(f"\nThe extracted network includes the main route plus")
        print(f"{args.branch_depth} level(s) of branching roads for traffic simulation.")

    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    main()
