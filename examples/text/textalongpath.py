from pyx import *

c = canvas.canvas()

p = path.path(path.moveto(-4, 0), path.curveto(-2, 0, -2, 1, 0, 1), path.curveto(2, 1, 2, 0, 4, 0))
label = " ".join([r"\PyX{} is fun."]*3)

c.draw(p, [trafo.translate(0, 1), deco.stroked([color.rgb.blue]), deco.curvedtext(label)])
c.draw(p, [deco.stroked([color.rgb.red]), deco.curvedtext(label, textattrs=[text.vshift.mathaxis], exclude=0.2)])

c.writeEPSfile("textalongpath")
c.writePDFfile("textalongpath")
