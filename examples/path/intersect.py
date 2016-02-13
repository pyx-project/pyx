from pyx import *

p1 = path.curve(0, 0, 1, 0, 1, 1, 2, 1)
p2 = path.circle(1, 0.5, 0.5)

(a1, a2), (b1, b2) = p1.intersect(p2)

x1, y1 = p1.at(a1)
x2, y2 = p1.at(a2)

c = canvas.canvas()
c.fill(path.circle(x1, y1, 0.1), [color.rgb.blue])
c.fill(path.circle(x2, y2, 0.1), [color.rgb.blue])
c.stroke(p1, [color.rgb.red])
c.stroke(p2, [color.rgb.green])
c.writeEPSfile("intersect")
c.writePDFfile("intersect")
c.writeSVGfile("intersect")
