#!/bin/bash
# Example: Extract route from SUMO network and convert to Lanelet2
# Run from commonroad-scenario-designer root: bash crdesigner/route_extractor/run_example.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$ROOT_DIR"

python -m crdesigner.route_extractor.full_pipeline \
  --net crdesigner/route_extractor/sample_data/aa.net.xml \
  --kml crdesigner/route_extractor/sample_data/Zinger2Sigma.kml \
  --output-dir map_conversion_output/zinger2sigma \
  --name zinger2sigma \
  --branch-depth 1
