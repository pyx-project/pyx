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
	cp -r icons build
	cp png/*.png ../manual/manual.pdf ../faq/pyxfaq.pdf build
	cp -r ../manual/manual build
	for d in "" $(shell grep / ../examples/INDEX); do mkdir build/examples/$$d; cp ../examples/$$d*.png ../examples/$$d*.eps build/examples/$$d; done
	PYTHONPATH=~/bin/python/Zope3/src ./pt2html.py

always:
	@# just ensure to always build new even when the directory already exists
