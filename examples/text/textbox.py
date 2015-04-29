from pyx import *
unit.set(xscale=3)

tbox = text.text(0, 0, r"Boxed text")
tpath = tbox.bbox().enlarged(3*unit.x_pt).path()

c = canvas.canvas()
c.draw(tpath, [deco.filled([color.cmyk.Yellow]), deco.stroked()])
c.insert(tbox)
c.writeEPSfile("textbox")
c.writePDFfile("textbox")
c.writeSVGfile("textbox")
