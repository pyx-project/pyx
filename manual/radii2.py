from pyx import *
c = canvas.canvas()

circle = path.circle(0, 0, 2)
line = path.line(-3, 1, 3, 2)

isects_circle, isects_line = circle.intersect(line)

arc1, arc2 = circle.split(isects_circle)

arc = arc1.arclen()<arc2.arclen() and arc1 or arc2

isects_line.sort()
line1, line2, line3 = line.split(isects_line)

segment = line2 << arc

c.fill(segment, [color.grey(0.5)])

c.stroke(circle, [style.linewidth.Thick])
c.stroke(line, [style.linewidth.Thick])

for isect in isects_circle:
    c.stroke(path.line(0, 0, *circle.at(isect)))

c.writePDFfile()
