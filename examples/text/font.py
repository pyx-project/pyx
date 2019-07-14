from pyx import *

text.set(text.LatexEngine)
text.preamble(r"\usepackage{times}")

c = canvas.canvas()
c.text(0, 0, r"\LaTeX{} doesn't need to look like \LaTeX{} all the time.")
c.writeEPSfile("font")
c.writePDFfile("font")
c.writeSVGfile("font")
