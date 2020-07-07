Usage example
=============

To start a conversion with osm_2_cr run main.py with either of the following arguments:

* **o** **filename** to open a osm file and convert it
* **d** to download a area specified in **config.py**
* **g** to open the GUI

Valid calls would for example be::

	$ python main.py o map.osm

Or::
	
	$ pyton main.py d
	
Or::

	$ python main.py g

In the following there is an example of how the methods in this package can be used without calling **main.py**.
The documentation of the converter file is given in 
This example can be found in **example.py**::
	
	import converter.converter as converter
	import converter.export as ex
	from converter import config
	from converter.donwloader import download_around_map
	
	config.USER_EDIT = False

	# download a map
	download_around_map(config.BENCHMARK_ID + '_downloaded.osm', 48.140289, 11.566272)

	# open the map and convert it to a scenario
	scenario = converter.Scenario(config.SAVE_PATH + config.BENCHMARK_ID + '_downloaded.osm')

	# draw and show the scenario
	scenario.plot()

	# save the scenario as commonroad file
	scenario.save_as_cr()
	# save the scenario as a binary
	scenario.save_to_file(config.SAVE_PATH + config.BENCHMARK_ID + '.pickle')

	# view the generated
	ex.view_xml(config.SAVE_PATH + config.BENCHMARK_ID + '.xml')

This downloads a map of an area defined in **config.py**.
This map is then converted to a scenario in graph structure.
The graph structure is plotted and shown.
Then, it is saved to disk once as a **CommonRoad** file and once as a binary.
Finnaly, the generated **CommonRoad** file is plotted. 