#TODO: - mutliple python runs when appropriate (new tex handling will render it unnecessary)

default: manual.dvi

pdf: manual.pdf
ps: manual.ps
dvi: manual.dvi

manual.pdf: manual.ps
	ps2pdf manual.ps

manual.ps: manual.dvi
	dvips manual.dvi

manual.dvi: $(wildcard *.tex) $(patsubst %.py, %.eps, $(wildcard *.py)) pyxversion.tex
	./runlatex.sh manual.tex
	-rm manual.ps manual.pdf

pyxversion.tex: ../pyx/__init__.py
	python -c "import sys;sys.path[:0]=[\"..\"];import pyx;print pyx.__version__" > pyxversion.tex

%.eps: %.py
	python $^
