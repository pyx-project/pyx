import sys; sys.path.insert(0, "../..")
import math
from pyx import *

a = 1
p = path.curve(-1, 0, 1, a, -1, a, 1, 0)

t = trafo.rotate(30).scaled(5)
x = 0.49

p = p.transformed(t)

c = canvas.canvas()
c.stroke(p)
t = p.normsubpaths[0].trafo([x])[0]
if t is not path.invalid:
    c.stroke(path.line(0, 0, 1, 0), [p.normsubpaths[0].trafo([x])[0], deco.earrow.normal, color.rgb.red])

c.text(-6, -5, "t=%f" % x)
c.text(-6, -5.5, "$x(t)=%f$" % (2.54/72*p.normsubpaths[0].normsubpathitems[0].x_pt(x)))
c.text(-6, -6, "$\dot x(t)=%f$" % (2.54/72*p.normsubpaths[0].normsubpathitems[0].xdot_pt(x)))
c.text(-6, -6.5, "$\ddot x(t)=%f$" % (2.54/72*p.normsubpaths[0].normsubpathitems[0].xddot_pt(x)))
c.text(-3, -5.5, "$y(t)=%f$" % (2.54/72*p.normsubpaths[0].normsubpathitems[0].y_pt(x)))
c.text(-3, -6, "$\dot y(t)=%f$" % (2.54/72*p.normsubpaths[0].normsubpathitems[0].ydot_pt(x)))
c.text(-3, -6.5, "$\ddot y(t)=%f$" % (2.54/72*p.normsubpaths[0].normsubpathitems[0].yddot_pt(x)))
c.text(0, -6, "datan2$(\dot y(t), \dot x(t))=%f$" % (math.atan2(2.54/72*p.normsubpaths[0].normsubpathitems[0].ydot_pt(x), 2.54/72*p.normsubpaths[0].normsubpathitems[0].xdot_pt(x))*180/math.pi))
c.text(0, -6.5, "datan2$(\ddot y(t), \ddot x(t))=%f$" % (math.atan2(2.54/72*p.normsubpaths[0].normsubpathitems[0].yddot_pt(x), 2.54/72*p.normsubpaths[0].normsubpathitems[0].xddot_pt(x))*180/math.pi))

g = c.insert(graph.graphxy(width=10, xpos=-5, ypos=-20, key=graph.key.key(), y=graph.axis.lin(min=-10, max=10)))
g.plot(graph.data.functionxy(lambda t: 2.54/72*p.normsubpaths[0].normsubpathitems[0].y_pt(t), title="$y(t)$", min=0, max=1))
g.plot(graph.data.functionxy(lambda t: 2.54/72*p.normsubpaths[0].normsubpathitems[0].ydot_pt(t), title="$\dot y(t)$", min=0, max=1))
g.plot(graph.data.functionxy(lambda t: 2.54/72*p.normsubpaths[0].normsubpathitems[0].yddot_pt(t), title="$\ddot y(t)$", min=0, max=1))
g.stroke(g.xgridpath(x), [color.rgb.red])
g.stroke(g.ygridpath(0))

g = c.insert(graph.graphxy(width=10, xpos=-5, ypos=0.5+g.ypos+g.height, key=graph.key.key(), x=graph.axis.linkedaxis(g.axes["x"]), y=graph.axis.lin(min=-10, max=10)))
g.plot(graph.data.functionxy(lambda t: 2.54/72*p.normsubpaths[0].normsubpathitems[0].x_pt(t), title="$x(t)$", min=0, max=1))
g.plot(graph.data.functionxy(lambda t: 2.54/72*p.normsubpaths[0].normsubpathitems[0].xdot_pt(t), title="$\dot x(t)$", min=0, max=1))
g.plot(graph.data.functionxy(lambda t: 2.54/72*p.normsubpaths[0].normsubpathitems[0].xddot_pt(t), title="$\ddot x(t)$", min=0, max=1))
g.stroke(g.xgridpath(x), [color.rgb.red])
g.stroke(g.ygridpath(0))

c.writeEPSfile("cusp")
