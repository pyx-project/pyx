#!/usr/bin/env python
# -*- coding: ISO-8859-15 -*-
import sys
sys.path.insert(0, "..")

import math
from math import *
from pyx import *
from pyx.graph import axis, data

# define some functions for the color values:
def red(x):   return 2*x*(1-x)**5 + 3.5*x**2*(1-x)**3 + 2.1*x*x*(1-x)**2 + 3.0*x**3*(1-x)**2 + x**0.5*(1-(1-x)**2)
def green(x): return 1.5*x**2*(1-x)**3 - 0.8*x**3*(1-x)**2 + 2.0*x**4*(1-x) + x**4
def blue(x):  return 5*x*(1-x)**5 - 0.5*x**2*(1-x)**3 + 0.3*x*x*(1-x)**2 + 5*x**3*(1-x)**2 + 0.5*x**6

# use the implemented converter for the grey value:
def grey(x): return color.rgb(red(x), green(x), blue(x)).grey().color["gray"]

# plot the color values
g = graph.graphxy(width=10, ratio=1)
g.plot(data.function("y(x)=red(x)",   min=0, max=1, context=locals()), [graph.style.line([color.rgb.red])])
g.plot(data.function("y(x)=green(x)", min=0, max=1, context=locals()), [graph.style.line([color.rgb.green])])
g.plot(data.function("y(x)=blue(x)",  min=0, max=1, context=locals()), [graph.style.line([color.rgb.blue])])
g.plot(data.function("y(x)=grey(x)",  min=0, max=1, context=locals()))

# plot the colors
n = 200
x = 0
for i in range(n):
    t = i * 1.0 / (n-1)
    g.fill(path.rect(x, -2, 10.5/(n-1), 1), [color.rgb(red(t), green(t), blue(t))])
    x += 10.0 / n

g.writeEPSfile("palettetest", paperformat=document.paperformat.A4)
g.writePDFfile("palettetest")

