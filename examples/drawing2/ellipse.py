from pyx import *

c = canvas.canvas()
circ = path.circle(0, 0, 1)

# variant 1: use trafo as a deformer
c.stroke(circ, [style.linewidth.THIck, 
                trafo.scale(sx=2, sy=0.9), trafo.rotate(45), trafo.translate(1, 0)])

# variant 2: transform a subcanvas
sc = canvas.canvas()
sc.stroke(circ, [style.linewidth.THIck])
c.insert(sc, [trafo.scale(sx=2, sy=0.9), trafo.rotate(45), trafo.translate(5, 0)])

c.writeEPSfile("ellipse")
c.writePDFfile("ellipse")
c.writeSVGfile("ellipse")
