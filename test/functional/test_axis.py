#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

import math
from pyx import *
from pyx.graph.axis.parter import linear as linparter
from pyx.graph.axis.painter import regular, ticklength, rotatetext
from pyx.graph.axis.texter import rational, exponential
from pyx.graph.axis.axis import lin, pathaxis

c = canvas.canvas()
lintest = {"title": "axis title", "min": 0, "max": 1, "parter": linparter(["0.25", "0.1/0.8"])}
c.insert(pathaxis(path.path(path.moveto(0, 0), path.lineto(0, 8)),
                        lin(**lintest),
                        direction=-1))
c.insert(pathaxis(path.path(path.moveto(1, 0), path.lineto(1, 8)),
                        lin(**lintest)))
c.insert(pathaxis(path.path(path.moveto(5, 0), path.lineto(5, 8)),
                        lin(painter=regular(labelattrs=[trafo.rotate(45)], titleattrs=[trafo.rotate(45)]), **lintest),
                        direction=-1))
c.insert(pathaxis(path.path(path.moveto(8, 0), path.lineto(8, 8)),
                        lin(painter=regular(labelattrs=[trafo.rotate(45), text.halign.right], titleattrs=[trafo.rotate(-45)]), **lintest),
                        direction=-1))
c.insert(pathaxis(path.path(path.moveto(11, 0), path.lineto(11, 8)),
                        lin(painter=regular(tickattrs=[color.rgb.red], innerticklength=0, outerticklength=ticklength.normal), **lintest),
                        direction=-1))
c.insert(pathaxis(path.path(path.moveto(12, 0), path.lineto(12, 8)),
                        lin(painter=regular(tickattrs=[attr.changelist([None, color.rgb.green])]), **lintest)))
c.insert(pathaxis(path.path(path.moveto(16, 0), path.lineto(16, 8)),
                        lin(texter=exponential(), **lintest),
                        direction=-1))
c.insert(pathaxis(path.path(path.moveto(18, 0), path.lineto(18, 8)),
                        lin(texter=rational(), **lintest),
                        direction=-1))
lintest = {"title": "axis title", "min": -2*math.pi, "max": 0, "divisor": math.pi, "parter": linparter("0.25")}
c.insert(pathaxis(path.path(path.moveto(0, 11), path.lineto(8, 11)),
                        lin(texter=rational(suffix="\pi"), **lintest)))
lintest = {"title": "axis title", "min": 0, "max": 2*math.pi, "divisor": math.pi, "parter": linparter("0.5")}
c.insert(pathaxis(path.path(path.moveto(10, 11), path.lineto(18, 11)),
                        lin(texter=rational(numsuffix="\pi", over="%s/%s"), **lintest)))
lintest = {"min": 0, "max": 2*math.pi, "divisor": math.pi, "parter": linparter("0.125")}
c.insert(pathaxis(path.circle(4, 17, 4),
                        lin(texter=rational(suffix="\pi"), **lintest)))
lintest = {"min": 0, "max": 2*math.pi, "divisor": math.pi/180, "parter": linparter("30")}
c.insert(pathaxis(path.circle(14, 17, 4),
                        lin(painter=regular(labeldirection=rotatetext.parallel), **lintest)))
c.writeEPSfile("test_axis", paperformat="a4")
c.writePDFfile("test_axis", paperformat="a4")

