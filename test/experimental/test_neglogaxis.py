#!/usr/bin/python3
import sys, math
import numpy
sys.path.insert(0, "../..")
import pyx
from pyx import *
from pyx.graph import axis

c = canvas.canvas()

def plot_xy_function(xmin=0.72, xmax=7.85):

    xaxis = graph.axis.linear(title=r"$x$", min=xmin, max=xmax)

    yaxis = graph.axis.log(title=r"$y$", min=None, max=None) #, parter=yparter, rater=yrater)

    g = graph.graphxy(width=10, x=xaxis, y=yaxis, key=graph.key.key())
    g.plot(graph.data.function("y(x) = -x**2", title=r"$-x^2$"))
    return g

def plot_color():
    # the example function to plot:
    def fct(x, y):
        return (3*x**5*y - 10*x**3*y**3 + 3*x*y**5) / 16.0

    zero_cutoff = 1e-5

    # create data on a grid:
    datapts = []
    for i, x in enumerate(numpy.linspace(-1.5, 1.5, num=70, endpoint=True)):
        for j, y in enumerate(numpy.linspace(-1.5, 1.5, num=70, endpoint=True)):
            f = fct(x, y)
            # Skip data too close to zero:
            if f > zero_cutoff:
                datapts.append((x, y, ('pos', f)))
            elif f < -zero_cutoff:
                datapts.append((x, y, ('neg', f)))

    # plot:
    width, height = 10, 10

    # define color gradients:
    gradientRedWhiteBlue = pyx.color.functiongradient_rgb(
        f_r=lambda x: 1-0.5*(1-2*x)**2 if x < 0.5 else 2 - 2*x,
        f_g=lambda x: 2*x if x < 0.5 else 2 - 2*x,
        f_b=lambda x: 2*x if x < 0.5 else 1 - 2*(x-0.5)**2)


    # plot:
    g = pyx.graph.graphxy(width=width, height=height,
        x=pyx.graph.axis.linear(title=r"$x$"),
        y=pyx.graph.axis.linear(title=r"$y$"),
    )
    kg = graph.graphx(xpos=width+0.5, length=10, x=graph.axis.split(dist=0.1, subaxes={"neg": graph.axis.log(rater_density=2),
                                                                                       "pos": graph.axis.log(rater_density=2, texter_basetexter_prefix='+')}))
    g.plot(pyx.graph.data.points(datapts, x=1, y=2, color=3, title=None), [graph.style.density(gradient=gradientRedWhiteBlue, keygraph=kg)])
    g.insert(kg)

    return g


c = canvas.canvas()
c.insert(plot_xy_function())
c.insert(plot_color(), [trafo.translate(0, -15)])
c.writePDFfile()

