import sys; sys.path.insert(0, "../..")
from pyx import *

c = canvas.canvas()

p = path.rect(0, 0, 3, 3) + path.rect(1, 1, 1, 1)

c.fill(p)

c.fill(p, [trafo.translate(4, 0), style.fillrule.even_odd])

c.writeEPSfile(paperformat=document.paperformat.A4, fittosize=1)
c.writePDFfile(paperformat=document.paperformat.A4, fittosize=1)

