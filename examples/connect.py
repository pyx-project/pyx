from pyx import *

unit.set(uscale=3)

c = canvas.canvas()

textattrs = [text.halign.center, text.vshift.middlezero]
A = c.text(0, 0, r"\bf A", textattrs)
B = c.text(1, 0, r"\bf B", textattrs)
C = c.text(1, 1, r"\bf C", textattrs)
D = c.text(0, 1, r"\bf D", textattrs)

for X in [A, B, C, D]:
    c.stroke(X.bbox().enlarged(0.1).rect())

for X,Y in [[A, B], [B, C], [C, D], [D, A]]:
    c.stroke(connector.arc(X, Y, boxdists=0.25), [color.rgb.red, deco.earrow.normal])

c.stroke(connector.curve(D, B, boxdists=0.25, relangle1=45, relangle2=-45, relbulge=0.8),
         [color.rgb.blue, deco.earrow.normal])

c.writeEPSfile("connect")
