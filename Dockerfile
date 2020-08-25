FROM ubuntu:20.04


# Install miniconda3
## Copied from https://hub.docker.com/r/continuumio/miniconda3/dockerfile
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV PATH /opt/conda/bin:$PATH

RUN apt-get update --fix-missing && \
    apt-get install -y wget bzip2 ca-certificates curl git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    /opt/conda/bin/conda clean -tipsy && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate base" >> ~/.bashrc

ENV TINI_VERSION v0.16.1
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /usr/bin/tini
RUN chmod +x /usr/bin/tini

ENTRYPOINT [ "/usr/bin/tini", "--" ]
CMD [ "/bin/bash" ]

RUN apt-get update && apt-get install -y sudo
RUN adduser --quiet --disabled-password cruser \
	&& usermod -aG sudo cruser \
	&& echo "cruser ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
USER cruser

ENV HOME="/home/cruser"
ARG PROFILE="$HOME/.profile"
ARG BASHRC="$HOME/.bashrc"
ENV PYENV_ROOT="$HOME/pyenv"
# ENV PATH="$PYENV_ROOT/shims:$PYENV_ROOT/bin:${PATH}"


RUN sudo apt-get update \
	&& sudo apt-get -y upgrade \
	&& sudo apt-get -y install git gcc g++ cmake make

# activate conda environment
RUN conda create --name commonroad python=3.7
# setup conda env
RUN echo "source activate commonroad" > ~/.bashrc
ENV PATH /opt/conda/envs/commonroad/bin:$PATH
SHELL ["/bin/bash", "-c"]

WORKDIR $HOME

# install SUMO
ENV SUMO_HOME=$HOME/sumo
ENV PATH=$PATH:$SUMO_HOME/bin
RUN sudo apt-get install -y ffmpeg \
	&& git clone https://github.com/eclipse/sumo \
	&& cd sumo \
#	&& git checkout smooth-lane-change \
	&& sudo apt-get install -y cmake python g++ libxerces-c-dev libfox-1.6-dev libgdal-dev libproj-dev libgl2ps-dev swig \
	&& export SUMO_HOME="$(pwd)" \
	&& echo "export SUMO_HOME=$(pwd)" >> ~/.bashrc \
	&& cd build \
	&& cmake .. \
	&& make -j8

# install libccd
RUN git clone https://github.com/danfis/libccd.git \
	&& cd libccd \
	&& mkdir build && cd build \
	&& cmake -G "Unix Makefiles" -DENABLE_DOUBLE_PRECISION=ON -DBUILD_SHARED_LIBS=ON .. \
	&& make -j8 \
	&& make install

# install fcl
RUN git clone https://github.com/flexible-collision-library/fcl.git \
	&& cd fcl \
	&& sudo apt-get install -y libboost-dev libboost-thread-dev libboost-test-dev libboost-filesystem-dev libeigen3-dev \
	&& mkdir build && cd build \
	&& cmake .. \
	&& make -j8 \
	&& make install

# install commonroad -collision checker
RUN git clone https://gitlab.lrz.de/tum-cps/commonroad-collision-checker.git \
	&& cd commonroad-collision-checker/ \
	&& mkdir build \
	&& cd build \
	&& cmake -DADD_PYTHON_BINDINGS=TRUE -DPATH_TO_PYTHON_ENVIRONMENT="/opt/conda/envs/commonroad" -DPYTHON_VERSION="3.7" -DCMAKE_BUILD_TYPE=Release .. \
	&& make -j8 \
	&& cd .. \
	&& source activate commonroad \
	&& python setup.py install

# Install cartopy
RUN source activate commonroad \
	&& python --version \
 	&& conda install -c conda-forge cartopy


# update pip
RUN source activate commonroad \
	&& pip install --upgrade pip \
	&& pip install wheel tox pytest numpy


# install commonroad-map-tool dependencies
ADD ./requirements.txt $HOME/requirements.txt
ADD ./test_requirements.txt $HOME/test_requirements.txt

# ENTRYPOINT ["conda", "activate", "commonroad"]
CMD /bin/bash -c "source activate commonroad \
	&& pip install -r /root/requirements.txt \
	&& pip install -r /root/test_requirements.txt \
	&& bash"