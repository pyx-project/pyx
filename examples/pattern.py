from pyx import *

p = canvas.pattern()
t = text.texrunner()
p.settexrunner(t)
p.text(0, 0, r"\PyX")

text.set(mode="latex")
text.preamble(r"\usepackage{sizesub}", text.texmessage.ignore)
text.preamble(r"\usepackage[200]{sizedef}", text.texmessage.ignore)

c = canvas.canvas()
c.text(0, 0, r"\PyX", p)
c.writetofile("pattern", paperformat="a4")

