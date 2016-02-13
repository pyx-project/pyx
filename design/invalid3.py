#!/usr/bin/env python
import sys;sys.path.insert(0, "..")
from math import *
from pyx import *
# File for invalid parametrisations of Bezier curves
# Some examples

def Dx_m(Dy):
    return (-1-2*Dy-sqrt((1+2*Dy)**2+3))/3.0

def Dx_p(Dy):
    return (-1-2*Dy+sqrt((1+2*Dy)**2+3))/3.0

def acurve(Dx_fct, Dy, Dx=None):
    if Dx is None:
        Dx = Dx_fct(Dy)
    p = path.curve(0,0, 0,1, Dx,1+Dy, 1,0)
    c = canvas.canvas()
    c.stroke(p, [deco.shownormpath()])
    c.text(-0.2, -10*unit.x_pt, r"\noindent$\Delta x=%g $\par\noindent$\Delta y=%g$"%(Dx,Dy),
           [text.parbox(4), text.size.footnotesize])
    return c

dx = 3
dy = -3
cc = acurve(Dx_m, 0)
c = acurve(Dx_m, 1); cc.insert(c, [trafo.translate(dx, 0)])
c = acurve(Dx_m, -1); cc.insert(c, [trafo.translate(2*dx, 0)])
c = acurve(Dx_m, -2); cc.insert(c, [trafo.translate(0, dy)])
c = acurve(Dx_p, -1); cc.insert(c, [trafo.translate(dx, dy)])
c = acurve(Dx_p, -3); cc.insert(c, [trafo.translate(2*dx, dy)])
cc.writePDFfile()

