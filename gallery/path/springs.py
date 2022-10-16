# contributed by Gert-Ludwig Ingold

from pyx import *

n = 3                 # number of masses
r = 3.0               # system radius
rcyc = 0.3            # radius of cycloid
nl = 13               # number of loops
rc = 0.5              # radius of masses
eps = 0.03            # extra spacing for surrounding circles

c = canvas.canvas()
springcircle = path.circle(0, 0, r)
masspositions = [i*springcircle.arclen()/n
                 for i in range(n)]
for springsegment in springcircle.split(masspositions):
    c.stroke(springsegment,
             [deformer.cycloid(rcyc, nl),
              deformer.smoothed(radius=0.1)])
for x, y in springcircle.at(masspositions):
    c.fill(path.circle(x, y, rc))

c.stroke(springcircle, [deformer.parallel(rc+eps)])
c.stroke(springcircle, [deformer.parallel(-rc-eps)])

c.writeEPSfile()
c.writePDFfile()
c.writeSVGfile()
