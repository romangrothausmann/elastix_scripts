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
    python3-dev

### cmake independent of distro version
RUN curl -s https://cmake.org/files/v3.11/cmake-3.11.4-Linux-x86_64.sh -o cmake.sh
RUN sh cmake.sh --prefix=/usr --exclude-subdir --skip-license

### ITK
RUN git clone --depth 1 -b v5.1rc01 https://github.com/InsightSoftwareConsortium/ITK.git

RUN mkdir -p ITK_build && \
    cd ITK_build && \
    cmake \
    	  -DCMAKE_INSTALL_PREFIX=/opt/itk/ \
	  -DCMAKE_BUILD_TYPE=Debug \
	  -DBUILD_SHARED_LIBS=ON \
	  -DBUILD_TESTING=OFF \
	  -DPYTHON_EXECUTABLE=/usr/bin/python3 \
	  -DITK_WRAP_PYTHON=ON \
	  ../ITK && \
    make -j"$(nproc)" && \
    make -j"$(nproc)" install


### ITKElastix
RUN git clone https://github.com/InsightSoftwareConsortium/ITKElastix

RUN mkdir -p ITKElastix_build && \
    cd ITKElastix_build && \
    cmake \
    	  -DCMAKE_INSTALL_PREFIX=/opt/itkElastix/ \
	  -DCMAKE_BUILD_TYPE=Debug \
	  -DPYTHON_EXECUTABLE=/usr/bin/python3 \
	  -DITK_DIR=/ITK_build \
	  -DBUILD_TESTING=OFF \
	  ../ITKElastix && \
    make -j"$(nproc)" && \
    make -j"$(nproc)" install


################################################################################
# install
################################################################################
FROM system as install

RUN apt-get update && apt-get install -y --no-install-recommends \
    imagemagick python3-pip

RUN pip3 install numpy

COPY --from=builder /opt/itk/ /opt/itk/
COPY --from=builder /opt/itkElastix/ /opt/itkElastix/

ENV PYTHONPATH "${PYTHONPATH}:/opt/itk/lib/python3/"

COPY . /opt/elastix-CLIs/
ENV PATH "/opt/elastix-CLIs/:${PATH}"
ENV LD_LIBRARY_PATH "/opt/itk/lib/:${LD_LIBRARY_PATH}"

WORKDIR /images
