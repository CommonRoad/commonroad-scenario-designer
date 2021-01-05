#!/bin/bash

version=$1
gitlab_img=gitlab.lrz.de:5005/cps/commonroad-map-tool/ci:$version

DOCKER_BUILDKIT=1 docker build -t "commonroad:$version" -f Dockerfile --no-cache .. \
&& echo "Runnning tests ..." \
&& docker run --rm --volume "$PWD/test.sh:/home/cruser/test.sh" \
                   --volume "$PWD/../:/home/cruser/commonroad-map-tool" \
                   --volume "$HOME/.ssh/:/home/cruser/.ssh" \
        "commonroad:$version" /home/cruser/test.sh \
&& docker login gitlab.lrz.de:5005 \
&& docker tag "commonroad:$version" "$gitlab_img" \
&& docker push "$gitlab_img"

