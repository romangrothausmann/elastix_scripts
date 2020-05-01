
DI?=registry.gitlab.com/romangrothausmann/elastix_scripts/master:latest

SE?=/opt/SimpleElastix/
export PYTHONPATH=$(SE)/lib/python/


.PHONY: test clean


test : ini_tra.png ini-16b_tra.png

clean:
	-rm -v ini_tra.png ini-16b_tra.png

ini.png : ../recRegStack/2016_12_02_0101_s00_01_g8b.png
	ln -sf $< $@

ini-16b.png : ../IMGs/16b/K2_0101_s00_01.png
	ln -sf $< $@

%_tra.png : %.png parameterFile.txt
	docker run -t --rm --user `id -u`:`id -g` -v $$(pwd)/../..:/elastix_scripts -w /elastix_scripts/tests/traImg $(DI) \
	/elastix_scripts/traImg.py -i $< -o $@ -p $(lastword $^)
