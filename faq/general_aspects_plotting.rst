====================================
General aspects of plotting with PyX
====================================

How do I generate multipage output?
===================================

With versions 0.8 and higher it is possible to produce multipage output,
i.e. a Postscript or PDF file containing more than one page. In order to
achieve this, one creates pages by drawing on a canvas as usual and 
appends them in the desired order to a document from which Postscript or
PDF output is produced. The following example serves as an illustration::

   from pyx import *

   d = document.document()
   for i in range(3):
       c = canvas.canvas()
       c.text(0, 0, "page %i" % (i+1))
       d.append(document.page(c, paperformat=document.paperformat.A4,
                                 margin=3*unit.t\_cm,
                                 fittosize=1))
   d.writePSfile("multipage")

Here, ``d`` is the document into which pages are inserted by means of the
``append`` method. When converting from a canvas to a document page, the page
properties like the paperformat are specified. In the last line, output is
produced from document ``d``.
