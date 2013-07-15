import sys; sys.path.insert(0, "../..")
from pyx import *
from solve import scalar, vector, solver

A = vector([0, 0], "A")
B = vector([10, 5], "B")
C = vector([0, 10], "C")
D = vector([scalar(), 0], "D")

solver.eq((B-A)*(D-C), 0)

def line(p1, p2):
    return path.line(float(p1.x), float(p1.y), float(p2.x), float(p2.y))

c = canvas.canvas()

c.stroke(line(A, B))
c.stroke(line(C, D))

c.writeEPSfile()
c.writePDFfile()

