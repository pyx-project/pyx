from pyx import *

c = canvas.canvas()
text.set(mode="latex",docopt="nomessages")
text.preamble(r"\usepackage{type1cm}\usepackage[12]{sizedef}\newcommand{\un}[1]{\ensuremath{\unskip\,\mathrm{#1}}}")
c.text(0, 0, r"Hello, world!")
c.stroke(path.line(0, 0, 2, 0))
c.writetofile("hello")
