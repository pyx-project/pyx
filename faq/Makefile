default: pyxfaq.pdf

clean: partclean
	-rm pyxfaq.pdf glifaq.pdf glifaq.sty

partclean:
	-rm *.aux *.out *.toc *.log *.glo *.idx
	-rm pyxversion.tex pyxdate.tex

all: pdf

pdf: pyxfaq.pdf glifaq.pdf

pyxfaq.pdf: pyxfaq.tex pyxversion.tex pyxdate.tex glifaq.sty
	pdflatex pyxfaq
	pdflatex pyxfaq
	pdflatex pyxfaq

glifaq.sty: glifaq.dtx glifaq.ins
	latex glifaq.ins

glifaq.pdf: glifaq.dtx
	pdflatex glifaq.dtx

pyxversion.tex: ../pyx/version.py
	python -c "import sys;sys.path[:0]=[\"..\"];import pyx.version;print pyx.version.version+'%'" > pyxversion.tex

pyxdate.tex: ../pyx/version.py
	python -c "import sys;sys.path[:0]=[\"..\"];import pyx.version;print pyx.version.date+'%'" > pyxdate.tex
