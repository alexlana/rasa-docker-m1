#################################################
# The base image used for all images
FROM ubuntu:20.04 as base

ENV DEBIAN_FRONTEND="noninteractive"

RUN apt-get update -qq && \
  apt-get install -y --no-install-recommends \
  python3 \
  python3-venv \
  python3-pip \
  python3-dev \
  # para o hdf5
  libhdf5-dev \
  # required by psycopg2 at build and runtime
  libpq-dev \
  # required for health check
  curl \
  && apt-get autoremove -y

# Make sure that all security updates are installed
RUN apt-get update && apt-get dist-upgrade -y --no-install-recommends

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 100 \
   && update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 100

# Create rasa user and group
RUN useradd -rm -d /app -s /sbin/nologin -g root -u 1001 rasa && groupadd -g 1001 rasa



#################################################
# builder com Spacy
FROM base as builder



RUN apt-get install -y dh-autoreconf libcurl4-gnutls-dev libexpat1-dev gettext libz-dev libssl-dev



RUN apt-get update -qq && \
  apt-get install -y --no-install-recommends \
  build-essential \
  wget \
  openssh-client \
  graphviz-dev \
  pkg-config \
  git-core \
  openssl \
  libssl-dev \
  libffi7 \
  libffi-dev \
  libpng-dev \
  && apt-get autoremove -y

# Make sure that all security updates are installed
RUN apt-get update && apt-get dist-upgrade -y --no-install-recommends




# copy files
COPY ./rasa /build/
COPY ./rasa/docker/configs/config_pretrained_embeddings_spacy_en.yml /build/config.yml
# COPY ./app/config.yml /build/config.yml

# change working directory
WORKDIR /build

# poetry
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
ENV PATH "/root/.poetry/bin:${PATH}"

# install dependencies
RUN python3 -m venv /opt/venv && \
  . /opt/venv/bin/activate && pip install --no-cache-dir -U "pip==21.*"
RUN . /opt/venv/bin/activate

RUN apt-get install pkg-config
RUN pip install h5py
ADD ["https://github.com/KumaTea/tensorflow-aarch64/releases/download/v2.6/tensorflow-2.6.0-cp38-cp38-linux_aarch64.whl", "/tensorflow-2.6.0-cp38-cp38-linux_aarch64.whl"]
RUN python3 -m pip install --no-cache-dir /tensorflow-2.6.0-cp38-cp38-linux_aarch64.whl
RUN rm /tensorflow-2.6.0-cp38-cp38-linux_aarch64.whl
COPY ./repo/bashrc /etc/bash.bashrc
RUN chmod a+rwx /etc/bash.bashrc


RUN apt-get install -y wget


RUN wget https://github.com/Qengineering/TensorFlow-Addons-Raspberry-Pi_64-bit/raw/main/tensorflow_addons-0.14.0.dev0-cp38-cp38-linux_aarch64.whl
RUN python3 -m pip install --no-cache-dir tensorflow_addons-0.14.0.dev0-cp38-cp38-linux_aarch64.whl
RUN rm tensorflow_addons-0.14.0.dev0-cp38-cp38-linux_aarch64.whl


RUN wget https://github.com/bazelbuild/bazel/releases/download/4.2.1/bazel-4.2.1-linux-arm64
RUN chmod +x bazel-4.2.1-linux-arm64
RUN mv bazel-4.2.1-linux-arm64 /usr/local/bin/bazel
RUN bazel version
RUN which bazel



RUN apt-get install -y git
# RUN git clone --depth=1 https://github.com/tensorflow/addons.git
# # RUN pip install --upgrade numpy
# RUN apt-get install -y sudo



# RUN wget https://github.com/Qengineering/TensorFlow-Addons-Raspberry-Pi_64-bit/raw/main/configure.py
# RUN mkdir ~/addons/
# RUN mv configure.py ~/addons/
# RUN wget https://github.com/Qengineering/TensorFlow-Addons-Raspberry-Pi_64-bit/raw/main/build_pip_pkg.sh
# RUN mkdir ~/addons/build_deps
# RUN mv build_pip_pkg.sh ~/addons/build_deps
# RUN chmod 755 ~/addons/build_deps/build_pip_pkg.sh
# RUN sudo ln -s /usr/local/lib/python3.8/dist-packages/tensorflow/python/_pywrap_tensorflow_internal.so /usr/lib/_pywrap_tensorflow_internal.so

# WORKDIR /root/addons

# RUN touch ~/.bazelrc
# RUN touch ~/WORKSPACE

# RUN python3 configure.py

# RUN bazel clean
# RUN bazel build build_pip_pkg
# RUN sudo bazel-bin/build_pip_pkg /tmp/tensoraddons_pkg
# WORKDIR /tmp/tensoraddons_pkg
# RUN sudo -H pip3 install tensorflow_addons-0.14.0.dev0-cp38-cp38m-linux_aarch64.whl
# RUN rm -rf ~/addons

# WORKDIR /build




# RUN wget https://github.com/Qengineering/TensorFlow-Addons-Raspberry-Pi_64-bit/raw/main/tensorflow_addons-0.14.0.dev0-cp38-cp38m-linux_arm64.whl
# RUN pip3 install tensorflow_addons-0.14.0.dev0-cp37-cp37m-linux_aarch64.whl

# RUN pip install tensorflow-text




RUN pip install --upgrade pip setuptools wheel

# a linha abaixo dah erro quando tenta encontrar o tensorflow 2.6.1
RUN poetry install --extras spacy --no-dev --no-root --no-interaction
RUN . /opt/venv/bin/activate
RUN poetry build -f wheel -n
RUN pip install --no-deps dist/*.whl
RUN rm -rf dist *.egg-info

# make sure we use the virtualenv
ENV PATH="/opt/venv/bin:$PATH"

# RUN python3 -m spacy download pt_core_news_md && \
#     python3 -m spacy link pt_core_news_md pt
# RUN python3 -m spacy download en_core_web_md



#################################################
# runner
FROM base as runner

# copy everything from /opt
COPY --from=builder /opt/venv /opt/venv

# make sure we use the virtualenv
ENV PATH="/opt/venv/bin:$PATH"

# set HOME environment variable
ENV HOME=/app

COPY ./app /app

# update permissions & change user to not run as root
WORKDIR /app
RUN chgrp -R 0 /app && chmod -R g=u /app && chmod o+wr /app
USER 1001

# Create a volume for temporary data
VOLUME /tmp

# change shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# the entry point
# EXPOSE 5005
# ENTRYPOINT ["rasa"]
# CMD ["--help"]
