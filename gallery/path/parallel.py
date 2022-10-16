from pyx import *

c = canvas.canvas()

p = path.path(path.moveto(0, 0), path.arc(0, 0, 1, 210, 150), path.closepath())
c.stroke(p, [style.linewidth(0.4)])

pp = deformer.parallel(-0.2, sharpoutercorners=1).deform(p) + deformer.parallel( 0.2, sharpoutercorners=1).deform(p).reversed()
c.stroke(pp, [trafo.translate(2.5, 0), deco.filled([color.rgb.red])])

# PyX gets the bounding box wrong, which leads to the clipping on the left
c.writeEPSfile()
c.writePDFfile()
c.writeSVGfile()
