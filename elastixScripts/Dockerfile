## Use selx as base
FROM selx:python2.7

RUN apt-get update && apt-get install -y --no-install-recommends \
    imagemagick

RUN git clone http://github.com/romangrothausmann/elastix_scripts.git

RUN cd elastix_scripts/tests/recRegStack/ && \
    make -j"$(nproc)" -B
