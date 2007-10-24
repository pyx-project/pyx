#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

from pyx import *

c = canvas.canvas()
text.set(mode="latex")
text.preamble(r"""%
    \usepackage{graphicx}
    \usepackage{color}
    \usepackage{rotating}
    \usepackage{helvet}
    \graphicspath{{eps/}}
%
    \definecolor{col0}{gray}{0.1}
    \definecolor{col1}{cmyk}{0.3, 0.2, 0.1, 0.1}
    \definecolor{col2}{rgb}{0.4, 0.3, 0.1}
    \definecolor{col3}{RGB}{200, 200, 200}
    \definecolor{col4}{hsb}{0.1, 0.1, 0.1}
    \definecolor{col5}{named}{Red}
    \definecolor{col6}{pyx}{pyx.color.cmyk.PineGreen}
    \definecolor{col7}{pyx}{color.cmyk(0.92, 0, 0.59, 0.25)}
    \definecolor{col0}{gray}{0.5}""")

c.stroke(path.line(-1, 0, 6, 0))

c.stroke(path.line(6, 5, 6.99, 5), [style.linewidth.THIN])
c.stroke(path.line(6, 6, 6.99, 6), [style.linewidth.THIN])
c.stroke(path.line(8.01, 5, 9, 5), [style.linewidth.THIN])
c.stroke(path.line(8.01, 6, 9, 6), [style.linewidth.THIN])
c.stroke(path.line(7, 4, 7, 4.99), [style.linewidth.THIN])
c.stroke(path.line(8, 4, 8, 4.99), [style.linewidth.THIN])
c.stroke(path.line(7, 6.01, 7, 7), [style.linewidth.THIN])
c.stroke(path.line(8, 6.01, 8, 7), [style.linewidth.THIN])
c.text(7, 5, "\\vrule width1truecm height1truecm")

c.text(6.2, 0, "0", [text.vshift.middlezero])
c.text(-1.2, 0, "abc", [text.vshift.mathaxis, text.halign.right])

t1 = text.text(0, 0, "a \PyXMarker{beforeb}b\PyXMarker{afterb} c d e f g h i j k l m n o p q r s t u v w x y z", [text.parbox(2, baseline=text.parbox.bottom)])
c.insert(t1)
c.stroke(t1.path())

t2 = c.insert(text.text(3, 0, "a \PyXMarker{beforeb}b\PyXMarker{afterb} c d e f g h i j k l m n o p q r s t u v w x y z", [text.parbox(2, baseline=text.parbox.top)]))
c.stroke(t2.path())
c.stroke(path.line(*(t1.marker("beforeb") + t2.marker("beforeb"))), [color.rgb.red])
c.stroke(path.line(*(t1.marker("afterb") + t2.marker("afterb"))), [color.rgb.green])

c.text(0, 3, r"\int\limits_{-\infty}^\infty \!{\rm d}x\, e^{-a x^2} = \sqrt{\pi\over a}", [text.mathmode])
c.text(0, 6, r"\int\limits_{-\infty}^\infty \!{\rm d}x\, e^{-a x^2} = \sqrt{\pi\over a}", [text.size.LARGE, text.mathmode])

c.stroke(c.text(1, 2, r"Hello, world!").path())

# test a virtual font with encoding
c.text(0, 8, r"\sffamily VF test: \"o\ss ffl \char0")
c.text(0, 9, r"\sffamily \fontsize{30}{35}\selectfont VF test: \"o\ss ffl \char0")

# scaling test
unit.set(xscale=2)
t = c.text(0, 11, r"scale test", [color.rgb.green])
unit.set(xscale=1)
t = c.text(0, 11, r"scale test", [color.rgb.red])

# test font stripping (proper usedchar selection)
from pyx.dvi import mapfile
fontmap = mapfile.readfontmap(["download35.map"])
c.text(0, 12, r"usechar test (``fl'' should be typed):")
myrunner = text.texrunner()
myrunner.preamble(r"\font\pyxfont=phvr8t\pyxfont")
c.insert(myrunner.text(5.5, 12, r"\char'035", fontmap=fontmap))

myrunner2 = text.texrunner()
myrunner2.preamble(r"\font\pyxfont=ptmr8t\pyxfont")
c.insert(myrunner2.text(6.5, 12, r"\char'035", fontmap=fontmap))

# test the specials
c.stroke(c.text(10, 2, r"Hello, \color{green}world!", [trafo.slant(1)]).path())
c.insert(c.text(10, 0, r"\begin{rotate}{90}\parbox{5cm}{rotated\\ in \LaTeX}\end{rotate}"))

d = canvas.canvas()
d.stroke(path.rect(0,0, 1,1))
d.stroke(path.line(0,0, 1,1))
d.stroke(path.line(1,0, 0,1))
d.writeEPSfile("eps/sample")
c.insert(c.text(10, 0, r"""
    \textcolor{col0}{col0}
    \textcolor{col1}{col1}
    \textcolor{col2}{col2}
    \textcolor{col3}{col3}
    \textcolor{col4}{col4}
    \textcolor{col5}{col5}
    \textcolor{col6}{col6}
    \textcolor{col7}{col7}%
    """, [text.parbox(3.5)]))
c.insert(c.text(15, 0, r"""
    \colorbox{col1}{ColorBox}\\
    \fcolorbox{col5}{col6}{FColorBox}"""))

c.text(4, 2, r"{\color[cmyk]{0.1,0.2,0.3,0.4}c\color[gray]{0.5}o\color[hsb]{0.2,0.3,0.4}l\color[rgb]{0.2,0.4,0.6}o\color[RGB]{100,200,50}r}s!")

c.writePDFfile("test_text", paperformat=document.paperformat.A4)

c.insert(c.text(10, 4, r"""%
    \fbox{\includegraphics[%
    %type=eps,             %% type of the file ... should not change anything --
                           %   BUG!!!!!!  size and filename information gets
                           %   wrong when this is used  ===> not supported!
    %command=...,          %% not supported!
    bb = 0 0 25 25,        %% bounding box in original size
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
    {sample}}"""))
c.writeEPSfile("test_text", paperformat=document.paperformat.A4)
