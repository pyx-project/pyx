PYTHON ?= python3

pyfiles = $(wildcard *.py)
epsfiles = $(patsubst %.py, %.eps, $(pyfiles))

all:
	make clean
	make eps

clean:
	-rm -f *.eps eps/*.eps *.pdf

eps: $(epsfiles)

%.eps: %.py
	export PYTHONPATH=$(CURDIR)/../..; cd $(dir $^) ; $(PYTHON) $(notdir $^)

