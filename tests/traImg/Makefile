
SE?=/opt/SimpleElastix/
export PYTHONPATH=$(SE)/lib/python/


.PHONY: test clean


test : ini_tra.png ini-16b_tra.png

clean:
	-rm -rv reg/

ini.png : ../recRegStack/2016_12_02_0101_s00_01.png
	ln -sf $< $@

ini-16b.png : ../IMGs/16b/K2_0101_s00_01.png
	ln -sf $< $@

%_tra.png : %.png parameterFile.txt
	python ../../traImg.py -i $< -o $@ -p $(lastword $^)
