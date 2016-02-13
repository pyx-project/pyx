from pyx import *

# Set properties of the defaulttexrunner, e.g. switch to LaTeX.
text.set(text.LatexRunner)

c = canvas.canvas()
# The canvas, by default, uses the default_runner from the text module.
# This can be changed by the canvas method settexrunner.
c.text(0, 0, r"This is \LaTeX.")

# If you want to use another texrunner temporarily, you can just insert
# a text box manually
plaintex = text.TexRunner() # plain TeX runner
c.insert(plaintex.text(0, -1, r"This is plain \TeX."))

c.writeEPSfile("texrunner")
c.writePDFfile("texrunner")
c.writeSVGfile("texrunner")
