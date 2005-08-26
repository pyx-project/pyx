default: pyx.pdf
	#

pyx.dvi: pyx.tex unitcircle.py arrow.py springs.py text.py arrow.eps springs.eps text.eps
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

clean:
	rm pyx.dvi pyx.log pyx.aux pyx.out pyx.toc pyx.ps pyx.pdf arrow.eps springs.eps text.eps
