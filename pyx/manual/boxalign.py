import math
from pyx import *

c = canvas.canvas()
t1 = text.text(0, 0, "circle align", [text.halign.center, text.size.huge])
x, y = t1.circlealignvector(1, 1, 1)
t1.circlealign(1, 1, 1)
c.stroke(path.path(path.arc(0, 0, 1, -30, 120)), [style.linestyle.dashed])
c.stroke(t1.path(centerradius=0.05), [style.linewidth.THin])
c.stroke(path.line(0, 0, x, y), [deco.earrow.normal])
c.insert(t1)
t2 = text.text(5, 0, "line align", [text.halign.center, text.size.huge])
x, y = t2.linealignvector(1, 1, 1)
t2.linealign(1, 1, 1)
c.stroke(path.line(5 + 1.5 * math.sqrt(2), -0.5 * math.sqrt(2), 5 - 0.5 * math.sqrt(2), 1.5 * math.sqrt(2)), [style.linestyle.dashed])
c.stroke(t2.path(centerradius=0.05), [style.linewidth.THin])
c.stroke(path.line(5, 0, 5 + x, y), [deco.earrow.normal])
c.insert(t2)
c.writePDFfile()

