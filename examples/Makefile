PYTHON ?= python3
GS ?= gs

files = $(foreach item, $(shell grep -v / INDEX), $(item)) $(foreach item, $(shell grep / INDEX), $(addprefix $(item), $(shell cat $(item)INDEX)))
pyfiles = $(addsuffix .py, $(files))
epsfiles = $(addsuffix .eps, $(files))
pdffiles = $(addsuffix .pdf, $(files))
pngfiles = $(addsuffix .png, $(files))
svgfiles = $(addsuffix .svg, $(files))
ipynbfiles = $(addsuffix .ipynb, $(files))
thumbpngfiles = $(addsuffix _thumb.png, $(files))

.PRECIOUS: $(epsfiles) $(pngfiles)

all:
	$(MAKE) clean
	$(MAKE) $(ipynbfiles)
	$(MAKE) $(thumbpngfiles)

clean:
	rm -f $(epsfiles) $(pdffiles) $(pngfiles) $(svgfiles) $(ipynbfiles) $(thumbpngfiles)

all_without_remove:
	$(MAKE) $(ipynbfiles)
	$(MAKE) $(thumbpngfiles)

%.eps: %.py
	cd $(dir $^); PYTHONPATH=$(CURDIR)/.. $(PYTHON) -W default $(notdir $^)

%.ipynb: %.png
	$(PYTHON) $(CURDIR)/../www/mkipynb.py $@

%.png: %.eps
	$(GS) -r100 -dEPSCrop -dNOPAUSE -dQUIET -dBATCH -sDEVICE=pngalpha -dTextAlphaBits=4 -dGraphicsAlphaBits=4 -sOutputFile=$@ $^

%_thumb.png: %.eps
	$(GS) -r50 -dEPSCrop -dNOPAUSE -dQUIET -dBATCH -sDEVICE=pngalpha -dTextAlphaBits=4 -dGraphicsAlphaBits=4 -sOutputFile=$@ $^
