#!/bin/bash
# run docker with the ability to display GUIs
docker run -it \
    --env="DISPLAY" \
    --net=host \
    --volume="$HOME/.Xauthority:/home/cruser/.Xauthority:rw" \
    --volume="$PWD/../:/home/cruser/commonroad-map-tool" \
    --volume="$HOME/.ssh/:/home/cruser/.ssh" \
    "commonroad:latest" /bin/bash
