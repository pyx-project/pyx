#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

from pyx import *

trafo1 = trafo.rotate(45)
trafo2 = trafo.translate(1, 1)
clip = canvas.clip(path.rect(-1, -1, 2, 2))
content = canvas.canvas()
content.fill(path.rect(-2, -2, 2, 2), [color.rgb.red])
content.fill(path.rect(-2, 0, 2, 2), [color.rgb.green])
content.fill(path.rect(0, -2, 2, 2), [color.rgb.blue])
content.fill(path.rect(0, 0, 2, 2), [color.rgb.black])

def apply1(*args):
    c = canvas.canvas(args)
    c.insert(content)
    return c

def apply2(*args):
    c = sub = canvas.canvas()
    for arg in reversed(args):
        sub = sub.insert(canvas.canvas([arg]))
    sub.insert(content)
    return c

c = canvas.canvas()

c.insert(apply1(clip, trafo1, trafo2), [trafo.translate(0, 0)])
c.stroke(apply1(clip, trafo1, trafo2).bbox().rect(), [trafo.translate(0, 0)])

c.insert(apply2(clip, trafo1, trafo2), [trafo.translate(0, 5)])
c.stroke(apply2(clip, trafo1, trafo2).bbox().rect(), [trafo.translate(0, 5)])

c.insert(apply1(clip, trafo2, trafo1), [trafo.translate(5, 0)])
c.stroke(apply1(clip, trafo2, trafo1).bbox().rect(), [trafo.translate(5, 0)])

c.insert(apply2(clip, trafo2, trafo1), [trafo.translate(5, 5)])
c.stroke(apply2(clip, trafo2, trafo1).bbox().rect(), [trafo.translate(5, 5)])

c.insert(apply1(trafo1, clip, trafo2), [trafo.translate(10, 0)])
c.stroke(apply1(trafo1, clip, trafo2).bbox().rect(), [trafo.translate(10, 0)])

c.insert(apply2(trafo1, clip, trafo2), [trafo.translate(10, 5)])
c.stroke(apply2(trafo1, clip, trafo2).bbox().rect(), [trafo.translate(10, 5)])

c.insert(apply1(trafo2, clip, trafo1), [trafo.translate(15, 0)])
c.stroke(apply1(trafo2, clip, trafo1).bbox().rect(), [trafo.translate(15, 0)])

c.insert(apply2(trafo2, clip, trafo1), [trafo.translate(15, 5)])
c.stroke(apply2(trafo2, clip, trafo1).bbox().rect(), [trafo.translate(15, 5)])

c.insert(apply1(trafo1, trafo2, clip), [trafo.translate(20, 0)])
c.stroke(apply1(trafo1, trafo2, clip).bbox().rect(), [trafo.translate(20, 0)])

c.insert(apply2(trafo1, trafo2, clip), [trafo.translate(20, 5)])
c.stroke(apply2(trafo1, trafo2, clip).bbox().rect(), [trafo.translate(20, 5)])

c.insert(apply1(trafo2, trafo1, clip), [trafo.translate(25, 0)])
c.stroke(apply1(trafo2, trafo1, clip).bbox().rect(), [trafo.translate(25, 0)])

c.insert(apply2(trafo2, trafo1, clip), [trafo.translate(25, 5)])
c.stroke(apply2(trafo2, trafo1, clip).bbox().rect(), [trafo.translate(25, 5)])

c.writeEPSfile()
c.writePDFfile()
