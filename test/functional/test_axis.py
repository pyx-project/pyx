#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

import math
from pyx import *
from pyx import attr

c = canvas.canvas()
lintest = {"title": "axis title", "min": 0, "max": 1, "parter": graph.linparter(["0.25", "0.1/0.8"])}
c.insert(graph.pathaxis(path.path(path.moveto(0, 0), path.lineto(0, 8)),
                        graph.linaxis(**lintest),
                        direction=-1))
c.insert(graph.pathaxis(path.path(path.moveto(1, 0), path.lineto(1, 8)),
                        graph.linaxis(**lintest)))
c.insert(graph.pathaxis(path.path(path.moveto(5, 0), path.lineto(5, 8)),
                        graph.linaxis(painter=graph.axispainter(labelattrs=[trafo.rotate(45)], titleattrs=[trafo.rotate(45)]), **lintest),
                        direction=-1))
c.insert(graph.pathaxis(path.path(path.moveto(8, 0), path.lineto(8, 8)),
                        graph.linaxis(painter=graph.axispainter(labelattrs=[trafo.rotate(45), text.halign.right], titleattrs=[trafo.rotate(-45)]), **lintest),
                        direction=-1))
c.insert(graph.pathaxis(path.path(path.moveto(11, 0), path.lineto(11, 8)),
                        graph.linaxis(painter=graph.axispainter(tickattrs=[color.rgb.red], innerticklength=0, outerticklength=graph.ticklength.normal), **lintest),
                        direction=-1))
c.insert(graph.pathaxis(path.path(path.moveto(12, 0), path.lineto(12, 8)),
                        graph.linaxis(painter=graph.axispainter(tickattrs=[attr.changelist([None, color.rgb.green])]), **lintest)))
c.insert(graph.pathaxis(path.path(path.moveto(16, 0), path.lineto(16, 8)),
                        graph.linaxis(texter=graph.exponentialtexter(), **lintest),
                        direction=-1))
c.insert(graph.pathaxis(path.path(path.moveto(18, 0), path.lineto(18, 8)),
                        graph.linaxis(texter=graph.rationaltexter(), **lintest),
                        direction=-1))
lintest = {"title": "axis title", "min": -2*math.pi, "max": 0, "divisor": math.pi, "parter": graph.linparter("0.25")}
c.insert(graph.pathaxis(path.path(path.moveto(0, 11), path.lineto(8, 11)),
                        graph.linaxis(texter=graph.rationaltexter(suffix="\pi"), **lintest)))
lintest = {"title": "axis title", "min": 0, "max": 2*math.pi, "divisor": math.pi, "parter": graph.linparter("0.5")}
c.insert(graph.pathaxis(path.path(path.moveto(10, 11), path.lineto(18, 11)),
                        graph.linaxis(texter=graph.rationaltexter(enumsuffix="\pi", over="%s/%s"), **lintest)))
lintest = {"min": 0, "max": 2*math.pi, "divisor": math.pi, "parter": graph.linparter("0.125")}
c.insert(graph.pathaxis(path.circle(4, 17, 4),
                        graph.linaxis(texter=graph.rationaltexter(suffix="\pi"), **lintest)))
lintest = {"min": 0, "max": 2*math.pi, "divisor": math.pi/180, "parter": graph.linparter("30")}
c.insert(graph.pathaxis(path.circle(14, 17, 4),
                        graph.linaxis(painter=graph.axispainter(labeldirection=graph.rotatetext.parallel), **lintest)))
c.writetofile("test_axis", paperformat="a4")

