default: build

htmlfiles = $(patsubst %.pt, %.html, $(filter-out maintemplate.pt examples.pt, $(wildcard *.pt))) examples/index.html $(patsubst %, examples/%index.html, $(shell grep / ../examples/INDEX))
imagefiles = valid-html401.png vcss.png pyx.ico
cssfiles = main.css
publicserver = shell.sourceforge.net
publicpath = /home/groups/p/py/pyx/htdocs

all:
	make clean
	make build

clean:
	rm -r build

public:
	scp -oCompression=yes -r build/* $(publicserver):$(publicpath)
	-ssh $(publicserver) "cd $(publicpath); chmod -fR g+w *"

build: htmlfiles always
	cp $(imagefiles) $(cssfiles) build
	cp png/*.png ../manual/manual.pdf ../faq/pyxfaq.pdf build
	cp -r ../manual/manual build
	for d in "" $(shell grep / ../examples/INDEX); do cp ../examples/$$d*.png ../examples/$$d*.eps build/examples/$$d; done

htmlfiles: $(htmlfiles)

%.html: $(wildcard *.pt) pt2html.py
	PYTHONPATH=/usr/src/ZopeCVS/Zope3/src:~/bin/python/Zope3/src ./pt2html.py $@

always:
	@# just ensure to always build new even when the directory already exists
