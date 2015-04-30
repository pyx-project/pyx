#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

from pyx import *

c = canvas.canvas()

s = svgfile.svgfile_pt(100, 200, 'data/testsvg.svg', width_pt=450, resolution=96, parsed=True)
c.insert(s)
c.stroke(s.bbox().enlarged(-style.linewidth.normal.width/2).rect())
c.fill(path.circle_pt(105, 205, 5))
c.fill(path.circle_pt(105, 495, 5))
c.fill(path.circle_pt(545, 205, 5))
c.fill(path.circle_pt(545, 495, 5))

s = svgfile.svgfile_pt(100, 600, 'data/testsvg.svg', width_pt=450, resolution=96)
c.insert(s)
c.stroke(s.bbox().enlarged(-style.linewidth.normal.width/2).rect())
c.fill(path.circle_pt(105, 605, 5))
c.fill(path.circle_pt(105, 895, 5))
c.fill(path.circle_pt(545, 605, 5))
c.fill(path.circle_pt(545, 895, 5))

c.writeSVGfile(page_bboxenlarge=0)
