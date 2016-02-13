PYTHON ?= python3
GS ?= gs

files = $(foreach item, $(shell grep -v / INDEX), $(item)) $(foreach item, $(shell grep / INDEX), $(addprefix $(item), $(shell cat $(item)INDEX)))
pyfiles = $(addsuffix .py, $(files))
epsfiles = $(addsuffix .eps, $(files))
pdffiles = $(addsuffix .pdf, $(files))
pngfiles = $(addsuffix .png, $(files))
ipynbfiles = $(addsuffix .ipynb, $(files))
thumbpngfiles = $(addsuffix _thumb.png, $(files))

.PRECIOUS: $(epsfiles) $(pngfiles)

all:
	rm -f $(epsfiles) $(pdffiles) $(pngfiles) $(ipynbfiles) $(thumbpngfiles)
	make $(ipynbfiles)
	make $(thumbpngfiles)

all_without_remove:
	make $(ipynbfiles)
	make $(thumbpngfiles)

%.eps: %.py
	cd $(dir $^); PYTHONPATH=$(CURDIR)/.. $(PYTHON) -W default $(notdir $^)

%.ipynb: %.png
	$(PYTHON) $(CURDIR)/../www/mkipynb.py $@

misc/pattern.png: misc/pattern.eps
	$(GS) -r400 -dEPSCrop -dNOPAUSE -dQUIET -dBATCH -sDEVICE=pnm -sOutputFile=- $^|pnmscale 0.25|pnmtopng -transparent 'rgb:ff/ff/ff' > $@

misc/pattern_thumb.png: misc/pattern.eps
	$(GS) -r200 -dEPSCrop -dNOPAUSE -dQUIET -dBATCH -sDEVICE=pnm -sOutputFile=- $^|pnmscale 0.25|pnmtopng -transparent 'rgb:ff/ff/ff' > $@

%.png: %.eps
	$(GS) -r100 -dEPSCrop -dNOPAUSE -dQUIET -dBATCH -sDEVICE=pngalpha -dTextAlphaBits=4 -dGraphicsAlphaBits=4 -sOutputFile=$@ $^

%_thumb.png: %.eps
	$(GS) -r50 -dEPSCrop -dNOPAUSE -dQUIET -dBATCH -sDEVICE=pngalpha -dTextAlphaBits=4 -dGraphicsAlphaBits=4 -sOutputFile=$@ $^
