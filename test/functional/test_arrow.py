#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

import pyx
from pyx import *
from pyx.path import *
import math

def testarrow(c):
    c.stroke(path(moveto(10,20),
                curveto(12,16,14,15,12,19),
                rcurveto(-3,2,3,3,-2,4)),
             [deco.barrow.small, deco.earrow.normal])

    c.stroke(path(arc(8,15,4,10,70)), [deco.barrow.small, deco.earrow.normal])
    c.stroke(path(arc(8,15,3,10,70)), [deco.barrow.small, deco.earrow.normal])
    c.stroke(path(arc(8,15,2,10,70)), [deco.barrow.small, deco.earrow.normal])
    c.stroke(path(arc(8,15,1,10,70)), [deco.barrow.small, deco.earrow.normal])
    c.stroke(path(arc(8,15,0.5,10,70)), [deco.barrow.small, deco.earrow.normal])

    base = 2

    c.stroke(path(moveto(5,10), rlineto(5,0)),
           [deco.barrow(size=base/math.sqrt(8)*unit.t_pt, constriction=None),
            deco.earrow.SMall])
    c.stroke(path(moveto(5,10.5), rlineto(5,0)),
           [deco.barrow(size=base/math.sqrt(4)*unit.t_pt, constriction=None),
            deco.earrow.Small])
    c.stroke(path(moveto(5,11), rlineto(5,0)),
           [deco.barrow(size=base/math.sqrt(2)*unit.t_pt, constriction=None),
            deco.earrow.small])
    c.stroke(path(moveto(5,11.5), rlineto(5,0)),
           [deco.barrow(size=base/math.sqrt(1)*unit.t_pt, constriction=None),
            deco.earrow.normal])
    c.stroke(path(moveto(5,12), rlineto(5,0)),
           [deco.barrow(size=base*math.sqrt(2)*unit.t_pt, constriction=None),
            deco.earrow.large])
    c.stroke(path(moveto(5,12.5), rlineto(5,0)),
           [deco.barrow(size=base*math.sqrt(4)*unit.t_pt, constriction=None),
            deco.earrow.Large])
    c.stroke(path(moveto(5,13), rlineto(5,0)),
           [deco.barrow(size=base*math.sqrt(8)*unit.t_pt, constriction=None),
            deco.earrow.LArge])
    c.stroke(path(moveto(5,13.5), rlineto(5,0)),
           [deco.barrow(size=base*math.sqrt(16)*unit.t_pt, constriction=None),
            deco.earrow.LARge])
   
    lt = style.linewidth.THick

    c.stroke(path(moveto(11,10), rlineto(5,0)),
           [lt,
            deco.barrow(size=base/math.sqrt(8)*unit.t_pt, constriction=None),
            deco.earrow.SMall])
    c.stroke(path(moveto(11,10.5), rlineto(5,0)),
           [lt,
            deco.barrow(size=base/math.sqrt(4)*unit.t_pt, constriction=None),
            deco.earrow.Small])
    c.stroke(path(moveto(11,11), rlineto(5,0)),
           [lt,
            deco.barrow(size=base/math.sqrt(2)*unit.t_pt, constriction=None),
            deco.earrow.small])
    c.stroke(path(moveto(11,11.5), rlineto(5,0)),
           [lt,
            deco.barrow(size=base/math.sqrt(1)*unit.t_pt, constriction=None),
            deco.earrow.normal])
    c.stroke(path(moveto(11,12), rlineto(5,0)),
           [lt,
            deco.barrow(size=base*math.sqrt(2)*unit.t_pt, constriction=None),
            deco.earrow.large])
    c.stroke(path(moveto(11,12.5), rlineto(5,0)),
           [lt,
            deco.barrow(size=base*math.sqrt(4)*unit.t_pt, constriction=None),
            deco.earrow.Large])
    c.stroke(path(moveto(11,13), rlineto(5,0)),
           [lt,
            deco.barrow(size=base*math.sqrt(8)*unit.t_pt, constriction=None),
            deco.earrow.LArge(attrs=[style.linestyle.dashed, color.rgb.green])])
    c.stroke(path(moveto(11,13.5), rlineto(5,0)),
           [lt,
            deco.barrow(size=base*math.sqrt(16)*unit.t_pt, constriction=None),
            deco.earrow.LARge(attrs=[color.rgb.red,
                                     deco.stroked([style.linejoin.round]),
                                     deco.filled([color.rgb.blue])])])



c=canvas.canvas()
testarrow(c)
c.writeEPSfile("test_arrow", paperformat="a4", rotated=0, fittosize=1)

