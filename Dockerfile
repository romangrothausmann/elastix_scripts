################################################################################
# base system
################################################################################
FROM ubuntu:latest as system

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip \
    imagemagick

RUN pip3 install itk-elastix

COPY . /opt/elastix-CLIs/
ENV PATH "/opt/elastix-CLIs/:${PATH}"

WORKDIR /images
