from pyx import *

circ1 = path.normpath(path.circle(0, 0, 1)) # you don't really need normpath,
circ2 = path.normpath(path.circle(1, 1, 1)) # but its better to have it once
                                            # for those operations
(circ1a, circ1b), (circ2a, circ2b) = circ1.intersect(circ2)
intersection = (circ1.split([circ1a, circ1b])[0]
                << circ2.split([circ2b, circ2a])[0])
intersection.append(path.closepath())

union = (circ1.split([circ1a, circ1b])[1]
         << circ2.split([circ2b, circ2a])[1])
union.append(path.closepath())

c = canvas.canvas()
c.fill(union, [color.rgb.blue])
c.fill(intersection, [color.rgb.red])
c.stroke(circ1)
c.stroke(circ2)
c.writeEPSfile("circles")
