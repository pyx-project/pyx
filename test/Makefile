PYTHON ?= python3

.PHONY:unit functional doc

all:unit functional doc

unit:
	cd unit; $(PYTHON) test.py

functional:
	cd functional; make

doc:
	cd ../pyx; nosetests --with-doctest
