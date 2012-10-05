import sys; sys.path.insert(0, "../..")
from pyx import *

c = canvas.layered_canvas()

c.layer("1") # create layer only
c.stroke(path.line(0, 0, 1, 0))
l2 = c.layer("2")
l1a = c.layer("1.a") # note the dot, which means we're creating a subcanvas in 1

l1 = c.layer('1') # get the already created layer

l1.text(0.25, 0, "1", [color.rgb.red, text.halign.center, text.vshift.mathaxis])
l2.text(0.5, 0, "2", [color.rgb.green, text.halign.center, text.vshift.mathaxis])
l1a.text(0.75, 0, "1a", [color.rgb.blue, text.halign.center, text.vshift.mathaxis])
l1a.stroke(path.line(0.25, -0.25, 0.25, 0.25), [color.rgb.blue])

c.writeEPSfile("test_layer", paperformat=document.paperformat.A4, fittosize=1)
c.writePDFfile("test_layer", paperformat=document.paperformat.A4, fittosize=1)

