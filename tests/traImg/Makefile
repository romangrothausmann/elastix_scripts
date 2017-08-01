

.PHONY: test clean


test : tra.png

clean:
	-rm -rv reg/

ini.png : ../recRegStack/2016_12_02_0101_s00_01.png
	ln -sf $< $@

tra.png : ini.png parameterFile.txt
	PYTHONPATH=/opt/SimpleElastix/lib/python/:$$PYTHONPATH \
		python ../../traImg.py -i $< -o $@ -p $(lastword $^)
