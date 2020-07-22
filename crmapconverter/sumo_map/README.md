# Map conversions between CommonRoad and SUMO's .net.xml

## Installation

1. Activate your python environment (Version 3.6 or 3.7):

   ```bash
   conda activate commonroad
   ```

2. Install the python requirements at the root of the project

   ```bash
   pip install -r requirements.txt
   ```

3. Install our patched SUMO Version form [here](https://github.com/octavdragoi/sumo).
   Step by step:

   ```bash
   # install system requirements (ubuntu)
   sudo apt-get install ffmpeg
   # Install SUMO
   git clone https://github.com/octavdragoi/sumo
   cd sumo
   git checkout smooth-lane-change
   sudo apt-get install cmake python g++ libxerces-c-dev libfox-1.6-dev libgdal-dev libproj-dev libgl2ps-dev swig
   export SUMO_HOME="$(pwd)"
   echo "export SUMO_HOME=$(pwd)" >> ~/.bashrc
   cd build
   cmake ..
   make -j8 # this will take some time
   cd $HOME
   ```

   **OR** if you don't want the smooth lane change istall the stable version of [SUMO](https://sumo.dlr.de/docs/Installing.html):

   ```bash
   sudo add-apt-repository ppa:sumo/stable
   sudo apt-get update
   sudo apt-get install sumo sumo-tools sumo-doc
   export SUMO_HOME="/usr/share/sumo"
   # add $SUMO_HOME to .bashrc (change if you're not using bash)
   echo "export SUMO_HOME=/usr/share/sumo" >> ~/.bashrc
   cd $HOME
   ```

4. Install the commonroad-collision-checker from [here](https://gitlab.lrz.de/tum-cps/commonroad-collision-checker):

   Install [libccd](https://github.com/danfis/libccd) (from master branch):

   ```bash
   # install dependencies
   git clone git@github.com:danfis/libccd.git
   cd libccd
   mkdir build && cd build
   cmake -G "Unix Makefiles" -DENABLE_DOUBLE_PRECISION=ON -DBUILD_SHARED_LIBS=ON ..
   make
   sudo make install
   cd $HOME
   ```

   Install [FCL -- The Flexible Collision Library](https://github.com/flexible-collision-library/fcl) (from master branch):

   ```bash
   git clone git@github.com:flexible-collision-library/fcl.git
   cd fcl
   sudo apt-get install libboost-dev libboost-thread-dev libboost-test-dev libboost-filesystem-dev libeigen3-dev
   # build FCL
   mkdir build && cd build
   cmake ..
   make
   sudo make install
   ```

   Install the [commonroad-collision-checker](https://gitlab.lrz.de/tum-cps/commonroad-collision-checker):

   ```bash
   git clone git@gitlab.lrz.de:tum-cps/commonroad-collision-checker.git
   cd commonroad-collision-checker/
   mkdir build
   cd build
   cmake -DADD_PYTHON_BINDINGS=TRUE -DPATH_TO_PYTHON_ENVIRONMENT="/path/to/your/anaconda3/envs/ commonroad-py37" -DPYTHON_VERSION="3.7" -DCMAKE_BUILD_TYPE=Release ..
   make -j8

   # Install pyrcc
   cd ..
   python setup.py install
   cd $HOME
   ```

5. Install [cartopy](https://scitools.org.uk/cartopy/docs/latest/installing.html):

   ```bash
   conda install -c conda-forge cartopy
   ```

# Getting started

Run the example file to convert a commonroad `.xml` file to sumo, simulate on traffic on it and save the result to disk:

```bash
git clone git@gitlab.lrz.de:cps/commonroad-map-tool.git
cd commonroad-map-tool
# install the requirements
pip install -r requirements.txt
# add the current module to the python path
export $PYTHONPATH="$PYTHONPATH:$(pwd)"
python crmapconverter/sumo_map/example.py
```
