import sys; sys.path[:0] = ["../.."]
from pyx import *

# text.set(texdebug="debug.tex", usefiles=["debug.dvi"])

t = r"""
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text

text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text

text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
%
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
%
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
%
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
%
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
%
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text

text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text

text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text

text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
text text text text text text text text text text text text
"""
s = r"""%
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\par
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\par
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\par
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\par
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
\display A-B\enddisplay
pg--\the\prevgraf--%
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\par
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
\display A-B\enddisplay
pg--\the\prevgraf--%
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\par
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
\display A-B\enddisplay
pg--\the\prevgraf--\tracingpages=2
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\par\tracingpages=0
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\par

\display A-B\enddisplay
pg--\the\prevgraf--%
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
\clubpenalty=500
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\par
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\par
Der Rabe Ralf rief schaurig ``Rah! Das End ist nah, das End ist nah!''\par
"""

c = canvas.canvas()
#shapes = [(8, 14), (11, 8), (8, 14), (11, 8), (8,14)]
shapes = [(10,7), (8,5)]*10
boxes = text.defaulttexrunner.textboxes(t, shapes)
y = 0
for i in range(len(boxes)):
    if i < len(shapes):
        shape = shapes[i]
    # else shape = shapes[-1] = last shape
    c.stroke(path.rect(0, y, shape[0], -shape[1]))
    c.stroke(boxes[i].bbox().path(), [trafo.translate(0, y), color.rgb.red])
    c.insert(boxes[i], [trafo.translate(0, y)])
    y -= shape[1] + 3
c.writeEPSfile("textboxes")

