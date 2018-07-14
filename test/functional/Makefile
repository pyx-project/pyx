PYTHON ?= python3

pyfiles = $(wildcard *.py)
pyfiles = $(filter-out test_connector.py test_deformer.py,$(wildcard *.py))
epsfiles = $(patsubst %.py, %.eps, $(pyfiles))

all:
	make clean
	make eps

clean:
	-rm -f *.eps eps/*.eps *.pdf *.svg

eps: $(epsfiles)

%.eps: %.py
	export PYTHONPATH=$(CURDIR)/../..; cd $(dir $^) ; $(PYTHON) -W default $(notdir $^)

