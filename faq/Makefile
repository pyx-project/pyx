default: pyxfaq.pdf

clean: partclean
	-rm pyxfaq.pdf glifaq.pdf glifaq.sty

partclean:
	-rm *.aux *.out *.toc *.log *.glo *.idx 

all: pdf

pdf: pyxfaq.pdf glifaq.pdf

pyxfaq.pdf: pyxfaq.tex glifaq.sty
	pdflatex pyxfaq
	pdflatex pyxfaq
	pdflatex pyxfaq

glifaq.sty: glifaq.dtx glifaq.ins
	latex glifaq.ins

glifaq.pdf: glifaq.dtx
	pdflatex glifaq.dtx
	pdflatex glifaq.dtx
