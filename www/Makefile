default: html

clean:
	-rm *.html

all:
	make clean
	make install

ptfiles = $(filter-out maintemplate.pt, $(wildcard *.pt))
htmlfiles = $(patsubst %.pt, %.html, $(ptfiles))
pngfiles = valid-html401.png vcss.png
cssfiles = main.css

html: $(htmlfiles) $(pngfiles)

install: html
	cp $(htmlfiles) $(pngfiles) $(cssfiles) ~/public-html/pyx
	cd png; make
	cp png/*.png ~/public-html/pyx

%.html: %.pt maintemplate.pt
	PYTHONPATH=~/bin/python/Zope3/src ./pt2html.py $<

%.eps.png: %.eps
	@# -dEPSCrop needs gs version >= 8.0
	gs8.0 -dEPSCrop -dNOPAUSE -dQUIET -dBATCH -sDEVICE=ppmraw -sOutputFile=- -r400 $^|pnmscale 0.25|pnmtopng > $^.png
