from pyx import *

circ1 = path.normpath(path.circle(0, 0, 1)) # you don't really need normpath,
circ2 = path.normpath(path.circle(1, 1, 1)) # but its better to have it once
                                            # for those operations
(circ1a, circ1b), (circ2a, circ2b) = circ1.intersect(circ2)
intersection = (circ1.split([circ1b, circ1a])[1]
                << circ2.split([circ2a, circ2b])[1]
                << path.closepath())
union = (circ1.split([circ1b, circ1a])[0]
         << circ2.split([circ2a, circ2b])[0]
         << path.closepath())

c = canvas.canvas()
c.fill(union, [color.rgb.blue])
c.fill(intersection, [color.rgb.red])
c.stroke(circ1)
c.stroke(circ2)
c.writetofile("circles")
