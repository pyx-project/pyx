from pyx import *

c = canvas.canvas()
c.text(0, 0, "Hello, world!")
c.stroke(path.line(0, 0, 2, 0))
c.writeEPSfile()
c.writePDFfile()
c.writeSVGfile()
