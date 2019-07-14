from pyx import *

text.set(text.UnicodeEngine)

c = canvas.canvas()
c.text(0, 2, "Hello, world!")

# We support basic primitives for math typesetting of numbers.
c.text(0, 1, ["a large value: 10", text.Text("100", shift=0.5, scale=0.8)])
c.text(0, 0, ["a fraction: ", text.StackedText([text.Text("1", shift=0.3),
                                                text.Text("42", shift=-0.9)],
                                               frac=True, align=0.5)])

c.writeEPSfile()
c.writePDFfile()
c.writeSVGfile()
