#!/bin/bash


AE=`compare -metric AE $1 $2 NULL: 2>&1` # compare pirnts AE on stderr
echo 1>&2
echo "AE (no fuzz): $AE" 1>&2

convert $1 $2 -clone 0 -combine png:- \
    | montage -geometry +4+4 $1 - $2 png:- \
    | display -title "$2" -resize 1920x1080 -

echo -n "AE (fuzz): " 1>&2  # compare returns AE on stderr and as a return value
compare -metric AE -fuzz 0.5% $1 $2 png:- \
    | montage -geometry +4+4 <( convert $1 -normalize -depth 8 png:- ) - <( convert $2 -normalize -depth 8 png:- ) png:- \
    | display -title "$2" -resize 1920x1080 -

# return value of compare is AE and possibly != 0 so ignore ret-value with || true if not used in a pipe to avoid "fatal: external diff died"
