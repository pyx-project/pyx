#!/usr/bin/python3
import sys, math
import numpy
sys.path.insert(0, "../..")
import pyx
from pyx import *
from pyx.graph import axis

c = canvas.canvas()

def plot_xy_function(xmin=0.72, xmax=7.85):
    # xmin, xmax are just some odd values to see if extendminmax works correctly
    print("data boundaries:", -xmax**2, -xmin**2) # -72.965764 -0.6084

    xparter = graph.axis.parter.autolinear()
    xrater = graph.axis.rater.linear()
    xaxis = graph.axis.linear(title=r"$x$", min=xmin, max=xmax, parter=xparter, rater=xrater)

    #yparter = graph.axis.parter.negative_autologarithmic() # try this as well
    yparter = graph.axis.parter.negative_logarithmic(
      tickpreexps=[graph.axis.parter.negative_logarithmic.pre1exp, graph.axis.parter.negative_logarithmic.pre1to9exp],
      extendtick=0, extendlabel=None
    )
    yrater = graph.axis.rater.negative_logarithmic()
    yaxis = graph.axis.negative_logarithmic(title=r"$y$", min=None, max=None, parter=yparter, rater=yrater)

    g = graph.graphxy(width=10, x=xaxis, y=yaxis, key=graph.key.key())
    g.plot(graph.data.function("y(x) = -x**2", title=r"$-x^2$"))
    return g

def plot_color():
    # the example function to plot:
    def fct(x, y):
        return (3*x**5*y - 10*x**3*y**3 + 3*x*y**5) / 16.0

    # create data on a grid:
    datapts = []
    for i, x in enumerate(numpy.linspace(-1.5, 1.5, num=70, endpoint=True)):
        for j, y in enumerate(numpy.linspace(-1.5, 1.5, num=70, endpoint=True)):
            datapts.append((x,y, fct(x,y)))

    # we might need explicit bounds for the color axes:
    mm = max(max(d[2] for d in datapts), -min(d[2] for d in datapts))
    #mm -= 2.5
    mm = None
    databds_pos = (1e-5, mm) # min, max
    databds_neg = (mm, -1e-5) # min, max

    # plot:
    width, height = 10, 10
    keydist, keysep, keywidth = 0.4, 0.5, 0.5
    keyheight = 0.5*(height - keysep)

    # define color gradients:
    gradient_neg = pyx.color.functiongradient_rgb( # red -> white
        f_r=lambda x: 1-0.5*(1-x)**2,
        f_g=lambda x: x,
        f_b=lambda x: x)
    gradient_pos = pyx.color.functiongradient_rgb( # white -> blue
        f_r=lambda x: 1-x,
        f_g=lambda x: 1-x,
        f_b=lambda x: 1-0.5*x**2)
    gradient_toolarge = pyx.color.rgb.black  # TODO: want to change this
    gradient_toosmall = pyx.color.rgb.white  # TODO: want to change this

    # define the coloraxes, keygraphs, density styles:
    cpd = dict()
    cpd["labeldist"] = 0.1 * unit.u_cm
    cpd["innerticklength"] = axis.painter.ticklength(0.2*unit.u_cm, 0.5)
    texter_pos = axis.texter.default(minusunity="-", plusunity="+")
    texter_neg = axis.texter.default(minusunity="-", plusunity="+")
    coloraxis_pos = axis.log   (min=databds_pos[0], max=databds_pos[1], title=None, painter=axis.painter.regular(**cpd), reverse=False, texter=texter_pos, density=5)
    coloraxis_neg = axis.neglog(min=databds_neg[0], max=databds_neg[1], title=None, painter=axis.painter.regular(**cpd), reverse=False, texter=texter_neg, density=5)
    keygraph_pos = graph.graphx(length=keyheight, size=keywidth, direction="vertical", x=coloraxis_pos)
    keygraph_neg = graph.graphx(length=keyheight, size=keywidth, direction="vertical", x=coloraxis_neg)
    keygraph_pos.axes["x2"] = axis.linkedaxis(keygraph_pos.axes["x"], painter=axis.painter.regular(innerticklength=None, labelattrs=None, titleattrs=None))
    keygraph_neg.axes["x2"] = axis.linkedaxis(keygraph_neg.axes["x"], painter=axis.painter.regular(innerticklength=None, labelattrs=None, titleattrs=None))
    density_pos = graph.style.density(coloraxis=coloraxis_pos, keygraph=keygraph_pos, gradient=gradient_pos)
    density_neg = graph.style.density(coloraxis=coloraxis_neg, keygraph=keygraph_neg, gradient=gradient_neg)

    # plot style:
    density_pos_neg = pyx.graph.style.density_posneglog(
        gradient_pos=gradient_pos, toosmall_pos=gradient_toosmall, toolarge_pos=gradient_toolarge, coloraxis_pos=coloraxis_pos, keygraph_pos=keygraph_pos,
        gradient_neg=gradient_neg, toosmall_neg=gradient_toosmall, toolarge_neg=gradient_toolarge, coloraxis_neg=coloraxis_neg, keygraph_neg=keygraph_neg)

    # plot:
    g = pyx.graph.graphxy(width=width, height=height,
        x=pyx.graph.axis.linear(title=r"$x$"),
        y=pyx.graph.axis.linear(title=r"$y$"),
    )
    g.plot(pyx.graph.data.points(datapts, x=1, y=2, color=3, title=None), [density_pos_neg])
    g.finish()

    # insert the keygraphs
    keygraph_neg.finish()
    keygraph_pos.finish()
    if True:
        g.insert(keygraph_pos, [trafo.translate(g.width + keydist, g.height - keyheight)])
        g.insert(keygraph_neg, [trafo.translate(g.width + keydist, 0)])

    return g


c = canvas.canvas()
c.insert(plot_xy_function())
c.insert(plot_color(), [trafo.translate(0, -15)])
c.writePDFfile()

