#TODO: - mutliple python runs when appropriate (new tex handling will render it unnecessary)

default: examples.dvi

clean:
	-rm examples.tex examples.log examples.aux examples.dvi examples.ps examples.pdf *.eps */*.eps *.py.html */*.py.html *.eps.png */*.eps.png

all:
	make clean
	make pdf

pdf: examples.pdf
ps: examples.ps
dvi: examples.dvi

examples.pdf: examples.ps
	ps2pdf examples.ps

examples.ps: examples.dvi
	dvips examples.dvi

pyfiles = $(filter-out examples.py,$(wildcard *.py)) $(wildcard */*.py)
htmlfiles = $(patsubst %.py, %.py.html, $(pyfiles))
epsfiles = $(patsubst %.py, %.eps, $(pyfiles))
pngfiles = $(patsubst %.py, %.eps.png, $(pyfiles))

examples.dvi: examples.py $(epsfiles)
	python examples.py $(basename $(epsfiles))
	latex examples.tex
	-rm examples.ps examples.pdf

html: $(htmlfiles) $(pngfiles)

%.eps: %.py
	export PYTHONPATH=$(PWD)/.. ; cd $(dir $^) ; python $(notdir $^)

%.py.html: %.py
	sh -c "py2html $^"

%.eps.png: %.eps
	@# -dEPSCrop needs gs version >= 8.0
	gs8.0 -dEPSCrop -dNOPAUSE -dQUIET -dBATCH -sDEVICE=ppmraw -sOutputFile=- -r400 $^|pnmscale 0.25|pnmtopng > $^.png
