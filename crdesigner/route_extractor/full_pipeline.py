#!/usr/bin/env python3
"""
Full Pipeline: KML Route Extraction + Format Conversion

This script combines the complete workflow:
1. Extract SUMO network along KML route with branching roads
2. Convert to OpenDRIVE (.xodr)
3. Convert to Lanelet2 (.osm) for Autoware
4. Generate map_projector_info.yaml for Autoware

Usage:
    python -m crdesigner.route_extractor.full_pipeline \
        --net network.net.xml \
        --kml route.kml \
        --output-dir output/my_route \
        --name my_route

Options:
    --branch-depth N    Levels of branching roads to include (default: 1)
    --radius M          Search radius in meters for edge detection (default: 100)
    --skip-lanelet2     Skip Lanelet2 conversion
"""

import argparse
import os
import sys
import subprocess
import re
import hashlib

# Get script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def sanitize_opendrive(xodr_file: str) -> str:
    """Sanitize OpenDRIVE file for crdesigner compatibility.

    - Converts non-numeric IDs to numeric hashes for signals/junctions
    """
    with open(xodr_file, 'r') as f:
        content = f.read()

    # Fix non-numeric IDs
    def replace_id(match):
        full_match = match.group(0)
        id_value = match.group(1)
        if id_value.lstrip('-').isdigit():
            return full_match
        hash_val = int(hashlib.md5(id_value.encode()).hexdigest()[:8], 16)
        return full_match.replace(f'id="{id_value}"', f'id="{hash_val}"')

    content = re.sub(r'<signal[^>]*id="([^"]+)"', replace_id, content)
    content = re.sub(r'<signalReference[^>]*id="([^"]+)"', replace_id, content)
    content = re.sub(r'<junction[^>]*id="([^"]+)"', replace_id, content)

    sanitized_file = xodr_file.replace('.xodr', '_sanitized.xodr')
    with open(sanitized_file, 'w') as f:
        f.write(content)

    return sanitized_file


def run_route_extraction(net_file: str, kml_file: str, output_file: str,
                         branch_depth: int = 1, radius: float = 100.0) -> bool:
    """Run route_with_branches.py to extract SUMO network."""
    script = os.path.join(SCRIPT_DIR, "route_with_branches.py")

    cmd = [
        sys.executable, script,
        '--net', net_file,
        '--kml', kml_file,
        '--output', output_file,
        '--branch-depth', str(branch_depth),
        '--radius', str(radius)
    ]

    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0 and os.path.exists(output_file)


def run_sumo_to_opendrive(input_file: str, output_file: str) -> bool:
    """Convert SUMO network to OpenDRIVE using netconvert."""
    cmd = [
        'netconvert',
        '--sumo-net-file', input_file,
        '--opendrive-output', output_file,
        '--verbose', 'false'
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return os.path.exists(output_file)


def run_opendrive_to_lanelet2(input_file: str, output_file: str) -> bool:
    """Convert OpenDRIVE to Lanelet2 using crdesigner API directly."""
    try:
        from crdesigner.map_conversion.map_conversion_interface import opendrive_to_lanelet

        # Sanitize OpenDRIVE file (fix non-numeric IDs from SUMO)
        sanitized_file = sanitize_opendrive(input_file)

        # Convert
        opendrive_to_lanelet(sanitized_file, output_file)

        # Cleanup sanitized file
        if os.path.exists(sanitized_file):
            os.remove(sanitized_file)

        return os.path.exists(output_file)
    except Exception as e:
        print(f"  Error during Lanelet2 conversion: {e}")
        return False


def get_first_coordinate(osm_file: str) -> tuple:
    """Extract first lat/lon from OSM file for map_projector_info.yaml."""
    with open(osm_file, 'r') as f:
        content = f.read()

    # Find first node with lat/lon
    match = re.search(r'lat="([^"]+)"\s+lon="([^"]+)"', content)
    if match:
        return float(match.group(1)), float(match.group(2))
    return None, None


def create_map_projector_info(output_dir: str, lat: float, lon: float) -> str:
    """Create map_projector_info.yaml for Autoware."""
    yaml_content = f"""projector_type: LocalCartesianUTM
vertical_datum: WGS84
map_origin:
  latitude: {lat}
  longitude: {lon}
  altitude: 0.0
"""
    yaml_file = os.path.join(output_dir, "map_projector_info.yaml")
    with open(yaml_file, 'w') as f:
        f.write(yaml_content)
    return yaml_file


def main():
    parser = argparse.ArgumentParser(
        description="Full pipeline: KML route extraction + format conversion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --net network.net.xml --kml route.kml --output-dir output/gandy --name gandy
  %(prog)s -n map.net.xml -k route.kml -o output/test -N test_route --branch-depth 2

Output files:
  <output-dir>/<name>.net.xml           - SUMO network
  <output-dir>/<name>.xodr              - OpenDRIVE
  <output-dir>/<name>_lanelet2.osm      - Lanelet2 for Autoware
  <output-dir>/map_projector_info.yaml  - Autoware projection info
        """
    )
    parser.add_argument('--net', '-n', required=True,
                        help='Input SUMO network file (.net.xml)')
    parser.add_argument('--kml', '-k', required=True,
                        help='Google Maps KML file with route')
    parser.add_argument('--output-dir', '-o', required=True,
                        help='Output directory')
    parser.add_argument('--name', '-N', required=True,
                        help='Base name for output files')
    parser.add_argument('--radius', '-r', type=float, default=100.0,
                        help='Search radius in meters for edge detection (default: 100)')
    parser.add_argument('--branch-depth', '-d', type=int, default=1,
                        help='Depth of branching roads to include (default: 1)')
    parser.add_argument('--skip-lanelet2', action='store_true',
                        help='Skip Lanelet2 conversion')

    args = parser.parse_args()

    # Validate inputs
    if not os.path.exists(args.net):
        print(f"Error: Network file not found: {args.net}")
        sys.exit(1)
    if not os.path.exists(args.kml):
        print(f"Error: KML file not found: {args.kml}")
        sys.exit(1)

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Output file paths
    output_net = os.path.join(args.output_dir, f"{args.name}.net.xml")
    output_xodr = os.path.join(args.output_dir, f"{args.name}.xodr")
    output_osm = os.path.join(args.output_dir, f"{args.name}_lanelet2.osm")

    print("\n" + "=" * 70)
    print("FULL PIPELINE: KML Route Extraction + Format Conversion")
    print("=" * 70)
    print(f"  Input network: {args.net}")
    print(f"  Input KML:     {args.kml}")
    print(f"  Output dir:    {args.output_dir}")
    print(f"  Base name:     {args.name}")
    print(f"  Branch depth:  {args.branch_depth}")

    # Step 1: Extract route with branches
    print("\n" + "-" * 70)
    print("[1/4] Extracting route with branches...")
    print("-" * 70)
    if not run_route_extraction(args.net, args.kml, output_net,
                                 args.branch_depth, args.radius):
        print("Error: Route extraction failed")
        sys.exit(1)
    net_size = os.path.getsize(output_net) / 1024
    print(f"  -> {output_net} ({net_size:.1f} KB)")

    # Step 2: Convert to OpenDRIVE
    print("\n" + "-" * 70)
    print("[2/4] Converting to OpenDRIVE...")
    print("-" * 70)
    if not run_sumo_to_opendrive(output_net, output_xodr):
        print("Error: OpenDRIVE conversion failed")
        sys.exit(1)
    xodr_size = os.path.getsize(output_xodr) / 1024
    print(f"  -> {output_xodr} ({xodr_size:.1f} KB)")

    # Step 3: Convert to Lanelet2
    if not args.skip_lanelet2:
        print("\n" + "-" * 70)
        print("[3/4] Converting to Lanelet2...")
        print("-" * 70)
        if not run_opendrive_to_lanelet2(output_xodr, output_osm):
            print("  Warning: Lanelet2 conversion failed or skipped")
        else:
            osm_size = os.path.getsize(output_osm) / 1024
            print(f"  -> {output_osm} ({osm_size:.1f} KB)")

            # Step 4: Create map_projector_info.yaml
            print("\n" + "-" * 70)
            print("[4/4] Creating Autoware projection info...")
            print("-" * 70)
            lat, lon = get_first_coordinate(output_osm)
            if lat and lon:
                yaml_file = create_map_projector_info(args.output_dir, lat, lon)
                print(f"  -> {yaml_file}")
                print(f"     Origin: ({lat}, {lon})")
            else:
                print("  Warning: Could not extract coordinates for projection info")
    else:
        print("\n[3/4] Skipping Lanelet2 conversion")
        print("[4/4] Skipping Autoware projection info")

    # Summary
    print("\n" + "=" * 70)
    print("COMPLETE")
    print("=" * 70)
    print(f"  SUMO network: {output_net}")
    print(f"  OpenDRIVE:    {output_xodr}")
    if not args.skip_lanelet2 and os.path.exists(output_osm):
        print(f"  Lanelet2:     {output_osm}")
        print(f"  Projection:   {os.path.join(args.output_dir, 'map_projector_info.yaml')}")
    print("\nFor Autoware, copy the entire output directory to your map folder.")


if __name__ == "__main__":
    main()
