################################################################################
# base system
################################################################################
FROM ubuntu:latest as system

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3


################################################################################
# builder
################################################################################
FROM system as builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates `# essential for git over https` \
    curl \
    build-essential \
    python3-dev libomp-dev bison

### cmake independent of distro version
RUN curl -s https://cmake.org/files/v3.17/cmake-3.17.0-rc3-Linux-x86_64.sh -o cmake.sh
RUN sh cmake.sh --prefix=/usr --exclude-subdir --skip-license

### ITK
RUN git clone --depth 1 -b v5.1rc02 https://github.com/InsightSoftwareConsortium/ITK.git

RUN mkdir -p ITK_build && \
    cd ITK_build && \
    cmake \
    	  -DCMAKE_INSTALL_PREFIX=/usr/ \
	  -DCMAKE_BUILD_TYPE=Debug \
	  -DBUILD_SHARED_LIBS=OFF \
	  -DBUILD_TESTING=OFF \
	  -DPYTHON_EXECUTABLE=/usr/bin/python3 \
	  -DITK_WRAP_PYTHON=ON \
	  ../ITK && \
    make -j"$(nproc)" && \
    make -j"$(nproc)" install


### ITKElastix
RUN git clone https://github.com/InsightSoftwareConsortium/ITKElastix && cd ITKElastix && git checkout fd5530b8af003ca5f09968ca7a66d09f0ba43e5d

RUN mkdir -p ITKElastix_build && \
    cd ITKElastix_build && \
    cmake \
    	  -DCMAKE_INSTALL_PREFIX=/usr/ \
	  -DCMAKE_BUILD_TYPE=Debug \
	  -DPYTHON_EXECUTABLE=/usr/bin/python3 \
	  -DITK_DIR=/ITK_build \
	  -DBUILD_TESTING=OFF \
	  ../ITKElastix && \
    make -j"$(nproc)" && \
    make -j"$(nproc)" install

RUN ldconfig


RUN apt-get update && apt-get install -y --no-install-recommends \
    imagemagick python3-pip

RUN pip3 install numpy

ENV PYTHONPATH "${PYTHONPATH}:/usr/lib/python3/"

COPY . /opt/elastix-CLIs/
ENV PATH "/opt/elastix-CLIs/:${PATH}"

WORKDIR /images
