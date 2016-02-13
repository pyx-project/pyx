from pyx import *

c = canvas.canvas()
p = path.line(0, 0, 2, 2)
p.append(path.curveto(2, 0, 3, 0, 4, 0))
c.stroke(p)
c.stroke(p, [deformer.parallel(0.2), color.rgb.blue])
c.stroke(p, [deformer.parallel(-0.2), color.rgb.red])
c.writeEPSfile("parallel")
c.writePDFfile("parallel")
c.writeSVGfile("parallel")
