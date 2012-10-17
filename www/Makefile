PYTHON ?= python

default: build

publicserver = web.sourceforge.net
publicpath = /home/groups/p/py/pyx/htdocs

all:
	make clean
	make build

clean:
	rm -r build

public:
	scp -oCompression=yes -r build/* $(publicserver):$(publicpath)

build: copy html

copy:
	mkdir -p build
	cp main.css build
	cp *.png *.ico build
	cp png/*.png ../manual/_build/latex/manual.pdf ../faq/_build/latex/pyxfaq.pdf build
	cp -r ../manual/_build/html build/manual
	cp -r ../manual/_build/html/manual.html build/manual/index.html
	cp -r ../faq/_build/html build/pyxfaq
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
	$(PYTHON) pt2html.py
