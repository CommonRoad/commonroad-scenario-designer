#!/bin/bash

cd commonroad-map-tool \
&& source activate commonroad-py37 \
&& pip install -r test_requirements.txt -r requirements.txt \
&& nice tox --current-env -e py37 -- test/ \
&& source activate commonroad-py38 \
&& pip install -r test_requirements.txt -r requirements.txt \
&& nice tox --current-env -e py38 -- test/ \
&& source activate commonroad-py39 \
&& pip install -r test_requirements.txt -r requirements.txt \
&& nice tox --current-env -e py39 -- test/ || /bin/bash
