from pyx import *

unit.set(uscale=3)

c = canvas.canvas()

A = c.text(0,0, r"\bf A", text.halign.center, text.vshift.middlezero)
B = c.text(1,0, r"\bf B", text.halign.center, text.vshift.middlezero)
C = c.text(1,1, r"\bf C", text.halign.center, text.vshift.middlezero)
D = c.text(0,1, r"\bf D", text.halign.center, text.vshift.middlezero)

for X in [A,B,C,D]:
    # center is in true points
    c.stroke(path.circle(unit.t_pt(X.center[0]), unit.t_pt(X.center[1]), "0.25 t"))

for X,Y in [[A,B], [B,C], [C,D], [D,A]]:
    c.stroke(connector.arc(X, Y, boxdists=0.2), [color.rgb.red, deco.earrow.normal])

c.stroke(connector.curve(D, B, boxdists=0.2, relangle1=45, relangle2=-45, relbulge=0.8),
         [color.rgb.blue, deco.earrow.normal])

c.writetofile("connect")
