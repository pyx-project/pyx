#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

from pyx import *
from pyx import text

c = canvas.canvas()
text.set(mode="latex", dvidebug=1, usefiles=("test_text.dvi","test_text.log"))
text.preamble(r"""%
    \makeatletter
    \let\saveProcessOptions=\ProcessOptions
    \def\ProcessOptions{%
      \saveProcessOptions
      \def\Gin@driver{../../contrib/pyx.def}%
      \def\c@lor@namefile{dvipsnam.def}}
    \makeatother
    \usepackage{graphicx}
    \usepackage{color}
    \usepackage{rotating}
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

t1 = text.text(0, 0, "a b c d e f g h i j k l m n o p q r s t u v w x y z", text.parbox(2), text.valign.bottombaseline)
c.insert(t1)
c.stroke(t1.path())

t2 = c.insert(text.text(3, 0, "a b c d e f g h i j k l m n o p q r s t u v w x y z", text.parbox(2)))
c.stroke(t2.path())

c.text(0, 3, r"\int\limits_{-\infty}^\infty \!{\rm d}x\, e^{-a x^2} = \sqrt{\pi\over a}", text.mathmode)
c.text(0, 6, r"\int\limits_{-\infty}^\infty \!{\rm d}x\, e^{-a x^2} = \sqrt{\pi\over a}", text.size.LARGE, text.mathmode)

c.stroke(c.text(1, 2, r"Hello, world!").path())
c.stroke(c.text(1, 2, r"Hello, \color{green}world!", trafo.slant(1)).path())
c.stroke(c.text(4, 0, r"\begin{rotate}{90}Rotated Text\end{rotate}"))

d = canvas.canvas()
d.stroke(path.rect(0,0, 1,1))
d.writetofile("sample")
#c.stroke(c.text(6, 0, r"""
#    \fbox{\includegraphics[%
#    bb = 0 0 130 130,
#    width=2.432cm,
#    height=4.976562cm,
#    totalheight=1.5cm,
#    angle=50,
#    origin=br,
#    type=eps,
#    trim=0 0 10.876 10.2348,
#    %command=ls sample.*, % not supported!
#    scale=5,
#    clip=]%
#    {sample.eps}}""", text.texmessage.graphicsload))
c.stroke(c.text(6, 0, r"""
    \fbox{\includegraphics[%
    width=2.432cm,
    height=4.976562cm,
    %type=eps,
    clip=]%
    {sample.eps}}""", text.texmessage.graphicsload))
c.stroke(c.text(10, 0, r"""
    \textcolor{col0}{abcdef}\\
    \textcolor{col1}{abcdef}\\
    \textcolor{col2}{abcdef}\\
    \textcolor{col3}{abcdef}\\
    \textcolor{col4}{abcdef}\\
    \textcolor{col5}{abcdef}\\
%    \textcolor{col6}{abcdef}%
    """))
c.stroke(c.text(15, 0, r"""
    \colorbox{col2}{ColorBox}\\
    \fcolorbox{col3}{col4}{FColorBox}"""))

c.text(4, 2, r"{\color[cmyk]{0.1,0.2,0.3,0.4}c\color[gray]{0.5}o\color[hsb]{0.2,0.3,0.4}l\color[rgb]{0.2,0.4,0.6}o\color[RGB]{100,200,50}r}s!")

c.writetofile("test_text", paperformat="a4")
