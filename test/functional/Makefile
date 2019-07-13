PYTHON ?= python3

pyfiles = $(wildcard *.py)
pyfiles = $(filter-out test_connector.py test_deformer.py,$(wildcard *.py))
epsfiles = $(patsubst %.py, %.eps, $(pyfiles))

all:
	$(MAKE) clean
	$(MAKE) eps

clean:
	-rm -f *.ps *.eps *.pdf *.svg

eps: $(epsfiles)

%.eps: %.py
	$(PYTHON) -W default $^

