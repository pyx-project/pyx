#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

from pyx import *

c = canvas.canvas()

c.stroke(path.line(10*unit.u_pt, 10*unit.u_pt, 40*unit.u_pt, 40*unit.u_pt)+
         path.line(10*unit.u_pt, 40*unit.u_pt, 40*unit.u_pt, 10*unit.u_pt))

c.writePDFfile("cross", page_bboxenlarge=0, write_writebbox=True)

c = canvas.canvas()

c.stroke(path.line(0, 4, 6, 4), [style.linestyle.dashed])
c.insert(pdffile.pdffile(0, 4, "cross.pdf", align="bl"))
c.insert(pdffile.pdffile(2, 4, "cross.pdf", align="cl"))
c.insert(pdffile.pdffile(4, 4, "cross.pdf", align="tl"))

c.stroke(path.line(3, 6, 3, 10), [style.linestyle.dashed])
c.insert(pdffile.pdffile(3, 6, "cross.pdf", align="bl"))
c.insert(pdffile.pdffile(3, 8, "cross.pdf", align="bc"))
c.insert(pdffile.pdffile(3, 10, "cross.pdf", align="br"))

c.insert(pdffile.pdffile(1, -1, "cross.pdf", scale=1))
c.insert(pdffile.pdffile(1, -1, "cross.pdf", scale=2))

c.insert(pdffile.pdffile(5, -1, "cross.pdf", scale=1, align="cc"))
c.insert(pdffile.pdffile(5, -1, "cross.pdf", scale=2, align="cc"))

c.insert(pdffile.pdffile(9, -1, "cross.pdf", scale=1, align="tr"))
c.insert(pdffile.pdffile(9, -1, "cross.pdf", scale=2, align="tr"))

c.insert(pdffile.pdffile(1, -5, "cross.pdf"))
c.insert(pdffile.pdffile(1, -5, "cross.pdf", width=2))

c.insert(pdffile.pdffile(5, -5, "cross.pdf", scale=1, align="cc"))
c.insert(pdffile.pdffile(5, -5, "cross.pdf", width=2, align="cc"))

c.insert(pdffile.pdffile(9, -5, "cross.pdf", scale=1, align="tr"))
c.insert(pdffile.pdffile(9, -5, "cross.pdf", width=2, align="tr"))

c.insert(pdffile.pdffile(1, -9, "cross.pdf"))
c.insert(pdffile.pdffile(1, -9, "cross.pdf", height=1.5))

c.insert(pdffile.pdffile(5, -9, "cross.pdf", scale=1, align="cc"))
c.insert(pdffile.pdffile(5, -9, "cross.pdf", height=1.5, align="cc"))

c.insert(pdffile.pdffile(9, -9, "cross.pdf", scale=1, align="tr"))
c.insert(pdffile.pdffile(9, -9, "cross.pdf", height=1.5, align="tr"))

c.insert(pdffile.pdffile(1, -13, "cross.pdf"))
c.insert(pdffile.pdffile(1, -13, "cross.pdf", width=2, height=1.5))

c.insert(pdffile.pdffile(5, -13, "cross.pdf", scale=1, align="cc"))
c.insert(pdffile.pdffile(5, -13, "cross.pdf", width=2, height=1.5, align="cc"))

c.insert(pdffile.pdffile(9, -13, "cross.pdf", scale=1, align="tr"))
c.insert(pdffile.pdffile(9, -13, "cross.pdf", width=2, height=1.5, align="tr"))

c.writePDFfile("test_pdffile")
