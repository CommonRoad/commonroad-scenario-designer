FROM ubuntu:22.04

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get -qq install \
    wget \
    git  \
    ffmpeg \
    sumo sumo-tools sumo-doc \
    && rm -rf /var/lib/apt/lists/*

ENV SUMO_HOME=$SUMO_HOME

ENV PATH="/root/miniconda3/bin:${PATH}"
ARG PATH="/root/miniconda3/bin:${PATH}"
RUN wget \
    https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && mkdir /root/.conda \
    && bash Miniconda3-latest-Linux-x86_64.sh -b \
    && rm -f Miniconda3-latest-Linux-x86_64.sh

RUN conda create --name cr38 python=3.8 && \
    conda create --name cr39 python=3.9 && \
    conda create --name cr310 python=3.10
