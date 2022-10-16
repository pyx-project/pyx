PYTHON ?= python3

default: build

publicserver = my
publicpath = pyx/www

all:
	$(MAKE) clean
	$(MAKE) build

clean:
	rm -rf build

public:
	scp -oCompression=yes -r build/* $(publicserver):$(publicpath)

build: copy html

copy:
	mkdir -p build
	cp main.css build
	cp *.ico build
	cp png/*.png ../manual/_build/latex/manual.pdf ../faq/_build/latex/pyxfaq.pdf build
	cp -r ../manual/_build/html build/manual
	cp -r ../manual/_build/html/manual.html build/manual/index.html
	cp -r ../faq/_build/html build/pyxfaq
	for d in "" $$(grep / ../examples/INDEX); \
	do \
	  mkdir -p build/examples/$$d; \
	  for t in png py ipynb jpg dat eps pdf svg; \
	  do \
	    cp ../examples/$$d*.$$t build/examples/$$d 2> /dev/null; \
	  done; \
	done; \
	for d in "" $$(grep / ../gallery/INDEX); \
	do \
	  mkdir -p build/gallery/$$d; \
	  for t in png py ipynb jpg dat eps pdf svg; \
	  do \
	    cp ../gallery/$$d*.$$t build/gallery/$$d 2> /dev/null; \
	  done; \
	done; \

html:
	$(PYTHON) pt2html.py
