#!/bin/bash

convert $1 $2 -clone 0 -combine png:- | montage -geometry +4+4 $1 - $2 png:- | display -title "$2" -
