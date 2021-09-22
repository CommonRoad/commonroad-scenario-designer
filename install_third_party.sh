#!/bin/bash
# Installs the traffic simulator SUMO, libgeos++-dev, and add all required path variables
# __author__ = "Sebastian Maierhofer"
# __copyright__ = "TUM Cyber-Physical Systems Group"
# __credits__ = ["BMW Car@TUM"]
# __version__ = "0.2"
# __maintainer__ = "Sebastian Maierhofer"
# __email__ = "commonroad@lists.lrz.de"
# __status__ = "Released"
sudo apt-get install sumo sumo-tools sumo-doc
sudo apt-get install libgeos++-dev
echo "export SUMO_HOME=/usr/share/sumo" >> ~/.bashrc
grep -qxF "export SUMO_HOME=/usr/share/sumo" ~/.zshrc || echo "export SUMO_HOME=/usr/share/sumo" >> ~/.zshrc
echo 'export PYTHONPATH="$SUMO_HOME/tools:$PYTHONPATH"' >> ~/.bashrc
grep -qxF 'export PYTHONPATH="$SUMO_HOME/tools:$PYTHONPATH"' ~/.zshrc || echo 'export PYTHONPATH="$SUMO_HOME/tools:$PYTHONPATH"' >> ~/.zshrc