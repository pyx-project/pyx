pyfiles = $(wildcard *.py)
epsfiles = $(patsubst %.py, %.eps, $(pyfiles))

all:
	make clean
	make eps

clean:
	-rm *.eps

eps: $(epsfiles)

%.eps: %.py
	export PYTHONPATH=$(CURDIR)/../..; cd $(dir $^) ; python $(notdir $^)

