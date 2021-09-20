FROM ubuntu:20.04

# Install miniconda3
## Copied from https://hub.docker.cocomm/r/continuumio/miniconda3/dockerfile
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
	conda update -n base -c defaults conda
    # echo "conda activate base" >> ~/.bashrc

ENV TINI_VERSION v0.16.1
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /usr/bin/tini
RUN chmod +x /usr/bin/tini

ENTRYPOINT [ "/usr/bin/tini", "--" ]
CMD [ "/bin/bash" ]

## the following two lines are required to make tzdata configuration non-interactive
ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
# Run all commands as cruser
RUN apt-get update && apt-get install -y sudo
RUN useradd --create-home --shell /bin/bash cruser \
	&& usermod -aG sudo cruser \
	&& echo "cruser ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
USER cruser
ENV HOME="/home/cruser"
ARG PROFILE="$HOME/.profile"
ARG BASHRC="$HOME/.bashrc"
ENV PYENV_ROOT="$HOME/pyenv"
WORKDIR $HOME
# ENV PATH="$PYENV_ROOT/shims:$PYENV_ROOT/bin:${PATH}"

RUN sudo apt-get update \
	&& sudo apt-get -y upgrade \
	&& sudo apt-get -y install git gcc g++ cmake make

SHELL ["/bin/bash", "-c"]


# install SUMO
## add environment variables / update $PATH
# ENV SUMO_HOME=$HOME/sumo
ENV SUMO_HOME=/usr/share/sumo
ENV PATH=$PATH:$SUMO_HOME/bin

RUN sudo apt-get install -y software-properties-common \
	&& sudo add-apt-repository -y ppa:sumo/stable \
	&& sudo apt-get update \
	&& sudo apt-get install -y ffmpeg sumo sumo-tools sumo-doc \
	&& echo "export SUMO_HOME=/usr/share/sumo" >> ~/.bashrc


# activate conda environment
RUN conda create --name commonroad-py37 python=3.7
RUN conda create --name commonroad-py38 python=3.8
RUN conda create --name commonroad-py39 python=3.9
# setup conda env
RUN echo "source activate commonroad-py39" > ~/.bashrc
ENV PATH /opt/conda/envs/commonroad-py39/bin:$PATH

# Install cartopy
RUN source activate commonroad-py37 \
	&& echo "Successfully installed Python version:" \
	&& python --version \
 	&& conda install -c conda-forge cartopy \
 	&& grep -v "git" requirements.txt | pip install -r /dev/stdin \
 	&& grep -v "git" test_requirements.txt | pip install -r /dev/stdin
RUN source activate commonroad-py38 \
	&& echo "Successfully installed Python version:" \
	&& python --version \
 	&& conda install -c conda-forge cartopy \
 	&& grep -v "git" requirements.txt | pip install -r /dev/stdin \
 	&& grep -v "git" test_requirements.txt | pip install -r /dev/stdin
RUN source activate commonroad-py39 \
	&& echo "Successfully installed Python version:" \
	&& python --version \
 	&& conda install -c conda-forge cartopy \
 	&& grep -v "git" requirements.txt | pip install -r /dev/stdin \
 	&& grep -v "git" test_requirements.txt | pip install -r /dev/stdin

# update path to include packages installed by conda
ENV PATH $HOME/.local/bin:$PATH
# install usefull tools
RUN sudo apt-get install -y vim nano

# install Tkinter
RUN sudo apt-get install -y tk-dev


