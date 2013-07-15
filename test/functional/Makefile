PYTHON ?= python

pyfiles = $(wildcard *.py)
epsfiles = $(patsubst %.py, %.eps, $(pyfiles))

all:
	make clean
	make eps

clean:
	-rm -f *.eps eps/*.eps

eps: $(epsfiles)

%.eps: %.py
	export PYTHONPATH=$(CURDIR)/../..; cd $(dir $^) ; $(PYTHON) $(notdir $^)

