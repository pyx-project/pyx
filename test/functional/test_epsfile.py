#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

from pyx import *

c = canvas.canvas()

c.stroke(path.line(10*unit.u_pt, 10*unit.u_pt, 40*unit.u_pt, 40*unit.u_pt)+
         path.line(10*unit.u_pt, 40*unit.u_pt, 40*unit.u_pt, 10*unit.u_pt))
#         path.rect(10*unit.u_pt, 10*unit.u_pt, 30*unit.u_pt, 30*unit.u_pt))

c.writeEPSfile("cross", bboxenlarge=0)

c = canvas.canvas()

c.stroke(path.line(0,4,6,4), [style.linestyle.dashed])
c.insert(epsfile.epsfile(0, 4, "cross.eps", align="bl"))
c.insert(epsfile.epsfile(2, 4, "cross.eps", align="cl"))
c.insert(epsfile.epsfile(4, 4, "cross.eps", align="tl"))

c.stroke(path.line(3,6,3,10), [style.linestyle.dashed])
c.insert(epsfile.epsfile(3, 6, "cross.eps", align="bl"))
c.insert(epsfile.epsfile(3, 8, "cross.eps", align="bc"))
c.insert(epsfile.epsfile(3, 10, "cross.eps", align="br"))

c.insert(epsfile.epsfile(1, -1, "cross.eps", scale=1))
c.insert(epsfile.epsfile(1, -1, "cross.eps", scale=2))

c.insert(epsfile.epsfile(5, -1, "cross.eps", scale=1, align="cc"))
c.insert(epsfile.epsfile(5, -1, "cross.eps", scale=2, align="cc"))

c.insert(epsfile.epsfile(9, -1, "cross.eps", scale=1, align="tr"))
c.insert(epsfile.epsfile(9, -1, "cross.eps", scale=2, align="tr"))

c.insert(epsfile.epsfile(1, -5, "cross.eps"))
c.insert(epsfile.epsfile(1, -5, "cross.eps", width=2))

c.insert(epsfile.epsfile(5, -5, "cross.eps", scale=1, align="cc"))
c.insert(epsfile.epsfile(5, -5, "cross.eps", width=2, align="cc"))

c.insert(epsfile.epsfile(9, -5, "cross.eps", scale=1, align="tr"))
c.insert(epsfile.epsfile(9, -5, "cross.eps", width=2, align="tr"))

c.insert(epsfile.epsfile(1, -9, "cross.eps"))
c.insert(epsfile.epsfile(1, -9, "cross.eps", height=1.5))

c.insert(epsfile.epsfile(5, -9, "cross.eps", scale=1, align="cc"))
c.insert(epsfile.epsfile(5, -9, "cross.eps", height=1.5, align="cc"))

c.insert(epsfile.epsfile(9, -9, "cross.eps", scale=1, align="tr"))
c.insert(epsfile.epsfile(9, -9, "cross.eps", height=1.5, align="tr"))

c.insert(epsfile.epsfile(1, -13, "cross.eps"))
c.insert(epsfile.epsfile(1, -13, "cross.eps", width=2, height=1.5))

c.insert(epsfile.epsfile(5, -13, "cross.eps", scale=1, align="cc"))
c.insert(epsfile.epsfile(5, -13, "cross.eps", width=2,height=1.5, align="cc"))

c.insert(epsfile.epsfile(9, -13, "cross.eps", scale=1, align="tr"))
c.insert(epsfile.epsfile(9, -13, "cross.eps", width=2, height=1.5, align="tr"))

c.writeEPSfile("test_epsfile")
