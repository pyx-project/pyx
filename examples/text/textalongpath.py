from pyx import *

c = canvas.canvas()

p = path.path(path.moveto(-4, 0), path.curveto(-2, 0, -2, 1, 0, 1), path.curveto(2, 1, 2, 0, 4, 0))

c.stroke(p, [trafo.translate(0, 1), deco.curvedtext(" ".join([r"\PyX{} is fun."]*3))])
c.stroke(p, [deco.curvedtext("left", textattrs=[text.halign.left, text.vshift.mathaxis], arclenfrombegin=1, exclude=0.2),
             deco.curvedtext("right", textattrs=[text.halign.right, text.vshift.mathaxis], arclenfromend=1, exclude=0.2)])

c.writeEPSfile("textalongpath")
c.writePDFfile("textalongpath")
