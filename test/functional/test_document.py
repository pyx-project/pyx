import sys; sys.path[:0] = ["../.."]

from pyx import *

d = document.document()

for nr in range(1, 10):
     c = canvas.canvas()
     if nr != 7:
         c.text(0, 0, "page %d" % nr)
     d.append(document.page(c, pagename=chr(64+nr), rotated=(nr-1)%2, fittosize=1, paperformat=document.paperformat.A4))

d.writePSfile("test_document")
d.writePDFfile("test_document")

