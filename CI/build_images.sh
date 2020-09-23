#/bin/bash

IMAGE_VERSION="v0.2"

docker build --build-arg PYTHON_VERSION=3.6 -t rasaford/commonroad-map-tool-py36:$IMAGE_VERSION .
docker build --build-arg PYTHON_VERSION=3.7 -t rasaford/commonroad-map-tool-py37:$IMAGE_VERSION .
docker build --build-arg PYTHON_VERSION=3.8 -t rasaford/commonroad-map-tool-py38:$IMAGE_VERSION .