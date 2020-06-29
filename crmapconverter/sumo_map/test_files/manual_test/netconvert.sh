#!/bin/bash

netconvert --plain.extend-edge-shape=true \
            --no-turnarounds=true \
            --junctions.internal-link-detail=20 \
            --geometry.avoid-overlap=true \
            --offset.disable-normalization=true \
            --node-files=nodes.net.xml \
            --edge-files=edges.net.xml \
            --connection-files=_connections.net.xml \
            --output-file=test.net.xml \
            --geometry.remove.keep-edges.explicit=true \
            --tls.guess=true \
            --tls.set=20 \
            --verbose=true