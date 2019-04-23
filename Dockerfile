################################################################################
# base system
################################################################################
FROM ubuntu:16.04 as system

RUN apt-get update && apt-get install -y --no-install-recommends \
    python


################################################################################
# builder
################################################################################
FROM system as builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates `# essential for git over https` \
    cmake \
    build-essential \
    python-dev

# RUN git config --global http.sslVerify false # better inst. ca-certificates
RUN git clone http://github.com/SuperElastix/SimpleElastix

## http://simpleelastix.readthedocs.io/GettingStarted.html#building-manually-on-linux
RUN mkdir -p selx_build && \
    cd selx_build && \
    cmake \
    	  -DWRAP_PYTHON=On \
    	  ../SimpleElastix/SuperBuild/ && \
    make -j"$(nproc)" && \
    python SimpleITK-build/Wrapping/Python/Packaging/setup.py  install --home /opt/SimpleElastix/


################################################################################
# install
################################################################################
FROM system as install

RUN apt-get update && apt-get install -y --no-install-recommends \
    imagemagick

COPY --from=builder /opt/SimpleElastix/ /opt/SimpleElastix/
ENV PYTHONPATH "${PYTHONPATH}:/opt/SimpleElastix/lib/python/"

COPY . /opt/elastix-CLIs/
ENV PATH "/opt/elastix-CLIs/:${PATH}"

WORKDIR /images
