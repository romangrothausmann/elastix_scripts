
SE?=/opt/SimpleElastix/
export PYTHONPATH=$(SE)/lib/python/


## run IM tools without setting cration and modification date (or -strip) to avoid changes in PNGs that are not visual: http://stackoverflow.com/questions/13577280/getting-imagemagick-convert-to-not-write-out-extra-info
## some bug now needs even more default options: http://unix.stackexchange.com/questions/255252/create-the-same-png-with-imagemagick-2-times-binaries-differ#255256
convertIM:= convert -define png:exclude-chunks=date,time +set date:create +set date:modify
mogrifyIM:= mogrify -define png:exclude-chunks=date,time +set date:create +set date:modify


SLICES= $(shell seq  -f %03.0f 1 9)
FNs:= $(SLICES:%=sMR3006g_OT1_s%.png)

.PHONY: test clean


test : reg reg/avg.png
test : reg2 reg2/avg.png
test : reg3 reg3/avg.png
test : reg4 reg4/avg.png

clean:
	-rm -v reg*.out
	-rm -rv reg/
	-rm -rv reg2/
	-rm -rv reg3/
	-rm -rv reg4/

## reg all test images starting with the first, make sure to run make clean first to avoid continue behavior on last slice
reg : parameterFile.txt
	python ../../recRegStack.py -i "*.png" -o $@ -p $< | tee $@.out

## test start and skip option
reg/2016_12_02_0101_s02_06.tif : reg
reg2 : parameterFile.txt | reg/2016_12_02_0101_s02_06.tif
	mkdir -p reg2/
	ln -sf ../reg/2016_12_02_0101_s02_06.tif reg2/
	python ../../recRegStack.py -i "*.png" -o $@ -p $< \
		-s 2016_12_02_0101_s03_01.png \
		-f \
		-S 2016_12_02_0101_s03_02.png 2016_12_02_0101_s03_03.png 2016_12_02_0101_s03_04.png | tee $@.out

## register forward from start slice and then continue backwards
reg3 : parameterFile.txt
	-rm -v $@/2016_12_02_0101_s02_06.tif # make sure file does not exist from former run, otherwise leads to "continue"
	python ../../recRegStack.py -i "*.png" -o $@ -p $< \
		-s 2016_12_02_0101_s03_01.png \
		-f -b | tee $@.out

## register only backwards from start slice
reg4 : parameterFile.txt 
	-rm -v $@/2016_12_02_0101_s03_02.tif # make sure file does not exist from former run, otherwise leads to "continue"
	python ../../recRegStack.py -i "*.png" -o $@ -p $< \
		-s 2016_12_02_0101_s03_02.png `# starting such, that corresponding images are the same as in reg3` \
		-b | tee $@.out

%/avg.png : %
	$(convertIM) -average $</*.tif $@
