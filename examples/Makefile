default: examples.dvi

clean:
	-rm -f examples.tex examples.log examples.aux examples.dvi *.eps */*.eps *.pdf */*.pdf *.png */*.png

all:
	make clean
	make examples.dvi
	make png

dvi: examples.dvi

files = $(foreach item, $(shell grep -v / INDEX), $(item)) $(foreach item, $(shell grep / INDEX), $(addprefix $(item), $(shell cat $(item)INDEX)))
pyfiles = $(addsuffix .py, $(files))
epsfiles = $(addsuffix .eps, $(files))
pngfiles = $(addsuffix .png, $(files))
thumbpngfiles = $(addsuffix _thumb.png, $(files))

eps: $(epsfiles)

examples.dvi: examples.py $(epsfiles)
	python examples.py $(basename $(pyfiles))
	latex examples.tex

png: $(pngfiles) $(thumbpngfiles)

%.eps: %.py
	cd $(dir $^); PYTHONPATH=$(CURDIR)/.. python $(notdir $^)

misc/pattern.png: misc/pattern.eps
	gs -r400 -dEPSCrop -dNOPAUSE -dQUIET -dBATCH -sDEVICE=pnm -sOutputFile=- $^|pnmscale 0.25|pnmtopng -transparent 'rgb:ff/ff/ff' > $@

misc/pattern_thumb.png: misc/pattern.eps
	gs -r200 -dEPSCrop -dNOPAUSE -dQUIET -dBATCH -sDEVICE=pnm -sOutputFile=- $^|pnmscale 0.25|pnmtopng -transparent 'rgb:ff/ff/ff' > $@

%.png: %.eps
	gs -r100 -dEPSCrop -dNOPAUSE -dQUIET -dBATCH -sDEVICE=pngalpha -dTextAlphaBits=4 -dGraphicsAlphaBits=4 -sOutputFile=$@ $^

%_thumb.png: %.eps
	gs -r50 -dEPSCrop -dNOPAUSE -dQUIET -dBATCH -sDEVICE=pngalpha -dTextAlphaBits=4 -dGraphicsAlphaBits=4 -sOutputFile=$@ $^
