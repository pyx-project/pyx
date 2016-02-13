from pyx import *

c = canvas.canvas()
c.stroke(path.rect(0, 0, 1, 1), [style.linewidth.Thick,
                                 color.rgb.red,
                                 deco.filled([color.rgb.green])])
c.writeEPSfile("strokefill")
c.writePDFfile("strokefill")
c.writeSVGfile("strokefill")
