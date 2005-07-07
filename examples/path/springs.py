# contributed by Gert-Ludwig Ingold

from pyx import *
from math import cos, sin, pi

n = 3                 # number of masses
r = 3.0               # system radius
dphi = 360.0/float(n) # angle between masses
dphir = dphi/180.0*pi #    the same in radians
rcyc = 0.3            # radius of cycloid
nl = 13               # number of loops
rc = 0.5              # radius of masses
eps = 0.03            # extra spacing for surrounding circles

c = canvas.canvas()
for i in range(n):
  c.stroke(path.path(path.arc(0, 0, r, i*dphi, (i+1)*dphi)), 
               [deformer.cycloid(rcyc, nl), deformer.smoothed(radius=0.1)])
  c.fill(path.circle(r*cos(i*dphir), r*sin(i*dphir), rc), 
               [deco.filled([color.grey.black])])

c.stroke(path.circle(0, 0, r - rc - eps))
c.stroke(path.circle(0, 0, r + rc + eps))

c.writeEPSfile("springs")
c.writePDFfile("springs")
