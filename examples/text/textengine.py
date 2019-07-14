from pyx import *

# Set properties of the defaulttextengine, e.g. switch to LaTeX.
text.set(text.LatexEngine)

c = canvas.canvas()
# The canvas, by default, uses the defaulttextengine from the text module.
# This can be changed by the canvas method settextengine.
c.text(0, 0, r"This is \LaTeX.")

# If you want to use another textengine temporarily, you can just insert
# a text box manually
plaintex = text.TexEngine() # plain TeX engine
c.insert(plaintex.text(0, -1, r"This is plain \TeX."))

# There also is the UnicodeEngine to output text directly without TeX/LaTeX.
unicodetext = text.UnicodeEngine() # unicode engine
c.insert(unicodetext.text(0, -2, "Simple unicode output without TeX/LaTeX."))

c.writeEPSfile("textengine")
c.writePDFfile("textengine")
c.writeSVGfile("textengine")
