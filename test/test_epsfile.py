#!/usr/bin/env python
import sys
sys.path[:0] = [".."]

from pyx import *

c = canvas.canvas()

c.stroke(path.line("10 pt", "10 pt", "40 pt", "40 pt")+
         path.line("10 pt", "40 pt", "40 pt", "10 pt"))
#         path.rect("10 pt", "10 pt", "30 pt", "30 pt"))

c.writetofile("cross", bboxenhance=0)

c = canvas.canvas()

c.stroke(path.line(0,4,6,4), canvas.linestyle.dashed)
c.insert(epsfile.epsfile("cross.eps", 0, 4, align="bl", showbbox=1))
c.insert(epsfile.epsfile("cross.eps", 2, 4, align="cl", showbbox=1))
c.insert(epsfile.epsfile("cross.eps", 4, 4, align="tl", showbbox=1))

c.stroke(path.line(3,6,3,10), canvas.linestyle.dashed)
c.insert(epsfile.epsfile("cross.eps", 3, 6, align="bl", showbbox=1))
c.insert(epsfile.epsfile("cross.eps", 3, 8, align="bc", showbbox=1))
c.insert(epsfile.epsfile("cross.eps", 3, 10, align="br", showbbox=1))

c.insert(epsfile.epsfile("cross.eps", 1, -1, scale=1, showbbox=1))
c.insert(epsfile.epsfile("cross.eps", 1, -1, scale=2, showbbox=1))

c.insert(epsfile.epsfile("cross.eps", 5, -1, scale=1, align="cc", showbbox=1))
c.insert(epsfile.epsfile("cross.eps", 5, -1, scale=2, align="cc", showbbox=1))

c.insert(epsfile.epsfile("cross.eps", 9, -1, scale=1, align="tr", showbbox=1))
c.insert(epsfile.epsfile("cross.eps", 9, -1, scale=2, align="tr", showbbox=1))

c.insert(epsfile.epsfile("cross.eps", 1, -5, showbbox=1))
c.insert(epsfile.epsfile("cross.eps", 1, -5, width=2, showbbox=1))

c.insert(epsfile.epsfile("cross.eps", 5, -5, scale=1, align="cc", showbbox=1))
c.insert(epsfile.epsfile("cross.eps", 5, -5, width=2, align="cc", showbbox=1))

c.insert(epsfile.epsfile("cross.eps", 9, -5, scale=1, align="tr", showbbox=1))
c.insert(epsfile.epsfile("cross.eps", 9, -5, width=2, align="tr", showbbox=1))

c.insert(epsfile.epsfile("cross.eps", 1, -9, showbbox=1))
c.insert(epsfile.epsfile("cross.eps", 1, -9, height=1.5, showbbox=1))

c.insert(epsfile.epsfile("cross.eps", 5, -9, scale=1, align="cc", showbbox=1))
c.insert(epsfile.epsfile("cross.eps", 5, -9, height=1.5, align="cc", showbbox=1))

c.insert(epsfile.epsfile("cross.eps", 9, -9, scale=1, align="tr", showbbox=1))
c.insert(epsfile.epsfile("cross.eps", 9, -9, height=1.5, align="tr", showbbox=1))

c.insert(epsfile.epsfile("cross.eps", 1, -13, showbbox=1))
c.insert(epsfile.epsfile("cross.eps", 1, -13, width=2, height=1.5, showbbox=1))

c.insert(epsfile.epsfile("cross.eps", 5, -13, scale=1, align="cc", showbbox=1))
c.insert(epsfile.epsfile("cross.eps", 5, -13, width=2,height=1.5, align="cc", showbbox=1))

c.insert(epsfile.epsfile("cross.eps", 9, -13, scale=1, align="tr", showbbox=1))
c.insert(epsfile.epsfile("cross.eps", 9, -13, width=2, height=1.5, align="tr", showbbox=1))

c.writetofile("test_epsfile")
