
pyfiles = $(wildcard *.py)
pngfiles = $(patsubst %.py, %.png, $(pyfiles))

default: $(pngfiles)

clean:
	-rm $(pngfiles)

%.png: %.py
	export PYTHONPATH=$(PWD)/../.. ; cd $(dir $^) ; python $(notdir $^)
	python ../../contrib/epstopng.py -o $@ $*.eps
	rm $*.eps
