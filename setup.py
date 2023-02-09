from setuptools import setup, find_packages  # type: ignore
import os

setup_dir = os.path.dirname(os.path.realpath(__file__))
with open(f"{setup_dir}/README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="commonroad-scenario-designer",
    version="0.6.1",
    description="Toolbox for Map Conversion and Scenario Creation for Autonomous Vehicles",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Technical University of Munich",
    author_email="commonroad@lists.lrz.de",
    url="https://commonroad.in.tum.de/",
    license="GNU General Public License v3.0",
    packages=find_packages(exclude=("test", "ci", "files", "docs", "tutorials")),
    include_package_data=True,
    install_requires=[
        "numpy>=1.21.6",
        "lxml>=4.3.4",
        "pyproj>=3.2.1",
        "scipy>=1.3.0",
        "mercantile>=1.1.3",
        "utm>=0.5.0",
        "PyQt5>=5.12.2",
        "matplotlib>=3.5",
        "shapely==1.8.5",
        "sumocr==2023.1",
        "commonroad-io==2022.3",
        "ordered-set>=4.0.2",
        "enum34>=1.1.10",
        "iso3166>=1.0.1",
        "networkx>=2.5",
        "omegaconf>=2.2.2",
        "pyyaml==6.0"
    ],
    extras_require={
        'doc': ['ipython>7.16.0',
                'sphinx>=2.2.1',
                'sphinx-autodoc-typehints>=1.11.0,<1.21.0',
                'sphinx-rtd-theme',
                'sphinxcontrib-apidoc',
                'sphinxcontrib-applehelp',
                'sphinxcontrib-devhelp',
                'sphinxcontrib-htmlhelp',
                'sphinxcontrib-jsmath',
                'sphinxcontrib-napoleon',
                'sphinxcontrib-qthelp',
                'sphinxcontrib-serializinghtml',
                'sphinx>=1.3.6',
                'graphviz>=0.3',
                'sphinx-autodoc-typehints>=1.3.0',
                'sphinx_rtd_theme>=0.4.1',
                'sphinx-gallery>=0.2.0',
                'ipython>=6.5.0'],
        'tests': ['pytest>=5.3.2',
                  'coverage>7.0.1'
                  'parameterized>=0.7.4'
                  'pytest-qt>=4.0.2',
                  'prospector'],
        'tutorials': ['jupyter>=1.0.0'],
    },
    python_requires=">=3.8",
    entry_points={"console_scripts": ["crdesigner=crdesigner.ui.cli.command_line:main"]},
)
