#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os

setup_dir = os.path.dirname(os.path.realpath(__file__))
with open(f"{setup_dir}/README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="opendrive2lanelet",
    version="1.2.0",
    description="Parser and converter from OpenDRIVE to lanelets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Technical University of Munich",
    author_email="commonroad-i06@in.tum.de",
    url="https://commonroad.in.tum.de/",
    license="GNU General Public License v3.0",
    packages=find_packages(exclude=("test",)),
    include_package_data=True,
    install_requires=[
        "numpy>=1.16.4",
        "lxml>=4.3.4",
        "commonroad-io>=2020.2",
        "pyproj>=2.2.0",
        "scipy>=1.3.0",
    ],
    extras_require={"GUI": ["PyQt5>=5.12.2", "matplotlib>=3.1.0"]},
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "opendrive2lanelet-convert=opendrive2lanelet.io.opendrive_convert:main",
            "opendrive2lanelet-gui=opendrive2lanelet.io.gui:main",
            "opendrive2lanelet-visualize=opendrive2lanelet.io.visualize_commonroad:main",
            "osm-convert=opendrive2lanelet.io.osm_convert:main",
        ]
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Operating System :: Unix",
    ],
)
