
pyfiles = $(wildcard *.py)
pngfiles = $(patsubst %.py, %.png, $(pyfiles))

default: $(pngfiles)

clean:
	-rm $(pngfiles)

%.png: %.py
	export PYTHONPATH=$(PWD)/../.. ; cd $(dir $^) ; python $(notdir $^)
	@# -dEPSCrop needs gs version >= 8.0
	python ../../contrib/epstopng.py -g gs8.0 -o $@ $*.eps
	rm $*.eps
