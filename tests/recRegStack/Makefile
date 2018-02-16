
SE?=/opt/SimpleElastix/
export PYTHONPATH=$(SE)/lib/python/


## run IM tools without setting cration and modification date (or -strip) to avoid changes in PNGs that are not visual: http://stackoverflow.com/questions/13577280/getting-imagemagick-convert-to-not-write-out-extra-info
## some bug now needs even more default options: http://unix.stackexchange.com/questions/255252/create-the-same-png-with-imagemagick-2-times-binaries-differ#255256
convertIM:= convert -define png:exclude-chunks=date,time +set date:create +set date:modify
mogrifyIM:= mogrify -define png:exclude-chunks=date,time +set date:create +set date:modify


SLICES= $(shell seq  -f %03.0f 1 9)
FNs:= $(SLICES:%=sMR3006g_OT1_s%.png)

.PHONY: test clean


test : reg/
test : reg/avg.png

clean:
	-rm -rv reg/

reg/ : parameterFile.txt
	python ../../recRegStack.py "*.png" reg/ parameterFile.txt 0 | tee recRegStack.out

reg/avg.png : reg/
	$(convertIM) -average $</*.tif $@
