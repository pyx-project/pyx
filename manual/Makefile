#TODO: - mutliple python runs when appropriate (new tex handling will render it unnecessary)

default: manual.dvi

clean:
	-rm -f manual.dvi manual.ps manual.pdf *.eps *.aux *.out *.toc *.log

all:
	make clean
	make pdf

pdf: manual.pdf
ps: manual.ps
dvi: manual.dvi

manual.pdf: manual.ps
	ps2pdf manual.ps

manual.ps: manual.dvi
	dvips -o manual.ps manual.dvi

manual.dvi: $(wildcard *.tex) $(patsubst %.py, %.eps, $(wildcard *.py)) pyxversion.tex
	./runlatex.sh manual.tex
	-rm -f manual.ps manual.pdf

pyxversion.tex: ../pyx/version.py
	python -c "import sys;sys.path[:0]=[\"..\"];import pyx.version;print pyx.version.version" > pyxversion.tex

%.eps: %.py
	export PYTHONPATH=$(PWD)/.. ; python $^
