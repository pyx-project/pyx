# extend module search path - not needed when PyX is installed properly
import sys; sys.path[:0] = [".."]

from pyx import *

# base tree length
l = 5

# base transformations for the left, center, and right part of the tree
ltrafo = trafo.rotate(65).scaled(0.5).translated(0, l*2.0/3.0)
ctrafo = trafo.rotate(-4).scaled(0.7).translated(0, l)
rtrafo = trafo.mirror(90).rotated(-65).scaled(0.5).translated(0, l)

def tree(depth):
    "returns a list of transformations for a recursive tree of given depth"
    r = [trafo.trafo()]
    if depth > 0:
        subtree = tree(depth - 1)
        r.extend([t*ltrafo for t in subtree])
        r.extend([t*ctrafo for t in subtree])
        r.extend([t*rtrafo for t in subtree])
    return r

c = canvas.canvas()
for t in tree(5):
    # apply the transformation to a "sub"-canvas and insert it into the "main" canvas
    c.insert(canvas.canvas(t).stroke(path.line(0, 0, 0, l)))
c.writetofile("tree", paperformat="a4")

