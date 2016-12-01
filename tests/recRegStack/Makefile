
SLICES= $(shell seq  -f %03.0f 1 9)
FNs:= $(SLICES:%=sMR3006g_OT1_s%.png)

.PHONY: test clean


test : reg/

clean:
	-rm -rv reg/

reg/ : $(FNs) parameterFile.txt
	PYTHONPATH=/opt/SimpleElastix/lib/python/:$$PYTHONPATH \
		python ../../recRegStack.py "sMR3006g_OT1_s00[0-9].png" reg/ parameterFile.txt
