#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

from pyx import *
from pyx import text

c = canvas.canvas()
text.set(mode="latex")
text.preamble(r"""%
    \usepackage{graphicx}
    \usepackage{color}
    \usepackage{rotating}
%    \graphicspath{{eps/}}

    \definecolor{col0}{gray}{0.1}
    \definecolor{col1}{cmyk}{0.3, 0.2, 0.1, 0.1}
    \definecolor{col2}{rgb}{0.4, 0.3, 0.1}
    \definecolor{col3}{RGB}{200, 200, 200}
    \definecolor{col4}{hsb}{0.1, 0.1, 0.1}
    \definecolor{col5}{named}{Red}
%    \definecolor{col6}{pyx}{Some-PyX-Colour}
    \definecolor{col0}{gray}{0.5}""", text.texmessage.ignore)

c.stroke(path.line(-1, 0, 6, 0))

c.stroke(path.line(6, 5, 6.99, 5), canvas.linewidth.THIN)
c.stroke(path.line(6, 6, 6.99, 6), canvas.linewidth.THIN)
c.stroke(path.line(8.01, 5, 9, 5), canvas.linewidth.THIN)
c.stroke(path.line(8.01, 6, 9, 6), canvas.linewidth.THIN)
c.stroke(path.line(7, 4, 7, 4.99), canvas.linewidth.THIN)
c.stroke(path.line(8, 4, 8, 4.99), canvas.linewidth.THIN)
c.stroke(path.line(7, 6.01, 7, 7), canvas.linewidth.THIN)
c.stroke(path.line(8, 6.01, 8, 7), canvas.linewidth.THIN)
c.text(7, 5, "\\vrule width1truecm height1truecm")

c.text(6.2, 0, "0", text.vshift.middlezero)
c.text(-1.2, 0, "abc", text.vshift.mathaxis, text.halign.right)

t1 = text.text(0, 0, "a \PyXMarker{beforeb}b\PyXMarker{afterb} c d e f g h i j k l m n o p q r s t u v w x y z", text.parbox(2), text.valign.bottombaseline)
c.insert(t1)
c.stroke(t1.path())

t2 = c.insert(text.text(3, 0, "a \PyXMarker{beforeb}b\PyXMarker{afterb} c d e f g h i j k l m n o p q r s t u v w x y z", text.parbox(2)))
c.stroke(t2.path())
c.stroke(path.line(*(t1.marker("beforeb") + t2.marker("beforeb"))), color.rgb.red)
c.stroke(path.line(*(t1.marker("afterb") + t2.marker("afterb"))), color.rgb.green)

c.text(0, 3, r"\int\limits_{-\infty}^\infty \!{\rm d}x\, e^{-a x^2} = \sqrt{\pi\over a}", text.mathmode)
c.text(0, 6, r"\int\limits_{-\infty}^\infty \!{\rm d}x\, e^{-a x^2} = \sqrt{\pi\over a}", text.size.LARGE, text.mathmode)

c.stroke(c.text(1, 2, r"Hello, world!").path())

# test the specials
c.stroke(c.text(10, 2, r"Hello, \color{green}world!", trafo.slant(1)).path())
c.stroke(c.text(10, 0, r"\begin{rotate}{90}\parbox{5cm}{rotated\\ in \LaTeX}\end{rotate}"))

d = canvas.canvas()
d.stroke(path.rect(0,0, 1,1))
d.stroke(path.line(0,0, 1,1))
d.stroke(path.line(1,0, 0,1))
d.writetofile("sample")
c.stroke(c.text(10, 4, r"""%
    \fbox{\includegraphics[%
    %type=eps,             %% type of the file ... should not change anything --
                           %   BUG!!!!!!  size and filename information gets
                           %   wrong when this is used  ===> not supported!
    %command=...,          %% not supported!
    %bb = 0 0 20 20,        %% bounding box in original size
    hiresbb=,              %! read high resolution in original file (if not bb)
    %viewport= 0 0 15 15,   %% bounding box with respect to bb
    %trim=1 1 1 1,          %% correction of the bounding box with respect to bb
    width=1in,             %! final width
    height=2in,            %! final height
    %totalheight=3in,       %% final height+depth
    %keepaspectratio=,      %! keep aspect ratio, but do not exceed width nor height
    angle=30,              %! wraps around include
    origin=tr,             %% one or two chars of 'lrtcbB' (B for baseline)
    %scale=2,               %! wraps around rotating and include
    %draft=,               %% do not print anything,
    clip=]%                %! directly in dvi
    {sample}}""", text.texmessage.graphicsload))
c.stroke(c.text(10, 0, r"""
    \textcolor{col0}{abc}
    \textcolor{col1}{abc}
    \textcolor{col2}{abc}
    \textcolor{col3}{abc}
    \textcolor{col4}{abc}
    \textcolor{col5}{abc}
%    \textcolor{col6}{abc}%
    """, text.parbox(3)))
c.stroke(c.text(15, 0, r"""
    \colorbox{col2}{ColorBox}\\
    \fcolorbox{col3}{col4}{FColorBox}"""))

c.text(4, 2, r"{\color[cmyk]{0.1,0.2,0.3,0.4}c\color[gray]{0.5}o\color[hsb]{0.2,0.3,0.4}l\color[rgb]{0.2,0.4,0.6}o\color[RGB]{100,200,50}r}s!")

c.writetofile("test_text", paperformat="a4")
