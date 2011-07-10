from pyx import *

c = canvas.canvas()

circle = path.circle(0, 0, 2)
line = path.line(-3, 1, 3, 2)
c.stroke(circle, [style.linewidth.Thick])
c.stroke(line, [style.linewidth.Thick])

isects_circle, isects_line = circle.intersect(line)
for isect in isects_circle:
    isectx, isecty = circle.at(isect)
    c.stroke(path.line(0, 0, isectx, isecty))

c.writePDFfile()
