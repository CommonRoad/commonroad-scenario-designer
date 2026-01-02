#!/usr/bin/env python3
"""
SUMO Network Format Converter

Converts a SUMO network (.net.xml) to:
1. OpenDRIVE format (.xodr)
2. Lanelet2 format (.osm)

Usage:
    python convert_formats.py --input network.net.xml --output-prefix output_name
    python convert_formats.py --input Extracted_routes/gandy2herbana_with_branches.net.xml --output-prefix Extracted_routes/gandy2herbana

This will generate:
    - output_name.xodr (OpenDRIVE)
    - output_name_lanelet2.osm (Lanelet2)
"""

import argparse
import os
import subprocess
import sys

# Path to crdesigner conda environment's Python
CRDESIGNER_PYTHON = "/home/haotian/miniconda3/envs/crdesigner/bin/python"


def convert_sumo_to_opendrive(input_file: str, output_file: str) -> None:
    """Convert SUMO network to OpenDRIVE format."""
    cmd = [
        'netconvert',
        '--sumo-net-file', input_file,
        '--opendrive-output', output_file,
        '--verbose', 'false'
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if not os.path.exists(output_file):
        print(f"Error: Failed to create OpenDRIVE file: {result.stderr}")
        sys.exit(1)


def convert_opendrive_to_lanelet2(input_file: str, output_file: str) -> None:
    """Convert OpenDRIVE to Lanelet2 format using crdesigner.

    Calls xodr_to_osm.py script within the crdesigner conda environment.
    """
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    xodr_to_osm_script = os.path.join(script_dir, "xodr_to_osm.py")

    if not os.path.exists(xodr_to_osm_script):
        print(f"Error: xodr_to_osm.py not found at {xodr_to_osm_script}")
        sys.exit(1)

    # Run the conversion script using crdesigner's Python
    result = subprocess.run(
        [CRDESIGNER_PYTHON, xodr_to_osm_script, '--input', input_file, '--output', output_file],
        capture_output=True,
        text=True
    )

    # Print stdout to see debug messages
    if result.stdout:
        print(result.stdout)

    if not os.path.exists(output_file):
        print(f"Error: Failed to create Lanelet2 file: {result.stderr}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Convert SUMO network to OpenDRIVE and Lanelet2 formats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --input network.net.xml --output-prefix output
  %(prog)s -i Extracted_routes/gandy2herbana_with_branches.net.xml -o Extracted_routes/gandy2herbana
  %(prog)s -i network.net.xml -o output --skip-lanelet2

Output files:
  <prefix>.xodr          - OpenDRIVE format
  <prefix>_lanelet2.osm  - Lanelet2 format
        """
    )
    parser.add_argument('--input', '-i', required=True,
                        help='Input SUMO network file (.net.xml)')
    parser.add_argument('--output-prefix', '-o', required=True,
                        help='Output file prefix (without extension)')
    parser.add_argument('--skip-lanelet2', action='store_true',
                        help='Skip Lanelet2 conversion (if crdesigner not available)')
    parser.add_argument('--skip-xodr', action='store_true',
                        help='Skip OpenDRIVE conversion')

    args = parser.parse_args()

    # Validate inputs
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    # Check crdesigner if needed
    if not args.skip_lanelet2 and not os.path.exists(CRDESIGNER_PYTHON):
        print(f"Warning: crdesigner not found at {CRDESIGNER_PYTHON}")
        print("Use --skip-lanelet2 to skip Lanelet2 conversion")
        sys.exit(1)

    # Output files
    output_xodr = f"{args.output_prefix}.xodr"
    output_lanelet2 = f"{args.output_prefix}_lanelet2.osm"

    # Create output directory
    output_dir = os.path.dirname(os.path.abspath(args.output_prefix))
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    print("\n" + "="*60)
    print("SUMO NETWORK FORMAT CONVERTER")
    print("="*60)
    print(f"  Input: {args.input}")

    # Step 1: Convert to OpenDRIVE
    if not args.skip_xodr:
        print("\n[1/2] Converting to OpenDRIVE...")
        convert_sumo_to_opendrive(args.input, output_xodr)
        xodr_size = os.path.getsize(output_xodr) / 1024
        print(f"      -> {output_xodr} ({xodr_size:.1f} KB)")
    else:
        print("\n[1/2] Skipping OpenDRIVE conversion")

    # Step 2: Convert to Lanelet2
    if not args.skip_lanelet2:
        if args.skip_xodr:
            # Need xodr for lanelet2 conversion
            print("\n[2/2] Converting to Lanelet2 (generating temp xodr first)...")
            temp_xodr = f"{args.output_prefix}_temp.xodr"
            convert_sumo_to_opendrive(args.input, temp_xodr)
            convert_opendrive_to_lanelet2(temp_xodr, output_lanelet2)
            os.remove(temp_xodr)
        else:
            print("\n[2/2] Converting to Lanelet2...")
            convert_opendrive_to_lanelet2(output_xodr, output_lanelet2)
        lanelet_size = os.path.getsize(output_lanelet2) / 1024
        print(f"      -> {output_lanelet2} ({lanelet_size:.1f} KB)")
    else:
        print("\n[2/2] Skipping Lanelet2 conversion")

    # Summary
    print("\n" + "="*60)
    print("COMPLETE")
    print("="*60)
    if not args.skip_xodr:
        print(f"  OpenDRIVE: {output_xodr}")
    if not args.skip_lanelet2:
        print(f"  Lanelet2:  {output_lanelet2}")


if __name__ == "__main__":
    main()
