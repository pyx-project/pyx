from pyx import *

c = canvas.canvas()

circ = path.circle(0, 0, 2)
line = path.line(-3, 1, 3, 2)
c.stroke(circ)
c.stroke(line)

isects = circ.intersect(line)[0]
for isect in isects:
    c.stroke(path.line(0, 0, *circ.at(isect)))

c.writeEPSfile("radii")
