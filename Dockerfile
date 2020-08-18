FROM continuumio/miniconda3:latest

# ARG HOME="/root"
# ARG PROFILE="$HOME/.profile"
# ARG BASHRC="$HOME/.bashrc"
# ENV PYENV_ROOT="$HOME/pyenv"
# ENV PATH="$PYENV_ROOT/shims:$PYENV_ROOT/bin:${PATH}"

RUN apt-get update \
	&& apt-get -y upgrade \
	&& apt-get -y install git gcc g++ cmake make

# activate conda environment
RUN conda create --name commonroad python=3.7

# install SUMO
ENV SUMO_HOME=$HOME/sumo
RUN apt-get install -y ffmpeg \
	&& git clone https://github.com/octavdragoi/sumo \
	&& cd sumo \
	&& git checkout smooth-lane-change \
	&& apt-get install -y cmake python g++ libxerces-c-dev libfox-1.6-dev libgdal-dev libproj-dev libgl2ps-dev swig \
	&& export SUMO_HOME="$(pwd)" \
	&& echo "export SUMO_HOME=$(pwd)" >> ~/.bashrc \
	&& cd build \
	&& cmake .. \
	&& make -j8 # this will take some time
# install libccd
RUN git clone https://github.com/danfis/libccd.git \
	&& cd libccd \
	&& mkdir build && cd build \
	&& cmake -G "Unix Makefiles" -DENABLE_DOUBLE_PRECISION=ON -DBUILD_SHARED_LIBS=ON .. \
	&& make \
	&& sudo make install
# install fcl
RUN git clone https://github.com/flexible-collision-library/fcl.git \
	&& cd fcl \
	&& sudo apt-get install -y libboost-dev libboost-thread-dev libboost-test-dev libboost-filesystem-dev libeigen3-dev \
	&& mkdir build && cd build \
	&& cmake .. \
	&& make \
	&& make install 

# Make RUN commands use the new environment:
# SHELL ["conda", "run", "-n", "commonroad", "/bin/bash", "-c"]

# install commonroad -collision checker
RUN git clone https://gitlab.lrz.de/tum-cps/commonroad-collision-checker.git \
	&& cd commonroad-collision-checker/ \ 
	&& mkdir build \ 
	&& cd build \ 
	&& # YOU NEED TO CHANGE THE PATH TO YOUR CONDA ENVIRONMENT AS WELL AS THE PYTHON VERSION HERE \ 
	&& cmake -DADD_PYTHON_BINDINGS=TRUE -DPATH_TO_PYTHON_ENVIRONMENT="/opt/conda/envs/commonroad" -DPYTHON_VERSION="3.7" -DCMAKE_BUILD_TYPE=Release .. \ 
	&& make -j8
	# && python setup.py install

# install cartopy
RUN conda install -c conda-forge cartopy




# build stuff for pyenv
# RUN apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
# 	libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
# 	xz-utils tk-dev libffi-dev liblzma-dev
# RUN apt-get install -y git locales

# # Set the locale
# RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
# 	dpkg-reconfigure --frontend=noninteractive locales && \
# 	update-locale LANG=en_US.UTF-8
# ENV LANG en_US.UTF-8
# ENV LANGUAGE en_US:en
# ENV LC_ALL en_US.UTF-8

# # install utils for working in the container
# RUN apt-get install -y vim

# RUN git clone --recursive --shallow-submodules \
# 	https://github.com/pyenv/pyenv.git \
# 	$PYENV_ROOT

# RUN echo "export PYENV_ROOT=$PYENV_ROOT" >> $PROFILE
# RUN echo 'export PATH=$PYENV_ROOT/bin:$PATH' >> $PROFILE
# RUN echo 'eval "$(pyenv init -)"' >> $PROFILE
# RUN echo 'eval "$(pyenv init -)"' >> $BASHRC

# RUN pyenv install 3.6.7
# RUN pyenv install 3.7.1

# # install cartopy dependencies
# RUN apt-get update && \
# 	apt-get install -y libgeos++-dev libproj-dev

# ADD ./requirements.txt $HOME/requirements.txt
# ADD ./test_requirements.txt $HOME/test_requirements.txt

# WORKDIR ${HOME}
# # install dependencies for development & testing

# CMD /bin/bash -c "source ./.bashrc &&\
# 	pyenv shell 3.7.1 &&\
# 	pip install --upgrade pip &&\
# 	pip install wheel tox pytest numpy &&\
# 	pip install -r $HOME/requirements.txt &&\
# 	pip install -r $HOME/test_requirements.txt &&\
# 	bash"