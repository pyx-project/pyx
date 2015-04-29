from pyx import *
from pyx.metapost.path import beginknot, endknot, smoothknot, tensioncurve

p1, p2, p3, p4, p5 = (0, 0), (2, 1.33), (1.3, 3), (0.33, 2.33), (1, 1.67)
openpath = metapost.path.path([
    beginknot(*p1), tensioncurve(), smoothknot(*p2), tensioncurve(),
    smoothknot(*p3), tensioncurve(), smoothknot(*p4), tensioncurve(),
    endknot(*p5)])
closedpath = metapost.path.path([
    smoothknot(*p1), tensioncurve(), smoothknot(*p2), tensioncurve(),
    smoothknot(*p3), tensioncurve(), smoothknot(*p4), tensioncurve(),
    smoothknot(*p5), tensioncurve()])
c = canvas.canvas()
for p in [p1, p2, p3, p4, p5]:
    c.fill(path.circle(p[0], p[1], 0.05), [color.rgb.red])
    c.fill(path.circle(p[0], p[1], 0.05), [color.rgb.red, trafo.translate(2, 0)])
c.stroke(openpath)
c.stroke(closedpath, [trafo.translate(2, 0)])

c.writeEPSfile("metapost")
c.writePDFfile("metapost")
c.writeSVGfile("metapost")
