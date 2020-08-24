#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os

setup_dir = os.path.dirname(os.path.realpath(__file__))
with open(f"{setup_dir}/README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="commonroad-map-converter",
    version="1.1.0",
    description="Convert maps to CommonRoad format",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Technical University of Munich",
    author_email="commonroad-i06@in.tum.de",
    url="https://commonroad.in.tum.de/",
    license="GNU General Public License v3.0",
    packages=find_packages(exclude=("test", )),
    include_package_data=True,
    install_requires=[
        "numpy>=1.16.4",
        "lxml>=4.3.4",
        "commonroad-io>=2020.2",
        "pyproj>=2.2.0",
        "scipy>=1.3.0",
        "Pillow >= 7.1.1",
        "mercantile >= 1.1.3",
        "utm >= 0.5.0",
        # TODO: This dependency is required for this package but fails to build on the CI server
        # therefore it is commented out for now
        # "cartopy >= 0.17.0",

        # only for graphical display
        "PyQt5>=5.12.2",
        "matplotlib>=3.1.0",
    ],
    extras_require={"GUI": ["matplotlib>=3.1.0"]},
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "opendrive2lanelet-convert=crmapconverter.io.opendrive_convert:main",
            "osm-convert=crmapconverter.io.osm_convert:main",
            "cr-designer=crmapconverter.io.scenario_designer.main_cr_designer:main"
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
