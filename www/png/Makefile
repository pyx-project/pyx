PYTHON ?= python

pyfiles = $(wildcard *.py)
pngfiles = $(patsubst %.py, %.png, $(pyfiles))

default: $(pngfiles)

clean:
	-rm $(pngfiles)

%.png: %.py
	export PYTHONPATH=$(CURDIR)/../.. ; cd $(dir $^) ; $(PYTHON) $(notdir $^)
	$(PYTHON) ../../contrib/epstopng.py -o $@ $*.eps
	rm $*.eps
