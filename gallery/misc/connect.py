from pyx import *
from pyx.connector import arc, curve

unit.set(uscale=3)

c = canvas.canvas()

textattrs = [text.halign.center, text.vshift.middlezero]
A = text.text(0, 0, r"\bf A", textattrs)
B = text.text(1, 0, r"\bf B", textattrs)
C = text.text(1, 1, r"\bf C", textattrs)
D = text.text(0, 1, r"\bf D", textattrs)

for X in [A, B, C, D]:
    c.draw(X.bbox().enlarged(0.1).path(),
        [deco.stroked(), deco.filled([color.grey(0.85)])])
    c.insert(X)

for X,Y in [[A, B], [B, C], [C, D], [D, A]]:
    c.stroke(arc(X, Y, boxdists=[0.2, 0.2], relangle=-45), [color.rgb.red, deco.earrow.normal])

c.stroke(curve(D, B, boxdists=[0.2, 0.2], relangle1=-45, relangle2=-45, relbulge=0.8),
         [color.rgb.blue, deco.earrow.normal])

c.writeEPSfile()
c.writePDFfile()
c.writeSVGfile()
