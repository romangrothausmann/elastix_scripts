## Use ubuntu:16.04 as base
FROM ubuntu:16.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates `# essential for git over https` \
    cmake

# RUN git config --global http.sslVerify false # better inst. ca-certificates
RUN git clone http://github.com/SuperElastix/SimpleElastix

## http://simpleelastix.readthedocs.io/GettingStarted.html#building-manually-on-linux
RUN mkdir -p selx_build && \
    cd selx_build && \
    cmake \
    	  -DPYTHON_EXECUTABLE=/usr/bin/python3 \
	  -DPYTHON_LIBRARY=/usr/lib/x86_64-linux-gnu/libpython3.4m.so.1 \
	  -DPYTHON_INCLUDE_DIR=/usr/include/python3.4m/ \
    	  ../SimpleElastix/SuperBuild/ && \
    make -j"$(nproc)" && \
    make -j"$(nproc)" install
