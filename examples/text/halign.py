# The horizontal alignment of text distinguishes between the
# alignment of the box and the alignment of the material within
# the box (when there are several lines, i.e. we have a parbox).
# The halign.left/center/right attributes combine both alignments.

from pyx import *

# you can use it in TeX and LaTeX ...
# text.set(mode="latex")

c = canvas.canvas()

c.set([style.linestyle.dotted])
c.stroke(path.line(-5, 0, -5, 4))
c.stroke(path.line(0, 0, 0, 4))
c.stroke(path.line(5, 0, 5, 4))

c.text(-5, 4, r"Hello, world!", [text.halign.boxleft])
c.text(0, 4, r"Hello, world!", [text.halign.boxcenter])
c.text(5, 4, r"Hello, world!", [text.halign.boxright])

c.text(0, 3, r"Hello,\par world!", [text.parbox(2.5), text.halign.boxcenter, text.halign.flushleft])
c.text(0, 2, r"Hello,\par world!", [text.parbox(2.5), text.halign.boxcenter, text.halign.flushcenter])
c.text(0, 1, r"Hello,\par world!", [text.parbox(2.5), text.halign.boxcenter, text.halign.flushright])

c.text(-5, 0, r"Hello,\par world!", [text.parbox(2.5), text.halign.left])
c.text(0, 0, r"Hello,\par world!", [text.parbox(2.5), text.halign.center])
c.text(5, 0, r"Hello,\par world!", [text.parbox(2.5), text.halign.right])

c.writeEPSfile("halign")
c.writePDFfile("halign")
