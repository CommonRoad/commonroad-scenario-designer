# Elevation correction feature pre-step

## Install `proj` for Linux

We build it from the source because of pip install will gives a mismatch version of `proj`

Download the file

```bash
wget https://download.osgeo.org/proj/proj-9.3.1.tar.gz
```

Unzip it

```bash
tar -xvzf proj-9.3.1.tar.gz
```

```bash
cd proj-9.3.1
```

Build

```bash
sudo apt install build-essential cmake pkg-config sqlite3 libsqlite3-dev
```

```bash
mkdir build && cd build
```

```bash
cmake ..
```

```bash
make -j4
```

```bash
sudo make install
```

```bash
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
```

## Setup elevation file `egm96_15.gtx` for commonroad-scenario-designer

- Attention: All of the context assumes that crd-designer running with poetry virtual enviroment. If not, please check this[https://python-poetry.org/docs/] for infomations.

Go to the code repository.

### Install poetry

Install pipx

```bash
sudo apt update
sudo apt install pipx
pipx ensurepath
```

Install potry

```bash
pipx install poetry==1.8.3
```

Create a new Python poetry virtual environment. DO NOT run poetry with `z-shell`(`zsh`), uses `bash` only.

```bash
poetry shell
poetry install --with tests,docs,tutorials
```

Install `pyproj` for python

```bash
pip install pyproj==3.6.1
```

Here is the version info of the machine that successfully setup.

```zsh
░▒▓ ~/Desktop/commonroad-scenario-designer │ on develop ?2  poetry env info                                                                                                                                            ✔ │ took 8s │ at 16:44:36 ▓▒░

Virtualenv
Python:         3.10.15
Implementation: CPython
Path:           /home/mobilab/Desktop/commonroad-scenario-designer/.venv
Executable:     /home/mobilab/Desktop/commonroad-scenario-designer/.venv/bin/python
Valid:          True

Base
Platform:   linux
OS:         posix
Python:     3.10.15
Path:       /usr
Executable: /usr/bin/python3.10

░▒▓ ~/Desktop/commonroad-scenario-designer │ on develop ?3  poetry about                                                                                                                                                         ✔ │ at 14:35:15 ▓▒░
Poetry - Package Management for Python

Version: 1.8.3
Poetry-Core Version: 1.9.0
```

### Install `egm96_15.gtx` file

```bash
wget https://download.osgeo.org/proj/proj-datumgrid-1.8.tar.gz
tar -xvzf proj-datumgrid-1.8.tar.gz
```

Copy file to portry venv

```bash
cp egm96_15.gtx ~/YOUR_ROOT_TO_CRD_DESIGNER/commonroad-scenario-designer/.venv/lib/python3.10/site-packages/pyproj/proj_dir/share/proj
```
