# You need mkhowto from the python distribution for creating this manual.
# Get a copy of a current python source archive and make a symbolic link
# from <whatever>/Python-x.x.x/Doc/tools/mkhowto into this directory.
# Furthermore you need tex, latex2html and a few other things to build
# the manual (see the python documentation about creating documentations
# for details).

default:dvi

clean:
	-rm -fr manual.dvi manual.ps manual.pdf *.eps *.png *.aux manual

all:
	make clean
	make html
	make pdf
	make dvi
	make ps

src=$(wildcard *.tex) pyxversion.tex pyxdate.tex

dvi:manual.dvi
ps:manual.ps
pdf:manual.pdf
html:manual/manual.html

manual.pdf: $(src) png
	#for index-with-own-hyperrefs debugging, anybody interested?
	#./mkhowto --a4 --pdf --keep manual.tex
	./mkhowto --a4 --pdf manual.tex

manual.ps: manual.dvi
	dvips -o manual.ps manual.dvi

manual.dvi: $(src) eps
	./mkhowto --a4 --dvi manual.tex

manual/manual.html: $(src) eps
	# move pdf png's out of the way
	-rm -f *.png
	./mkhowto --image-type png --favicon "/pyx.ico" \
	          --up-link "/" --up-title "PyX homepage" \
	          --html manual.tex

pyxversion.tex: ../pyx/version.py
	python -c "import sys;sys.path[:0]=[\"..\"];import pyx.version;print pyx.version.version+'%'" > pyxversion.tex

pyxdate.tex: ../pyx/version.py
	python -c "import sys;sys.path[:0]=[\"..\"];import pyx.version;print pyx.version.date+'%'" > pyxdate.tex

eps: $(patsubst %.py, %.eps, $(wildcard *.py))
png: $(patsubst %.py, %.png, $(wildcard *.py))

%.eps: %.py
	export PYTHONPATH=$(PWD)/.. ; python $^

%.png: %.eps
	gs -dEPSCrop -dNOPAUSE -dQUIET -dBATCH -sDEVICE=png16m -sOutputFile=$@ -r600 $^

