from pyx import *

# set properties of the defaulttexrunner, e.g. switch to LaTeX
text.set(mode="latex")

c = canvas.canvas()
# the canvas, by default, uses the defaulttexrunner from the text module
# (this can be changed by the canvas settexrunner method)
c.text(0, 0, r"This is \LaTeX.")

# you can have several texrunners (several running TeX/LaTeX instances)
plaintex = text.texrunner()
c.insert(plaintex.text(0, -1, r"This is plain \TeX."))

c.writetofile("latex")
