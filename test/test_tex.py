#!/usr/bin/env python 
import sys
sys.path.append("..")
from pyx import *

# c=canvas.canvas()
# t=c.insert(tex.tex())
t=tex.tex()

t.text(0, 0, "Hello, world!")
print "width of 'Hello, world!': ", t.textwd("Hello, world!")
print "height of 'Hello, world!': ", t.textht("Hello, world!")
print "depth of 'Hello, world!': ", t.textdp("Hello, world!")

t.writetofile("test_tex")

c=canvas.canvas()
t=c.insert(tex.tex(tex.mode.LaTeX))
c.draw(path.rect(0, 0, 22, 1))
t.text(0, 0, r"""\linewidth22cm\begin{itemize}
\item This is an example. This is an example. This is an example.
      This is an example. This is an example. This is an example.
      This is an example. This is an example. This is an example.
      This is an example. This is an example. This is an example.
\item This is an example. This is an example. This is an example.
      This is an example. This is an example. This is an example.
      This is an example. This is an example. This is an example.
      This is an example. This is an example. This is an example.
\end{itemize}""", tex.valign.bottom, tex.hsize(22))
c.writetofile("test_tex2")
