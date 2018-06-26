## Use ubuntu:16.04 as base
FROM ubuntu:16.04 as builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates `# essential for git over https` \
    cmake \
    build-essential

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-dev

# RUN git config --global http.sslVerify false # better inst. ca-certificates
RUN git clone http://github.com/SuperElastix/SimpleElastix

## http://simpleelastix.readthedocs.io/GettingStarted.html#building-manually-on-linux
RUN mkdir -p selx_build && \
    cd selx_build && \
    cmake \
    	  -DWRAP_PYTHON=On \
    	  -DPYTHON_EXECUTABLE=/usr/bin/python3 \
	  -DPYTHON_LIBRARY=/usr/lib/x86_64-linux-gnu/libpython3.5m.so.1 \
	  -DPYTHON_INCLUDE_DIR=/usr/include/python3.5m/ \
    	  ../SimpleElastix/SuperBuild/ && \
    make -j"$(nproc)" && \
    python3 SimpleITK-build/Wrapping/Python/Packaging/setup.py  install --home /opt/SimpleElastix/


FROM ubuntu:16.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3

COPY --from=builder /opt/SimpleElastix/ /opt/SimpleElastix/
