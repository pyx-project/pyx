PYTHON ?= python
PDFLATEX ?= pdflatex
LATEX ?= latex

default: pyxfaq.pdf

clean: partclean
	-rm pyxfaq.pdf glifaq.pdf glifaq.sty

partclean:
	-rm *.aux *.out *.toc *.log *.glo *.idx
	-rm pyxversion.tex pyxdate.tex

all: pdf

pdf: pyxfaq.pdf glifaq.pdf

pyxfaq.pdf: pyxfaq.tex pyxversion.tex pyxdate.tex glifaq.sty
	$(PDFLATEX) pyxfaq
	$(PDFLATEX) pyxfaq
	$(PDFLATEX) pyxfaq

glifaq.sty: glifaq.dtx glifaq.ins
	$(LATEX) glifaq.ins

glifaq.pdf: glifaq.dtx
	$(PDFLATEX) glifaq.dtx
	$(PDFLATEX) glifaq.dtx

pyxversion.tex: ../pyx/version.py
	$(PYTHON) -c "import sys;sys.path[:0]=[\"..\"];import pyx.version;print pyx.version.version+'%'" > pyxversion.tex

pyxdate.tex: ../pyx/version.py
	$(PYTHON) -c "import sys;sys.path[:0]=[\"..\"];import pyx.version;print pyx.version.date+'%'" > pyxdate.tex

publicserver = shell.sourceforge.net
publicpath = /home/groups/p/py/pyx/htdocs

public:
	@bash -c 'yn=""; while [ "x"$$yn != "xy" ]; do echo -n "upload pyxfaq.pdf? [y/n] "; read yn; if [ "x"$$yn == "xn" ]; then exit 1; fi; done'
	scp pyxfaq.pdf $(publicserver):$(publicpath)
	-ssh $(publicserver) "cd $(publicpath); chmod -fR g+w pyxfaq.pdf"

tipapyks.pdf: tipa.py
	$(PYTHON) tipa.py "pYks" "pyks"

tipapyx.pdf: tipa.py
	$(PYTHON) tipa.py "pYx" "pyx"

tipapych.pdf: tipa.py
	$(PYTHON) tipa.py "pY\\c c" "pych"
