import math, sys
sys.path[:0] = [".."]

from pyx import *

def tree(depth):
    result = [trafo.trafo()]
    if depth > 0:
        subtree = tree(depth - 1)
        result.extend([t.rotate(65).scale(0.5).translate(0, 2.0/3.0) for t in subtree])
        result.extend([t.rotate(-4).scale(0.7).translate(0, 1) for t in subtree])
        result.extend([t.mirror(90).rotate(-65).scale(0.5).translate(0, 1) for t in subtree])
    return result

w = 0.01
c = canvas.canvas()
#for t in tree(8):
#    c.insert(canvas.canvas(t).stroke(path.line(0, 0, 0, 1)))

for t in tree(8):
    c.fill(path.path(path.moveto(-w, 0),
                     path.lineto(-0.7*w, 1+w*math.sin(4*math.pi/180)),
                     path.lineto(0.7*w, 1-w*math.sin(4*math.pi/180)),
                     path.lineto(w, 0),
                     path.closepath()).transformed(t))
c.writetofile("tree", paperformat="a4", fittosize=1)

