from pyx import *

c = canvas.canvas()

p = path.path(path.moveto(-2, 0), path.curveto(-1, 0, -1, 1, 0, 1), path.curveto(1, 1, 1, 0, 2, 0))

c.stroke(p, [deco.curvedtext(r"\PyX{} is fun!"),
             deco.curvedtext("left", textattrs=[text.halign.left, text.vshift.mathaxis], arclenfrombegin=0.5, exclude=0.1),
             deco.curvedtext("right", textattrs=[text.halign.right, text.vshift.mathaxis], arclenfromend=0.5, exclude=0.1)])

c.writeEPSfile("textalongpath")
c.writePDFfile("textalongpath")
c.writeSVGfile("textalongpath")
