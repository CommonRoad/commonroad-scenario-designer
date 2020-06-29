#!/bin/bash

netconvert --plain.extend-edge-shape=true \
            --no-turnarounds=true \
            --junctions.internal-link-detail=20 \
            --geometry.avoid-overlap=true \
            --offset.disable-normalization=true \
            --sumo-net-file=test.net.xml \
            --geometry.remove.keep-edges.explicit=true \
            --tls.guess=true \
            --tls.set=20 \
            --output-file=test.net.xml \
            --verbose=true