
SE?=/opt/SimpleElastix/
export PYTHONPATH=$(SE)/lib/python/


.PHONY: test clean


test : tra.png

clean:
	-rm -rv reg/

ini.png : ../recRegStack/2016_12_02_0101_s00_01.png
	ln -sf $< $@

tra.png : ini.png parameterFile.txt
	python ../../traImg.py -i $< -o $@ -p $(lastword $^)
