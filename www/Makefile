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
builddir = build

html: $(htmlfiles) $(pngfiles)
	cd png; make

install: html
	-mkdir $(builddir)
	cp $(htmlfiles) $(pngfiles) $(cssfiles) $(builddir)
	cd png; make
	cp png/*.png ../examples/*.png ../examples/*/*.png $(builddir)
	cp ../examples/*.eps ../examples/*/*.eps $(builddir)
	cp ../manual/manual.pdf $(builddir)
	chmod -R 664 $(builddir)/*
	scp -oCompression=yes -p -r $(builddir)/* shell.sourceforge.net:/home/groups/p/py/pyx/htdocs

%.html: %.pt maintemplate.pt pt2html.py
	PYTHONPATH=/usr/src/ZopeCVS/Zope3/src:~/bin/python/Zope3/src ./pt2html.py $<
