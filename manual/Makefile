# Makefile for Sphinx documentation
#

PYTHON ?= python3
GS ?= gs

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
PAPER         =
BUILDDIR      = _build

# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d $(BUILDDIR)/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .

.PHONY: help clean all html latexpdf figs

all: html latexpdf
	@echo "Done."

clean:
	-rm -rf $(BUILDDIR)/* *.pdf *.png

html: figs
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(BUILDDIR)/html
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/html."

latexpdf: figs
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) $(BUILDDIR)/latex
	@echo "Running LaTeX files through pdflatex..."
	$(MAKE) -C $(BUILDDIR)/latex all-pdf
	@echo "pdflatex finished; the PDF files are in $(BUILDDIR)/latex."

doctest:
	cd ../pyx;$(SPHINXBUILD) -b doctest ../manual ../manual/$(BUILDDIR)/doctest

figs: $(patsubst %.py, %.png, $(filter-out conf.py,$(wildcard *.py)))

%.pdf: %.py
	$(PYTHON) $^

%.png: %.pdf
	$(GS) -r100 -dNOPAUSE -dQUIET -dBATCH -sDEVICE=pngalpha -dTextAlphaBits=4 -dGraphicsAlphaBits=4 -sOutputFile=$@ $^
