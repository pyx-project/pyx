from pyx import *

p = pattern.pattern()
p.text(0, 0, r"\PyX")

c = canvas.canvas()
c.text(0, 0, r"\PyX", [trafo.scale(25), p])
c.writeEPSfile()
c.writePDFfile()
c.writeSVGfile()
