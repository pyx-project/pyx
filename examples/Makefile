default: examples.dvi

clean:
	-rm -f examples.tex examples.log examples.aux examples.dvi examples.ps examples.pdf *.eps */*.eps *.py.html */*.py.html *.png */*.png

all:
	make clean
	make pdf
	make html

pdf: examples.pdf
ps: examples.ps
dvi: examples.dvi

examples.pdf: examples.ps
	ps2pdf examples.ps

examples.ps: examples.dvi
	dvips -o examples.ps examples.dvi

files = $(foreach item, $(shell grep -v / INDEX), $(item)) $(foreach item, $(shell grep / INDEX), $(addprefix $(item), $(shell cat $(item)INDEX)))
pyfiles = $(addsuffix .py, $(files))
htmlfiles = $(addsuffix .py.html, $(files))
epsfiles = $(addsuffix .eps, $(files))
pngfiles = $(addsuffix .png, $(files))

eps: $(epsfiles)

examples.dvi: examples.py $(epsfiles)
	python examples.py $(basename $(pyfiles))
	latex examples.tex
	-rm -f examples.ps examples.pdf

html: $(htmlfiles) $(pngfiles)

%.eps: %.py
	cd $(dir $^); PYTHONPATH=$(PWD)/.. python $(notdir $^)

%.py.html: %.py
	sh -c "py2html -format:rawhtml $^"

%.png: %.eps
	python ../contrib/epstopng.py -o $@ $^
