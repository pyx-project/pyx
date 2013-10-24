#!/usr/bin/env python
import sys;sys.path.insert(0, "..")
from math import *
#sys.path.insert(0, os.path.expanduser("~/python/pyx-trunk"))
from pyx import *
# File for invalid parametrisations of Bezier curves
# Some examples

def Dx_m(Dy):
    return (-1-2*Dy-sqrt((1+2*Dy)**2+3))/3.0

def Dx_p(Dy):
    return (-1-2*Dy+sqrt((1+2*Dy)**2+3))/3.0

def pass00(Dy):
    return 1.0/(3.0*(Dy+1))

def pass10(Dy):
    return (1.0+Dy**3)/(3.0*(Dy+1))

def acurve(Dx, Dy, trafo_reverse=False):
    p = path.curve(0,0, 0,1, Dx,1+Dy, 1,0)
    if trafo_reverse:
        # calculate the trafo to put p2=(1,-1):
        # (for the right branch only)
        x2, y2 = Dx, Dy+1
        tr1 = trafo.scale(1, -1.0/y2)
        pp = tr1.apply_pt(x2, y2)
        tr2 = trafo.trafo(matrix=((1, (pp[0]-1)), (0, 1)))
        p = p.transformed(tr2*tr1)
    c = canvas.canvas()
    c.stroke(p, [deco.shownormpath()])
    #c.text(-0.2, -10*unit.x_pt, r"\noindent$\Delta x=%g $\par\noindent$\Delta y=%g$"%(Dx,Dy),
    #       [text.parbox(4), text.size.footnotesize])
    return c

dx = 3
dy = -3

Dy = -2.5
e = 0.1
# test the left branch:
cc = acurve(pass00(Dy), Dy) # passes through startpoint
#cc = acurve(Dx_m(Dy)-e, Dy)
c  = acurve(Dx_m(Dy)  , Dy); cc.insert(c, [trafo.translate(1*dx, 0)])
c  = acurve(Dx_m(Dy)+e, Dy); cc.insert(c, [trafo.translate(2*dx, 0)])

# test the right branch:
#cc = acurve(Dx_p(Dy)-e, Dy, True)
#c  = acurve(Dx_p(Dy)  , Dy, True); cc.insert(c, [trafo.translate(1*dx, 0)])
##c  = acurve(Dx_p(Dy)+e, Dy, True); cc.insert(c, [trafo.translate(2*dx, 0)])
#c  = acurve(pass10(Dy), Dy, True); cc.insert(c, [trafo.translate(2*dx, 0)]) # passes through endpoint

cc.writePDFfile()

