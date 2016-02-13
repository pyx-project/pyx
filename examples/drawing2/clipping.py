from pyx import *

clippath = path.circle(0, 0, 1)
drawpath = path.line(-2, -2, 1.2, 2)

cl = canvas.canvas([canvas.clip(clippath)])
cl.stroke(drawpath, [color.rgb.red, style.linewidth(1.0)])

c = canvas.canvas()
c.stroke(drawpath, [style.linewidth(1.0)])
c.insert(cl)
c.stroke(clippath)

c.writeEPSfile("clipping")
c.writePDFfile("clipping")
c.writeSVGfile("clipping")
