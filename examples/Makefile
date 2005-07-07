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

eps: $(epsfiles)

examples.dvi: examples.py $(epsfiles)
	python examples.py $(basename $(pyfiles))
	latex examples.tex

png: $(pngfiles)

%.eps: %.py
	cd $(dir $^); PYTHONPATH=$(CURDIR)/.. python $(notdir $^)

%.png: %.eps
	python ../contrib/epstopng.py -o $@ $^
