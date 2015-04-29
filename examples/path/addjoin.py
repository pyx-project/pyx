from pyx import *

unit.set(wscale=10)

c = canvas.canvas()

c.stroke(path.line(0, 0, 1, 0) +
         path.line(1, 0, 1, 1) +
         path.line(1, 1, 0, 1) +
         path.line(0, 1, 0, 0))

c.stroke(path.line(2, 0, 3, 0) <<
         path.line(3, 0, 3, 1) <<
         path.line(3, 1, 2, 1) <<
         path.line(2, 1, 2, 0))

p = path.line(4, 0, 5, 0) << path.line(5, 0, 5, 1) << path.line(5, 1, 4, 1)
p.append(path.closepath())
c.stroke(p)

c.writeEPSfile("addjoin")
c.writePDFfile("addjoin")
c.writeSVGfile("addjoin")
