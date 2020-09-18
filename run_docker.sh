#!/bin/bash
# run docker with the ability to display GUIs
docker run -it \
    --env="DISPLAY" \
    --net=host \
    --volume="$HOME/.Xauthority:/home/cruser/.Xauthority:rw" \
    --workdir="/home/$USER" \
    --volume="/home/$USER:/home/$USER" \
    commonroad

