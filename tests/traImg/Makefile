
DI?=registry.gitlab.com/romangrothausmann/elastix_scripts/master:34cb4e3c

SE?=/opt/SimpleElastix/
export PYTHONPATH=$(SE)/lib/python/


.PHONY: test clean


test : ini_tra.png ini-16b_tra.png

clean:
	-rm -rv *_tra.png

ini.png : ../recRegStack/2016_12_02_0101_s00_01.png
	ln -sf $< $@

ini-16b.png : ../IMGs/16b/K2_0101_s00_01.png
	ln -sf $< $@

%_tra.png : %.png parameterFile.txt
	docker run -t --rm --user `id -u`:`id -g` -v $$(pwd):/images -v $$(pwd)/../..:/elastix_scripts $(DI) \
	/elastix_scripts/traImg.py -i $< -o $@ -p $(lastword $^)
