
SE?=/opt/SimpleElastix/
export PYTHONPATH=$(SE)/lib/python/


## run IM tools without setting cration and modification date (or -strip) to avoid changes in PNGs that are not visual: http://stackoverflow.com/questions/13577280/getting-imagemagick-convert-to-not-write-out-extra-info
## some bug now needs even more default options: http://unix.stackexchange.com/questions/255252/create-the-same-png-with-imagemagick-2-times-binaries-differ#255256
convertIM:= convert -define png:exclude-chunks=date,time +set date:create +set date:modify
mogrifyIM:= mogrify -define png:exclude-chunks=date,time +set date:create +set date:modify


SLICES= $(shell seq  -f %03.0f 1 9)
FNs:= $(SLICES:%=sMR3006g_OT1_s%.png)

.PHONY: test clean


test : reg
test : reg/avg.png
test : reg2
test : reg3

clean:
	-rm -rv reg/
	-rm -rv reg2/

reg : parameterFile.txt
	python ../../recRegStack.py -i "*.png" -o $@ -p $< | tee $@.out

reg/2016_12_02_0101_s02_06.tif : reg
reg2 : parameterFile.txt | reg/2016_12_02_0101_s02_06.tif
	mkdir -p reg2/
	ln -sf ../reg/2016_12_02_0101_s02_06.tif reg2/
	python ../../recRegStack.py -i "*.png" -o $@ -p $< \
		-s 2016_12_02_0101_s03_01.png \
		-S 2016_12_02_0101_s03_02.png 2016_12_02_0101_s03_03.png 2016_12_02_0101_s03_04.png | tee $@.out

reg3 : parameterFile.txt
	python ../../recRegStack.py -i "*.png" -o $@ -p $< \
		-s 2016_12_02_0101_s03_01.png \
		-b | tee $@.out

reg/avg.png : reg/
	$(convertIM) -average $</*.tif $@
