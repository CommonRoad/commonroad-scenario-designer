from pathlib import Path

from crdesigner.map_conversion.map_conversion_interface import commonroad_to_opendrive

input_path = Path.cwd().parent.parent / "tests/map_conversion/test_maps/cr2odr/ZAM_Over-1_1.xml"
output_name = Path.cwd() / "example_files/opendrive/ZAM_Over-1_1.odr"

if not (Path.cwd() / "example_files/opendrive").exists():
    (Path.cwd() / "example_files/opendrive").mkdir(parents=True, exist_ok=True)

commonroad_to_opendrive(input_path, output_name)
