
SLICES= $(shell seq  -f %03.0f 1 9)
FNs:= $(SLICES:%=sMR3006g_OT1_s%.png)

.PHONY: test clean


test : reg/

clean:
	-rm -rv reg/

reg/ : parameterFile.txt
	PYTHONPATH=/opt/SimpleElastix/lib/python/:$$PYTHONPATH \
		python ../../recRegStack.py "*.png" reg/ parameterFile.txt
