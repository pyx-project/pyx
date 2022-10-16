from pyx import *

circ1 = path.circle(0, 0, 1.5)
circ2 = path.circle(1, 1, 1)
(circ1a, circ1b), (circ2a, circ2b) = circ1.intersect(circ2)
intersection = (circ2.split([circ2b, circ2a])[1]
                << circ1.split([circ1a, circ1b])[1])
intersection[-1].close()

union = (circ1.split([circ1a, circ1b])[0]
         << circ2.split([circ2b, circ2a])[0])
union[-1].close()

c = canvas.canvas()
c.fill(union, [color.rgb.blue])
c.fill(intersection, [color.rgb.red])
c.stroke(circ1)
c.stroke(circ2)
c.writeEPSfile()
c.writePDFfile()
c.writeSVGfile()
