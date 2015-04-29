from pyx import *

c = canvas.canvas()
c.stroke(path.line(0, 0, 4, 0),
         [style.linewidth.THICK, style.linestyle.dashed, color.rgb.red])
c.stroke(path.line(0, -1, 4, -1),
         [style.linewidth(0.2), style.linecap.round, color.rgb.green])
c.fill(path.rect(0, -3, 4, 1), [color.rgb.blue])
c.writeEPSfile("style")
c.writePDFfile("style")
c.writeSVGfile("style")
