from pyx import *

circ1 = path.circle(0, 0, 1).normpath() # you don't really need normpath,
circ2 = path.circle(1, 1, 1).normpath() # but its better to have it once
                                        # for those operations
(circ1a, circ1b), (circ2a, circ2b) = circ1.intersect(circ2)
intersection = (circ2.split([circ2a, circ2b])[1]
                << circ1.split([circ1b, circ1a])[1])
intersection[-1].close()

union = (circ1.split([circ1b, circ1a])[0]
         << circ2.split([circ2a, circ2b])[0])
union[-1].close()

c = canvas.canvas()
c.fill(union, [color.rgb.blue])
c.fill(intersection, [color.rgb.red])
c.stroke(circ1)
c.stroke(circ2)
c.writeEPSfile("circles")
