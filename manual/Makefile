# Makefile for Sphinx documentation
#

PYTHON ?= python

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
	make -C $(BUILDDIR)/latex all-pdf
	@echo "pdflatex finished; the PDF files are in $(BUILDDIR)/latex."

figs: $(patsubst %.py, %.png, $(filter-out conf.py,$(wildcard *.py)))

%.png: %.py
	export PYTHONPATH=$(CURDIR)/.. ; $(PYTHON) $^
	$(PYTHON) ../contrib/epstopng.py -o $@ $*.pdf
