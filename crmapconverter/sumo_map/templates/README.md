# Template files

# `default.sumo.cfg`
This file contains the default SUMO Simulation configuration template.
Specific file paths are overwirtten in `converter.py`.

# `*.typ.xml`

SUMO edge type files for each country. These files describe the
specific `speed limits`, `lane priorities` and `allowed / disallowed`
SUMO vehicle classes which can access the lane types in the `type`
attribute.

Only the country codes with template files in this folder are valid
in the conversion. For all others the fallback file `DEU.typ.xml` will be used.

For more information see: [SUMO Edge Type File Docs](https://sumo.dlr.de/docs/SUMO_edge_type_file.html)
