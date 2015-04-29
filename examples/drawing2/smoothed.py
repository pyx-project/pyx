from pyx import *

c = canvas.canvas()
p = path.line(0, 0, 2, 2)
p.append(path.curveto(2, 0, 3, 0, 4, 0))
c.stroke(p)
c.stroke(p, [deformer.smoothed(1.0), color.rgb.blue])
c.stroke(p, [deformer.smoothed(2.0), color.rgb.red])
c.writeEPSfile("smoothed")
c.writePDFfile("smoothed")
c.writeSVGfile("smoothed")
