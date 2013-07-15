from pyx import *

c = canvas.canvas()

rect1 = path.path(path.moveto(0, 0), path.lineto(1, 0),
                  path.moveto(1, 0), path.lineto(1, 1),
                  path.moveto(1, 1), path.lineto(0, 1),
                  path.moveto(0, 1), path.lineto(0, 0))

rect2 = path.path(path.moveto(0, 0), path.lineto(0, 1),
                  path.lineto(1, 1), path.lineto(1, 0),
                  path.lineto(0, 0))

rect3 = path.path(path.moveto(0, 0), path.lineto(0, 1),
                  path.lineto(1, 1), path.lineto(1, 0),
                  path.closepath())

c.stroke(rect1, [trafo.scale(2), style.linewidth.THICK])
c.text(1, -0.7, "(a)", [text.halign.center])

c.stroke(rect2, [trafo.scale(2).translated(4, 0), style.linewidth.THICK])
c.text(5, -0.7, "(b)", [text.halign.center])

c.stroke(rect3, [trafo.scale(2).translated(8, 0), style.linewidth.THICK])
c.text(9, -0.7, "(c)", [text.halign.center])

c.stroke(rect3, [trafo.scale(2).translated(12, 0), style.linewidth.THICK, deco.filled([color.grey(0.5)])])
c.text(13, -0.7, "(d)", [text.halign.center])

c.writePDFfile()
