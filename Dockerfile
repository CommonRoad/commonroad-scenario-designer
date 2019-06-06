FROM debian:9.6

ARG HOME="/root"
ARG PROFILE="$HOME/.profile"
ENV PYENV_ROOT="$HOME/pyenv"
ENV PATH="$PYENV_ROOT/shims:$PYENV_ROOT/bin:${PATH}"

RUN apt-get update
RUN apt-get -y upgrade

# build stuff for pyenv
RUN apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
xz-utils tk-dev libffi-dev liblzma-dev
RUN apt-get install -y git locales

# Set the locale
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
	dpkg-reconfigure --frontend=noninteractive locales && \
	update-locale LANG=en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

RUN git clone --recursive --shallow-submodules \
	https://github.com/pyenv/pyenv.git \
	$PYENV_ROOT

RUN echo "export PYENV_ROOT=$PYENV_ROOT" >> $PROFILE
RUN echo 'export PATH=$PYENV_ROOT/bin:$PATH' >> $PROFILE
RUN echo 'eval "$(pyenv init -)"' >> $PROFILE

RUN pyenv install 3.6.7
RUN pyenv install 3.7.1

ENTRYPOINT ["/bin/bash", "--login", "-i", "-c"]
CMD ["bash"]
