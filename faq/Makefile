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

publicserver = shell.sourceforge.net
publicpath = /home/groups/p/py/pyx/htdocs

public:
	@bash -c 'yn=""; while [ "x"$$yn != "xy" ]; do echo -n "upload pyxfaq.pdf? [y/n] "; read yn; if [ "x"$$yn == "xn" ]; then exit 1; fi; done'
	scp pyxfaq.pdf $(publicserver):$(publicpath)
	-ssh $(publicserver) "cd $(publicpath); chmod -fR g+w pyxfaq.pdf"
