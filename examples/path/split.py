from pyx import *

p = path.curve(0, 0, 1, 0, 1, 1, 2, 1)
p1, p2, p3 = p.split([0.5, p.end()-0.5])

c = canvas.canvas()
c.stroke(p, [style.linewidth.Thin, color.rgb.red])
c.stroke(p2, [style.linewidth.Thick, color.rgb.green])
c.writeEPSfile("split")
c.writePDFfile("split")
c.writeSVGfile("split")
