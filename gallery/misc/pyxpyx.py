from pyx import *

textpath = text.text(0, 0, r"\PyX").textpath().reversed()
decotext = r"\PyX{} is fun! "*50
scale = text.text(0, 0, decotext).width/textpath.arclen()

c = canvas.canvas()
c.draw(textpath, [trafo.scale(scale),
                  deco.filled([color.gray(0.5)]),
                  deco.curvedtext(decotext)])
c.writeEPSfile()
c.writePDFfile()
c.writeSVGfile()
