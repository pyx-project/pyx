default: build

htmlfiles = $(patsubst %.pt, %.html, $(filter-out maintemplate.pt examples.pt, $(wildcard *.pt))) examples/index.html $(patsubst %, examples/%index.html, $(shell grep / ../examples/INDEX))
publicserver = shell.sourceforge.net
publicpath = /home/groups/p/py/pyx/htdocs

all:
	make clean
	make build

clean:
	rm -r build

public:
	scp -oCompression=yes -r build/* $(publicserver):$(publicpath)
	make chmod

chmod:
	-ssh $(publicserver) "cd $(publicpath); chmod -fR g+w *"

build: always
	-mkdir build
	cp main.css build
	-cp *.png *.ico build
	cp png/*.png ../manual/manual.pdf ../faq/pyxfaq.pdf build
	cp -r ../manual/manual build
	for d in "" $(shell grep / ../examples/INDEX); \
	do \
	  mkdir build/examples/$$d; \
	  for s in png py jpg dat eps pdf; \
	  do \
	    cp ../examples/$$d*.$$s build/examples/$$d 2> /dev/null; \
	  done; \
	done
	PYTHONPATH=~/bin/python/Zope3/src ./pt2html.py

always:
	@# just ensure to always build new even when the directory already exists
