#!/usr/bin/env python

import sys; sys.path[:0]=[".."]
import pyx

tex = open("examples.tex", "w")
tex.write(r"""
\documentclass[abstracton]{scrreprt}
\usepackage{pyx,graphicx,scrpage,listings}
\lstloadlanguages{Python}
\lstset{language=Python}
\begin{document}
\subject{\texttt{http://pyx.sourceforge.net/}}
\title{\PyX{} %s\\Examples}
\author{J\"org Lehmann \texttt{<joergl@users.sourceforge.net>}\and
Andr\'e Wobst \texttt{<wobsta@users.sourceforge.net>}}
\maketitle
\begin{abstract}
This is an automatic generated document from the \PyX{} examples directory.
For each \PyX{} example file therein, its name, the source code and the
postscript output is shown. Please refere to source code comments within
the examples for further informations about the subject of each example.
\end{abstract}
""" % pyx.__version__)
for file in sys.argv[1:]:
    tex.write("\\deftripstyle{mypagestyle}{}{%s}{}{}{\\pagemark}{}\n" % file)
    tex.write("\\pagestyle{mypagestyle}{}\n")
    tex.write("\\section*{%s}\n" % file)
    tex.write("\\lstinputlisting{%s.py}\n" % file)
#    tex.write("\\begin{lstlisting}\n")
#    tex.writelines(open("%s.py" % file, "r").readlines())
#    tex.write("\\end{lstlisting}\n")
    tex.write("\\centerline{\\includegraphics{%s}}\n\\clearpage\n" % file)
tex.write("\\end{document}\n")

