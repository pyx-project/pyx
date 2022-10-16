from math import sin, cos, pi
from pyx import *

r = 1.5

# create a box list of regular polygons
boxes = [box.polygon([(-r*sin(i*2*pi/n), r*cos(i*2*pi/n))
                      for i in range(n)])
         for n in range(3, 8)]
# tile with spacing 0 horizontally
box.tile(boxes, 0, 1, 0)

c = canvas.canvas()
for b in boxes:
    # plot the boxes path
    c.stroke(b.path(), [color.rgb.green])
    # a second time with bezier rounded corners
    c.stroke(b.path(), [deformer.smoothed(radius=0.5), color.rgb.red])
c.writeEPSfile()
c.writePDFfile()
c.writeSVGfile()
