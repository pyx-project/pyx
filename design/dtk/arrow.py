from pyx import *
c = canvas.canvas()
p = path.curve(0, 0, 0.05, 0.3, 0.2, 0.5, 0.5, 0.5)
d = [deco.filled([color.gray(0.7)]),
     deco.stroked([color.gray(0.3), style.linejoin.round])]
a = deco.earrow.large(d)
c.stroke(p, [style.linestyle.dashed, a])
c.writeEPSfile("arrow")
