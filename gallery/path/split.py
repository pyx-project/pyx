import math
from pyx import *

circle = path.circle(0, 0, 5/math.pi)
opencircle, = circle.split(circle.begin())

c = canvas.canvas()

def showsplit(x, y, path, splitpoints, description):
    c.text(x, y, description, [text.halign.center, text.vshift.mathaxis])
    segments = path.transformed(trafo.translate(x, y)).split(splitpoints)
    print("path sement lengths for ``%s'':" % description)
    for segment, segment_color in zip(segments, [color.rgb.red, color.rgb.green, color.rgb.blue]):
        print("  %s" % segment.arclen())
        c.stroke(segment, [deco.earrow.normal, style.linestyle.dashed, segment_color])
    print()

showsplit(0, 0, opencircle, [opencircle.begin()+1, opencircle.end()-1], "open, $p_1 < p_2$")
showsplit(0, -5, opencircle, [opencircle.end()-1, opencircle.begin()+1], "open, $p_1 > p_2$")

showsplit(5, 0, circle, [circle.begin()+1, circle.end()-1], "closed, $p_1 < p_2$")
showsplit(5, -5, circle, [circle.end()-1, circle.begin()+1], "closed, $p_1 > p_2$")

c.writeEPSfile()
c.writePDFfile()
c.writeSVGfile()
