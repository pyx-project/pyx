from pyx import *

c = canvas.canvas()

rect1 = path.path(path.moveto(0, 0), path.lineto(1, 0),
                  path.moveto(1, 0), path.lineto(1, 1),
                  path.moveto(1, 1), path.lineto(0, 1),
                  path.moveto(0, 1), path.lineto(0, 0))
rect2 = path.path(path.moveto(2, 0), path.lineto(3, 0),
                  path.lineto(3, 1), path.lineto(2, 1),
                  path.lineto(2, 0))
rect3 = path.path(path.moveto(4, 0), path.lineto(5, 0),
                  path.lineto(5, 1), path.lineto(4, 1),
                  path.closepath())

c.stroke(rect1, [style.linewidth.THICK])
c.stroke(rect2, [style.linewidth.THICK])
c.stroke(rect3, [style.linewidth.THICK])

c.writeEPSfile("pathitem")
c.writePDFfile("pathitem")
c.writeSVGfile("pathitem")
