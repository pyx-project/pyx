from pyx import *
unit.set(uscale=2, xscale=2)

col = color.cmyk.PineGreen

text.set(text.LatexEngine)
text.preamble(r"\usepackage{color}")
text.preamble(r"\definecolor{COL}{cmyk}{%g,%g,%g,%g}" % (col.c, col.m, col.y, col.k))

c = canvas.canvas()
c.text(0, 0, r"\textcolor{COL}{Text} and outline have the same color")
c.stroke(path.rect(-0.2, -0.2, 6.2, 0.6), [col])
c.writeEPSfile("color")
c.writePDFfile("color")
c.writeSVGfile("color")
