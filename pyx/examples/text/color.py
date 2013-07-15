from pyx import *
unit.set(uscale=2, xscale=2)

col = color.cmyk.PineGreen

text.set(mode="latex")
text.preamble(r"\usepackage{color}")
text.preamble(r"\definecolor{COL}{cmyk}{%(c)g,%(m)g,%(y)g,%(k)g}" % col.color)

c = canvas.canvas()
c.text(0, 0, r"\textcolor{COL}{Text} and outline have the same color")
c.stroke(path.rect(-0.2, -0.2, 6.2, 0.6), [col])
c.writeEPSfile("color")
c.writePDFfile("color")
