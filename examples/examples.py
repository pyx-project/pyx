#!/usr/bin/env python

import sys; sys.path[:0]=[".."]
import pyx

tex = open("examples.tex", "w")
tex.write(r"""
\documentclass[abstracton]{scrreprt}
\usepackage{pyx,graphicx}
\begin{document}
\subject{\texttt{http://pyx.sourceforge.net/}}
\title{\PyX{} %s\\Examples}
\author{J\"org Lehmann \texttt{<joergl@users.sourceforge.net>}\and
Andr\'e Wobst \texttt{<wobsta@users.sourceforge.net>}}
\maketitle
""" % pyx.__version__)
for file in sys.argv[1:]:
    tex.write("\\section*{%s}\n" % file)
    tex.write("\\begin{verbatim}\n")
    tex.writelines(open("%s.py" % file, "r").readlines())
    tex.write("\\end{verbatim}\n")
    tex.write("\\centerline{\\includegraphics{%s}}\n\\clearpage\n" % file)
tex.write("\\end{document}\n")

