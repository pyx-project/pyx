pyfiles = $(wildcard *.py)
epsfiles = $(patsubst %.py, %.eps, $(pyfiles))

all:
	make clean
	make eps

clean:
	-rm *.eps

eps: $(epsfiles)

%.eps: %.py
	export PYTHONPATH=$(PWD)/../..; cd $(dir $^) ; python $(notdir $^)

