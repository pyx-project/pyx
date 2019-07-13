PYTHON ?= python3

.PHONY:unit functional svg doctest

all:unit functional svg doctest

clean:
	cd functional; $(MAKE) clean
	cd svg; $(MAKE) clean

unit:
	cd unit; $(PYTHON) test.py

functional:
	cd functional; $(MAKE)

svg:
	cd svg; $(MAKE)

doctest:
	cd ../manual; $(MAKE) doctest

