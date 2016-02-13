from pyx import *

c = canvas.canvas()

p1 = path.curve(0, 0, 1, 0, 1, 1, 2, 1)
p2 = path.line(0, 0, p1.arclen(), 0)
c.stroke(p1)
c.stroke(p2)

c.writeEPSfile("arclen")
c.writePDFfile("arclen")
c.writeSVGfile("arclen")
