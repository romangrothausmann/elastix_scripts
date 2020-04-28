################################################################################
# base system
################################################################################
FROM ubuntu:latest as system

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    python


################################################################################
# builder
################################################################################
FROM system as builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates `# essential for git over https` \
    cmake \
    build-essential \
    python-dev

# RUN git config --global http.sslVerify false # better inst. ca-certificates
RUN git clone http://github.com/SuperElastix/SimpleElastix && cd SimpleElastix && git checkout 4c3a0d1cb5c2bb57712eb1fbd575797578077da5

## http://simpleelastix.readthedocs.io/GettingStarted.html#building-manually-on-linux
RUN mkdir -p selx_build && \
    cd selx_build && \
    cmake \
    	  -DCMAKE_CXX_STANDARD=11 \
    	  -DCMAKE_INSTALL_PREFIX=/opt/SimpleElastix/ \
	  -DCMAKE_BUILD_TYPE=Release \
	  -DBUILD_TESTING=OFF \
	  -DBUILD_EXAMPLES=OFF \
    	  -DWRAP_PYTHON=On \
    	  ../SimpleElastix/SuperBuild/ && \
    make -j"$(nproc)" && \
    cd SimpleITK-build/Wrapping/Python `# essential for py install ` && \
    python Packaging/setup.py  install --home /opt/SimpleElastix/


################################################################################
# install
################################################################################
FROM system as install

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    imagemagick

COPY --from=builder /opt/SimpleElastix/ /opt/SimpleElastix/
ENV PYTHONPATH "${PYTHONPATH}:/opt/SimpleElastix/lib/python/"

COPY . /opt/elastix-CLIs/
ENV PATH "/opt/elastix-CLIs/:${PATH}"

WORKDIR /images
