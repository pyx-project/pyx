from pyx import *
c = canvas.canvas()
c.text(0, 0, r"Das ist eine Textausgabe mit \TeX.")
c.writeEPSfile("text")
