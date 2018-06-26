## Use selx as base
FROM romangrothausmann/selx:python2

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates `# essential for git over https` \
    make \
    imagemagick

RUN git clone http://github.com/romangrothausmann/elastix_scripts.git
