#!/usr/bin/env python

import sys; sys.path[:0]=[".."]
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
\begin{abstract}
This is an automatic generated document from the \PyX{} examples directory. For
each \PyX{} example file its name, the source code and the postscript output is
shown. Please pay attention to source code comments within the examples for
further information.
\end{abstract}
""" % pyx.__version__)
for file in sys.argv[1:]:
    tex.write("\\deftripstyle{mypagestyle}{}{%s}{}{}{\\pagemark}{}\n" % file)
    tex.write("\\pagestyle{mypagestyle}{}\n")
    tex.write("\\section*{%s}\n" % file)
    tex.write("\\lstinputlisting{%s.py}\n" % file)
    tex.write("\\centerline{\\includegraphics{%s}}\n\\clearpage\n" % file)
tex.write("\\end{document}\n")

