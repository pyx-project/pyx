from pyx import *

c = canvas.canvas()

rect1 = path.path(path.moveto(0, 0), path.lineto(0, 1),
                  path.lineto(1, 1), path.lineto(1, 0),
                  path.lineto(0, 0))

rect2 = path.path(path.moveto(0, 0), path.lineto(0, 1),
                  path.lineto(1, 1), path.lineto(1, 0),
                  path.closepath())

c.stroke(rect1, [trafo.scale(2), style.linewidth.THICK])
c.text(1, -0.7, "not closed", [text.halign.center])
c.stroke(rect2, [trafo.scale(2).translated(4, 0), style.linewidth.THICK])
c.text(5, -0.7, "closed", [text.halign.center])

c.stroke(rect2, [trafo.scale(2).translated(8, 0), style.linewidth.THICK, deco.filled([color.grey(0.95)])])
c.text(9, -0.7, "filled", [text.halign.center])

c.writeEPSfile("rects", paperformat="a4")

