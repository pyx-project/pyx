from pyx import *
unit.set(xscale=3)

c = canvas.canvas()
t = c.text(0, 0, r"Here\PyXMarker{id} is a marker.")
center = t.marker("id")
c.stroke(path.circle(center[0], center[1], 1), [color.rgb.red])
c.stroke(path.line(center[0]-1, center[1], center[0]+1, center[1]), [color.rgb.red])
c.stroke(path.line(center[0], center[1]-1, center[0], center[1]+1), [color.rgb.red])
c.writeEPSfile("marker")
c.writePDFfile("marker")
c.writeSVGfile("marker")
