from pyx import *

def mark(x, y):
    return path.circle(x, y, 0.1)

c = canvas.canvas()

p1 = path.curve(0, 0, 1, 0, 1, 1, 2, 1)
c.stroke(p1)
c.fill(mark(*p1.atbegin()))
c.fill(mark(*p1.at(0.5*p1.arclen())))
c.fill(mark(*p1.atend()))

p2 = path.curve(3, 0, 4, 0, 4, 1, 5, 1)
c.stroke(p2)
c.fill(mark(*p2.at(p2.begin()+0.5)))
c.fill(mark(*p2.at(p2.end()-0.5)))

c.writeEPSfile("at")
c.writePDFfile("at")
c.writeSVGfile("at")
