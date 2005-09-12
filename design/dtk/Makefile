default: pyx.pdf
	#

pyx.dvi: pyx.tex unitcircle.py arrow.py springs.py text.py piaxis.py arrow.eps springs.eps text.eps valign.eps piaxis.eps
	latex pyx
	latex pyx

pyx.ps: pyx.dvi
	dvips pyx

pyx.pdf: pyx.ps
	ps2pdf -sPAPERSIZE=a4 pyx.ps

arrow.eps: arrow.py
	PYTHONPATH=../.. python arrow.py

springs.eps: springs.py
	PYTHONPATH=../.. python springs.py

text.eps: text.py
	PYTHONPATH=../.. python text.py

valign.eps: valign.py
	PYTHONPATH=../.. python valign.py

piaxis.eps: piaxis.py
	PYTHONPATH=../.. python piaxis.py

clean:
	rm pyx.dvi pyx.log pyx.aux pyx.out pyx.ps pyx.pdf arrow.eps springs.eps text.eps valign.eps piaxis.eps
