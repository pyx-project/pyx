ZOPEDIR ?= $(HOME)/bin/python/Zope3/src
PYTHON ?= python

default: build

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

build: copy html

copy:
	mkdir -p build
	cp main.css build
	cp *.png *.ico build
	cp png/*.png ../manual/manual.pdf ../faq/pyxfaq.pdf build
	cp -r ../manual/manual build
	for s in examples gallery; \
	do \
	  for d in "" $$(grep / ../$$s/INDEX); \
	  do \
	    mkdir -p build/$$s/$$d; \
	    for t in png py jpg dat eps pdf; \
	    do \
	      cp ../$$s/$$d*.$$t build/$$s/$$d 2> /dev/null; \
	    done; \
	  done; \
	done

html:
	PYTHONPATH=$(ZOPEDIR) $(PYTHON) pt2html.py
