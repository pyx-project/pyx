import sys; sys.path.insert(0, "../..")
from pyx import *

c = canvas.canvas()

l1b = c.layer("1.b")
c.stroke(path.line(0, 0, 1, 0))
l2 = c.layer("2")
l1a = c.layer("1.a", below="1.b")

l1b.text(0.22, 0, "1b", [color.rgb.red, text.halign.center, text.vshift.mathaxis])
l2.text(0.5, 0, "2", [color.rgb.green, text.halign.center, text.vshift.mathaxis])
l1a.text(0.75, 0, "1a", [color.rgb.blue, text.halign.center, text.vshift.mathaxis])
l1a.stroke(path.line(0.25, -0.25, 0.25, 0.25), [color.rgb.blue])

c.writeEPSfile("test_layer", page_paperformat=document.paperformat.A4, page_fittosize=1)
c.writePDFfile("test_layer", page_paperformat=document.paperformat.A4, page_fittosize=1)

