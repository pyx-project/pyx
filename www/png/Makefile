PYTHON ?= python

pngfiles = example.png bend.png pyxlogo.png

default: $(pngfiles)

clean:
	-rm $(pngfiles)

%.png: %.py
	export PYTHONPATH=$(CURDIR)/../.. ; cd $(dir $^) ; $(PYTHON) $(notdir $^)
	$(PYTHON) ../../contrib/epstopng.py -o $@ $*.eps
	rm $*.eps
