# You need mkhowto from the python distribution for creating this manual.
# Get a copy of a current python source archive and make a symbolic link
# from <whatever>/Python-x.x.x/Doc/tools/mkhowto into this directory.
# Furthermore you need tex, latex2html and a few other things to build
# the manual (see the python documentation about creating documentations
# for details).

PYTHON ?= python

default: dvi

clean:
	-rm -fr manual.dvi *.eps *.pdf *.aux *.out *.toc *.log manual

all:
	make clean
	make html
	make pdf
	make dvi

src=$(wildcard *.tex) pyxversion.tex pyxdate.tex

dvi: manual.dvi
pdf: manual.pdf
html: manual/manual.html

manual.pdf: $(src) pdf_figs
	#for index-with-own-hyperrefs debugging, anybody interested?
	#./mkhowto --a4 --pdf --keep manual.tex
	./mkhowto --a4 --pdf manual.tex

manual.dvi: $(src) eps_figs
	./mkhowto --a4 --dvi manual.tex

manual/manual.html: $(src) eps_figs
	./mkhowto --image-type png --favicon "/pyx.ico" \
	          --up-link "/" --up-title "PyX homepage" \
	          --html manual.tex

pyxversion.tex: ../pyx/version.py
	$(PYTHON) -c "import sys;sys.path[:0]=[\"..\"];import pyx.version;print pyx.version.version+'%'" > pyxversion.tex

pyxdate.tex: ../pyx/version.py
	$(PYTHON) -c "import sys;sys.path[:0]=[\"..\"];import pyx.version;print pyx.version.date+'%'" > pyxdate.tex

eps_figs: $(patsubst %.py, %.eps, $(wildcard *.py))

pdf_figs: $(patsubst %.py, %.pdf, $(wildcard *.py))

%.eps: %.py
	export PYTHONPATH=$(CURDIR)/.. ; $(PYTHON) $^

%.pdf: %.py
	export PYTHONPATH=$(CURDIR)/.. ; $(PYTHON) $^
