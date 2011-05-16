# this example is adapted from a MetaPost example by Hans Hagen

import sys; sys.path.insert(0, "../..")
from pyx import *
from solve import scalar, vector, solver

# define the inner quadrilateral
p = vector([0, 0])
q = vector([2, 5])
r = vector([8, 6])
s = vector([5, -1])

# some points of the outer squares are equal to points of the inner quadrilateral
z11 = p
z12 = q
z21 = q
z22 = r
z31 = r
z32 = s
z41 = s
z42 = p

# complete the definition of the outer squares
z1diff = z12 - z11
z2diff = z22 - z21
z3diff = z32 - z31
z4diff = z42 - z41

z13 = vector([z12.x-z1diff.y, z12.y+z1diff.x])
z14 = vector([z11.x-z1diff.y, z11.y+z1diff.x])
z23 = vector([z22.x-z2diff.y, z22.y+z2diff.x])
z24 = vector([z21.x-z2diff.y, z21.y+z2diff.x])
z33 = vector([z32.x-z3diff.y, z32.y+z3diff.x])
z34 = vector([z31.x-z3diff.y, z31.y+z3diff.x])
z43 = vector([z42.x-z4diff.y, z42.y+z4diff.x])
z44 = vector([z41.x-z4diff.y, z41.y+z4diff.x])

# define the centers of the outer squares
z1 = 0.5*(z11 + z13)
z2 = 0.5*(z21 + z23)
z3 = 0.5*(z31 + z33)
z4 = 0.5*(z41 + z43)

# define the crossing point by some equations
z0 = vector(2)
solver.eq(z0, z1 + scalar()*(z3-z1))
solver.eq(z0, z2 + scalar()*(z4-z2))

# finally draw the result

def line(p1, p2):
    return path.line(float(p1.x), float(p1.y), float(p2.x), float(p2.y))

def square(p1, p2, p3, p4):
    return path.path(path.moveto(float(p1.x), float(p1.y)),
                     path.lineto(float(p2.x), float(p2.y)),
                     path.lineto(float(p3.x), float(p3.y)),
                     path.lineto(float(p4.x), float(p4.y)),
                     path.closepath())

c = canvas.canvas()

c.stroke(square(z11, z12, z13, z14))
c.stroke(square(z21, z22, z23, z24))
c.stroke(square(z31, z32, z33, z34))
c.stroke(square(z41, z42, z43, z44))

c.stroke(line(z11, z13), [style.linestyle.dashed, style.linewidth.Thin])
c.stroke(line(z12, z14), [style.linestyle.dashed, style.linewidth.Thin])
c.stroke(line(z21, z23), [style.linestyle.dashed, style.linewidth.Thin])
c.stroke(line(z22, z24), [style.linestyle.dashed, style.linewidth.Thin])
c.stroke(line(z31, z33), [style.linestyle.dashed, style.linewidth.Thin])
c.stroke(line(z32, z34), [style.linestyle.dashed, style.linewidth.Thin])
c.stroke(line(z41, z43), [style.linestyle.dashed, style.linewidth.Thin])
c.stroke(line(z42, z44), [style.linestyle.dashed, style.linewidth.Thin])

c.stroke(square(p, q, r, s), [color.rgb.red, style.linewidth.THick])

c.stroke(line(z1, z3), [color.rgb.green])
c.stroke(line(z2, z4), [color.rgb.green])

c.fill(path.circle(float(z0.x), float(z0.y), 0.1), [color.rgb.blue])

c.writeEPSfile("quadrilateral")

