from pyx import *

c = canvas.canvas()

c.stroke(path.line(-5, 0, -5, 5))
c.stroke(path.line(0, 0, 0, 5))
c.stroke(path.line(5, 0, 5, 5))

c.text(-5, 5, r"boxleft", [text.halign.boxleft])
c.text(0, 5, r"boxcenter", [text.halign.boxcenter])
c.text(5, 5, r"boxright", [text.halign.boxright])

c.text(0, 4, r"boxcenter and flushleft",
       [text.parbox(3), text.halign.boxcenter, text.halign.flushleft])
c.text(0, 3, r"boxcenter and flushcenter",
       [text.parbox(3), text.halign.boxcenter, text.halign.flushcenter])
c.text(0, 2, r"boxcenter and flushright",
       [text.parbox(3), text.halign.boxcenter, text.halign.flushright])

c.text(-5, 0, r"left: boxleft and flushleft",
       [text.parbox(3), text.halign.left])
c.text(0, 0, r"center: boxcenter and flushcenter",
       [text.parbox(3), text.halign.center])
c.text(5, 0, r"right: boxright and flushright",
       [text.parbox(3), text.halign.right])

c.writeEPSfile("halign")
c.writePDFfile("halign")
c.writeSVGfile("halign")
