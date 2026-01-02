#!/usr/bin/env python3
"""
OpenDRIVE to Lanelet2 (OSM) Converter

Usage:
    python -m crdesigner.route_extractor.xodr_to_osm --input file.xodr --output file.osm
"""

import argparse
import os
import sys
import re
import hashlib

from crdesigner.map_conversion.map_conversion_interface import opendrive_to_lanelet


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


def main():
    parser = argparse.ArgumentParser(
        description="Convert OpenDRIVE (.xodr) to Lanelet2 (.osm)"
    )
    parser.add_argument('--input', '-i', required=True,
                        help='Input OpenDRIVE file (.xodr)')
    parser.add_argument('--output', '-o', required=True,
                        help='Output Lanelet2 file (.osm)')

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    print(f"Input:  {args.input}")
    print(f"Output: {args.output}")

    # Sanitize the xodr file
    print("Sanitizing OpenDRIVE file...")
    sanitized_file = sanitize_opendrive(args.input)

    # Convert
    print("Converting to Lanelet2...")
    opendrive_to_lanelet(sanitized_file, args.output)

    # Cleanup
    if os.path.exists(sanitized_file):
        os.remove(sanitized_file)

    if os.path.exists(args.output):
        size_kb = os.path.getsize(args.output) / 1024
        print(f"Done! Output: {args.output} ({size_kb:.1f} KB)")
    else:
        print("Error: Conversion failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
