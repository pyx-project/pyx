from pyx import *

c = canvas.canvas()
c.stroke(path.circle(0, 0, 1), [trafo.scale(sx=2, sy=1.5),
                                trafo.rotate(45),
                                trafo.translate(1, 0)])
c.writeEPSfile("ellipse")
c.writePDFfile("ellipse")
