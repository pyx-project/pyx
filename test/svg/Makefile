PYTHON ?= python3

.PHONY: default

default: suite
	PYTHONPATH=$(CURDIR)/../.. $(PYTHON) svgtest.py

clean:
	rm -f svgtest.pdf

suite:
	mkdir suite
	(cd suite; curl -O https://www.w3.org/Graphics/SVG/Test/20110816/archives/W3C_SVG_11_TestSuite.tar.gz; tar xzvf W3C_SVG_11_TestSuite.tar.gz)
