# There are nice packages to influence fonts in LaTeX. Let us use
# LaTeX and load some fancy fonts. You can also install your own
# Type1 fonts in your TeX/LaTeX system and they'll be immediately
# available for use in PyX as well.

from pyx import *

text.set(mode="latex")
text.preamble(r"\usepackage{palatino}")

c = canvas.canvas()
c.text(0, 0, r"\LaTeX{} doesn't need to look like \LaTeX{} all the time.")
c.writeEPSfile("font")
c.writePDFfile("font")
