#!/bin/bash

version=<version> #last version v0.6.9_22.04
gitlab_img=gitlab.lrz.de:5005/cps/commonroad-scenario-designer/ci:$version

DOCKER_BUILDKIT=1 docker build -t "commonroad:$version" -f Dockerfile --no-cache .. \
&& docker tag "commonroad:$version" "latest" \
&& docker login gitlab.lrz.de:5005 \
&& docker tag "commonroad:$version" "$gitlab_img" \
&& docker push "$gitlab_img"

