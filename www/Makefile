default: build

clean:
	-rm *.html
	rm -r build

all:
	make clean
	make build

ptfiles = $(filter-out maintemplate.pt, $(wildcard *.pt))
htmlfiles = $(patsubst %.pt, %.html, $(ptfiles))
imagefiles = valid-html401.png vcss.png pyx.ico
cssfiles = main.css
builddir = build
exampledirs = $(shell cd ..; find examples -type d|grep -v CVS)
publicserver = shell.sourceforge.net
publicpath = /home/groups/p/py/pyx/htdocs

public: build
	scp -oCompression=yes -r $(builddir)/* $(publicserver):$(publicpath)
	-ssh $(publicserver) "cd $(publicpath); chmod -R g+w *"

build: htmlfiles otherhtml
	-rm -r $(builddir)
	mkdir $(builddir)
	cp $(htmlfiles) $(imagefiles) $(cssfiles) $(builddir)
	cp png/*.png ../manual/manual.pdf ../faq/pyxfaq.pdf $(builddir)
	cp -r ../manual/manual $(builddir)
	echo $(exampledirs)
	for d in $(exampledirs); do mkdir $(builddir)/$$d; cp ../$$d/*.png ../$$d/*.eps $(builddir)/$$d; done

htmlfiles: $(htmlfiles)

%.html: %.pt maintemplate.pt pt2html.py
	PYTHONPATH=/usr/src/ZopeCVS/Zope3/src:~/bin/python/Zope3/src ./pt2html.py $<

otherhtml:
	cd png; make
	cd ../examples; make html
	cd ../manual; make pdf
	cd ../manual; make html
	cd ../faq; make

