#!/usr/bin/env python

import sys; sys.path[:0]=[".."]
import os.path
import pyx

tex = open("examples.tex", "w")
tex.write(r"""
\documentclass[abstracton,a4paper]{scrreprt}
\areaset{17cm}{24cm}
\usepackage{pyx,graphicx,scrpage,listings,color}
\usepackage[latin1]{inputenc}
\lstloadlanguages{Python}
\lstset{language=Python,commentstyle={\itshape\lstset{columns=fullflexible}},extendedchars=true}
\begin{document}
\subject{\texttt{http://pyx.sourceforge.net/}}
\title{\PyX{} %s\\Examples}
\author{J\"org Lehmann \texttt{<joergl@users.sourceforge.net>}\and
Andr\'e Wobst \texttt{<wobsta@users.sourceforge.net>}}
\maketitle
""" % pyx.__version__)
lastdir = None
for file in sys.argv[1:]:
    dir = os.path.dirname(file)
    if dir != lastdir:
        try:
            tex.write("\\begin{abstract}\n%s\\end{abstract}\n" % open(os.path.join(dir, "README")).read().replace("__version__", pyx.__version__))
        except IOError:
            print "ignore missing README in %s" % dir
        lastdir = dir
    tex.write("\\deftripstyle{mypagestyle}{}{%s}{}{}{\\pagemark}{}\n" % file)
    tex.write("\\pagestyle{mypagestyle}{}\n")
    tex.write("\\section*{%s}\n" % file)
    tex.write("\\lstinputlisting{%s.py}\n" % file)
    tex.write("\\vspace{1cm}\n")
    tex.write("\\centerline{\\includegraphics{%s}}\n\\clearpage\n" % file)
tex.write("\\end{document}\n")

