#TODO: - mutliple python runs when appropriate (new tex handling will render it unnecessary)

default: examples.dvi

pdf: examples.pdf
ps: examples.ps
dvi: examples.dvi

examples.pdf: examples.ps
	ps2pdf examples.ps

examples.ps: examples.dvi
	dvips examples.dvi

pyfiles = $(filter-out examples.py,$(wildcard *.py)) $(wildcard */*.py)
epsfiles = $(patsubst %.py, %.eps, $(pyfiles))

examples.dvi: examples.py $(epsfiles)
	python examples.py $(basename $(epsfiles))
	latex examples.tex
	-rm examples.ps examples.pdf

%.eps: %.py
	cd $(dir $^) && python $(notdir $^)
